# Lab 7 - A configurable video analytics application, with error handling that matters

**Section path:** [Overview](../index.md) · Modules [VD12](../vd12-video-classification-and-events.md), [VD14](../vd14-evaluation-and-deployment.md) · **Lab 7** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 5 hours |
| **Hardware** | CPU-only; a 60-frame run takes ~1.5 s |
| **Code** | `projects/video-ai/lab7_video_analytics.py`, config `projects/video-ai/configs/video_analytics.json` |
| **Prerequisites** | Labs 2, 3; VD12, VD14 |

## Objectives

1. Assemble detection, tracking, counting, drawing, and reporting into one program driven by a
   JSON config plus CLI overrides.
2. Produce a summary document with counts, flow, per-frame statistics, and warnings.
3. Make the program fail *well* on five kinds of bad input, with a clear reason and a non-zero
   exit code - and write nothing on failure.
4. Distinguish "no events" from "no data" in the exit codes, and explain why that matters.

## Prerequisites

- Labs 2 and 3 complete (this lab reuses their components, not their reports).
- Config at `configs/video_analytics.json`. Read it before running: every value it holds is a
  decision this lab makes for you.

## The config, line by line

```json
{
  "video": "street_day",
  "stride": 1,
  "model": "tiny",
  "score_threshold": 0.5,
  "nms_iou": 0.3,
  "tracking": {"enabled": true, "max_age": 6, "min_hits": 2, "iou_threshold": 0.3},
  "counting": {"enabled": true, "line": {"kind": "vertical", "at": 0.55, "anchor": "bottom"}},
  "output": {"video": "outputs/lab7_analytics.mp4", "summary": "outputs/lab7_summary.json"},
  "runtime": {"warn_below_fps": 5.0, "max_frames_without_detection": 30}
}
```

| Key | Why it is a parameter | Sensible alternative |
| --- | --- | --- |
| `model` | speed vs domain fit | `ssdlite` for a COCO-like domain |
| `score_threshold` | precision/recall trade | 0.6 for a tracker downstream (Lab 4) |
| `stride` | cost vs count accuracy | 2-3 for throughput (Lab 8) |
| `line.at` | where the tripwire sits | 0.5 if vehicles overlap near 0.55 |
| `max_age` | occlusion tolerance | 6 for 10 fps |
| `warn_below_fps` | surfaces a slow machine | 5 for interactive review |

## Procedure

### 1. Run the default analysis

```bash
cd projects/video-ai
python lab7_video_analytics.py
```

```
=== analysing street_day
  config     : .../configs/video_analytics.json
  input      : 640x360, 10.0 fps, 60 frames, FMP4
  processed  : 60 frames (stride 1) in ~1.5 s
  speed      : ~22 ms/frame -> ~45 fps
  detections : 347
  counted    : 6 crossings {'truck:positive': 3, 'motorcycle:negative': 1,
                           'car:negative': 1, 'motorcycle:positive': 1}
  flow       : 3600.0 per hour (extrapolated)
  video      : .../outputs/lab7_analytics.mp4
  summary    : outputs/lab7_summary.json
```

### 2. Override without editing code

```bash
python lab7_video_analytics.py --video street_crowd --stride 2
python lab7_video_analytics.py --no-tracking
python lab7_video_analytics.py --model ssdlite --score 0.4 --limit 20
```

`--no-tracking` turns off tracking and counting together: a count without identity is not a
count, and the lab refuses to pretend otherwise.

### 3. Run the error-handling selftest - this is the actual lab

```bash
python lab7_video_analytics.py --selftest
```

It creates five bad inputs and one good one, and checks the behaviour of each:

```
  case                    exit  outcome
  --------------------------------------------------------------------
  missing file            2     not a file and not a known scene name
  truncated               2     cannot open with any installed decoder
  not a video             2     cannot open with any installed decoder
  empty file              2     cannot open with any installed decoder
  video bytes, .txt name  2     cannot open with any installed decoder
  a good video            0     ok, 10 frames

  rejected: model must be 'tiny' or 'ssdlite', got 'yolo9000'

  processed  : 30 frames at 209.99 fps
  detections : 167 (5.567/frame)
  counted    : 5 crossings

  10/10 checks passed
```

Note what the `not a video` case is: an HTML page named `.mp4`, which is what a misconfigured
download server hands you. It is the most common real-world failure and the one most scripts
report as "0 detections".

### 4. Verify the write-nothing-on-failure rule

```bash
rm -f outputs/lab7_summary.json
python lab7_video_analytics.py --video /nonexistent.mp4; echo "exit=$?"; ls outputs/lab7_summary.json
```

Exit 2, message on stderr, and no summary file. If a summary exists after a failed run, a
dashboard could pick it up and report stale counts as current - which is worse than a crash.

### 5. Break the config

```bash
printf '{"model": "yolo9000"}' > /tmp/bad.json
python lab7_video_analytics.py --config /tmp/bad.json; echo "exit=$?"
```

Exit 3 with a message naming the valid options. A config error is not an input error: the file
was fine, the request was not.

## Expected output

Full run: exit 0, 6 crossings, summary and video written (as shown above; your milliseconds
will differ slightly between runs, the counts will not).

Selftest: exit 0 and `10/10 checks passed`, with the five rejections table.

Exit codes, complete:

| Code | Meaning |
| --- | --- |
| 0 | success; summary written (with or without crossings) |
| 2 | input unusable: missing, truncated, undecodable, zero frames |
| 3 | invalid config |

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Default run produces summary + video | 3 | files on disk, counts match Lab 3 |
| CLI overrides work without editing code | 2 | one run per override |
| Five bad inputs rejected with reasons | 3 | the selftest table |
| Nothing written on failure | 1 | the `rm` + run check |
| One paragraph: why "no events" ≠ "no data" | 1 | your own words |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Exit 2 with "not a file and not a known scene name" | typo in `--video`, or a path outside the project | pass an absolute path or a generated scene name |
| Exit 2 with "cannot open with any installed decoder" | truncated/invalid file | check the file size and header; regenerate |
| Exit 3 on a config you did not edit | stale file from an earlier lab | compare with `configs/video_analytics.json` |
| Summary has `warnings` about fps | machine slower than `warn_below_fps` | expected on a busy machine; report it |
| `--no-tracking` gives no counts | by design | counting requires identity |
| Video is written but summary is not | write failure mid-run | check disk space and permissions; the lab raises |

## Extensions

1. **Add a second camera.** Run the same config over two clips and merge the summaries into one
   report. What could go wrong if the two lines are not the same physical location?
2. **Event log output.** Emit one JSON line per crossing (`track_id`, `frame`, `t_s`, `class`,
   `direction`) for ingestion by a log system. Include a schema version.
3. **Graceful degradation.** If `score_threshold` yields zero detections for 30 consecutive
   frames, emit a warning rather than a silent zero count (the config already has
   `max_frames_without_detection`; wire it to a warning).
4. **A real bad input.** Record a 3-second phone video, interrupt the copy halfway, and run the
   lab on the truncated file. Report the exact message.
5. **Config schema validation.** Add a JSON schema and validate on load; report every invalid
   key at once instead of the first.

## Submit

- Full run output, `outputs/lab7_summary.json`, and the annotated video.
- The selftest table with the five rejections and their reasons.
- Exit-code table, in your own words.
- One paragraph on why a summary file must never exist after a failed run.
