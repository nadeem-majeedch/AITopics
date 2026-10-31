# Level 2 - Language AI

**Modules:** M06-M10 | **Hours:** 94 | **Hardware:** CPU-only to GPU required

Level 2 takes you from the internals of a transformer to a domain chatbot with
retrieval, citations, guardrails, and measured quality. You will train a tiny
language model, fine-tune a small instruct model, adapt it efficiently, and build
a RAG system.

!!! note "Level outcome"
    You can explain how a decoder-only language model works, fine-tune a small
    model on your own data, control memory with LoRA/QLoRA, and build a cited
    RAG chatbot with an evaluation suite.

## Readiness check

- Can you explain tokenization, attention, and next-token prediction?
- Have you fine-tuned any neural model and evaluated it on held-out data?
- Can you measure retrieval quality and generation quality separately?
- Do you have access to a GPU (local, Colab, or Kaggle) for M07-M08?

If not, complete M03-M06 first. M07 without M06 is guesswork.

---

## M06 - Transformers and language models {#m06}

**Level 2 | 18 hours | CPU or GPU | Prerequisite: M03, M05**

### Learning objectives

By the end of this module, you can:

1. Explain tokenization and compare character, word, and BPE tokenizers.
2. Describe embeddings, positional information, self-attention, and causal
   masking.
3. Implement a small decoder-only transformer block and training loop.
4. Explain next-token prediction, loss, perplexity, and decoding strategies.
5. Train a tiny language model on a public-domain corpus.
6. Diagnose memorization versus generalization in a small model.
7. Estimate the memory and compute implications of context length and model size.

### Prerequisites

- M03 (tensors, autograd, training loops).
- M05 (splits and dataset documentation).
- Basic probability and comfort with matrix operations.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 5 h | 7 h | 5 h | 1 h | 18 h |

### Required theory

- Tokenization: character-level, word-level, BPE, WordPiece, and vocabulary size.
- Token embeddings, positional encodings, and context windows.
- Scaled dot-product attention, multi-head attention, and causal masks.
- Residual connections, layer normalization, and feed-forward blocks.
- Decoder-only architecture and parameter counting.
- Pretraining objective: next-token prediction.
- Loss, cross-entropy, perplexity, and what perplexity does not tell you.
- Decoding: greedy, beam search, temperature, top-k, and nucleus sampling.
- KV caching and inference memory.
- Scaling intuition: parameters, data, compute, and context length.
- Memorization, contamination, and data licensing.

### Guided notebook

**Planned path:** `notebooks/llm-fine-tuning/m06_transformers.ipynb`

The notebook will:

1. Train a character-level tokenizer and a small BPE tokenizer on the same corpus.
2. Compare vocabulary size, sequence length, and compression.
3. Implement causal self-attention and a transformer block.
4. Assemble and train a tiny decoder-only model.
5. Compute training and validation loss and perplexity.
6. Generate text with different temperatures and top-p values.
7. Probe memorization by comparing train and validation continuations.
8. Visualize an attention map and interpret it cautiously.

**Dataset:** TinyShakespeare (public domain) for the core path. TinyStories may
be used as an optional larger corpus; verify its current license.

**Hardware:** A tiny model trains on CPU in minutes; a GPU makes the lab faster.

### Independent lab

**Brief:** Train a tiny language model on a public-domain corpus of your choice
and write an analysis.

Required evidence:

- Corpus description, license, size, and preprocessing.
- Tokenizer choice with a quantitative comparison.
- Model configuration and parameter count.
- Training and validation curves.
- Perplexity on held-out text and samples at three decoding settings.
- A memorization check using train vs validation prompts.
- A discussion of at least three failure modes (repetition, drift, factual
  errors, context limits).

**Constraints:** Keep the model small enough to train within the budget (for
example under 10M parameters). Do not train on copyrighted text you cannot use.
Do not claim reasoning ability from fluent samples.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- The causal mask is correct (no future-token leakage).
- Training and validation loss are both reported.
- Samples are analyzed, not just pasted.
- Memorization risk is tested explicitly.

### Deliverables

- Executed notebook.
- Tiny model training script or notebook.
- Sample outputs and perplexity table.
- Analysis report with failure modes.

### Next step

M07 - Small language models and supervised fine-tuning.

### Risks and notes

- **Do not confuse fluency with truth.** A tiny model can produce plausible
  nonsense.
- **Perplexity is corpus-dependent.** Compare models only on the same tokenizer
  and validation set.
- **Context length is expensive.** Attention memory grows with sequence length.
- **Licensing:** public domain and permissively licensed corpora only.

---

## M07 - Small language models and supervised fine-tuning {#m07}

**Level 2 | 24 hours | GPU required for core lab | Prerequisite: M06, M05**

### Learning objectives

By the end of this module, you can:

1. Select a small base model using license, size, capability, and hardware.
2. Apply the correct chat template and special tokens.
3. Build and validate an instruction-tuning dataset.
4. Fine-tune a small instruct model with supervised fine-tuning (SFT).
5. Use loss masking, packing, gradient accumulation, and checkpointing correctly.
6. Compare base and fine-tuned models on a held-out evaluation set.
7. Recognize catastrophic forgetting, overfitting, and evaluation contamination.
8. Produce a model card with intended use, metrics, and limitations.

### Prerequisites

- M06.
- M05.
- Access to a GPU with about 16 GB VRAM, such as a free Colab T4 or Kaggle GPU.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 5 h | 9 h | 9 h | 1 h | 24 h |

### Required theory

- Pretraining vs instruction tuning vs preference optimization.
- Small model families and licenses: SmolLM2, Qwen2.5, Phi-3, TinyLlama, Gemma.
- Chat templates, system/user/assistant roles, and special tokens.
- Instruction dataset formats: prompt-completion, conversations, and tool calls.
- Data quality, deduplication, and evaluation-set contamination.
- Loss masking: train on assistant tokens, not the prompt.
- Packing, truncation, padding, and sequence length.
- Hyperparameters: learning rate, epochs, batch size, warmup, weight decay.
- Catastrophic forgetting and how to detect it.
- Evaluation: task metrics, rubric scoring, LLM-as-judge caveats, and human
  spot checks.
- Model cards and responsible release.

### Guided notebook

**Planned path:** `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb`

The notebook will:

1. Inspect a small instruct model's tokenizer, chat template, and license.
2. Build 500-1,000 instruction examples from owned course content.
3. Validate roles, token lengths, duplicates, and template rendering.
4. Create a held-out set of 50 prompts before training.
5. Fine-tune with the Hugging Face `Trainer` or TRL `SFTTrainer`.
6. Log loss, learning rate, and GPU memory.
7. Compare base and tuned models on the held-out prompts.
8. Score outputs with a rubric plus a small human spot check.
9. Write a model card.

**Suggested base models:** SmolLM2-360M-Instruct, Qwen2.5-0.5B-Instruct, or a
similar small instruct model. Verify each model's license and terms.

**Dataset:** course-owned FAQ or documentation; no personal or copyrighted data.

**Hardware:** GPU required for the core path. A free T4 with 16 GB VRAM is
sufficient for a 0.5B model with small batches and gradient accumulation.

### Independent lab

**Brief:** Fine-tune a small language model for a bounded domain and evaluate it
honestly.

Required evidence:

- Domain definition, users, and non-goals.
- Dataset card: source, license, count, format, and cleaning steps.
- Chat template and token-length analysis.
- Training configuration and GPU memory log.
- Base vs tuned comparison on at least 100 held-out prompts.
- Quantitative rubric and at least 20 human-reviewed outputs.
- Failure taxonomy with examples: hallucination, refusal, format, verbosity,
  off-topic, and repetition.
- Model card and a one-page deployment recommendation.

**Constraints:** No evaluation prompts in training data. No test-set tuning. Do
not claim general capability from a narrow evaluation. Respect the base model's
license.

**CPU fallback:** If no GPU is available, complete dataset preparation and
evaluate a pre-fine-tuned public adapter. The full lab credit requires a training
run; document the limitation.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- The chat template is applied exactly as the model expects.
- The evaluation set is created before training and never trained on.
- Base and tuned models use the same evaluation protocol.
- At least 20 outputs are reviewed by a human, not only a model judge.

### Deliverables

- SFT dataset card and sample records.
- Training notebook or script with configuration.
- Adapter or model reference, not committed weights.
- Evaluation table and failure analysis.
- Model card and deployment recommendation.

### Next step

M08 - LoRA, QLoRA, quantization, and efficient training.

### Risks and notes

- **GPU memory:** reduce sequence length and batch size before changing the
  model. Use gradient accumulation to keep an effective batch size.
- **Template mismatch** is the most common cause of a model that "ignores"
  fine-tuning.
- **Contamination:** even a few evaluation prompts in training inflate results.
- **Catastrophic forgetting:** test general prompts, not only domain prompts.
- **Licensing:** some models have acceptable-use policies beyond the code
  license. Read them.

---

## M08 - LoRA, QLoRA, quantization, and efficient training {#m08}

**Level 2 | 18 hours | GPU required | Prerequisite: M07**

### Learning objectives

By the end of this module, you can:

1. Explain low-rank adaptation and the roles of rank, alpha, dropout, and target
   modules.
2. Explain QLoRA: 4-bit NF4, double quantization, and paged optimizers.
3. Estimate adapter and optimizer memory for a given model and batch size.
4. Train a model with QLoRA on a free GPU and measure peak memory.
5. Merge adapters and export a quantized model for local inference.
6. Compare quality, memory, latency, and throughput across configurations.
7. Choose an adaptation strategy for a stated budget and deployment target.

### Prerequisites

- M07.
- Comfort with PyTorch, Hugging Face models, and GPU memory concepts.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 7 h | 7 h | 1 h | 18 h |

### Required theory

- Full fine-tuning vs parameter-efficient fine-tuning.
- Low-rank decomposition and adapter parameter counts.
- Rank, alpha, scaling, dropout, and target module selection.
- QLoRA: NF4 quantization, double quantization, and paged optimizers.
- Memory components: weights, gradients, optimizer states, activations, KV cache.
- Gradient checkpointing and its speed/memory trade-off.
- Adapter merging and precision choices.
- Post-training quantization: GPTQ, AWQ, GGUF, and 8-bit/4-bit inference.
- Quality evaluation after quantization.
- Serving options: Transformers, llama.cpp, Ollama, and vLLM.
- Licensing of base models and quantized derivatives.

### Guided notebook

**Planned path:** `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb`

The notebook will:

1. Load a small instruct model in 4-bit mode.
2. Attach a LoRA adapter and print trainable parameter counts.
3. Train on a small SFT dataset with QLoRA.
4. Measure peak GPU memory and runtime.
5. Compare LoRA and QLoRA settings on the same evaluation set.
6. Merge the adapter into the base model.
7. Export a GGUF or run a quantized inference path.
8. Measure latency and quality before and after quantization.

**Hardware:** GPU required. Use a free T4 or better. Native Windows may require
a bitsandbytes workaround; Colab or WSL2 is the reliable path.

### Independent lab

**Brief:** Produce an efficiency trade-off study for a small model and a fixed
task.

Compare at least four configurations, such as:

- LoRA with two ranks.
- QLoRA with two quantization settings.
- Merged adapter vs unmerged adapter.
- Quantized inference at two bit widths.

For each, report:

- Peak VRAM and training time.
- Adapter size and merged model size.
- Task quality on the same held-out set.
- Inference latency and throughput.
- Failure cases introduced by quantization.

Conclude with a recommendation for a stated deployment budget.

**Constraints:** Same evaluation set for every configuration. Honest memory
measurement. Do not compare runs with different sequence lengths or batch sizes
without accounting for it.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Memory is measured, not guessed.
- Quality is evaluated after every compression step.
- The trade-off recommendation matches the evidence.
- Base-model license is respected.

### Deliverables

- Trade-off matrix with memory, quality, and latency.
- Training and inference configurations.
- Quantized model or reproducible export instructions.
- Recommendation memo.

### Next step

M09 - Chatbots and conversational applications.

### Risks and notes

- **Windows + bitsandbytes:** use Colab, WSL2, or a documented CPU fallback.
- **Quantization is lossy.** Evaluate after quantization; do not assume parity.
- **Adapter merging** can change behavior slightly; re-evaluate.
- **Disk and download limits:** small models still consume several GB.
- **License compatibility:** some base models restrict commercial use.

---

## M09 - Chatbots and conversational applications {#m09}

**Level 2 | 16 hours | CPU or GPU | Prerequisite: M07 or M08**

### Learning objectives

By the end of this module, you can:

1. Design a conversation flow for a bounded domain and user group.
2. Write system prompts that define role, scope, tone, and refusal behavior.
3. Manage conversation state and context-window limits.
4. Stream responses and handle errors in a simple web interface.
5. Apply basic guardrails for unsafe, out-of-scope, and sensitive requests.
6. Evaluate helpfulness, correctness, safety, and latency with a test set.
7. Instrument a chatbot without collecting unnecessary personal data.

### Prerequisites

- M07 or M08 (a fine-tuned or adapted model).
- Basic web UI experience is helpful but not required.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 6 h | 6 h | 1 h | 16 h |

### Required theory

- Conversation design: tasks, turns, clarifications, and failure recovery.
- System prompt architecture and instruction hierarchy.
- Context windows, truncation, summarization, and state.
- Streaming, timeouts, retries, and graceful degradation.
- Tool calling as a precursor to agents (conceptual).
- Guardrails: input filters, output checks, refusal policies, and escalation.
- Prompt injection and jailbreak risks.
- Evaluation: task success, answer quality, refusal appropriateness, latency.
- Privacy, logging, retention, and user consent.
- Accessibility and inclusive language.

### Guided notebook

**Planned path:** `notebooks/chatbots-rag/m09_chatbot.ipynb`

The notebook will:

1. Load a small local instruct model or connect to an optional hosted model.
2. Implement a chat loop with a system prompt and bounded history.
3. Add context summarization when the history exceeds a limit.
4. Build a Gradio interface with streaming and a reset button.
5. Add input and output guardrails for a defined domain.
6. Create a 30-prompt evaluation set with expected behavior.
7. Measure correctness, refusal appropriateness, and latency.
8. Log only the minimum necessary metadata.

**Hardware:** CPU works with a 0.5B-1.5B model; a GPU reduces latency. A hosted
API is optional for comparison.

### Independent lab

**Brief:** Build and evaluate a domain chatbot.

Required evidence:

- Conversation design document: users, tasks, scope, non-goals, escalation.
- System prompt with explicit refusal rules.
- State management and context policy.
- Guardrails with test cases.
- 50-prompt evaluation set covering normal, edge, unsafe, and out-of-scope
  requests.
- Results table with correctness, refusal appropriateness, and latency.
- Prompt-injection tests and observed failures.
- Privacy note: what is logged, where, and for how long.

**Constraints:** No personal data collection. No hidden logging. The bot must
refuse clearly when it does not know. Do not claim safety from a handful of tests.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Refusal behavior is defined and tested.
- Evaluation includes adversarial and out-of-scope prompts.
- Latency and cost are measured.
- Logging minimizes personal data.

### Deliverables

- Working chatbot demo.
- Conversation design document.
- Evaluation set and results.
- Guardrail and injection test report.
- Privacy note.

### Next step

M10 - Embeddings, vector search, and retrieval-augmented generation.

### Risks and notes

- **A chatbot is not a search engine.** Without retrieval, it will invent
  answers.
- **Guardrails are probabilistic.** Test them; do not assume they hold.
- **Do not log full conversations by default.** Minimize and document.
- **Model licenses** may restrict commercial deployment.

---

## M10 - Embeddings, vector search, and RAG {#m10}

**Level 2 | 18 hours | CPU-only | Prerequisite: M09 or M07**

### Learning objectives

By the end of this module, you can:

1. Explain embeddings, cosine similarity, and approximate nearest-neighbor search.
2. Choose an embedding model using quality, license, dimension, and cost.
3. Chunk documents with metadata and overlap appropriate to the content.
4. Build a vector index and a keyword baseline.
5. Combine dense and sparse retrieval, with optional reranking.
6. Generate answers with citations and refuse when evidence is insufficient.
7. Evaluate retrieval and generation separately.
8. Test RAG-specific attacks such as poisoned documents and prompt injection.

### Prerequisites

- M09 or M07.
- Basic information retrieval intuition is helpful.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 6 h | 8 h | 1 h | 18 h |

### Required theory

- Embedding models and semantic similarity.
- Chunking strategies: fixed size, sentence, section, and semantic.
- Metadata, filters, and access control.
- Vector indexes: flat, IVF, HNSW; FAISS basics.
- Dense vs sparse retrieval (BM25) and hybrid search.
- Reranking and cross-encoders.
- Query rewriting and multi-query retrieval.
- Context assembly, citations, and answer grounding.
- Evaluation: recall@k, MRR, nDCG, faithfulness, answer relevance, refusal.
- Hallucination and unsupported claims.
- Prompt injection through retrieved documents and data poisoning.
- Licensing of documents and embedding models.

### Guided notebook

**Planned path:** `notebooks/chatbots-rag/m10_rag.ipynb`

The notebook will:

1. Curate a small corpus of course-owned documents.
2. Parse and chunk with metadata (title, section, source, URL).
3. Generate embeddings with a small sentence-transformer model.
4. Build a FAISS index and a BM25 baseline.
5. Implement hybrid retrieval and optional reranking.
6. Assemble context with citations and a refusal rule.
7. Build a 30-question evaluation set with gold passages.
8. Compute recall@k, citation accuracy, and answer faithfulness.
9. Inject a malicious document and observe the failure.

**Dataset:** course-owned documentation, so licensing and privacy are controlled.

**Hardware:** CPU-only with a small embedding model.

### Independent lab

**Brief:** Build a RAG system over a document collection you are allowed to use
and evaluate it against a 50-question benchmark.

Required evidence:

- Corpus card: sources, licenses, size, and access rules.
- Chunking policy with rationale.
- Dense baseline and at least one improvement (hybrid, reranking, query
  rewriting, or better chunking).
- recall@k and MRR for retrieval.
- Citation accuracy and faithfulness for answers.
- Refusal test for unanswerable questions.
- Prompt-injection test with a poisoned document.
- Latency and index size.

**Constraints:** No confidential documents. No personal data. Do not evaluate on
the same questions you used to tune chunking unless you label it as development
data.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Retrieval is evaluated separately from generation.
- Citations point to the supporting passage.
- Unanswerable questions produce refusals, not guesses.
- At least one retrieval improvement is measured against a baseline.

### Deliverables

- RAG app or notebook.
- Corpus card and chunking policy.
- Evaluation benchmark and results.
- Injection test report.
- Short report on retrieval vs generation failures.

### Next step

M11 - Image classification and computer vision, or M15 - AI agents for the agent
path.

### Risks and notes

- **RAG does not eliminate hallucination.** It changes where errors come from.
- **Chunking dominates quality.** Test more than one policy.
- **Access control matters.** Retrieval must not surface documents a user cannot
  see.
- **Retrieved text is untrusted input.** Treat it as a potential injection vector.

---

## Level 2 completion checklist

- [ ] I can explain tokenization, attention, and decoding.
- [ ] I trained a tiny language model and analyzed its failures.
- [ ] I fine-tuned a small model with the correct chat template.
- [ ] I evaluated base vs tuned models on held-out prompts.
- [ ] I measured LoRA/QLoRA memory and quality trade-offs.
- [ ] I built a chatbot with explicit refusal behavior.
- [ ] I built a RAG system and evaluated retrieval and generation separately.
- [ ] I have portfolio artifacts for M06-M10.

Proceed to [Level 3 - Vision, speech, and video AI](level-3-vision-video.md).
