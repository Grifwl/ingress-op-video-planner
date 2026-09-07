# Building the video with ffmpeg

You should have a folder of numbered PNG frames from
[`render_images.md`](render_images.md) (e.g. `sample_0001.png`,
`sample_0002.png`, ...).

## Silent video

```bash
ffmpeg -framerate 1 -i sample_%04d.png \
  -vf "minterpolate=fps=25:mi_mode=blend" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 \
  sample_fade.mp4
```

- `-framerate 1` tells ffmpeg each input PNG represents one second of
  animation time (matching the QGIS export rate).
- `minterpolate=fps=25:mi_mode=blend` generates smooth in-between frames up
  to 25 fps by blending consecutive stills, instead of a jarring 1 fps
  slideshow.
- `-crf 18` is visually near-lossless; raise it (e.g. 23) for a smaller
  file if the video is only going to be shared online.

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

```bash
# 1. Get the silent video's duration
ffprobe -v error -show_entries format=duration -of csv=p=0 sample_fade.mp4
# -> e.g. 298.04

# 2. Mix in the music: loop it if it's shorter than the video, trim it to
#    the video's exact length, and fade the last 3 seconds so it doesn't
#    cut off abruptly.
ffmpeg -i sample_fade.mp4 -stream_loop -1 -i music.mp3 \
  -filter_complex "[1:a]atrim=0:298.04,afade=t=out:st=295.04:d=3[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k -shortest \
  sample_final.mp4
```

Replace `298.04` (the video duration from step 1) and `295.04`
(`duration - 3`, where the fade-out starts) with your own numbers.

- `-stream_loop -1` loops the music track indefinitely, so a short song
  never runs out before the video ends.
- `atrim=0:298.04` cuts the (possibly looped) audio down to exactly the
  video's length.
- `afade=t=out:st=295.04:d=3` fades the last 3 seconds of audio to silence.
- `-c:v copy` re-uses the already-encoded video stream as-is (fast, no
  quality loss); only the audio gets (re-)encoded.
- `-shortest` is a safety net in case the trim/fade math is slightly off.
