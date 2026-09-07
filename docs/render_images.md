# Rendering the animation to PNG frames

With the Temporal Controller configured and the animation range set (see
[`qgis_import.md`](qgis_import.md)), you're ready to export a PNG per
frame.

## 1. Frame your map

Before exporting, zoom/pan the map canvas to the extent you want in the
final video, and style the three layers however you like (portal icons,
link/field colors, a basemap, labels, etc.) — whatever is on the canvas
when you export is what ends up in the video.

## 2. Export the animation

In the **Temporal Controller** panel, click **Export Animation** (the
film-strip icon).

- **Output directory**: pick an empty folder for the frames.
- **Filename template**: use a name ending in a run of `#` characters,
  e.g. `sample_####` — each `#` becomes one digit of the frame number
  (four `#` gives `0001.png`, `0002.png`, ...).
- **Frame rate**: leave at `1` frame per second of animation time — the
  operation's own timestamps already carry the pacing; you'll set the
  *video's* playback smoothness later, in `ffmpeg`.
- **Width/Height**: pick your target video resolution (e.g. 1920x1080).

Click **Export** and QGIS renders one PNG per second of the animation
range into your chosen folder.

Next: [`make_video.md`](make_video.md).
