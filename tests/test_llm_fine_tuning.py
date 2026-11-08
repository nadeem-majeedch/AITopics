"""Tests for the shared M06-M08 package.

These cover the invariants the lessons rely on: tokenizers round-trip, the causal
mask hides the future, prompt masking excludes the question from the loss, LoRA
merging is functionally identical, and weight-only quantization stays within one
quantization step.

Run from the repository root:

    python -m unittest tests.test_llm_fine_tuning -v
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "projects" / "llm-fine-tuning"))

import llm_core as lc  # noqa: E402

SMALL_TEXT = "The fox found a silver key near the river. The baker carried a red scarf."


def small_model(vocab_size: int = 32):
    return lc.build_model(vocab_size, seed=0, block_size=16, n_layer=1, n_head=2, n_embd=16, dropout=0.0)


class TokenizerTests(unittest.TestCase):
    def test_char_roundtrip_and_vocab(self) -> None:
        tokenizer = lc.CharTokenizer.from_text(SMALL_TEXT)
        ids = tokenizer.encode(SMALL_TEXT)
        self.assertEqual(tokenizer.decode(ids), SMALL_TEXT)
        self.assertEqual(ids[0], tokenizer.stoi["T"])
        self.assertGreaterEqual(len(tokenizer), len(set(SMALL_TEXT)) + 2)

    def test_char_unknown_character_is_mapped_not_crashing(self) -> None:
        tokenizer = lc.CharTokenizer.from_text("abc")
        ids = tokenizer.encode("abz")
        self.assertEqual(ids[-1], tokenizer.unk_id)
        self.assertIn("?", tokenizer.decode(ids))

    def test_word_roundtrip_keeps_punctuation(self) -> None:
        tokenizer = lc.WordTokenizer.from_text("Hello, world. Hello there!", min_count=1, lowercase=False)
        text = "Hello, world."
        self.assertEqual(tokenizer.decode(tokenizer.encode(text)), text)
        self.assertLess(len(tokenizer.encode(text)), len(text))

    def test_bpe_roundtrip_and_compression(self) -> None:
        text = "the old boatman carried a folded map near the river. " * 8
        tokenizer = lc.BPETokenizer.train(text, vocab_size=280)
        ids = tokenizer.encode(text)
        self.assertEqual(tokenizer.decode(ids), text)
        self.assertLess(len(ids), len(text.encode("utf-8")))
        self.assertGreater(len(tokenizer.merges), 10)

    def test_tokenizer_report_shape(self) -> None:
        tokenizer = lc.CharTokenizer.from_text(SMALL_TEXT)
        report = lc.tokenizer_report(tokenizer, SMALL_TEXT)
        self.assertEqual(report["characters"], len(SMALL_TEXT))
        self.assertEqual(report["tokens"], len(SMALL_TEXT))
        self.assertIn("chars_per_token", report)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = lc.ensure_datasets()

    def test_manifest_matches_generator(self) -> None:
        files = lc.manifest()["files"]
        self.assertEqual(files["tickets_clean.csv"]["rows"], 600)
        self.assertEqual(files["tickets_messy.csv"]["rows"], 650)
        self.assertEqual(files["faq_pairs.csv"]["rows"], 152)
        self.assertIn("tiny_corpus.txt", files)

    def test_faq_splits_are_disjoint_by_question(self) -> None:
        train = {row["question"] for row in lc.load_faq("train")}
        test = {row["question"] for row in lc.load_faq("test")}
        self.assertTrue(train.isdisjoint(test))
        self.assertEqual(len(lc.load_faq("train")), 120)
        self.assertEqual(len(lc.load_faq("validation")), 16)
        self.assertEqual(len(lc.load_faq("test")), 16)

    def test_corpus_has_sentences(self) -> None:
        sentences = lc.corpus_sentences()
        self.assertGreater(len(sentences), 500)
        self.assertTrue(all(sentence.endswith(".") for sentence in sentences))

    def test_messy_tickets_keep_the_planted_defects(self) -> None:
        messy = lc.load_tickets(messy=True)
        labels = {row["label"] for row in messy}
        self.assertIn("Tech ", labels)
        self.assertGreater(len(messy), 600)


class ModelTests(unittest.TestCase):
    def test_forward_shapes_and_loss(self) -> None:
        model = small_model()
        x = torch.randint(0, 32, (2, 8))
        logits, loss = model(x, x)
        self.assertEqual(tuple(logits.shape), (2, 8, 32))
        self.assertIsNotNone(loss)
        self.assertTrue(torch.isfinite(loss))

    def test_future_tokens_cannot_change_past_logits(self) -> None:
        model = small_model().eval()
        x = torch.randint(0, 32, (1, 8))
        altered = x.clone()
        altered[0, -1] = (altered[0, -1] + 5) % 32
        with torch.no_grad():
            first, _ = model(x)
            second, _ = model(altered)
        self.assertTrue(torch.allclose(first[:, :-1], second[:, :-1], atol=1e-6))
        self.assertFalse(torch.allclose(first[:, -1], second[:, -1], atol=1e-6))

    def test_greedy_generation_is_deterministic(self) -> None:
        model = small_model()
        idx = torch.tensor([[1, 2, 3]])
        a = model.generate(idx, 6, temperature=0.0)
        b = model.generate(idx, 6, temperature=0.0)
        self.assertTrue(torch.equal(a, b))
        self.assertEqual(a.shape[1], 9)

    def test_parameter_accounting_matches_float_bytes(self) -> None:
        model = small_model()
        self.assertEqual(model.param_bytes(4), model.parameter_count() * 4)
        self.assertGreater(model.parameter_count(), 0)


class TrainingTests(unittest.TestCase):
    def test_train_lm_reports_measured_history(self) -> None:
        tokenizer = lc.CharTokenizer.from_text(SMALL_TEXT * 4)
        ids = tokenizer.encode(SMALL_TEXT * 4)
        model = lc.build_model(len(tokenizer), seed=0, block_size=8, n_layer=1, n_head=2, n_embd=16, dropout=0.0)
        history = lc.train_lm(model, ids, steps=4, batch_size=2, block_size=8, log_every=1, warmup=1)
        summary = history.summary()
        self.assertEqual(summary["steps"], 4)
        self.assertEqual(summary["tokens"], 4 * 2 * 8)
        self.assertGreater(history.seconds, 0.0)
        self.assertTrue(all(loss == loss for loss in history.losses))

    def test_schedule_warms_up_then_decays(self) -> None:
        self.assertAlmostEqual(lc.lr_at(0, 100, 1.0, warmup=10), 0.1)
        self.assertAlmostEqual(lc.lr_at(9, 100, 1.0, warmup=10), 1.0)
        self.assertAlmostEqual(lc.lr_at(99, 100, 1.0, warmup=10), 0.1, places=2)
        self.assertGreater(lc.lr_at(20, 100, 1.0, warmup=10), lc.lr_at(80, 100, 1.0, warmup=10))

    def test_estimate_loss_accepts_a_token_list(self) -> None:
        ids = (torch.arange(200) % 30).tolist()
        model = small_model(30)
        loss = lc.estimate_loss(model, ids, batch_size=2, block_size=8, batches=2)
        self.assertTrue(loss == loss)

    def test_estimate_loss_is_deterministic(self) -> None:
        ids = torch.arange(200) % 30
        model = small_model(30)
        first = lc.estimate_loss(model, ids, batch_size=2, block_size=8, batches=3)
        second = lc.estimate_loss(model, ids, batch_size=2, block_size=8, batches=3)
        self.assertAlmostEqual(first, second, places=6)


class SFTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pairs = lc.load_faq("train")[:6]
        text = " ".join(pair["question"] + " " + pair["answer"] for pair in cls.pairs)
        cls.tokenizer = lc.CharTokenizer.from_text(text + "User: Assistant:\n")
        cls.examples = lc.build_examples(cls.pairs, cls.tokenizer, block_size=192)

    def test_prompt_tokens_are_masked(self) -> None:
        example = self.examples[0]
        self.assertEqual(len(example.input_ids), len(example.labels))
        self.assertTrue(all(label == -100 for label in example.labels[: example.prompt_tokens - 1]))
        self.assertNotEqual(example.labels[example.prompt_tokens - 1], -100)
        self.assertTrue(all(label != -100 for label in example.labels[example.prompt_tokens - 1 :]))
        self.assertGreater(example.answer_tokens, 0)

    def test_labels_are_shifted_by_one(self) -> None:
        for example in self.examples:
            for index, label in enumerate(example.labels[:-1]):
                if label != -100:
                    self.assertEqual(label, example.input_ids[index + 1])
            self.assertEqual(len(example.input_ids), len(example.labels))
            self.assertNotEqual(example.labels[-1], -100)

    def test_prompt_fraction_is_a_ratio(self) -> None:
        fraction = lc.prompt_fraction(self.examples)
        self.assertGreater(fraction, 0.0)
        self.assertLess(fraction, 1.0)

    def test_long_prompt_is_bounded_and_flagged(self) -> None:
        example = lc.build_example("ticket detail " * 200, "A short reply.", self.tokenizer, block_size=64)
        self.assertLessEqual(len(example.input_ids), 64)
        self.assertGreater(example.answer_tokens, 0)
        self.assertTrue(example.prompt_truncated)

    def test_normal_example_is_not_flagged_as_truncated(self) -> None:
        example = lc.build_example("Is installation included?", "Yes, installation is included.", self.tokenizer, block_size=192)
        self.assertFalse(example.prompt_truncated)
        self.assertFalse(example.answer_truncated)

    def test_collate_pads_without_training_on_padding(self) -> None:
        generator = torch.Generator().manual_seed(0)
        x, y = lc.collate(self.examples, batch_size=4, pad_id=self.tokenizer.pad_id, generator=generator)
        self.assertEqual(tuple(x.shape), tuple(y.shape))
        padded = x == self.tokenizer.pad_id
        self.assertTrue(torch.all(y[padded] == -100))
        self.assertGreater(int((y != -100).sum()), 0)

    def test_train_sft_runs_and_stays_finite(self) -> None:
        model = lc.build_model(len(self.tokenizer), seed=0, block_size=192, n_layer=1, n_head=2, n_embd=16, dropout=0.0)
        history = lc.train_sft(
            model,
            self.examples,
            steps=3,
            batch_size=2,
            pad_id=self.tokenizer.pad_id,
            log_every=1,
            warmup=1,
        )
        self.assertEqual(len(history.losses), 3)
        self.assertTrue(all(loss == loss for loss in history.losses))
        generated = lc.generate_text(model, self.tokenizer, lc.format_prompt("Is installation included?"), max_new_tokens=5)
        self.assertIsInstance(generated, str)


class GenerationEvaluationTests(unittest.TestCase):
    def test_generation_report_separates_exact_match_from_empty_output(self) -> None:
        report = lc.generation_report(["Yes.", "", "the the the the"], ["Yes.", "No.", "a useful reply"])
        self.assertEqual(report["n"], 3)
        self.assertAlmostEqual(report["exact_match"], 1 / 3, places=4)
        self.assertAlmostEqual(report["empty_rate"], 1 / 3, places=4)
        self.assertGreater(report["mean_repetition_3"], 0.0)

    def test_generate_answer_passes_newline_as_a_stop_token(self) -> None:
        tokenizer = lc.CharTokenizer.from_text("abc\n")

        class RecordingModel:
            def __init__(self) -> None:
                self.stop_ids = ()

            def generate(self, idx, max_new_tokens, *, stop_ids=(), **kwargs):
                self.stop_ids = stop_ids
                return idx

        model = RecordingModel()
        answer = lc.generate_answer(model, tokenizer, "a")
        self.assertEqual(answer, "")
        self.assertIn(tokenizer.stoi["\n"], model.stop_ids)


class LoRATests(unittest.TestCase):
    def test_adapters_start_as_no_ops_and_only_lora_trains(self) -> None:
        model = small_model().eval()
        x = torch.randint(0, 32, (1, 8))
        with torch.no_grad():
            before, _ = model(x)
        report = lc.apply_lora(model, rank=2, alpha=4.0)
        with torch.no_grad():
            after, _ = model(x)
        self.assertTrue(torch.allclose(before, after, atol=1e-7))
        self.assertGreater(len(report["replaced"]), 0)
        self.assertLess(report["trainable_fraction"], 0.2)
        self.assertTrue(all(p.requires_grad == ("lora_" in name) for name, p in model.named_parameters()))

    def test_merge_reproduces_the_adapted_model(self) -> None:
        model = small_model().eval()
        lc.apply_lora(model, rank=2, alpha=8.0)
        with torch.no_grad():
            for name, module in model.named_modules():
                if isinstance(module, lc.LoRALinear):
                    module.lora_B.weight.normal_(0.0, 0.05)
        x = torch.randint(0, 32, (2, 8))
        with torch.no_grad():
            adapted, _ = model(x)
        merged_copy = copy.deepcopy(model)
        merged_count = lc.merge_lora(merged_copy)
        with torch.no_grad():
            merged, _ = merged_copy(x)
        self.assertGreater(merged_count, 0)
        self.assertTrue(torch.allclose(adapted, merged, atol=1e-5))
        self.assertEqual(lc.lora_bytes(model), sum(t.numel() * t.element_size() for t in lc.lora_state_dict(model).values()))


class QuantizationTests(unittest.TestCase):
    def test_quantize_tensor_stays_on_the_grid(self) -> None:
        torch.manual_seed(0)
        weight = torch.randn(6, 5)
        quantized, scale = lc.quantize_tensor(weight, bits=8)
        restored = lc.dequantize_tensor(quantized, scale)
        self.assertEqual(quantized.dtype, torch.int8)
        self.assertTrue(torch.all((restored - weight).abs() <= scale.max() / 2 + 1e-6))

    def test_report_and_compression(self) -> None:
        state = small_model().state_dict()
        original = state["blocks.0.attn.c_attn.weight"].clone()
        restored_state, report = lc.quantize_state_dict(state, bits=8)
        self.assertGreater(report["compression_ratio"], 1.5)
        self.assertGreater(report["max_abs_error"], 0.0)
        self.assertTrue(torch.equal(state["blocks.0.attn.c_attn.weight"], original))
        self.assertLessEqual(report["max_abs_error"], 0.02)

    def test_four_bits_are_less_accurate_than_eight(self) -> None:
        state = small_model().state_dict()
        _, eight = lc.quantize_state_dict(state, bits=8)
        _, four = lc.quantize_state_dict(state, bits=4)
        self.assertGreaterEqual(four["max_abs_error"], eight["max_abs_error"])
        self.assertGreater(four["compression_ratio"], eight["compression_ratio"])

    def test_quantized_copy_mostly_agrees(self) -> None:
        model = small_model().eval()
        clone, report = lc.quantized_copy(model, bits=8)
        x = torch.randint(0, 32, (2, 8))
        with torch.no_grad():
            logits_a, _ = model(x)
            logits_b, _ = clone(x)
        self.assertGreater(lc.top1_agreement(logits_a, logits_b), 0.8)
        self.assertIsInstance(report["quantized_bytes"], int)


class EvaluateTests(unittest.TestCase):
    def test_word_f1_endpoints(self) -> None:
        self.assertAlmostEqual(lc.word_f1("a red scarf", "A red scarf."), 1.0)
        self.assertEqual(lc.word_f1("completely unrelated", "a red scarf"), 0.0)
        self.assertAlmostEqual(lc.word_f1("red scarf", "a red scarf"), 2 * 1.0 * (2 / 3) / (1 + 2 / 3))

    def test_exact_match_ignores_case_and_punctuation(self) -> None:
        self.assertEqual(lc.exact_match("Yes, we do!", "yes we do"), 1.0)

    def test_perplexity_and_bits(self) -> None:
        self.assertAlmostEqual(lc.perplexity(0.0), 1.0)
        self.assertAlmostEqual(lc.bits_per_token(0.69314718056), 1.0, places=6)

    def test_distinct_n_and_repetition(self) -> None:
        self.assertAlmostEqual(lc.distinct_n(["a b c d"], n=2), 1.0)
        self.assertLess(lc.distinct_n(["a b a b a b"], n=2), 0.5)
        self.assertGreater(lc.repetition_rate("a b c a b c a b c"), 0.0)

    def test_table_contains_every_column(self) -> None:
        text = lc.format_table([{"a": 1, "b": "x"}], ["a", "b"])
        self.assertIn("a", text)
        self.assertIn("x", text)


if __name__ == "__main__":
    unittest.main()
