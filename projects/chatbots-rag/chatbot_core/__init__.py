"""chatbot_core: the shared, importable spine of the conversational AI section.

Import order for a new project:

* ``documents``   load and chunk text, keep metadata
* ``embeddings``  turn text into vectors (offline by default)
* ``retrieval``   dense, sparse, and hybrid search
* ``model_client`` talk to a model (fake, local, or hosted)
* ``generation``  prompts, structured output, grounding, abstention
* ``citations``   validate and display sources
* ``guardrails``  injection screening and redaction
* ``history``     conversation state and context limits
* ``evaluation``  fixed question set, metrics, report
* ``chatbot``     the orchestrator most projects use
"""

from .chatbot import RAGChatbot
from .citations import Citation, build_registry, validate
from .documents import Chunk, Document, build_chunks, chunk_text, load_documents, split_sections, tokenize
from .embeddings import Embedder, HashingEmbedder, SentenceTransformerEmbedder, cosine_similarity, default_embedder
from .evaluation import compare, evaluate, format_table, load_questions, write_report
from .generation import Answer, GenerationConfig, build_messages, detect_conflict, generate, parse_model_output, render_answer
from .guardrails import contains_sensitive, redact, scan_for_injection
from .history import ConversationHistory
from .logging_safe import SafeLogger, hash_text
from .model_client import (
    ABSTAIN_TEXT,
    SYSTEM_PROMPT,
    FakeModelClient,
    HostedAPIClient,
    LocalTransformersClient,
    get_client,
)
from .retrieval import BM25, HybridRetriever, RetrievalResult, VectorIndex

__all__ = [
    "ABSTAIN_TEXT",
    "Answer",
    "BM25",
    "Chunk",
    "Citation",
    "ConversationHistory",
    "Document",
    "Embedder",
    "FakeModelClient",
    "GenerationConfig",
    "HashingEmbedder",
    "HostedAPIClient",
    "HybridRetriever",
    "LocalTransformersClient",
    "RAGChatbot",
    "RetrievalResult",
    "SYSTEM_PROMPT",
    "SafeLogger",
    "SentenceTransformerEmbedder",
    "VectorIndex",
    "build_chunks",
    "build_messages",
    "build_registry",
    "chunk_text",
    "compare",
    "contains_sensitive",
    "cosine_similarity",
    "default_embedder",
    "detect_conflict",
    "evaluate",
    "format_table",
    "generate",
    "get_client",
    "hash_text",
    "load_documents",
    "load_questions",
    "parse_model_output",
    "redact",
    "render_answer",
    "scan_for_injection",
    "split_sections",
    "tokenize",
    "validate",
    "write_report",
]
