"""The orchestrator that ties retrieval, generation, and history together.

Everything a project needs is available here, and nothing else:

    bot = RAGChatbot.from_directory("data/chatbots-rag/corpus")
    answer = bot.ask("When does enrollment close?")
    print(render_answer(answer))

The class holds no policy of its own. Retrieval lives in ``retrieval``, prompt and
abstention policy in ``generation``, citation checking in ``citations``, and
privacy in ``logging_safe``. If you want different behaviour, change the module
that owns it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .documents import Chunk, build_chunks, load_documents
from .embeddings import Embedder, default_embedder
from .generation import Answer, GenerationConfig, generate
from .history import ConversationHistory
from .logging_safe import SafeLogger
from .model_client import ModelClient, get_client
from .retrieval import HybridRetriever, RetrievalResult


@dataclass
class RAGChatbot:
    """A retrieval-augmented assistant over one small document collection."""

    retriever: HybridRetriever
    client: ModelClient
    chunks: Sequence[Chunk] = field(default_factory=tuple)
    config: GenerationConfig = field(default_factory=GenerationConfig)
    history: ConversationHistory = field(default_factory=ConversationHistory)
    logger: SafeLogger | None = None

    @classmethod
    def from_directory(
        cls,
        corpus_dir: Path | str,
        *,
        client: ModelClient | None = None,
        embedder: Embedder | None = None,
        config: GenerationConfig | None = None,
        history: ConversationHistory | None = None,
        logger: SafeLogger | None = None,
        max_chars: int = 600,
        overlap: int = 80,
        vector_weight: float = 0.6,
    ) -> "RAGChatbot":
        documents = load_documents(corpus_dir)
        if not documents:
            raise ValueError(f"no .md or .txt documents found in {corpus_dir}")
        chunks = build_chunks(documents, max_chars=max_chars, overlap=overlap)
        if not chunks:
            raise ValueError("documents produced no chunks; check max_chars and content")
        retriever = HybridRetriever(chunks, embedder or default_embedder(), vector_weight=vector_weight)
        return cls(
            retriever=retriever,
            client=client or get_client(),
            chunks=tuple(chunks),
            config=config or GenerationConfig(),
            history=history or ConversationHistory(),
            logger=logger,
        )

    def retrieve(self, question: str, k: int | None = None) -> list[RetrievalResult]:
        return self.retriever.search(question, k=k or self.config.k)

    def retrieve_doc_ids(self, question: str, k: int | None = None) -> list[str]:
        return [result.chunk.doc_id for result in self.retrieve(question, k=k)]

    def ask(self, question: str, *, use_history: bool = True) -> Answer:
        """Answer one question, optionally continuing the stored conversation."""
        if not question or not question.strip():
            raise ValueError("question cannot be empty")

        started = time.perf_counter()
        results = self.retrieve(question)
        answer = generate(
            question=question,
            chunks=[result.chunk for result in results],
            scores=[result.score for result in results],
            client=self.client,
            config=self.config,
            history=self.history.messages() if use_history else None,
        )
        latency_ms = (time.perf_counter() - started) * 1000.0

        if use_history:
            self.history.add_exchange(question, answer.text)
        if self.logger is not None:
            self.logger.log(question, answer, latency_ms)
        return answer

    def reset(self) -> None:
        self.history.reset()
