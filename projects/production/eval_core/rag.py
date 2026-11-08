"""Retrieval quality and answer faithfulness for a small offline RAG system.

Two different questions are measured, and they fail independently:

* **Retrieval**: did the right document appear, and how high? recall@k, MRR, nDCG@k.
* **Faithfulness**: is every claim in the answer supported by the text that was
  cited? A good retriever with an ungrounded answer still produces confident
  nonsense, and a grounded answer from the wrong document is still wrong.

The generator here is a deterministic extractive summariser, not a language model.
That is a feature: the numbers are reproducible, and the failure modes being
measured are in the pipeline, not in a sampled token.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from . import metrics

STOPWORDS = frozenset(
    """a an and are as at be been but by can could did do does for from had has have how
    i if in into is it its may me my no not of on or our should so than that the their
    them then there these they this to us was we were what when where which who why will
    with would you your""".split()
)

WORD = re.compile(r"[a-z0-9]+")
# Numbers must stand alone: "mc-01" is an identifier, not a quantity.
NUMBER = re.compile(r"(?<![\w-])\d+(?:\.\d+)?(?![\w-])")
SENTENCE = re.compile(r"(?<=[.!?])\s+")


SUFFIXES = ("ations", "ation", "ions", "ion", "ings", "ing", "ers", "er", "ed", "es", "s")


def stem(word: str) -> str:
    """A deliberately small suffix stripper.

    Not a linguistic stemmer: it exists so that "cancellation" and "cancel" meet,
    which a bag-of-words index otherwise misses. The lab's retrieval numbers are
    quoted with this choice visible, because a stemmer is a modelling decision.
    """
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            word = word[: -len(suffix)]
            break
    return word


def tokenize(text: str) -> list[str]:
    return [stem(word) for word in WORD.findall(text.lower()) if word not in STOPWORDS]


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    title: str
    index: int
    text: str


def load_corpus(corpus_dir: Path) -> list[tuple[str, str, str]]:
    """Return (doc_id, title, text) for every Markdown document, sorted by id."""
    docs = []
    for path in sorted(Path(corpus_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        first = next((line for line in text.splitlines() if line.startswith("# ")), "")
        docs.append((path.stem, first[2:].strip() or path.stem, text))
    return docs


def chunk_text(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    """Split on paragraph boundaries, packing up to ``size`` characters per chunk.

    Overlap keeps a sentence that straddles a boundary retrievable from either
    side. Both numbers are reported with every measurement, because a retrieval
    score without its chunking parameters is not reproducible.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > size:
            chunks.append(current.strip())
            tail = current[-overlap:] if overlap else ""
            current = (tail + "\n\n" + paragraph).strip()
        else:
            current = (current + "\n\n" + paragraph).strip() if current else paragraph
        while len(current) > size:
            chunks.append(current[:size].strip())
            current = current[size - overlap :].strip()
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


class BM25:
    """Okapi BM25 over chunks. Deterministic, no embeddings, no download."""

    def __init__(self, chunks: Sequence[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = list(chunks)
        self.k1 = k1
        self.b = b
        self.tokens = [tokenize(chunk.text) for chunk in self.chunks]
        self.lengths = [len(tokens) for tokens in self.tokens]
        self.avg_length = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        document_frequency: Counter = Counter()
        for tokens in self.tokens:
            document_frequency.update(set(tokens))
        n = len(self.chunks) or 1
        self.idf = {
            term: math.log(1 + (n - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        }

    def scores(self, query: str) -> list[float]:
        terms = tokenize(query)
        scores = []
        for tokens, length in zip(self.tokens, self.lengths):
            frequencies = Counter(tokens)
            score = 0.0
            for term in terms:
                if term not in frequencies:
                    continue
                tf = frequencies[term]
                denominator = tf + self.k1 * (1 - self.b + self.b * length / (self.avg_length or 1))
                score += self.idf.get(term, 0.0) * tf * (self.k1 + 1) / (denominator or 1)
            scores.append(score)
        return scores

    def search(self, query: str, k: int = 3) -> list[tuple[Chunk, float]]:
        scores = self.scores(query)
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
        return [(self.chunks[i], scores[i]) for i in order[:k] if scores[i] > 0]


def build_index(docs: Sequence[tuple[str, str, str]], chunk_size: int = 600,
                overlap: int = 100, min_tokens: int = 0) -> BM25:
    """Index the corpus, optionally dropping chunks with too few content tokens.

    ``min_tokens`` exists because a heading-only chunk can rank first: it matches
    the query words, contains no sentence, and yields an empty extractive answer.
    Setting it to 0 keeps that failure visible, which Lab 4 uses on purpose.
    """
    chunks: list[Chunk] = []
    for doc_id, title, text in docs:
        for position, text_chunk in enumerate(chunk_text(text, size=chunk_size, overlap=overlap)):
            if min_tokens and len(tokenize(text_chunk)) < min_tokens:
                continue
            chunks.append(Chunk(doc_id, title, position, text_chunk))
    return BM25(chunks)


def ranked_docs(index: BM25, question: str, k: int = 3) -> list[str]:
    """Document ids in ranked order, de-duplicated (a doc can win twice)."""
    seen: list[str] = []
    for chunk, _ in index.search(question, k=k):
        if chunk.doc_id not in seen:
            seen.append(chunk.doc_id)
    return seen


def retrieval_report(index: BM25, qa: Sequence[dict], k: int = 3) -> dict:
    rows = []
    for item in qa:
        ranked = ranked_docs(index, item["question"], k=max(k, 5))
        rows.append(
            {
                "id": item["id"],
                "gold": item["gold_doc"],
                "ranked": ranked,
                "hit": item["gold_doc"] in ranked[:k],
                "recall": metrics.recall_at_k(ranked, [item["gold_doc"]], k),
                "rr": metrics.reciprocal_rank(ranked, [item["gold_doc"]]),
                "ndcg": metrics.ndcg_at_k(ranked, [item["gold_doc"]], k),
                "top1": ranked[0] if ranked else "",
            }
        )
    return {
        "k": k,
        "rows": rows,
        "recall_at_k": sum(row["recall"] for row in rows) / len(rows) if rows else float("nan"),
        "mrr": sum(row["rr"] for row in rows) / len(rows) if rows else float("nan"),
        "ndcg_at_k": sum(row["ndcg"] for row in rows) / len(rows) if rows else float("nan"),
        "top1_accuracy": sum(1 for row in rows if row["top1"] == row["gold"]) / len(rows) if rows else float("nan"),
    }


def best_sentences(question: str, passage: str, max_sentences: int = 2) -> str:
    """Deterministic extractive answer: the sentences that overlap the question."""
    terms = set(tokenize(question))
    # Headings are not sentences. Left in, they get glued to the first sentence
    # and the quote reads like a table of contents.
    body = "\n".join(line for line in passage.splitlines() if not line.lstrip().startswith("#"))
    sentences = [s.strip() for s in SENTENCE.split(body) if s.strip()]
    scored = []
    for position, sentence in enumerate(sentences):
        overlap = len(terms & set(tokenize(sentence)))
        scored.append((overlap, -position, sentence))
    scored.sort(reverse=True)
    chosen = [sentence for overlap, _, sentence in scored[:max_sentences] if overlap > 0]
    if not chosen:  # nothing matched: quote the opening sentence rather than invent one
        chosen = sentences[:1]
    return " ".join(chosen)


def answer_question(index: BM25, question: str, k: int = 3, max_sentences: int = 2) -> dict:
    hits = index.search(question, k=k)
    if not hits:
        return {"answer": "", "docs": [], "cited_text": "", "abstained": True}
    top_chunk, _ = hits[0]
    answer = best_sentences(question, top_chunk.text, max_sentences=max_sentences)
    return {
        "answer": answer,
        "docs": [chunk.doc_id for chunk, _ in hits],
        "cited_text": top_chunk.text,
        "abstained": False,
    }


def faithfulness(answer: str, cited_text: str) -> dict:
    """Is the answer supported by the passage it cites?

    Three checks, each able to fail on its own:

    * every number in the answer appears in the passage (numbers are the easiest
      claim to verify and the easiest to hallucinate);
    * content-word coverage: the answer does not introduce vocabulary the passage
      does not contain;
    * sentence support: each answer sentence shares at least two content words
      with the passage.

    These are heuristics. A paraphrase can fail the vocabulary check while being
    supported, and a copied sentence can pass while being irrelevant. The lesson
    says so, and the lab reports the raw counts rather than only a score.
    """
    numbers_answer = set(NUMBER.findall(answer))
    numbers_passage = set(NUMBER.findall(cited_text))
    unsupported_numbers = sorted(numbers_answer - numbers_passage)

    answer_terms = set(tokenize(answer))
    passage_terms = set(tokenize(cited_text))
    coverage = len(answer_terms & passage_terms) / len(answer_terms) if answer_terms else 0.0

    sentences = [s.strip() for s in SENTENCE.split(answer) if s.strip()]
    supported = sum(1 for s in sentences if len(set(tokenize(s)) & passage_terms) >= 2)
    support_rate = supported / len(sentences) if sentences else 0.0

    ok = not unsupported_numbers and coverage >= 0.9 and support_rate == 1.0
    return {
        "ok": ok,
        "unsupported_numbers": unsupported_numbers,
        "coverage": coverage,
        "sentence_support": support_rate,
        "numbers_checked": len(numbers_answer),
    }


def evaluate_answers(index: BM25, qa: Sequence[dict], k: int = 3) -> dict:
    rows = []
    for item in qa:
        result = answer_question(index, item["question"], k=k)
        checks = faithfulness(result["answer"], result["cited_text"]) if not result["abstained"] else {
            "ok": False, "unsupported_numbers": [], "coverage": 0.0, "sentence_support": 0.0,
            "numbers_checked": 0,
        }
        gold_hit = item["gold_doc"] in result["docs"]
        contains = [phrase for phrase in item["answer_contains"]
                    if phrase.lower() in result["answer"].lower()]
        rows.append(
            {
                "id": item["id"],
                "retrieved": gold_hit,
                "faithful": checks["ok"] and gold_hit,
                "answer_ok": bool(contains) and gold_hit,
                "coverage": checks["coverage"],
                "unsupported_numbers": checks["unsupported_numbers"],
                "answer": result["answer"][:160],
            }
        )
    n = len(rows) or 1
    return {
        "rows": rows,
        "retrieval_accuracy": sum(row["retrieved"] for row in rows) / n,
        "faithfulness": sum(row["faithful"] for row in rows) / n,
        "answer_accuracy": sum(row["answer_ok"] for row in rows) / n,
        "mean_coverage": sum(row["coverage"] for row in rows) / n,
    }
