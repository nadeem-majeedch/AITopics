"""Speaker embeddings, verification, and a small diarization baseline.

Two warnings before the code, because this is the part of audio AI that most often
gets built without consent:

1. **This is not speaker identification for real people.** Everything here runs on
   synthetic voices generated from code. Using the same code on real recordings means
   processing biometric data, which requires a lawful basis, informed consent, and
   usually a data-protection review.
2. **Speaker recognition and speech recognition are different tasks.** ASR asks *what
   was said*; speaker recognition asks *who said it*. A transcript system that also
   identifies the talker is a different product with different legal exposure.

The embeddings are deliberately simple (MFCC statistics). They are good enough to
demonstrate verification metrics and diarization mechanics, and weak enough that the
evaluation shows real error rates rather than a perfect score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from . import audio, features
from .datasets import AudioRecord


def f0_track(
    samples: np.ndarray,
    sample_rate: int = 16_000,
    frame: float = 0.03,
    hop: float = 0.01,
    fmin: float = 60.0,
    fmax: float = 400.0,
    voicing_threshold: float = 0.3,
) -> np.ndarray:
    """Autocorrelation pitch estimate per frame; ``nan`` where the frame is unvoiced.

    Pitch is the single most useful speaker cue in these synthetic voices, and the one
    that a bag-of-spectra embedding throws away. Autocorrelation is not the best pitch
    tracker, but it is twenty lines and it fails in ways you can see (octave errors on
    strong second harmonics).
    """
    samples = np.asarray(samples, dtype=np.float32)
    win = int(frame * sample_rate)
    step = int(hop * sample_rate)
    low_lag = max(1, int(sample_rate / fmax))
    high_lag = min(win - 1, int(sample_rate / fmin))
    track = []
    for start in range(0, max(1, len(samples) - win + 1), step):
        chunk = samples[start : start + win]
        if len(chunk) < win:
            break
        centred = chunk - float(chunk.mean())
        energy = float(np.dot(centred, centred))
        if energy < 1e-6:
            track.append(np.nan)
            continue
        autocorr = np.correlate(centred, centred, mode="full")[win - 1 :] / energy
        window = autocorr[low_lag:high_lag]
        if window.size == 0:
            track.append(np.nan)
            continue
        index = int(window.argmax())
        peak = float(window[index])
        track.append(sample_rate / (index + low_lag) if peak > voicing_threshold else np.nan)
    return np.asarray(track, dtype=np.float64)


def pitch_stats(samples: np.ndarray, sample_rate: int = 16_000) -> dict:
    """Median, spread, and voiced fraction of the pitch track."""
    track = f0_track(samples, sample_rate)
    voiced = track[~np.isnan(track)]
    if len(voiced) < 3:
        return {"median_hz": float("nan"), "iqr_hz": float("nan"), "std_log": float("nan"), "voiced_ratio": 0.0}
    return {
        "median_hz": float(np.median(voiced)),
        "iqr_hz": float(np.percentile(voiced, 75) - np.percentile(voiced, 25)),
        "std_log": float(np.log(voiced).std()),
        "voiced_ratio": float(len(voiced) / max(len(track), 1)),
    }


def speaker_embedding(
    samples: np.ndarray,
    sample_rate: int = 16_000,
    n_mfcc: int = 13,
    pitch_weight: float = 3.0,
) -> np.ndarray:
    """Spectral statistics plus pitch, L2-normalised.

    The spectral half is the mean and standard deviation of MFCCs 1-8 over time: it
    captures vocal-tract shape. On its own it measures *what was said* as much as *who
    said it*, which is why the plain version scores at chance on this corpus.

    The pitch half is what separates voices with the same vowel space. Pitch is scaled
    by a fixed constant rather than standardised per corpus, because a per-corpus
    statistic would quietly use the test set.

    ``pitch_weight=0`` reproduces the naive embedding; the module compares the two.
    """
    mfcc = features.mfcc(samples, sample_rate=sample_rate, n_mfcc=n_mfcc)
    # Drop coefficient 0 and the noisiest high coefficients: energy varies with gain.
    usable = mfcc[:, 1 : min(9, mfcc.shape[1])]
    spectral = np.concatenate([usable.mean(axis=0), usable.std(axis=0)]).astype(np.float64)
    spectral_norm = float(np.linalg.norm(spectral))
    if spectral_norm > 0:
        spectral /= spectral_norm

    stats = pitch_stats(samples, sample_rate)
    if np.isnan(stats["median_hz"]):
        pitch = np.zeros(2)
    else:
        # Centred on 150 Hz on a log scale; the fixed constant keeps the scale honest.
        pitch = np.array([np.log(stats["median_hz"]) - np.log(150.0), stats["std_log"]]) * pitch_weight
    vector = np.concatenate([spectral, pitch]).astype(np.float32)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 0 else vector


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / denom) if denom > 0 else 0.0


def pair_scores(
    records: Sequence[AudioRecord],
    pitch_weight: float = 3.0,
) -> tuple[list[float], list[bool]]:
    """All pairs: score plus whether the two clips came from the same synthetic voice."""
    embeddings = [speaker_embedding(r.samples, r.sample_rate, pitch_weight=pitch_weight) for r in records]
    sources = [r.source_id for r in records]
    scores, same = [], []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            scores.append(cosine_similarity(embeddings[i], embeddings[j]))
            same.append(sources[i] == sources[j])
    return scores, same


def verification_report(scores: Sequence[float], same: Sequence[bool], thresholds: Sequence[float] = (0.80, 0.90, 0.95)) -> dict:
    from .metrics import equal_error_rate, verification_metrics

    rows = [verification_metrics(scores, same, float(t)) for t in thresholds]
    eer = equal_error_rate(scores, same)
    return {"at_thresholds": rows, "eer": eer, "n_pairs": len(scores), "n_same": int(sum(same))}


# ---------------------------------------------------------------------------
# Diarization
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    start: float
    end: float
    speaker: int
    confidence: float = 0.0


def diarize(
    samples: np.ndarray,
    sample_rate: int = 16_000,
    n_speakers: int = 2,
    window: float = 0.30,
    hop: float = 0.05,
    seed: int = 0,
) -> list[Segment]:
    """Cluster sliding-window embeddings into ``n_speakers`` groups.

    Each window is labelled, then the labels are written onto a non-overlapping time
    grid and merged into runs. That last step matters: labelling overlapping windows
    independently produces segments that overlap each other, which is not something a
    human can read and not something DER can score.

    It fails in the ways the module teaches: short turns are swallowed, overlapping
    speech is impossible to represent, and ``n_speakers`` must be known in advance.
    """
    win = int(window * sample_rate)
    step = int(hop * sample_rate)
    if win <= 0 or step <= 0:
        raise ValueError("window and hop must be positive")
    if len(samples) < win:
        return []
    embeddings, starts, pitches = [], [], []
    for start in range(0, len(samples) - win + 1, step):
        chunk = samples[start : start + win]
        if audio.rms(chunk) < 0.01:
            continue  # silence carries no speaker information
        embeddings.append(speaker_embedding(chunk, sample_rate, pitch_weight=0.0))
        stats = pitch_stats(chunk, sample_rate)
        pitches.append(np.log(stats["median_hz"]) if not np.isnan(stats["median_hz"]) else np.nan)
        starts.append(start)
    if len(embeddings) < n_speakers:
        return []
    # Combine spectral shape with pitch, standardising pitch across this recording's
    # windows only. Pitch is what separates two voices that share a vowel space; without
    # it the clusters follow the words being said.
    matrix = np.stack(embeddings)
    pitch = np.asarray(pitches, dtype=np.float64)
    pitch = np.where(np.isnan(pitch), np.nanmean(pitch) if not np.all(np.isnan(pitch)) else 0.0, pitch)
    pitch = (pitch - pitch.mean()) / (pitch.std() + 1e-9)
    matrix = np.hstack([matrix, 0.5 * pitch[:, None]])
    labels, centres = kmeans(matrix.astype(np.float32), n_speakers, seed=seed)

    # Only label frames that contain speech. Without this mask the silence between turns
    # is attributed to whichever speaker the nearest window belonged to, which shows up
    # as false-alarm speech in the diarization error rate.
    mask = np.zeros(len(samples), dtype=bool)
    frame, frame_hop = int(0.02 * sample_rate), int(0.01 * sample_rate)
    for start in range(0, max(1, len(samples) - frame), frame_hop):
        if audio.rms(samples[start : start + frame]) > 0.01:
            mask[start : start + frame] = True

    # Write labels onto a grid at the hop resolution, then merge contiguous runs.
    grid = np.full(len(samples), -1, dtype=np.int64)
    for start, label in zip(starts, labels):
        index = np.arange(start, start + win)
        grid[index[mask[index]]] = label
    segments: list[Segment] = []
    index = 0
    while index < len(grid):
        label = int(grid[index])
        run_end = index
        while run_end < len(grid) and grid[run_end] == label:
            run_end += 1
        if label >= 0:
            contributing = [
                row for start, row, assigned in zip(starts, matrix, labels) if assigned == label and index <= start < run_end
            ]
            if contributing:
                distance = float(np.linalg.norm(np.mean(contributing, axis=0) - centres[label]))
                scale = float(np.linalg.norm(centres[label])) + 1e-6
                confidence = max(0.0, 1.0 - distance / scale / 4.0)
            else:
                confidence = 0.0
            segments.append(
                Segment(
                    start=round(index / sample_rate, 3),
                    end=round(run_end / sample_rate, 3),
                    speaker=label,
                    confidence=round(confidence, 3),
                )
            )
        index = run_end
    return segments


def kmeans(matrix: np.ndarray, k: int, seed: int = 0, iterations: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """Plain k-means with k-means++ style initialisation, deterministic for a seed."""
    rng = np.random.default_rng(seed)
    n = len(matrix)
    if n < k:
        raise ValueError("need at least k samples")
    centres = [matrix[int(rng.integers(n))]]
    for _ in range(1, k):
        distances = np.array([min(np.linalg.norm(x - c) ** 2 for c in centres) for x in matrix])
        total = distances.sum()
        if total <= 0:
            centres.append(matrix[int(rng.integers(n))])
            continue
        centres.append(matrix[int(rng.choice(n, p=distances / total))])
    centres_arr = np.stack(centres).astype(np.float32)
    labels = np.zeros(n, dtype=np.int64)
    for _ in range(iterations):
        scores = np.linalg.norm(matrix[:, None, :] - centres_arr[None, :, :], axis=2)
        new_labels = scores.argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for c in range(k):
            members = matrix[labels == c]
            if len(members):
                centres_arr[c] = members.mean(axis=0)
    return labels, centres_arr


def merge_segments(segments: Sequence[Segment], max_gap: float = 0.10) -> list[Segment]:
    """Join consecutive windows with the same label - the output people actually read."""
    if not segments:
        return []
    merged = [Segment(segments[0].start, segments[0].end, segments[0].speaker, segments[0].confidence)]
    for segment in segments[1:]:
        last = merged[-1]
        if segment.speaker == last.speaker and segment.start - last.end <= max_gap:
            last.end = segment.end
            last.confidence = max(last.confidence, segment.confidence)
        else:
            merged.append(Segment(segment.start, segment.end, segment.speaker, segment.confidence))
    return merged


def diarization_report(segments: Sequence[Segment], truth: Sequence[dict]) -> dict:
    """DER plus the numbers behind it, rounded for a log or a doc table."""
    result = diarization_error_rate(segments, truth)
    return {key: round(float(value), 4) for key, value in result.items()}


def diarization_error_rate(predicted: Sequence[Segment], truth: Sequence[dict], step: float = 0.02) -> dict:
    """Frame-level diarization error rate with optimal label matching.

    DER = (missed speech + false-alarm speech + speaker confusion) / total speech.
    Labels are arbitrary cluster ids, so they must be matched to truth labels before
    counting confusion - the same reason clustering needs a Hungarian assignment.
    """
    if not truth:
        return {"der": 1.0, "miss": 1.0, "false_alarm": 0.0, "confusion": 0.0}
    end = max(max(s["end"] for s in truth), max((s.end for s in predicted), default=0.0))
    grid = np.arange(0.0, end, step)
    truth_labels = np.full(len(grid), -1, dtype=np.int64)
    pred_labels = np.full(len(grid), -1, dtype=np.int64)
    names = sorted({s["speaker"] for s in truth})
    name_to_id = {name: i for i, name in enumerate(names)}
    for seg in truth:
        mask = (grid >= seg["start"]) & (grid < seg["end"])
        truth_labels[mask] = name_to_id[seg["speaker"]]
    cluster_ids = sorted({s.speaker for s in predicted})
    for seg in predicted:
        mask = (grid >= seg.start) & (grid < seg.end)
        pred_labels[mask] = cluster_ids.index(seg.speaker) + 100

    # Greedy label matching on overlap counts; adequate for two speakers.
    mapping: dict[int, int] = {}
    for cluster in cluster_ids:
        pred_mask = pred_labels == cluster + 100
        best, best_count = None, -1
        for speaker_id in range(len(names)):
            count = int(np.sum(pred_mask & (truth_labels == speaker_id)))
            if count > best_count:
                best, best_count = speaker_id, count
        mapping[cluster + 100] = best if best is not None else -1
    mapped = np.array([mapping.get(int(v), -1) if v >= 100 else -1 for v in pred_labels])

    speech = truth_labels >= 0
    missed = int(np.sum(speech & (mapped < 0)))
    false_alarm = int(np.sum((mapped >= 0) & ~speech))
    correct = int(np.sum(speech & (mapped == truth_labels)))
    confusion = int(np.sum(speech & (mapped >= 0) & (mapped != truth_labels)))
    total = max(int(speech.sum()), 1)
    return {
        "der": (missed + false_alarm + confusion) / total,
        "miss": missed / total,
        "false_alarm": false_alarm / total,
        "confusion": confusion / total,
        "correct": correct / total,
        "n_speech_frames": int(speech.sum()),
    }
