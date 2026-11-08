# VD01 - Digital video: frames, rate, resolution, codecs, timestamps {#vd01}

**Section path:** [Overview](index.md) · **Module 1** · [Labs](index.md#the-labs) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 1.5 h reading, 1.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [CV01](../computer-vision/cv01-digital-images.md) |
| **You will produce** | A one-page description of a video file that separates what the container claims from what the decoder delivers |

## Why this module exists

Almost every video bug that looks like a modelling bug is a timing, resolution, or codec
misunderstanding. A system samples "every 10th frame" of a clip someone re-encoded at 25 fps
and silently changes its sampling interval from one second to 0.4 seconds. A detector trained
on 640x360 frames meets a 1080p camera and misses every distant vehicle because each car is
now 18 pixels wide. A counting application reports a rate per hour from a six-second clip.

None of those raise an error. All of them are decided in this module.

## What a video file contains

Three layers, and confusing them causes most of the trouble:

| Layer | What it is | Where it goes wrong |
| --- | --- | --- |
| **Container** | The file: MP4, AVI, MKV. Holds tracks, timestamps, an index | An index written only at the end is lost when a download is cut short |
| **Codec** | How pixels are compressed: H.264, MPEG-4 Part 2, Motion JPEG | A codec the machine cannot decode opens as "no frames" |
| **Elementary stream** | Frames, grouped into GOPs around keyframes | Seeking lands on the nearest keyframe, not the frame you asked for |

A file extension tells you about the container and nothing about the codec. `CAP_PROP_FOURCC`
tells you what the decoder actually negotiated:

```python
from video_core import video

info = video.probe("data/video/street_day.mp4")
print(info.fourcc, info.backend)        # FMP4 FFMPEG  (MPEG-4 Part 2 inside an MP4)
print(info.width, info.height, info.fps, info.frame_count)
```

`FMP4` is the four-character code OpenCV reports for the `mp4v` encoder used by this
section's generator. It is not H.264, and it will not play in every browser - a trade-off
explained below.

## Frame rate, and what it does to everything downstream

Frame rate is nominal, not guaranteed. Three separate things are called "the frame rate":

1. **Nominal rate** - what the header says: `CAP_PROP_FPS`. Usually 10, 25, 30, or 60.
2. **Presentation timestamps** - when each frame should be shown. A variable-frame-rate
   (VFR) phone recording has no single rate; two consecutive frames may be 16 ms and 40 ms
   apart.
3. **Decode rate** - how fast your machine can actually read frames. This is what Lab 8
   measures, and it is a property of your hardware, not the file.

For analytics, only the second one is real. Frame `i` is at `t = i / fps` **only** for
constant-rate files. This section handles that honestly by deriving every timestamp from the
decoder and asserting the two agree:

```python
for index, stamp, frame in video.iter_frames(path, stride=5):
    # iter_frames yields the container's timestamp, so this asserts that the file really is
    # constant-rate. Lab 1 uses a 0.11 s window because MP4 timestamps are stored in
    # milliseconds and the generator's clock is not the decoder's.
    assert abs(stamp - index / info.fps) < 0.11, (index, stamp, index / info.fps)
```

If you work with phone footage, read the container's timestamps rather than dividing by a
nominal rate, and record in your report that you did.

## Resolution, aspect ratio, and the cost of both

Resolution is pixels per frame, and the number that matters for detection is not the frame's
width but the **pixels on the object**. A car that is 104 pixels wide in a 640-pixel frame is
42 pixels wide after the frame is resized to the detector's 256-pixel input. At 1080p the
same car, at the same distance from the camera, is 176 pixels wide and survives the resize
much better - which is why a model trained on 640x360 footage behaves differently on 1080p
feeds even though nothing about the model changed.

```python
note = video.aspect_note(info)     # '16:9 (1.78)'
```

Odd frame dimensions are a genuine hazard: many codecs require even width and height, and
OpenCV will happily open a writer for an odd size and then produce a file that cannot be
read. This section's writer refuses before writing anything:

```python
try:
    video.VideoWriter("out.mp4", fps=10, size=(641, 361))
except video.VideoError as exc:
    print(exc.reason)     # 'width and height must be even for mp4v/MJPG'
```

## Codecs: what actually works, and what it costs

The container/codec pair decides three things: whether the file plays where you need it,
how big it is, and whether a decoder on your machine can read it at all. The table below is
what was verified on this section's reference machine (Windows 11, Python 3.12,
`opencv-python-headless` 4.14.0), not what the documentation claims:

| FourCC | Container | Verified here | Notes |
| --- | --- | --- | --- |
| `mp4v` | `.mp4` | yes | MPEG-4 Part 2. Best size/quality of the working options; not H.264 |
| `MJPG` | `.avi` | yes | Every frame is a JPEG. Large files, trivially seekable, robust |
| `XVID` | `.avi` | yes | MPEG-4 Part 2 in AVI. Wide compatibility with older tools |
| `avc1` / `H264` | `.mp4` | **no** | Needs the OpenH264 library, which is not bundled. Fails at writer open |
| `VP80`/`VP90` | `.webm` | not bundled | Requires a build of OpenCV with VP8/VP9 support |

`avc1` failing is normal on a stock `opencv-python` wheel and is worth experiencing once. The
important design lesson is in how the failure is surfaced. OpenCV's `VideoWriter` returns an
object whose `isOpened()` is False and whose `write()` silently does nothing. Students end up
with a 0-byte MP4 and no exception. `video.VideoWriter` checks the codec against
`video.SUPPORTED_FOURCC`, verifies `isOpened()`, and raises `VideoError` with a reason:

```python
SUPPORTED_FOURCC = {"mp4v": ".mp4", "MJPG": ".avi", "XVID": ".avi"}
```

Compression is lossy and it changes your labels' accuracy. Re-encoding a clip at a lower
bitrate blurs small objects; a detector's recall on that clip drops even though the ground
truth did not change. Lab 9 of the computer vision section measures this for images; the same
logic applies per frame here.

### Why this section stores its video as `mp4v`

Because it is the encoder that exists everywhere the course runs, produces files small enough
to regenerate in two seconds, and can be decoded by the same OpenCV install that wrote it.
The cost is that the files do not play in a browser. If you need that, keep `mp4v` for the
pipeline and transcode once for distribution - and record which file was used for which
number.

## Keyframes, GOPs, and why seeking is approximate

Compressed video stores a **keyframe** (I-frame) every N frames and encodes the frames in
between as differences. Seeking to frame 137 usually decodes from the nearest keyframe at or
before it. Consequences:

- Random access costs more than sequential access; a per-frame random sampler can be an
  order of magnitude slower than a sequential read.
- A single corrupted frame can damage every frame until the next keyframe.
- Analytics pipelines that need low latency prefer short GOPs, at the cost of file size.

For a course pipeline the practical rule is: **read sequentially, decide what to keep, and
never seek per frame.**

## Timestamps, durations, and the lie in the header

`CAP_PROP_FRAME_COUNT` is a claim written by whatever produced the file. It is wrong often
enough that this section always compares it with a real decode:

```python
header = video.probe(path)                     # fast: header values only
truth  = video.probe(path, count_frames=True)  # decodes every frame; slow but honest
print(header.frame_count, truth.frame_count, truth.codec_note)
```

On this section's seven generated clips the two agree exactly (60 and 60), which is what makes
them a reliable teaching baseline. On truncated downloads, phone recordings, and files written
by streaming tools they frequently do not, and `VideoInfo.codec_note` records the discrepancy
rather than hiding it.

Duration follows from the decoded count, not the header:

\[
\text{duration} \approx \frac{\text{frames decoded}}{\text{fps}}
\]

Approximate, because of variable frame rate. That "≈" is why the counting lab reports a rate
in vehicles per second and treats the per-hour figure as an extrapolation with a note attached.

## Cheat sheet

| Question | Property | Trust it? |
| --- | --- | --- |
| Width, height | `CAP_PROP_FRAME_WIDTH/HEIGHT` | Yes, after decoding one frame and checking `shape` |
| Frame rate | `CAP_PROP_FPS` | Usually; verify against decoded timestamps for VFR files |
| Frame count | `CAP_PROP_FRAME_COUNT` | No. Decode and count when the number matters |
| Codec | `CAP_PROP_FOURCC` | Yes - it is what the decoder negotiated |
| Duration | derived | Approximate by construction |

## Checks

- [ ] You can explain the difference between a container and a codec without notes.
- [ ] You can name two reasons `CAP_PROP_FRAME_COUNT` might be wrong.
- [ ] You know which four FourCCs this machine writes, and why `avc1` is not one of them.
- [ ] You can compute the interval between samples given `fps` and `stride`, including the
      rounding, and state the error.
- [ ] You have looked at a `VideoInfo` for a file you did not generate and found one field
      you would not trust.
