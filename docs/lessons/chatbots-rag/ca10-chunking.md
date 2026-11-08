# CA10 - Chunking, document parsing, and metadata {#ca10}

**Section path:** [Overview](index.md) · **Module 10** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CA09 |
| **You will produce** | A chunking policy with a rationale, and a measured comparison of two policies |

## Why this module exists

Chunking is the highest-leverage, least-discussed decision in a RAG system. It decides
what unit of text can ever be retrieved. If a fact is split across two chunks, no
embedding model, no retriever, and no prompt can recover it cleanly.

This section's own pipeline had a real chunking bug that took a measurement to find.
That bug is the module's centrepiece.

## What a chunk needs to carry

A chunk is not just text. To cite it, filter it, and debug it, it needs:

| Field | Why |
| --- | --- |
| `chunk_id` | Stable identifier, unique across the corpus |
| `doc_id` | Which document it came from |
| `title` | Human-readable source for the citation |
| `section` | Heading context, often the best short description of the content |
| `source` | Relative path, so a reader can open the file |
| `start`, `end` | Character offsets within the section for verification |

```python
@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    section: str
    text: str
    source: str
    start: int
    end: int
```

Without `title` and `section`, a citation is a bare number and a user cannot check it.
Without offsets, you cannot prove the excerpt is verbatim.

## The bug this section actually had

The first implementation indexed only the body text of each chunk. A query like *"What
are the module assessment weights?"* then failed to retrieve the section titled "Module
weights", because the body said "Each module is scored with four components..." and
never used the words *assessment* or *weights*.

Retrieval ranked three unrelated data-policy chunks above it. The fix was one property:

```python
@property
def retrieval_text(self) -> str:
    """Text indexed for search: heading context plus body."""
    return f"{self.title} - {self.section}\n{self.text}"
```

The citation still shows the body, so evidence stays readable; the index sees the
heading, so a query naming the section can match it.

Two lessons, both worth writing down:

1. **A retrieval failure can be a chunking bug.** Check whether the target text exists
   in the index at all before you tune scores.
2. **The text you embed and the text you show need not be identical.** Keep them
   separate on purpose.

## Splitting on structure, then on length

```python
def split_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading, body) pairs, dropping the leading title."""
```

Structure first: a section boundary is a semantic boundary authored by a human. Only
then split by length, on sentence boundaries, with overlap:

```python
def chunk_text(text: str, max_chars: int = 600, overlap: int = 80) -> list[tuple[str, int, int]]:
```

| Parameter | Effect | Symptom when wrong |
| --- | --- | --- |
| `max_chars` too small | Facts split mid-idea | Retrieval finds half an answer |
| `max_chars` too large | Chunk covers several topics; embedding averages them | Retrieval finds a chunk about the right topic with the wrong fact |
| `overlap` too small | Boundary facts appear nowhere | A fact stated across a heading break is unreachable |
| `overlap` too large | Duplicate content, inflated index | Two nearly identical chunks both cite the same claim |

Defaults here: 600 characters with 80 overlap, about 13%. That is a starting point, not
a recommendation; the lab asks you to measure an alternative.

## Parsing what you actually have

| Format | Library | Trap |
| --- | --- | --- |
| `.md`, `.txt` | standard library | Headings carry meaning; do not discard them |
| `.pdf` | `pypdf` | Two-column layouts and tables scramble reading order |
| `.docx` | `python-docx` | Headings become styles, not text; map them explicitly |
| HTML | `beautifulsoup4` | Navigation boilerplate pollutes chunks |
| Scans | OCR | Errors are silent; a wrong digit looks like a fact |

Whatever the source, the pipeline in `documents.py` takes plain text with Markdown
headings. Convert to that shape first, and record the conversion step, because it is
part of your evidence chain.

## Near-duplicate content

Duplicate chunks distort both retrieval and evaluation: they inflate `hit_at_k` and make
citation precision look better than it is. Cheap checks:

- compare chunk hashes after whitespace normalisation;
- compare the first and last 100 characters of chunks from the same document;
- treat repeated boilerplate (headers, footers, licence blocks) as removable.

## What the corpus looks like

`scripts/make_chatbot_data.py` produces 13 documents and 41 chunks at the default
settings. Inspect them before trusting any metric:

```bash
cd projects/chatbots-rag
python -c "from chatbot_core import *; from pathlib import Path; \
docs = load_documents(Path('../../data/chatbots-rag/corpus')); \
chunks = build_chunks(docs); print(len(docs), len(chunks)); \
print('\n'.join(c.chunk_id for c in chunks[:8]))"
```

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| The answer is almost right, missing one clause | Chunk boundary, or overlap too small | Print the chunk text around the boundary |
| A section is unsearchable by its own title | Heading excluded from indexed text | Check `retrieval_text` |
| Two citations for one claim | Overlap plus near-duplicate chunks | Deduplicate, or reduce overlap |
| Chunk ids collide | Same section name in one document, index not incremented | Verify `#<piece_index>` suffix |
| Offsets do not match the text | Text normalised before offsets were computed | Compute offsets on the final string |
| Retrieval works but the answer cites the wrong section | Metadata from the wrong section | Print `chunk.section` against the source file |

## Checkpoint

- [ ] You can list the metadata a citable chunk needs.
- [ ] You can explain the heading-indexing bug and why it was invisible in a demo.
- [ ] You can state the trade-off in each direction for chunk size.
- [ ] You can name one parsing trap per format you intend to support.

## Next step

Read [CA11 - Vector search and retrieval](ca11-vector-search.md), then measure your own
chunking policy in [Project E](projects/e-course-docs-bot.md).
