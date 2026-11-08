# Transformers and small language models (M06-M08)

This section builds a language model from tokens to a served adapter. The scale is
deliberately small: a 239,040-parameter transformer that trains in under 30 seconds
on a CPU. Small enough to inspect, complete enough that every modern component is
present.

| | |
| --- | --- |
| **Level** | 2 - after training fundamentals |
| **Study time** | 34 hours: 16 h reading, 15 h labs, 3 h write-up |
| **Hardware** | CPU-only for the teaching path. A GPU shortens optional runs; no API key is required |
| **Prerequisites** | [MT01-MT05](../model-training/index.md), [LF01](lf01-tokens-and-embeddings.md) assumes basic linear algebra |
| **You will produce** | A trained tiny LM, an SFT adapter, an efficiency report, and a serving contract |

## Modules

| Module | Question | Lessons | Notebook |
| --- | --- | --- | --- |
| M06 | How does a transformer predict the next token? | [LF01](lf01-tokens-and-embeddings.md) - [LF04](lf04-tiny-lm-training.md) | [Open notebook](../../notebooks/llm-fine-tuning/m06_transformers.ipynb) |
| M07 | How do you turn a base model into an instruction follower? | [LF05](lf05-sft-data-and-templates.md) - [LF07](lf07-evaluating-assistants.md) | [Open notebook](../../notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb) |
| M08 | How do you fine-tune and serve with a small memory budget? | [LF08](lf08-lora.md) - [LF10](lf10-merging-and-serving.md) | [Open notebook](../../notebooks/llm-fine-tuning/m08_lora_qlora.ipynb) |

## Measured anchors

* TinyGPT: **239,040** parameters; 400 steps in **about 23 s** on CPU (24.8 s in an earlier run); loss
  **3.454 -> 0.433**; final perplexity **1.54**.
* SFT: answer loss **1.039 -> 0.315**; exact match **0.688 -> 0.905**; first-12
  accuracy **0.411 -> 0.818**; word F1 **0.087 -> 0.258**; corpus forgetting loss
  **0.885 -> 1.072**.
* LoRA `r=4`: **8,448** trainable parameters (**3.34%**); answer loss **0.601** and
  exact match **0.816** at the same budget, versus full SFT's **0.315 / 0.905**.
* Merge check: maximum absolute difference **6.7e-6**.
* Quantization: int8 **259.8 KiB (3.758x)** with 0.905 accuracy and **0.992**
  agreement; int4 **139.1 KiB (7.022x)** with 0.900 accuracy and **0.895**
  agreement.

These are teaching-scale results, not benchmarks. Their value is that you can
reproduce them and explain each one.

## The section's argument

1. **Tokenization is part of the model.** Vocabulary, context length, and loss are
   coupled.
2. **The causal mask is non-negotiable.** A mask bug improves the training curve
   while destroying the model.
3. **SFT is still next-token prediction.** The data and the label mask do the work;
   the objective does not change.
4. **Loss is not the product.** Report task metrics and inspect failures.
5. **Efficiency is a trade, not a free win.** LoRA and quantization cost accuracy
   or agreement; measure both.

## Optional GPU path

The notebooks run on CPU. A real Hugging Face + PEFT + bitsandbytes run is optional
and is **not** executed in this repository's validation, because it needs a GPU, a
model download, and packages that are not installed. If you take that path, report
the GPU, the package versions, and the base model revision; do not reuse the
teaching numbers.

## How to study this section

Read LF01-LF04 with the M06 notebook open. Then read LF05-LF07 and run the SFT
notebook, changing the mask to see the failure. Finish with LF08-LF10 and the
efficiency notebook. The labs ask for the same tables the notebooks print; the
marking is in the interpretation.

## Practical work

| Work | What it asks for |
| --- | --- |
| [Lab 1 - Tiny language model](labs/lab-1-tiny-lm.md) | Train, evaluate, and explain a tiny LM |
| [Lab 2 - SFT and LoRA](labs/lab-2-sft-and-lora.md) | Fine-tune, mask, adapt, and compare |
| [Lab 3 - Efficiency report](labs/lab-3-efficiency-report.md) | Measure size, quality, and agreement trade-offs |

## Assessment

[Assessment](assessment.md): three labs (90%) and a reproduction defense (10%).

## Next

Continue to [M15 - AI agents](../ai-agents/index.md).
