# CA15 - Integrating fine-tuned models into a chatbot {#ca15}

**Section path:** [Overview](index.md) · **Module 15** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h integration |
| **Hardware** | CPU-only to integrate; GPU needed to train (M07-M08) |
| **Prerequisites** | CA12, M07 or M08 |
| **You will produce** | A fine-tuned checkpoint wired into the same pipeline, or a documented reason it was not run |

## Why this module exists

Students finish a fine-tuning module and then cannot use the result. The adapter exists,
the notebook ran, and there is no path from "a directory of weights" to "an answer with
a citation".

The integration is small and mostly about interface discipline: a fine-tuned model is
just another `ModelClient`. Everything the pipeline does around it — retrieval, prompt
assembly, citation validation, refusal — stays identical. That is the test of whether the
architecture in Module 3 was worth building.

## Fine-tuning changes behaviour, not knowledge

| Goal | Fine-tuning helps? | Retrieval helps? |
| --- | --- | --- |
| Answer in a house style | Yes | Only by example |
| Follow a strict output format | Yes | Prompt can do it, less reliably |
| Learn a new fact | Poorly, and it cannot be cited | Yes |
| Update a fact | No | Yes, edit the document |
| Answer from documents | No | Yes |
| Refuse out of scope | Partly | No |

A fine-tuned model that memorises facts gives you an assistant that is confidently wrong,
cannot be updated, and cites nothing. The course's position is explicit: facts come from
retrieval, behaviour from fine-tuning, and both are measured.

## Wiring it in

```python
from chatbot_core import LocalTransformersClient, RAGChatbot, GenerationConfig
from pathlib import Path

client = LocalTransformersClient("path/to/your/adapter-or-model")
bot = RAGChatbot.from_directory(
    Path("data/chatbots-rag/corpus"),
    client=client,
    config=GenerationConfig(k=4, min_score=0.12),
)
print(bot.ask("How much does a paid workshop cost?").as_dict())
```

Note what did **not** change: the corpus, the chunking, the retrieval, the prompt, the
citation validator. If your fine-tuned model requires changing those, the model is
carrying knowledge it should be retrieving.

### The one thing that usually breaks

Chat templates. A fine-tuned model expects the exact template it was trained on, with the
same special tokens and role names. A mismatch produces a model that appears to ignore
its training.

```python
tokenizer = AutoTokenizer.from_pretrained(path)
messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": turn}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

Check three things before concluding the adapter failed:

1. the template string matches the training configuration;
2. the system role is supported (some small models have no system role);
3. the adapter is loaded on the same base model revision it was trained against.

## Evaluating the integration

Use the same harness, not a fresh demo:

```bash
python project_g_evaluation.py --split test --finetuned-model path/to/model
```

The report gains a `hybrid+finetuned` leg alongside the others. Compare on:

| Metric | What a change means |
| --- | --- |
| `answer_accuracy` | Did behaviour improve, or only tone? |
| `citation_precision` | Did the model start citing badly? |
| `false_answer_rate_unanswerable` | Did fine-tuning make it less willing to refuse? |
| `mean_latency_ms` | What did you pay for the improvement? |

A common and important finding: fine-tuning for style *reduces* refusal rate, because
the training data rarely contained refusals. If `false_answer_rate_unanswerable` rises,
the fine-tune made the system less safe, and that belongs in the report.

## If you did not train a model

That is an acceptable outcome for this section. The requirement is that you can explain
the integration path and evaluate the claim honestly. Write:

- what you would fine-tune for (behaviour, not facts);
- which base model and licence you would use;
- which metrics would detect a regression;
- why you did not run it (hardware, time, data).

The harness records the leg as `skipped` either way. A skipped experiment reported
honestly is worth more than a fabricated table.

## Cost and maintenance

| Item | Consideration |
| --- | --- |
| Storage | Adapters are small (MBs); merged models are GBs |
| Serving | Adapter loading adds startup time |
| Versioning | Record base model, adapter, and template together |
| Drift | A base-model update can invalidate the adapter |
| Licensing | The base model's terms still apply |

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Output ignores the system prompt | Template mismatch, or no system role | Print the templated prompt string |
| Output repeats the question | Template missing the generation prompt | `add_generation_prompt=True` |
| Quality collapses after loading | Adapter applied to a different base revision | Compare base model ids |
| Citations missing | Fine-tune taught prose-only answers | Keep the JSON contract in the prompt; validate and refuse |
| Refuses everything | Over-trained on refusals, or a broken template | Test one in-domain question with the raw prompt |
| Very slow | Merged model on CPU | Use the adapter, or quantise |

## Checkpoint

- [ ] You can explain why fine-tuning is a poor way to store facts.
- [ ] You can name the one interface a fine-tuned model must satisfy.
- [ ] You can describe what a rising `false_answer_rate_unanswerable` implies.
- [ ] You can state what you did or did not run, and why.

## Next step

Read [CA16 - Logging, privacy, access control, and deployment](ca16-privacy-and-deployment.md),
then complete [Project H](projects/h-domain-assistant.md).
