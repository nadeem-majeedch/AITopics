"""Tests for the speech and audio section.

Every expected value here is either computed by hand in the test or a property that
must hold for any correct implementation (filterbank rows summing to one, a collapsed
CTC output, a gain-invariant fingerprint). Nothing asserts a number that was read off
a previous run, because that turns a test into a screenshot.

Run from the repository root:

    python -m unittest tests.test_speech_audio -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "projects" / "speech-audio"))

from speech_core import (  # noqa: E402
    asr,
    audio,
    datasets,
    evaluate,
    features,
    metrics,
    models,
    speaker,
    synth,
    text,
    training,
    tts,
)


class AudioIOTests(unittest.TestCase):
    def test_wav_round_trip_preserves_samples(self):
        samples = (0.5 * np.sin(2 * np.pi * 220 * np.linspace(0, 0.25, 4000))).astype(np.float32)
        with tempfile.TemporaryDirectory() as tmp:
            path = audio.write_wav(Path(tmp) / "tone.wav", samples, 16_000)
            back, rate = audio.read_wav(path)
        self.assertEqual(rate, 16_000)
        self.assertEqual(len(back), len(samples))
        # 16-bit storage quantises to 1/32767, and write/read differ by one step, so
        # the error bound is one and a half quantisation steps.
        self.assertLess(float(np.max(np.abs(back - samples))), 1.5 / 32767)

    def test_resample_halves_length_and_keeps_duration(self):
        samples = synth.tone(440.0, 0.2, 16_000)
        down = audio.resample(samples, 16_000, 8_000)
        self.assertEqual(len(down), 1600)
        self.assertAlmostEqual(len(down) / 8000.0, 0.2, places=2)

    def test_to_mono_averages_channels(self):
        stereo = np.array([[0.2, 0.4], [0.6, 0.8]], dtype=np.float32)
        mono = audio.to_mono(stereo)
        np.testing.assert_allclose(mono, [0.3, 0.7], atol=1e-6)

    def test_change_gain_minus_six_db_halves_amplitude(self):
        samples = np.full(100, 0.5, dtype=np.float32)
        quieter = audio.change_gain(samples, -6.0)
        self.assertAlmostEqual(float(quieter[0]), 0.5 * 10 ** (-6 / 20), places=3)

    def test_more_noise_means_lower_snr(self):
        clean = synth.tone(300.0, 0.3, 16_000)
        mild = audio.add_noise(clean, 30.0, seed=1)
        heavy = audio.add_noise(clean, 5.0, seed=1)
        self.assertGreater(audio.snr_between(clean, mild), audio.snr_between(clean, heavy))

    def test_trim_silence_removes_leading_zeros(self):
        samples = np.concatenate([np.zeros(800, dtype=np.float32), synth.tone(400.0, 0.1, 16_000)])
        trimmed = audio.trim_silence(samples, threshold=0.01, pad=0)
        self.assertLess(len(trimmed), len(samples))
        self.assertGreater(len(trimmed), 1000)

    def test_pad_or_trim_exact_length(self):
        self.assertEqual(len(audio.pad_or_trim(np.ones(50, dtype=np.float32), 80)), 80)
        self.assertEqual(len(audio.pad_or_trim(np.ones(120, dtype=np.float32), 80)), 80)

    def test_play_wav_never_raises_and_reports_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = audio.write_wav(Path(tmp) / "x.wav", np.zeros(1600, dtype=np.float32), 16_000)
            played, message = audio.play_wav(path)
        self.assertIsInstance(played, bool)
        self.assertIsInstance(message, str)
        self.assertTrue(message)


class FeatureTests(unittest.TestCase):
    def test_stft_bins_and_tone_position(self):
        # 16 kHz, n_fft 400 -> 40 Hz per bin; a 440 Hz tone peaks in bin 11.
        samples = synth.tone(440.0, 0.3, 16_000)
        spec = np.abs(features.stft(samples, n_fft=400, hop_length=160))
        self.assertEqual(spec.shape[1], 201)
        peak_bin = int(spec.mean(axis=0).argmax())
        self.assertEqual(peak_bin, 11)

    def test_mel_scale_round_trip(self):
        freqs = np.array([0.0, 100.0, 1000.0, 4000.0, 8000.0])
        np.testing.assert_allclose(features.mel_to_hz(features.hz_to_mel(freqs)), freqs, rtol=1e-9)

    def test_filterbank_rows_normalised(self):
        bank = features.mel_filterbank(16_000, 400, 40)
        self.assertEqual(bank.shape, (40, 201))
        np.testing.assert_allclose(bank.sum(axis=1), 1.0, atol=1e-5)
        self.assertTrue(np.all(bank >= 0))

    def test_band_frequencies_increasing_and_inside_nyquist(self):
        freqs = features.mel_band_frequencies(16_000, 40)
        self.assertEqual(len(freqs), 40)
        self.assertTrue(np.all(np.diff(freqs) > 0))
        self.assertGreater(freqs[0], 0.0)
        self.assertLess(freqs[-1], 8000.0)

    def test_power_to_db_has_zero_maximum(self):
        power = np.array([[1.0, 10.0], [100.0, 0.0]], dtype=np.float32)
        db = features.power_to_db(power, ref=float(power.max()), top_db=None)
        self.assertAlmostEqual(float(db.max()), 0.0, places=5)
        # power 1 against a reference of 100 is 10*log10(1/100) = -20 dB.
        self.assertAlmostEqual(float(db[0, 0]), -20.0, places=4)

    def test_mel_and_mfcc_shapes(self):
        samples = synth.speak("stop", datasets.voice_for(0), 16_000)
        mel = features.mel_spectrogram(samples, sample_rate=16_000, n_mels=40)
        mfcc = features.mfcc(samples, sample_rate=16_000, n_mfcc=13)
        self.assertEqual(mel.shape[1], 40)
        self.assertEqual(mfcc.shape, (mel.shape[0], 13))

    def test_dct_matrix_is_orthonormal(self):
        mat = features.dct_matrix(40, 13)
        product = mat @ mat.T
        np.testing.assert_allclose(product, np.eye(13), atol=1e-5)

    def test_deltas_keep_shape_and_zero_for_constant(self):
        constant = np.ones((20, 5), dtype=np.float32)
        deltas = features.deltas(constant)
        self.assertEqual(deltas.shape, constant.shape)
        np.testing.assert_allclose(deltas, 0.0, atol=1e-6)

    def test_ascii_spectrogram_line_count(self):
        mel = features.mel_spectrogram(synth.tone(300.0, 0.3), n_mels=40)
        art = features.ascii_spectrogram(mel, width=20, height=6)
        self.assertEqual(len(art.splitlines()), 6)
        self.assertTrue(all(len(line) == 20 for line in art.splitlines()))


class SynthAndDatasetTests(unittest.TestCase):
    def test_every_word_is_synthesised_from_known_phonemes(self):
        for word in synth.WORDS:
            for phoneme in synth.word_phonemes(word):
                self.assertIn(phoneme, synth.PHONEMES, msg=f"{word} uses unknown phoneme {phoneme}")

    def test_speak_is_bounded_and_audible(self):
        samples = synth.speak("start", datasets.voice_for(0), 16_000)
        self.assertLessEqual(float(np.max(np.abs(samples))), 1.0)
        self.assertGreater(audio.rms(samples), 0.005)
        self.assertTrue(0.15 < len(samples) / 16_000 < 0.8)

    def test_group_split_has_no_shared_sources(self):
        records = datasets.make_env_dataset(n_sources=5, variants_per_source=2, seed=3)
        splits = datasets.group_split(records, seed=0)
        train = {r.source_id for r in splits["train"]}
        val = {r.source_id for r in splits["val"]}
        test = {r.source_id for r in splits["test"]}
        self.assertFalse(train & val)
        self.assertFalse(train & test)
        self.assertFalse(val & test)
        # Four classes x five sources each, so twenty sources in total.
        self.assertEqual(len(train | val | test), 20)

    def test_random_split_shares_sources_and_audit_notices(self):
        records = datasets.make_env_dataset(n_sources=6, variants_per_source=3, seed=3)
        naive = datasets.random_split(records, seed=0)
        audit = datasets.audit_leakage(naive)
        self.assertGreater(audit["n_shared_sources"], 0)
        self.assertTrue(audit["leaky"])
        grouped = datasets.audit_leakage(datasets.group_split(records, seed=0))
        self.assertFalse(grouped["leaky"])

    def test_fingerprint_ignores_gain(self):
        samples = synth.env_sound("alarm", 0.8, 16_000, seed=7)
        louder = audio.change_gain(samples, 6.0)
        distance = datasets.hamming(datasets.fingerprint(samples), datasets.fingerprint(louder))
        self.assertLessEqual(distance, 4)

    def test_class_balance_counts_every_clip(self):
        records = datasets.make_speech_dataset(n_speakers=2, utterances_per_word=1, seed=5)
        balance = datasets.class_balance(records, datasets.WORDS)
        self.assertEqual(sum(balance.values()), len(records))
        self.assertEqual(balance["yes"], 2)

    def test_voice_profiles_are_distinct(self):
        pitches = [datasets.voice_for(i).f0 for i in range(24)]
        self.assertEqual(len(set(round(p, 3) for p in pitches)), 24)


class TextTests(unittest.TestCase):
    def test_substitution_and_insertion_counts(self):
        result = text.word_error_rate("a b c", "a x c d")
        self.assertEqual(result["substitutions"], 1)
        self.assertEqual(result["insertions"], 1)
        self.assertEqual(result["deletions"], 0)
        self.assertAlmostEqual(result["wer"], 2 / 3, places=6)

    def test_deletion_count(self):
        result = text.word_error_rate("start the engine now", "start engine now")
        self.assertEqual(result["deletions"], 1)
        self.assertAlmostEqual(result["wer"], 0.25, places=6)

    def test_corpus_wer_differs_from_mean_of_clips(self):
        pairs = [("a b c d", "a b c d"), ("yes", "no")]
        corpus = text.corpus_error_rates(pairs)
        mean_of_clips = np.mean([text.word_error_rate(r, h)["wer"] for r, h in pairs])
        self.assertAlmostEqual(corpus["wer"], 1 / 5, places=6)
        self.assertAlmostEqual(mean_of_clips, 0.5, places=6)
        self.assertNotAlmostEqual(corpus["wer"], mean_of_clips, places=3)

    def test_cer_counts_characters(self):
        # "start" -> "stat" drops the r: one deletion over five characters.
        result = text.character_error_rate("start", "stat")
        self.assertEqual(result["reference_chars"], 5)
        self.assertEqual(result["deletions"], 1)
        self.assertAlmostEqual(result["cer"], 0.2, places=6)

    def test_normalisation_removes_case_and_punctuation(self):
        self.assertEqual(text.normalize_text("Stop, LEFT!"), "stop left")

    def test_char_vocab_starts_with_blank_and_sorts(self):
        vocab = text.build_char_vocab(["stop", "yes"])
        self.assertEqual(vocab[0], "<blank>")
        self.assertEqual(vocab[1:], sorted(set("stop" + "yes")))

    def test_encode_decode_round_trip(self):
        vocab = text.build_char_vocab(["start"])
        encoded = text.encode_transcript("start", vocab)
        self.assertEqual(text.decode_indices(encoded, vocab), "start")


class MetricsTests(unittest.TestCase):
    def test_confusion_matrix_and_accuracy(self):
        report = metrics.classification_report([0, 0, 1, 1], [0, 1, 0, 1], ["a", "b"])
        self.assertEqual(report["accuracy"], 0.5)
        self.assertEqual(report["confusion_matrix"], [[1, 1], [1, 1]])
        self.assertAlmostEqual(report["per_class"]["a"]["recall"], 0.5, places=6)

    def test_verification_far_frr_by_hand(self):
        scores = [0.9, 0.8, 0.2, 0.1]
        same = [True, True, False, False]
        result = metrics.verification_metrics(scores, same, threshold=0.5)
        self.assertAlmostEqual(result["far"], 0.0, places=6)
        self.assertAlmostEqual(result["frr"], 0.0, places=6)
        result = metrics.verification_metrics(scores, same, threshold=0.85)
        self.assertAlmostEqual(result["frr"], 0.5, places=6)

    def test_equal_error_rate_is_zero_when_perfectly_separable(self):
        eer = metrics.equal_error_rate([0.99, 0.95, 0.1, 0.05], [True, True, False, False])
        self.assertLess(eer["eer"], 0.05)

    def test_ece_is_zero_for_perfectly_calibrated_bins(self):
        confidences = [0.5, 0.5, 0.5, 0.5]
        correct = [1, 0, 1, 0]
        self.assertAlmostEqual(metrics.expected_calibration_error(confidences, correct, n_bins=10), 0.0, places=6)

    def test_identification_rank1_counts_gallery_labels(self):
        gallery = np.array([[1.0, 0.0], [0.0, 1.0]])
        # The third probe is labelled "a" but points at the "b" gallery vector.
        probes = np.array([[0.9, 0.1], [0.2, 0.8], [0.2, 0.9]])
        result = metrics.identification_accuracy(probes, ["a", "b", "a"], gallery, ["a", "b"])
        self.assertAlmostEqual(result["rank1"], 2 / 3, places=6)


class DecodingTests(unittest.TestCase):
    def _peaked(self, indices: list[int], vocab: int = 4) -> np.ndarray:
        matrix = np.full((len(indices), vocab), -10.0, dtype=np.float64)
        for frame, index in enumerate(indices):
            matrix[frame, index] = 0.0
        return matrix

    def test_ctc_collapse_drops_blanks_and_repeats(self):
        vocab = ["<blank>", "a", "b"]
        # a a blank a b b -> "aab"
        matrix = self._peaked([1, 1, 0, 1, 2, 2], vocab=3)
        decoded, confidence = asr.ctc_greedy_decode(matrix, vocab)
        self.assertEqual(decoded, "aab")
        self.assertGreater(confidence, 0.9)

    def test_ctc_without_blank_cannot_repeat_letters(self):
        vocab = ["<blank>", "s", "t"]
        matrix = self._peaked([1, 1, 1, 2], vocab=3)
        self.assertEqual(asr.ctc_greedy_decode(matrix, vocab)[0], "st")

    def test_lexicon_snaps_near_miss(self):
        decision = asr.lexicon_decode("ys", ["yes", "no", "stop"])
        self.assertEqual(decision["text"], "yes")
        self.assertTrue(decision["applied"])

    def test_lexicon_leaves_distant_word_alone(self):
        decision = asr.lexicon_decode("banana", ["yes", "no", "stop"], max_ratio=0.2)
        self.assertEqual(decision["text"], "banana")
        self.assertFalse(decision["applied"])

    def test_frame_budget_error_is_explicit(self):
        record = datasets.AudioRecord(
            samples=synth.tone(200.0, 0.06, 16_000),
            sample_rate=16_000,
            label=0,
            source_id="tiny",
            meta={"transcript": "abcdefghijkl"},
        )
        model = models.TinyCRNN(vocab_size=14, stride_time=4)
        vocab = ["<blank>", *sorted(set("abcdefghijkl"))]
        with self.assertRaises(ValueError) as caught:
            training.train_ctc(model, [record], vocab, [record], epochs=1, log=False)
        self.assertIn("frames", str(caught.exception))


class RecogniserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = datasets.make_speech_dataset(n_speakers=6, utterances_per_word=1, seed=11)
        splits = datasets.group_split(cls.records, seed=0)
        cls.train, cls.val, cls.test = splits["train"], splits["val"], splits["test"]

    def test_save_and_load_round_trip(self):
        rec, _ = asr.Recognizer.train(self.train, self.val, epochs=1, seed=0, log=False)
        before = [row["text"] for row in rec.transcribe(self.test[:4])]
        with tempfile.TemporaryDirectory() as tmp:
            path = rec.save(Path(tmp) / "rec.pt")
            reloaded = asr.Recognizer.load(path)
        after = [row["text"] for row in reloaded.transcribe(self.test[:4])]
        self.assertEqual(before, after)
        self.assertAlmostEqual(reloaded.mean, rec.mean, places=6)
        self.assertEqual(reloaded.vocab, rec.vocab)

    def test_normalisation_stats_are_stored_and_used(self):
        # A recogniser trained on log-Mel values around -31 dB must remember that number:
        # applying different statistics at inference is the single most common silent bug
        # in audio pipelines, and it is invisible in a smoke test.
        rec, _ = asr.Recognizer.train(self.train, self.val, epochs=2, seed=0, log=False)
        self.assertNotAlmostEqual(rec.mean, 0.0, places=3)
        self.assertGreater(rec.std, 1.0)
        explicit = asr.transcribe_records(rec.model, self.test, rec.vocab, mean=rec.mean, std=rec.std)
        wrapped = rec.transcribe(self.test)
        self.assertEqual([r["text"] for r in wrapped], [r["text"] for r in explicit])
        self.assertEqual([r["confidence"] for r in wrapped], [r["confidence"] for r in explicit])

    def test_freeze_reduces_trainable_parameters(self):
        model = models.TinyCRNN(vocab_size=5)
        total = models.count_parameters(model)
        frozen = asr.freeze_feature_extractor(model)
        self.assertGreater(frozen, 0)
        self.assertEqual(models.count_parameters(model), total - frozen)


class SpeakerTests(unittest.TestCase):
    def test_cosine_similarity_of_identical_vectors(self):
        vector = np.array([1.0, 2.0, 3.0])
        self.assertAlmostEqual(speaker.cosine_similarity(vector, vector), 1.0, places=9)

    def test_kmeans_separates_two_clusters(self):
        cluster_a = np.random.default_rng(0).normal(0.0, 0.05, size=(20, 4))
        cluster_b = np.random.default_rng(1).normal(5.0, 0.05, size=(20, 4))
        matrix = np.vstack([cluster_a, cluster_b]).astype(np.float32)
        labels, centres = speaker.kmeans(matrix, 2, seed=0)
        self.assertEqual(len({int(v) for v in labels[:20]}), 1)
        self.assertEqual(len({int(v) for v in labels[20:]}), 1)
        self.assertNotEqual(labels[0], labels[-1])
        self.assertEqual(centres.shape, (2, 4))

    def test_merge_segments_joins_same_speaker(self):
        segments = [speaker.Segment(0.0, 0.2, 0), speaker.Segment(0.22, 0.4, 0), speaker.Segment(0.5, 0.7, 1)]
        merged = speaker.merge_segments(segments, max_gap=0.05)
        self.assertEqual(len(merged), 2)
        self.assertAlmostEqual(merged[0].end, 0.4, places=6)

    def test_perfect_diarization_has_zero_error(self):
        truth = [{"start": 0.0, "end": 0.5, "speaker": "a"}, {"start": 0.5, "end": 1.0, "speaker": "b"}]
        predicted = [speaker.Segment(0.0, 0.5, 0), speaker.Segment(0.5, 1.0, 1)]
        self.assertAlmostEqual(speaker.diarization_error_rate(predicted, truth)["der"], 0.0, places=6)

    def test_no_prediction_is_total_miss(self):
        truth = [{"start": 0.0, "end": 0.5, "speaker": "a"}]
        self.assertAlmostEqual(speaker.diarization_error_rate([], truth)["der"], 1.0, places=6)


class SynthesisTests(unittest.TestCase):
    def test_in_vocabulary_text_is_spoken(self):
        engine = tts.FormantTTS(voice_index=0)
        result = engine.synthesize("start left")
        self.assertTrue(result.in_vocabulary)
        self.assertEqual(len(result.samples) > 2000, True)
        self.assertAlmostEqual(len(result.samples) / result.sample_rate, result.duration, places=6)

    def test_out_of_vocabulary_text_is_spelled_and_flagged(self):
        engine = tts.FormantTTS(voice_index=0)
        result = engine.synthesize("banana")
        self.assertFalse(result.in_vocabulary)
        self.assertIn("banana", result.note)
        self.assertGreater(len(result.samples), 1000)

    def test_neural_tts_report_is_a_tuple(self):
        available, reason = tts.neural_tts_available()
        self.assertIsInstance(available, bool)
        self.assertTrue(reason)


class EvaluationTests(unittest.TestCase):
    def test_clean_condition_is_identity(self):
        records = datasets.make_env_dataset(n_sources=1, variants_per_source=1, seed=4)
        clean = next(c for c in evaluate.CONDITIONS if c.name == "clean")
        perturbed = evaluate.apply_condition(records, clean)
        np.testing.assert_allclose(perturbed[0].samples, records[0].samples)

    def test_resampled_condition_changes_bandwidth_not_length(self):
        records = datasets.make_speech_dataset(n_speakers=1, utterances_per_word=1, seed=6)
        condition = next(c for c in evaluate.CONDITIONS if c.name == "narrowband_4khz")
        perturbed = evaluate.apply_condition(records, condition)
        self.assertAlmostEqual(len(perturbed[0].samples) / records[0].sample_rate, records[0].duration, delta=0.02)

    def test_lexicon_ablation_reports_both_sides(self):
        pairs = [("yes", "ys"), ("no", "no")]
        result = evaluate.lexicon_ablation(pairs, ["yes", "no", "stop"])
        self.assertAlmostEqual(result["wer_before"], 0.5, places=6)
        self.assertAlmostEqual(result["wer_after"], 0.0, places=6)
        self.assertEqual(result["utterances_changed"], 1)


if __name__ == "__main__":
    unittest.main()
