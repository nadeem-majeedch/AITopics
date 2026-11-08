"""Course code for the speech and audio section.

The package is deliberately dependency-light: ``numpy``, ``scipy`` (filtering and
resampling), ``torch`` (the two neural models), and ``Pillow`` (optional PNG output).
No ``librosa``, ``torchaudio``, ``soundfile``, or ``sounddevice`` is required, because
students hit install problems with all four. Where those libraries would be used,
this package implements the same maths in a few dozen lines, which is also the point
of the fundamentals modules.

Layers, bottom to top::

    audio   ->  features  ->  datasets  ->  training  ->  models
                     |            |            |
                   text  ->      asr  ->    evaluate
                     |
                  speaker, tts, metrics, cards

Every module imports only from the layer below it, so a lesson can point at one file
and not drag the rest in.
"""

from __future__ import annotations

__all__ = [
    "audio",
    "features",
    "synth",
    "datasets",
    "text",
    "models",
    "training",
    "asr",
    "speaker",
    "tts",
    "metrics",
    "evaluate",
    "cards",
    "dataio",
]

__version__ = "1.0.0"
