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

## Adding background music

This second command hasn't been tested against a real track yet — treat it
as a solid starting point to tune once you have music to try it with.

```bash
# 1. Get the silent video's duration
ffprobe -v error -show_entries format=duration -of csv=p=0 sample_fade.mp4
# -> e.g. 254.0

# 2. Mix in the music: loop it if it's shorter than the video, trim it to
#    the video's exact length, and fade the last 3 seconds so it doesn't
#    cut off abruptly.
ffmpeg -i sample_fade.mp4 -stream_loop -1 -i music.mp3 \
  -filter_complex "[1:a]atrim=0:254.0,afade=t=out:st=251.0:d=3[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k -shortest \
  sample_final.mp4
```

Replace `254.0` (the video duration from step 1) and `251.0`
(`duration - 3`, where the fade-out starts) with your own numbers.

- `-stream_loop -1` loops the music track indefinitely, so a short song
  never runs out before the video ends.
- `atrim=0:254.0` cuts the (possibly looped) audio down to exactly the
  video's length.
- `afade=t=out:st=251.0:d=3` fades the last 3 seconds of audio to silence.
- `-c:v copy` re-uses the already-encoded video stream as-is (fast, no
  quality loss); only the audio gets (re-)encoded.
- `-shortest` is a safety net in case the trim/fade math is slightly off.
