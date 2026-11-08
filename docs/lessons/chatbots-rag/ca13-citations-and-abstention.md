# CA13 - Citations, source grounding, and abstention {#ca13}

**Section path:** [Overview](index.md) · **Module 13** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h Project F |
| **Hardware** | CPU-only |
| **Prerequisites** | CA12 |
| **You will produce** | A citation validator with tests, including a fabricated-citation case |

## Why this module exists

A citation is a claim about provenance, and a model can make it up. "According to the
handbook, refunds take 14 days [2]" reads as verified even when block 2 says something
else, or does not exist.

This module makes citations checkable in code rather than persuasive in prose.

## Numbering is a contract

```python
def build_registry(chunks, scores=None) -> dict[int, Citation]:
    for index, chunk in enumerate(chunks, start=1):
        ...
```

`[1]` means *the first chunk retrieved for this request*. Three consequences:

- the registry is rebuilt per request, never cached across turns;
- the prompt's numbering and the validator's numbering come from the same object;
- a citation that resolves is a citation you can render with title, section, and path.

## Validation, and what it catches

```python
def validate(claimed, answer_text, registry) -> ValidationOutcome:
    for number in claimed:
        outcome.valid.append(...) if number in registry else outcome.invalid_numbers.append(number)

    for match in BRACKET_CITATION.finditer(answer_text or ""):
        if int(match.group(1)) not in registry:
            outcome.fabricated_in_text.append(int(match.group(1)))
```

Two channels are checked, because models cheat in two ways:

| Channel | Example | Why it happens |
| --- | --- | --- |
| Structured field | `"citations": [9]` with 4 chunks | Model invents an index |
| Inline marker | "within 30 days [9]" | Model writes prose instead of obeying the schema |

Checking only the structured field misses the second. Checking only the text misses a
model that cites correctly in JSON and invents in prose.

## Fail closed, not fail open

```python
if outcome.fabricated:
    return Answer(text=ABSTAIN_TEXT, abstained=True, dropped_citations=dropped, ...)
```

An answer that cites a source outside the retrieved set is **replaced by a refusal**. The
dropped numbers are recorded so the failure is visible to whoever reads the debug panel,
but the user never sees the fabricated claim.

Compare the alternatives:

| Policy | Effect on a wrong citation |
| --- | --- |
| Show it anyway | User trusts an invented source |
| Strip the citation, keep the claim | Unsourced claim, silently devalued |
| Replace with refusal (this section) | Failure is visible and safe |

The third is stricter and less helpful. That is the correct trade for a system whose
value is checkability.

## Abstention as a first-class outcome

| Situation | Correct outcome | Test |
| --- | --- | --- |
| No relevant passage retrieved | Refuse | `test_rag_missing_document_abstains` |
| Passage retrieved, question unanswerable from it | Refuse | `test_rag_unsupported_question_abstains` |
| Evidence quarantined | Refuse | `test_rag_prompt_injection_in_document_is_quarantined` |
| Malformed model reply | Refuse | `test_rag_invalid_json_fails_closed` |
| Invented citation | Refuse | `test_rag_fabricated_citation_fails_closed` |

Refusal is scored, not excused: `abstention_correct` measures how often the system
refuses when it should, and `false_answer_rate_unanswerable` measures the opposite.
A system that answers everything scores 0.0 on the first metric, which is exactly the
information a demo hides.

## Conflicting sources

Two documents can both be retrieved and disagree. Silently choosing one is a factual
error the user cannot see. The pipeline flags it:

```python
conflict, note = detect_conflict(list(usable), question)
```

```python
return True, f"Sources disagree about the {unit}: {detail}."
```

The heuristic is narrow on purpose — same unit, different values, different documents,
sentences that share content words with the question. It catches two refund policies
stating 14 and 30 days. It does not attempt general contradiction detection, and saying
so is part of the module.

The scope decision matters too: conflict detection runs over **all retrieved evidence**,
not only the chunk the model chose to quote, because the disagreement the user needs to
hear about may sit in the passage the model skipped.

## Rendering sources so they can be checked

```python
def render(answer, show_withheld=False):
    ...
    for citation in answer.citations:
        lines.append(f"  [{citation.number}] {citation.title} - {citation.section}")
        lines.append(f"      file: {citation.source}  score: {citation.score:.3f}")
```

A source display needs: the heading (what it is about), the file (where it lives), and
the score (how confident retrieval was). A bare number is not a citation; it is a
decoration.

## What "grounded" means, precisely

An answer is grounded when **every factual claim in it is supported by a cited chunk**.
This section checks a necessary condition automatically (citations resolve) and leaves
the sufficient condition (claims are actually supported) to human review in Module 14.
Be explicit about that gap: automated citation validation catches invention, not
misrepresentation.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Citation numbers shifted by one | Off-by-one between prompt numbering and registry | Print both in the same function |
| Valid answer refused | Model cited an index beyond `k` | Inspect the raw reply and `dropped_citations` |
| Citations resolve but the claim is wrong | Misrepresentation, not fabrication | Human review: compare claim to chunk text |
| Conflict never detected | Different units, or wording differs | Print the numeric tokens per chunk |
| Refusal text treated as an answer | Downstream string check missing | Compare against `ABSTAIN_TEXT`, and check `abstained` |

## Checkpoint

- [ ] You can explain why the citation registry is rebuilt per request.
- [ ] You can name both fabrication channels and how each is caught.
- [ ] You can state what fail-closed means and why it is the chosen policy.
- [ ] You can give one reason automated validation is not sufficient.

## Next step

Read [CA14 - RAG evaluation and error analysis](ca14-evaluation.md) and build
[Project G](projects/g-evaluation.md).
