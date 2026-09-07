# Building the video with ffmpeg

You should have a folder of numbered PNG frames from
[`render_images.md`](render_images.md) named `frame_0001.png`,
`frame_0002.png`, etc. (using that exact filename template in QGIS means
the commands below work unchanged, without editing them for your own
operation).

## Silent video

```bash
ffmpeg -framerate 1 -i frame_%04d.png \
  -vf "minterpolate=fps=25:mi_mode=blend" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 \
  silent.mp4
```

- `-framerate 1` tells ffmpeg each input PNG represents one second of
  animation time (matching the QGIS export rate).
- `minterpolate=fps=25:mi_mode=blend` generates smooth in-between frames up
  to 25 fps by blending consecutive stills, instead of a jarring 1 fps
  slideshow.
- `-crf 18` is visually near-lossless; raise it (e.g. 23) for a smaller
  file if the video is only going to be shared online.

### Smaller file size

The settings above favor quality over size. If the file is too heavy to
share comfortably, two flags matter far more than anything else, and they
combine:

```bash
ffmpeg -framerate 1 -i frame_%04d.png \
  -vf "minterpolate=fps=12:mi_mode=blend" \
  -c:v libx264 -pix_fmt yuv420p -crf 23 \
  silent_small.mp4
```

- Lowering the interpolation target (`fps=12` instead of `fps=25`) simply
  means fewer frames to encode. This is the single biggest lever — for
  content like this (portals/links/fields slowly appearing, not fast
  motion), 12fps still reads as smooth.
- Raising `-crf` (18 → 23) asks the encoder for a lower bitrate at the
  same resolution; 23 is still good quality for online sharing, just no
  longer "near-lossless".

Measured on a real 300-frame, 1920×1080, 298s render:

| Settings | File size | Change |
| --- | --- | --- |
| `fps=25`, `crf 18` (quality settings above) | 9.4 MB | — |
| `fps=12`, `crf 18` | 5.6 MB | -40% |
| `fps=25`, `crf 23` | 7.2 MB | -23% |
| `fps=12`, `crf 23` (combined, settings above) | 4.3 MB | -54% |

A slower `-preset` (e.g. `veryslow`) is often suggested for smaller files
at unchanged quality, but tested against this same footage it made no
difference (in fact came out very slightly larger than the default
`medium` preset) — not worth the much longer encode time here.

If the video is headed for YouTube, keep in mind YouTube re-encodes
whatever you upload anyway, so there's little reason to keep a
near-lossless local master just to upload it — the smaller settings above
are a safe default for that use case.

### Why the output is a couple of seconds shorter than the frame count

If you exported, say, 300 PNG frames at one frame per second, you might
expect exactly 300 seconds of video — but `ffprobe` will report something
like 298.04s. This is expected, and the shortfall doesn't depend on how
many frames you have: it's a fixed amount, not proportional to the length
of the sequence.

The cause is `minterpolate` itself, not your QGIS export or frame count.
Instead of just repeating stills, `minterpolate` generates each in-between
frame by estimating motion *between* two real, consecutive source frames.
That means it always needs one real frame before and one real frame after
the point it's interpolating. Right at the very end of the sequence there
is no "next" real frame to interpolate towards, so the filter cannot
produce that last stretch of output and trims it off — always the same
fixed amount (about 49 output frames at 25fps ≈ 1.96s), regardless of how
long the source sequence is. It's an edge effect of the interpolation
algorithm, not a bug in the pipeline or a sign that a frame is missing.

## Adding background music

Validated against a real render (300 frames) and a real music track from
the YouTube Audio Library.

**macOS / Linux / Git Bash (bash or zsh):**

```bash
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 silent.mp4) && \
FADE_START=$(awk "BEGIN{print $DURATION - 3}") && \
ffmpeg -i silent.mp4 -stream_loop -1 -i music.mp3 \
  -filter_complex "[1:a]atrim=0:$DURATION,afade=t=out:st=$FADE_START:d=3[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k -shortest \
  output.mp4
```

**Windows (PowerShell):**

```powershell
$DURATION = ffprobe -v error -show_entries format=duration -of csv=p=0 silent.mp4
$FADE_START = $DURATION - 3
ffmpeg -i silent.mp4 -stream_loop -1 -i music.mp3 -filter_complex "[1:a]atrim=0:${DURATION},afade=t=out:st=${FADE_START}:d=3[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest output.mp4
```

`silent.mp4` here can just be the file dragged straight in from the
previous step (or `silent_small.mp4` if you used the smaller-size
variant). `output.mp4` is a placeholder — rename it to whatever you want
the final video called before running the command.

Both versions compute the video's duration itself with `ffprobe`
(`DURATION`), and where the 3-second fade-out should start (`FADE_START`,
`duration - 3`), then feed both straight into the `ffmpeg` filter — no
numbers to edit by hand. In bash this needs `awk` for the subtraction,
since bash can't do decimal arithmetic on its own; PowerShell converts the
text to a number automatically. Either way, send the whole thing as one
single command — in bash the `\` line continuations matter (or paste it
as one line); in PowerShell each line runs in the same session as long as
you paste all of them together. `$DURATION`/`$FADE_START` only exist for
the shell process that set them, so running these as separate commands
loses the variables in between.

In the PowerShell version, `${DURATION}` and `${FADE_START}` are written
with curly braces rather than plain `$DURATION`/`$FADE_START` — inside a
double-quoted string, PowerShell treats `$FADE_START:d` as an attempt to
read a scope-qualified variable (like `$env:PATH`), not "the variable
followed by literal `:d`", which silently breaks the filter string. The
curly braces remove the ambiguity.

- `-stream_loop -1` loops the music track indefinitely, so a short song
  never runs out before the video ends.
- `atrim=0:$DURATION` cuts the (possibly looped) audio down to exactly the
  video's length.
- `afade=t=out:st=$FADE_START:d=3` fades the last 3 seconds of audio to
  silence.
- `-c:v copy` re-uses the already-encoded video stream as-is (fast, no
  quality loss); only the audio gets (re-)encoded.
- `-shortest` is a safety net in case the trim/fade math is slightly off.

### Step by step (optional)

Equivalent to the one-liner above, useful if you want to see the duration
before running ffmpeg, or plug the numbers in manually:

```bash
# 1. Get the silent video's duration
ffprobe -v error -show_entries format=duration -of csv=p=0 silent.mp4
# -> e.g. 298.04

# 2. Mix in the music: loop it if it's shorter than the video, trim it to
#    the video's exact length, and fade the last 3 seconds so it doesn't
#    cut off abruptly.
ffmpeg -i silent.mp4 -stream_loop -1 -i music.mp3 \
  -filter_complex "[1:a]atrim=0:298.04,afade=t=out:st=295.04:d=3[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k -shortest \
  output.mp4
```

Replace `298.04` (the video duration from step 1) and `295.04`
(`duration - 3`, where the fade-out starts) with your own numbers.
