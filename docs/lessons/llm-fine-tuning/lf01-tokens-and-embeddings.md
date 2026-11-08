# LF01 - Tokens, vocabulary, and embeddings {#lf01}

**Section path:** [Overview](index.md) · **Module 6** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours |
| **Hardware** | CPU-only |
| **Prerequisites** | [MT01](../model-training/mt01-training-loop.md), basic linear algebra |
| **You will produce** | A tokenizer comparison and a trained embedding table |


## Learning objectives

By the end of this lesson you can:

* explain why a language model sees token IDs rather than text
* implement a vocabulary, encoder, and decoder and handle unknown tokens
* describe what an embedding matrix learns and why its shape matters

## The model never sees text

A language model sees integer token ids. Tokenization decides what counts as a
unit, and that decision propagates through context length, vocabulary size, loss,
and generation quality.

| Tokenizer | Unit | Vocabulary | `"unbelievable"` becomes |
| --- | --- | --- | --- |
| character | one character | about 70 | `u n b e l i e v a b l e` |
| word | whitespace word | grows with corpus | `unbelievable` or `<unk>` |
| byte-pair (BPE) | merged subwords | fixed, e.g. 512 | `un bel iev able` |

The notebook implements all three in `llm_core.tokenizer`. The tiny model uses a
character tokenizer: the vocabulary is small, every string is representable, and
sequences are long. That is a teaching trade-off, not a recommendation for
production.

## Beginner: special tokens

Every tokenizer needs at least:

* `<pad>` - fills a batch to equal length; masked out of the loss;
* `<bos>` / `<eos>` - start and end of a sequence;
* `<unk>` - unknown token (word-level only; byte/character tokenizers do not need
  it).

Special tokens occupy ids. If you add a token after training, the embedding matrix
must grow and the new row starts random. Adding tokens invalidates a checkpoint
unless you resize and fine-tune the embeddings.

## Intermediate: BPE in one paragraph

Byte-pair encoding starts with bytes or characters and repeatedly merges the most
frequent adjacent pair. The merge list is the tokenizer. At encode time, the same
merges are applied greedily. Frequent words become one token; rare words remain
several. This gives a fixed vocabulary and no unknown tokens for arbitrary text.

```python
class BPE:
    def __init__(self, merges):
        self.merges = merges           # ordered list of (left, right)
        self.vocab = {i: bytes([i]) for i in range(256)}

    def encode(self, text: str) -> list[int]:
        tokens = list(text.encode("utf-8"))
        for left, right in self.merges:
            merged, out, i = left + right, [], 0
            while i < len(tokens):
                if i + 1 < len(tokens) and tokens[i] == left and tokens[i + 1] == right:
                    out.append(merged); i += 2
                else:
                    out.append(tokens[i]); i += 1
            tokens = out
        return tokens
```

Expected behaviour: the sequence length falls as merges are learned, and decoding
`encode(text)` returns the original bytes exactly.

## Advanced: embeddings are learned coordinates

An embedding table maps each id to a vector. Training moves vectors so that tokens
used in similar contexts become similar. The table is not a semantic dictionary:
"similar" means "predictive of the same neighbours", which can encode sentiment,
topic, and also bias.

The notebook's model ties the output projection to the embedding matrix or keeps
them separate? The tiny model uses a separate output head, which is simpler to
reason about. Tying saves parameters (vocabulary × width) and often helps small
models; untied heads are easier to inspect.

## Diagram: text to logits

```mermaid
flowchart LR
    A[Text] --> B[Tokenizer]
    B --> C[Token ids]
    C --> D[Embedding table]
    D --> E[Position information]
    E --> F[Transformer blocks]
    F --> G[Output head]
    G --> H[Next-token logits]
```

## Practice

1. Tokenize the FAQ corpus with all three tokenizers. Report the average tokens per
   character and the vocabulary size for each.
2. Add a new special token to a trained character model. What happens to the loss
   on the first batch, and why?
3. Train a BPE tokenizer with 256 merges. Compare its compression ratio with the
   character tokenizer on the same corpus.
4. Inspect the nearest neighbours of five embedding vectors. Are they semantic,
   syntactic, or both?

## Common mistakes

* **Changing the tokenizer without retraining the model.**
* **Forgetting to mask padding in the loss.** The model learns to predict `<pad>`.
* **Assuming a larger vocabulary is always better.** It grows the embedding and
  output matrices.
* **Using word tokenization on noisy text without an `<unk>` strategy.**
* **Counting characters and tokens interchangeably when estimating context.**

## Knowledge checks

1. Why does a character tokenizer avoid unknown tokens?
   *Every character has an id, and any Unicode string can be decomposed; the
   vocabulary is fixed and complete for the encoding.*
2. What is the cost of a character tokenizer?
   *Longer sequences for the same text, which costs attention compute and context
   length.*
3. What does an embedding vector represent?
   *A learned coordinate that helps predict context; similarity is predictive, not
   a definition.*
4. Why must special tokens be reserved before training?
   *Their ids must exist in the embedding table; adding them later changes the
   checkpoint's shape.*

## Lab connection

[Lab 1](labs/lab-1-tiny-lm.md) asks you to train a tiny language model and report
its tokenizer's compression ratio. Use `llm_core.tokenizer` rather than writing a
fourth implementation.

## Further reading

* Sennrich et al., *Neural Machine Translation of Rare Words with Subword Units*
  (2016).
* Kudo and Richardson, *SentencePiece* (2018).
* OpenAI, *Tokenizer* documentation - byte-level BPE in practice.

---

**Previous:** [MT10 - Dataset cards](../model-training/mt10-dataset-cards.md)
**Next:** [LF02 - Attention](lf02-attention.md)
