# Rendering the animation to PNG frames

With the Temporal Controller configured and the animation range set (see
[`qgis_import.md`](qgis_import.md)), you're ready to export a PNG per
frame.

## 1. Frame your map

Before exporting, zoom/pan the map canvas to the extent you want in the
final video, and style the three layers however you like (portal icons,
link/field colors, a basemap, labels, etc.) — whatever is on the canvas
when you export is what ends up in the video.

**Get the aspect ratio right before you touch the extent.** YouTube's
standard playback frame is 16:9 (e.g. 1920×1080). If you frame the map
freely and only fix the pixel size in the export dialog afterwards, QGIS
will export exactly the width/height you type — but the *content* you
framed may end up stretched, cropped, or floating with big empty margins
if your map canvas wasn't already 16:9 when you framed it (this is what
happened in the test render: 1618×704 is roughly 2.3:1, not 16:9). To
avoid that:

1. Resize the QGIS map canvas panel itself (drag its edges, or maximize
   the window and undock/resize the panel) until it is proportioned 16:9
   — you don't need the exact pixel count, just the ratio; the export step
   below will scale it to the exact resolution.
2. *Then* zoom/pan to frame the operation, with some empty margin on all
   sides so portals near the edge of the operation don't sit flush against
   the video border.

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
- **Width/Height**: `1920` × `1080` (Full HD, 16:9 — YouTube's standard
  resolution). Keep **Lock aspect ratio** enabled: since the canvas is
  already 16:9 from step 1, this exports at the exact target resolution
  without distorting or cropping anything. If you'd left the canvas at an
  arbitrary shape, a locked aspect ratio here would preserve *that* shape
  instead, not fix it — the ratio has to be right before you get here.

Click **Export** and QGIS renders one PNG per second of the animation
range into your chosen folder. Open the first and last frame afterwards
and check the whole operation is comfortably inside the frame, with no
portal or field touching the edge.

Next: [`make_video.md`](make_video.md).
