# CA16 - Logging, privacy, access control, and deployment {#ca16}

**Section path:** [Overview](index.md) · **Module 16** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h Project H |
| **Hardware** | CPU-only |
| **Prerequisites** | CA13, CA14 |
| **You will produce** | A deployed-quality assistant with minimal logging and a written risk note |

## Why this module exists

A chatbot sees whatever users type, and users type personal things. The default
instrumentation of a web app — log everything, keep it forever — turns a study aid into a
personal-data store nobody audited.

This module is the last one because privacy and access control are constraints on the
design, not features added at the end. A system that logs verbatim questions cannot be
made private by editing the README.

## Log the minimum that answers "what happened?"

```python
@dataclass
class LogRecord:
    timestamp_utc: str
    session_id: str          # hashed
    model: str
    retrieved: int
    top_score: float
    abstained: bool
    conflict: bool
    citations: int
    quarantined: int
    latency_ms: float
    question: str | None = None   # None unless store_text=True
    answer: str | None = None
```

| Field | Question it answers |
| --- | --- |
| `retrieved`, `top_score` | Was the evidence there? |
| `abstained`, `conflict` | Did the policy fire? |
| `citations`, `quarantined` | Did validation and screening work? |
| `latency_ms` | Was it slow? |
| `session_id` (hashed) | Which session, without identifying a person |

```python
def hash_text(value: str, salt: str = "course") -> str:
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:16]
```

Hashing is pseudonymisation, not anonymisation: a small set of candidate ids can be
brute-forced. Say "pseudonymous", and treat the hash as personal data if the mapping
exists anywhere.

## Consent is a gate, not a notice

```python
if not consent_to_send:
    raise PermissionError(
        "HostedAPI is opt-in: pass consent_to_send=True only after confirming "
        "you may send this document text to a third party."
    )
```

A notice in a README is easy to miss; a constructor that refuses is not. The same
principle applies to documents: sending a private corpus to any third party requires the
owner's permission, and "the tool did it automatically" is not permission.

## Access control belongs in retrieval

If a user may not read a document, its chunks must be excluded **before** scoring:

```python
allowed = [chunk for chunk in chunks if chunk.doc_id in permitted_doc_ids]
```

Filtering after generation is not equivalent. A model that has seen a forbidden passage
can paraphrase it, and a refusal that names the document still discloses that it exists.

| Approach | Verdict |
| --- | --- |
| Filter chunks by permission before search | Correct |
| Retrieve everything, instruct the model to stay silent | Leaks through paraphrase |
| Retrieve everything, filter citations after | Leaks through the answer text |
| Put all documents in one shared index | Fails as soon as there are two users |

## Redaction, and its limits

```python
REDACTIONS = [
    (EMAIL, "[email redacted]"),
    (STUDENT_ID, "[student id redacted]"),
    (EXTENSION, "[extension redacted]"),
    (PHONE, "[number redacted]"),
]
```

Redaction runs before the prompt and before the log. It is a pattern filter with known
false positives (an ID-shaped number) and false negatives (a name, a free-text address).
Claim what it does: it catches obvious identifiers in a fixed set of formats.

## Deployment checklist

```bash
cd projects/chatbots-rag
python project_h_domain_assistant.py --checklist
```

The checklist is deliberately nine items long:

- [ ] I have the right to use every document.
- [ ] The corpus contains no personal data I may not process.
- [ ] Retrieval enforces per-user document permissions.
- [ ] A fixed question set with gold evidence exists.
- [ ] Refusal rate on unanswerable questions is measured.
- [ ] At least one prompt-injection document has been tested.
- [ ] Logs contain no raw user text or document text.
- [ ] A rollback exists: previous index and previous prompt.
- [ ] I can name one question the system answers badly, and why.

The last item is the one that separates an engineer from a demo author.

## Rollback, versioning, and drift

| Artefact | Version it | Why |
| --- | --- | --- |
| Corpus + index | Hash and date | Documents change silently |
| Prompt | Explicit version string | Small edits move metrics |
| Model | Id, revision, date | Providers update models |
| Retrieval config | `k`, `min_score`, weights | Tuning changes behaviour |

A rollback that requires rebuilding the index is not a rollback; keep the previous index
artefact so a bad deployment can be reverted in minutes.

## Limits you must state

Every deployment note in this section ends with three sentences:

1. What the system is for, and who it is for.
2. What it does badly, with a concrete example from your own evaluation.
3. What it must not be used for.

If you cannot fill in (2) from evidence, you have not evaluated it.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Logs contain full questions | `store_text=True` left on | Inspect one record |
| A user sees another user's document | Shared index without filtering | Test with two permission sets |
| Personal data in a citation | Redaction applied to prompt but not display | Check the render path |
| Metrics changed with no code change | Corpus or model drifted | Compare index hashes and model ids |
| Cannot revert a bad prompt | Prompt edited in place, no version | Keep prompt text under version control |
| API key in the repository | Key pasted into a file | Rotate it, then remove it from history |

## Checkpoint

- [ ] You can explain pseudonymisation versus anonymisation.
- [ ] You can state where access control must be enforced and why.
- [ ] You can name your rollback artefacts.
- [ ] You can describe one limitation of your own system with evidence.

## Next step

Complete [Project H](projects/h-domain-assistant.md) and score the whole section with the
[assessment](assessment.md).
