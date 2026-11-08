"""Video AI building blocks: video I/O, synthetic scenes, metrics, detection, tracking.

Importing this package has no side effects - no downloads, no model construction, no
directories created. Torch is only imported by the modules that need it (``detect``,
``actions``, ``garments``), so ``python -c "from video_core import video"`` works even in an
environment that has OpenCV but not PyTorch.
"""

from __future__ import annotations

from . import counting, labels, metrics, synth, video

__all__ = ["counting", "labels", "metrics", "synth", "video", "actions", "detect",
           "garments", "report", "tracking"]

_LAZY = {"actions", "detect", "garments", "report", "tracking"}


def __getattr__(name: str):
    """Import torch-dependent modules on first use rather than at package import."""
    if name in _LAZY:
        import importlib

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__version__ = "1.0.0"
