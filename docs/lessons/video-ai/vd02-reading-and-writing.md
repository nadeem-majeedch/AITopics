# VD02 - Reading and writing video with OpenCV {#vd02}

**Section path:** [Overview](index.md) · **Module 2** · [Lab 1](labs/lab-1-preprocessing.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 1 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD01](vd01-digital-video.md) |
| **You will produce** | A reader/writer pair that fails loudly instead of producing an empty file |

## Why this module exists

OpenCV's video API is small - six functions cover everything in this section - but it is
unforgiving in three specific ways:

1. **Failures are silent.** `VideoCapture` on a broken file returns an object whose
   `isOpened()` is `False`; every later `read()` returns `(False, None)`. `VideoWriter` on an
   unavailable codec does the same. Without explicit checks you get no frames and no error.
2. **Resources leak.** A `VideoCapture` left open holds a file handle; on Windows it can stop
   the file being deleted or re-encoded.
3. **Colour order is BGR**, not RGB. Every model in this course that takes RGB converts
   explicitly, and every conversion happens in one place.

This section's `video_core.video` is a thin, opinionated wrapper: it checks the things that
fail silently, and it raises `VideoError` with a machine-readable `reason`.

## Reading

```python
from video_core import video

info = video.probe("data/video/street_day.mp4", count_frames=True)
print(info.as_dict())
# {'path': ..., 'width': 640, 'height': 360, 'fps': 10.0, 'frame_count': 60,
#  'duration_s': 6.0, 'fourcc': 'FMP4', 'megapixels': 0.23, 'codec_note': '',
#  'backend': 'FFMPEG'}
```

`probe` opens, reads properties, optionally decodes everything, and closes. It never leaves a
handle open, and it raises rather than returning `None`:

```python
try:
    video.probe("missing.mp4")
except video.VideoError as exc:
    print(exc.reason, "|", exc.detail)
    # 'file not found | '
```

The three reasons it distinguishes are `file not found`, `cannot open with any installed
decoder`, and `no decodable frames`. Those are different problems with different fixes, so
they get different messages - Lab 7 tests all of them.

### Iterating frames

```python
for index, stamp, frame in video.iter_frames("data/video/street_day.mp4", stride=5):
    print(index, round(stamp, 3), frame.shape)
# 0 0.0 (360, 640, 3)
# 5 0.5 (360, 640, 3)
# ...
```

Three details that matter:

- **`index` is the source frame number**, not the loop counter. With `stride=5` you get
  0, 5, 10..., which is what makes it possible to join detections back to ground truth.
- **`stamp` is the container's presentation time**, read from `CAP_PROP_POS_MSEC`, not a
  recomputed `index / fps`. On a constant-rate clip the two agree to well under 0.11 s, which
  is the tolerance Lab 1 asserts; on a variable-rate clip they do not, and the container is
  right.
- **`resize` decodes at full size then resizes**, unless you pass a smaller size, in which
  case OpenCV resizes as it decodes. On large files that is a real saving; on this section's
  640x360 clips it is not, which Lab 8 measures rather than assumes.

Reading a single frame for a thumbnail or a test:

```python
frame = video.frame_at("data/video/street_day.mp4", 30)
```

`frame_at` is slower than sequential reading because it may decode from the nearest keyframe.
Do not put it in a loop over thousands of frames; do put it in a test.

## Writing

```python
from video_core import video

with video.VideoWriter("outputs/out.mp4", fps=10, size=(640, 360)) as writer:
    for frame in frames:
        writer.write(frame)
```

What the wrapper guarantees:

| Failure | Plain OpenCV | `video.VideoWriter` |
| --- | --- | --- |
| Codec not installed | Empty file, no error | Raises `VideoError` before writing |
| Odd width/height | File that will not decode | Raises with the reason |
| Wrong frame size | Undefined behaviour | Resizes to the declared size |
| Grayscale frame | Undefined behaviour | Converts to BGR |
| Forgot `release()` | Truncated or empty file | Context manager closes it |
| Zero frames written | 0-byte file | `write_video` raises after closing |

The last row is the one students hit most often: a loop that never runs produces a valid,
empty, unreadable MP4. `video.write_video` checks the file size after closing and raises.

```python
path = video.write_video("outputs/out.mp4", (f for f, _ in rendered), fps=10,
                         size=(640, 360))
print(path.stat().st_size)     # bytes actually on disk
```

### Frame rate when you skip frames

If you process every second frame and write the annotated result, the output has half as many
frames. To keep playback speed correct, write at `fps / stride`:

```python
in_stride = 2
with video.VideoWriter(out, fps=info.fps / in_stride, size=(info.width, info.height)) as w:
    ...
```

Getting this wrong produces a video that plays at double speed and a report that says the
clip is three seconds long when it is six. Lab 7's summary prints both the processed frame
count and the source duration so the mistake is visible.

## Annotating

```python
drawn = video.annotate_frame(frame, boxes, ["car 0.91", "truck 0.77"],
                             colour=(80, 220, 80))
trailed = video.draw_trails(drawn, trails)     # list of polylines, one per track
```

`annotate_frame` copies the frame, draws rectangles and caption boxes, and returns the copy -
the caller never has to remember whether the input was modified. Captions are clipped to the
frame so a box at the top edge does not push its label off-screen.

## Contact sheets

A contact sheet is the cheapest debugging tool in video work. Ten frames tiled on one image
tells you in two seconds whether the camera moved, whether the lighting changed, whether the
clip is one long freeze, and whether your extraction interval is doing what you think.

```python
sheet = video.contact_sheet(frames, cols=4, thumb=(160, 90),
                            labels=[f"f{i} {t:.1f}s" for i, t in times])
video.save_contact_sheet("outputs/contact.png", sheet)
```

Lab 1 writes one per clip. Look at yours before you trust any result computed from the frames.

## Resource handling, and why it matters on Windows

Every helper in `video_core.video` closes its capture before returning, including on the error
path. If you write your own loop, use a `finally`:

```python
cap = cv2.VideoCapture(str(path))
if not cap.isOpened():
    raise video.VideoError(path, "cannot open with any installed decoder")
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        ...
finally:
    cap.release()
```

Symptom of getting this wrong: `PermissionError` when you try to delete or overwrite the file
later in the same session, and on some systems a leak that only appears after a few hundred
clips.

## A complete, correct loop

Putting the pieces together - this is the shape every later lab uses:

```python
from video_core import video

def process(source, out_path, *, stride=1):
    info = video.probe(source, count_frames=True)
    if info.frame_count == 0:
        raise video.VideoError(source, "no decodable frames")
    written = 0
    with video.VideoWriter(out_path, info.fps / stride, (info.width, info.height)) as writer:
        for index, stamp, frame in video.iter_frames(source, stride=stride):
            detections = []                      # replaced by a real detector
            drawn = video.annotate_frame(frame, [d.box for d in detections])
            writer.write(drawn)
            written += 1
    if written == 0:
        raise video.VideoError(source, "no frames survived decoding")
    return written
```

## Common mistakes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Output file is 0 bytes | No frames written, or codec unavailable | Check `frames_written`, use `mp4v`/`MJPG` |
| Colours are swapped in the output | Wrote an RGB array into OpenCV | Keep everything BGR until the model boundary |
| Output plays too fast | Wrote at the source fps after striding | Use `fps / stride` |
| `PermissionError` on cleanup | Capture not released | Use the context manager or `finally` |
| Frame indices do not match labels | Used the loop counter instead of the source index | Use the `index` that `iter_frames` yields |
| Seeking is very slow | Random access decodes from keyframes | Read sequentially |

## Checks

- [ ] You can explain what `isOpened()` returning False implies for `read()`.
- [ ] You have produced a `VideoError` deliberately, and know its `reason` and `detail`.
- [ ] You can write a strided annotated video that plays at the correct speed.
- [ ] You have inspected a contact sheet before quoting a number computed from the frames.
- [ ] You can name the resource leak that a missing `release()` causes on Windows.
