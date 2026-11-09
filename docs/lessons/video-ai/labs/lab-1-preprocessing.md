# Lab 1 - Video preprocessing: metadata, interval extraction, and a contact sheet

**Section path:** [Overview](../index.md) · Modules [VD02](../vd02-reading-and-writing.md), [VD03](../vd03-frame-extraction-and-datasets.md) · **Lab 1** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 8% of the section assessment |
| **Time** | 2 hours |
| **Hardware** | CPU-only; the whole lab runs in about 2 seconds |
| **Code** | `projects/video-ai/lab1_video_preprocessing.py` |
| **Prerequisites** | VD01-VD03 |

## Objectives

By the end of this lab you can:

1. Report a clip's real properties - resolution, frame rate, decoded frame count, duration,
   codec - and say which of them you trust and why.
2. Convert a time interval (seconds) into a frame stride, and state the rounding error.
3. Predict the number of frames a given interval extracts **before** running the code.
4. Produce and read a contact sheet, and use it to catch a data problem the numbers hide.
5. Show that re-reading a frame gives identical pixels (determinism), which is what makes the
   rest of the section reproducible.

## Prerequisites

- Modules VD01-VD03 read.
- `python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"` works.
- Data generated: `python projects/video-ai/scripts/make_video_data.py` from the repository root. It writes seven
  clips, their manifests, annotations, and a dataset card into `projects/video-ai/data/video/`.
  The directory is git-ignored and regenerates in about two seconds.

### The dataset, in one table

| Clip | Split | Content | Frames | What it is for |
| --- | --- | --- | --- | --- |
| `street_day` | train | clear daylight, 6 vehicles | 60 | the easy reference clip |
| `street_dusk` | train | low sun, long shadows | 60 | second training condition |
| `street_quiet` | val | daylight, light traffic | 60 | threshold selection only |
| `street_night` | test | headlights, dark road | 60 | lighting shift |
| `street_rain` | test | blur and spray | 60 | weather shift |
| `street_shake` | test | whole-frame camera motion | 60 | motion-model failure |
| `street_crowd` | test | 8 vehicles, heavy overlap | 60 | association failure |

All clips: 640x360, 10 fps, 6.00 s, `mp4v`, CC0-1.0, deterministic for a given seed.

## Procedure

### 1. Run the lab

```bash
cd projects/video-ai
python lab1_video_preprocessing.py
```

Options:

| Flag | Meaning |
| --- | --- |
| `--interval 0.5` | seconds between extracted frames (default 0.5) |
| `--video street_day` | process one clip instead of all seven |
| `--no-frames` | skip writing JPEGs (keep the reports) |
| `--selftest` | one clip, assertions only, no full report |

### 2. Predict before you look

For each clip, write down: `stride = round(fps × interval)` and
`expected frames = ceil(frame_count / stride)`. At 10 fps and 0.5 s the stride is 5 and a
60-frame clip yields 12 samples (indices 0, 5, ..., 55). If your prediction disagrees with the
output, find out why *before* moving on - that disagreement is the lesson.

### 3. Inspect the output

```
outputs/frames/street_day/000000.jpg ...   extracted frames
outputs/contact_street_day.png             one tiled sheet per clip
outputs/lab1_video_preprocessing.json      the report
```

Open at least two contact sheets. Look for: a frozen clip (identical tiles), a lighting change
mid-clip, a clip whose vehicles are all in the same lane, and a sheet whose tiles do not look
like the scene you expected.

### 4. Break something on purpose

```bash
python lab1_video_preprocessing.py --interval 0.1
```

0.1 s at 10 fps rounds to stride 1, so the "interval" becomes 0.1 s exactly (lucky). Now try
`--interval 0.15`: stride rounds to 2, and the actual interval is 0.2 s - a 33% error. Read the
printed `interval` line and confirm the lab reports both the requested and actual values rather
than pretending they match.

### 5. Verify determinism

Every frame table carries a digest. Run the lab twice and compare reports:

```bash
python lab1_video_preprocessing.py > /tmp/run1.txt && python lab1_video_preprocessing.py > /tmp/run2.txt
diff /tmp/run1.txt /tmp/run2.txt && echo "identical"
```

If the digests differ, your data is not the data the manifest describes - regenerate it.

## Expected output

The measured run on this repository's machine:

```
=== street_day
  resolution : 640x360 (16:9 (1.78))
  fourcc     : FMP4  backend FFMPEG
  frames     : header says 60, decoded 60  60 expected
  duration   : 6.00 s  (6.00 s in the generator)
  interval   : asked 0.5 s, used 5 frames = 0.5 s
  extracted  : 12 frames -> contact_street_day.png
  [PASS] decoded frame count matches the generator  (60 vs 60)
  [PASS] frame rate matches the generator  (10.00)
  [PASS] extraction count is what the interval implies  (12 of 12)
  [PASS] contact sheet written and nonempty
  [PASS] timestamps are monotonic and match frame/fps
  [PASS] re-reading a frame gives identical pixels  (d36307f47380beea == d36307f47380beea)

=== columns in the extracted table
  frame  t_s    mean_luma  digest
  0      0.000  113.280    d36307f47380beea
  5      0.500  113.450    c8b5099399d1a009
  10     1.000  114.020    6af5c6e50204219d
  15     1.500  114.580    e3abf39edb75cd6b

  36/36 checks passed
```

36 checks = 5 per clip for six clips, 6 for `street_crowd` (it adds the determinism check).
Your digests will match these exactly if your data came from the same seed; your timings will
not, and that is expected.

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| All checks pass | 4 | `36/36 checks passed` |
| Interval arithmetic explained with both numbers | 3 | your prediction table vs the output |
| Contact sheet inspected, one observation reported | 3 | a specific observation, not "looks fine" |
| Determinism demonstrated | 2 | two runs compared |

Full marks require that your prediction table was written *before* the run. A submission that
"predicts" the observed number after the fact is not evidence of anything.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `VideoError: file not found` | data not generated | `python projects/video-ai/scripts/make_video_data.py` |
| `cannot open with any installed decoder` | file truncated or wrong codec build | regenerate; check `cv2.getBuildInformation()` for FFMPEG: YES |
| Extraction count is 60, not 12 | interval too small for the frame rate | check `round(fps*interval)`, it is 1 |
| Contract sheet tiles are all identical | interval shorter than the scene's motion, or a frozen clip | try `--interval 1.0` |
| Digests differ between runs | data regenerated between runs, or manifest mismatch | regenerate once, then compare again |
| `PermissionError` on `data/video` | a previous process still holds a file | close Python sessions, retry |

## Extensions

1. **A time-based sampler that seeks.** Implement extraction with `CAP_PROP_POS_MSEC` seeking
   and compare wall time with the sequential stride loop on the same clip. Explain the
   difference in terms of keyframes (VD01).
2. **Near-duplicate filter.** Add a mean-absolute-difference threshold and report how many of
   the 60 frames survive at 0.01, 0.02, and 0.05. Which threshold would you use for a 60 fps
   clip, and why is it different?
3. **Your own clip.** Record 10 seconds of any scene with your phone, write a data card for it
   (provenance, licence, consent, retention), and run the lab on it with `--video` pointing at
   the file. Report the header-versus-decoded frame count.
4. **Codec comparison.** Write the same 60 frames as `mp4v`, `MJPG`, and `XVID`, and compare
   file size and peak signal-to-noise ratio against the source frames. Which would you ship?

## Submit

- Your prediction table (written before the run) with the actual values beside it.
- The full lab output.
- `outputs/contact_street_night.png` and one paragraph on what it tells you that the numbers
  do not.
- The answer to: "at 25 fps, what interval do you actually get if you ask for 0.1 s, and what
  is the percentage error?"
