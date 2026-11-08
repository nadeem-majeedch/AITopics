# LF06 - The SFT loss and label masking {#lf06}

**Section path:** [Overview](index.md) · **Module 7** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours |
| **Hardware** | CPU-only |
| **Prerequisites** | [LF05](lf05-sft-data-and-templates.md) |
| **You will produce** | A verified shift-and-mask implementation and a loss comparison |


## Learning objectives

By the end of this lesson you can:

* shift labels correctly for next-token prediction
* mask prompt tokens so only the answer contributes to the loss
* handle padding and verify the mask with a hand-checked example

## The bug that looks like success

The notebook's first SFT run produced a loss of **0.02** and degenerate output:
the model repeated the prompt. The labels had not been shifted. At position `i`,
the model was asked to predict the token at `i`, which it had just received as
input. The task was copy the input, and the model got very good at it.

This is the most important debugging story in the section. A loss near zero is
not proof of learning; it is a reason to inspect the target.

## The correct alignment

For input tokens `t[0..n-1]`:

```text
input  = t[0], t[1], ..., t[n-2]
label  = t[1], t[2], ..., t[n-1]
```

Then mask positions that belong to the prompt:

```python
def sft_batch(tokens, prompt_length):
    input_ids = tokens[:-1]
    labels = tokens[1:].clone()
    keep_from = max(0, prompt_length - 1)
    labels[:keep_from] = -100
    return input_ids, labels
```

The `-100` positions are ignored by `cross_entropy(..., ignore_index=-100)`. If
`prompt_length` counts tokens up to and including the assistant marker, the first
assistant token is the first target to keep.

## Measured before and after

| Run | Answer loss | Exact-match accuracy | First-12 accuracy | Word F1 |
| --- | --- | --- | --- | --- |
| base model, no SFT | 1.039 | 0.688 | 0.411 | 0.087 |
| SFT, shifted + masked | 0.315 | 0.905 | 0.818 | 0.258 |

The answer loss is computed on assistant tokens only. The base model has a lower
answer loss than you might expect because it is a language model that has seen
similar text; it simply does not follow the template reliably. SFT improves exact
match and the stricter first-12 metric, and word F1 more than doubles.

Forgetting is also measured: loss on the original corpus rises from **0.885** to
**1.072**. Fine-tuning costs general language modelling performance. That is
expected; report it rather than hiding it.

## Beginner: why `-100`

PyTorch's cross-entropy accepts `ignore_index`, and `-100` is the conventional
value because it is not a valid token id. Masked positions contribute nothing to
the loss or the gradient. Use a boolean mask for clarity, then convert:

```python
loss = F.cross_entropy(logits.view(-1, vocab), labels.view(-1), ignore_index=-100)
```

## Intermediate: padding and batching

Conversations have different lengths. Pad to the longest sequence in the batch,
mask the padding in the loss, and use an attention mask so padding does not affect
the representations:

```python
labels[attention_mask == 0] = -100
```

If you pad on the left (common for generation), the position ids and the causal
mask must be consistent. Mixing left padding with right-shifted labels is a
classic source of silent errors.

## Advanced: what the loss does not measure

Answer loss measures token-level fit to the reference answer. It does not measure:

* factual correctness on questions with multiple valid answers;
* refusal behaviour on unsafe requests;
* robustness to paraphrases (the FAQ test split measures a little of this);
* verbosity or style drift.

The notebook therefore reports exact match, first-12 accuracy, and word F1
alongside loss. No single metric is the objective.

## Diagram: shift then mask

```mermaid
flowchart LR
    A[tokens] --> B[input = t:-1]
    A --> C[labels = t[1:]]
    C --> D[labels before assistant = -100]
    B --> E[model]
    D --> F[cross_entropy ignore_index=-100]
    E --> F
```

```text
tokens:   <u> Q </u> <a> A1 A2
input:    <u> Q </u> <a> A1
labels:   Q </u> <a> A1 A2
masked:  -100 -100 -100 A1 A2
```

## Practice

1. Remove the shift but keep the mask. Report the loss and a sample. Explain why
   the model copies.
2. Shift but do not mask. Report the fraction of loss contributed by prompt
   tokens.
3. Compute answer loss for the base and SFT models on the same 16 test pairs.
   Confirm the direction of the table.
4. Measure forgetting on a held-out corpus before and after SFT. Is the increase
   acceptable for your use case?

## Common mistakes

* **Computing loss on the prompt.**
* **Shifting after masking.** The first assistant token is dropped.
* **Using `-1` as the ignore index.** It is a valid index in some vocabularies.
* **Forgetting padding in the attention mask.**
* **Reporting only loss.** Pair it with a task metric.

## Knowledge checks

1. Why did the unshifted model's loss collapse to 0.02?
   *It was trained to copy its input, an easy task; the target was the input token
   itself.*
2. What does `ignore_index=-100` do?
   *Excludes those positions from the loss and gradient.*
3. Why does answer loss not fully measure assistant quality?
   *It measures token fit to one reference, not correctness, refusal, or
   robustness.*
4. What is catastrophic forgetting in this context?
   *The fine-tuned model loses general language-modelling ability; measured here as
   corpus loss rising from 0.885 to 1.072.*

## Lab connection

[Lab 2](labs/lab-2-sft-and-lora.md) requires a test that fails on unshifted labels.
The test should compare the label at position `i` with the input at `i+1`.

## Further reading

* Ouyang et al., *InstructGPT* (2022) - SFT followed by preference optimisation.
* Hugging Face, *TRL SFTTrainer* documentation - masking options in practice.
* Howard and Ruder, *Universal Language Model Fine-tuning* (2018) - discriminative
  fine-tuning and forgetting.

---

**Previous:** [LF05 - Instruction data and templates](lf05-sft-data-and-templates.md)
**Next:** [LF07 - Evaluating assistants](lf07-evaluating-assistants.md)
