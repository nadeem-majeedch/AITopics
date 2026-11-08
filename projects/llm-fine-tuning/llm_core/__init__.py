"""Shared code for the language-model units M06-M08.

The package is importable by adding ``projects/llm-fine-tuning`` to
``sys.path``:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd() / "projects" / "llm-fine-tuning"))
    from llm_core import CharTokenizer, TinyGPT, train_lm

Nothing here downloads a model, calls an API, or needs a GPU.
"""

from .data import (
    DATA_DIR,
    ROOT,
    corpus_sentences,
    ensure_datasets,
    load_corpus,
    load_faq,
    load_tickets,
    manifest,
    read_rows,
    read_text,
    vocab_preview,
)
from .evaluate import (
    bits_per_token,
    distinct_n,
    exact_match,
    format_table,
    generate_answer,
    generation_report,
    generate_text,
    masked_accuracy,
    mean,
    normalize_text,
    perplexity,
    repetition_rate,
    tokenizer_comparison,
    word_f1,
)
from .lora import (
    LoRALinear,
    apply_lora,
    freeze_except_lora,
    lora_bytes,
    lora_state_dict,
    merge_lora,
    trainable_parameters,
)
from .model import GPTConfig, TinyGPT, build_model
from .quantize import (
    dequantize_tensor,
    quantize_state_dict,
    quantize_tensor,
    quantized_copy,
    quantized_size_bytes,
    top1_agreement,
)
from .sft import (
    ASSISTANT_PREFIX,
    SFTExample,
    SYSTEM_PROMPT,
    build_example,
    build_examples,
    collate,
    estimate_sft_loss,
    format_example,
    format_prompt,
    pad_batch,
    prompt_fraction,
    train_sft,
)
from .tokenizer import BPETokenizer, CharTokenizer, WordTokenizer, tokenizer_report
from .train import History, estimate_loss, get_batch, lr_at, train_lm

__version__ = "1.0.0"

__all__ = [
    "ASSISTANT_PREFIX",
    "BPETokenizer",
    "CharTokenizer",
    "DATA_DIR",
    "GPTConfig",
    "History",
    "LoRALinear",
    "ROOT",
    "SFTExample",
    "SYSTEM_PROMPT",
    "TinyGPT",
    "WordTokenizer",
    "__version__",
    "apply_lora",
    "bits_per_token",
    "build_example",
    "build_examples",
    "build_model",
    "collate",
    "corpus_sentences",
    "dequantize_tensor",
    "distinct_n",
    "ensure_datasets",
    "estimate_loss",
    "estimate_sft_loss",
    "exact_match",
    "format_example",
    "format_prompt",
    "format_table",
    "freeze_except_lora",
    "generation_report",
    "generate_answer",
    "generate_text",
    "get_batch",
    "load_corpus",
    "load_faq",
    "load_tickets",
    "lora_bytes",
    "lora_state_dict",
    "lr_at",
    "manifest",
    "masked_accuracy",
    "mean",
    "merge_lora",
    "normalize_text",
    "pad_batch",
    "perplexity",
    "prompt_fraction",
    "quantize_state_dict",
    "quantize_tensor",
    "quantized_copy",
    "quantized_size_bytes",
    "read_rows",
    "read_text",
    "repetition_rate",
    "tokenizer_comparison",
    "tokenizer_report",
    "top1_agreement",
    "train_sft",
    "train_lm",
    "trainable_parameters",
    "vocab_preview",
    "word_f1",
]
