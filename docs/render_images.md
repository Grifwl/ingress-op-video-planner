# Rendering the animation to PNG frames

With the Temporal Controller configured and the animation range set (see
[`qgis_import.md`](qgis_import.md)), you're ready to export a PNG per
frame.

## 1. Frame your map

Before exporting, zoom/pan the map canvas to roughly the extent you want in
the final video, with some empty margin on all sides so portals near the
edge of the operation don't end up flush against the video border. Style
the three layers however you like (portal icons, link/field colors, a
basemap, labels, etc.). You don't need to be precise about the exact
framing yet — the exact aspect ratio gets fixed in the export dialog, not
here.

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
- **Width/Height**: unlock the chain/lock icon next to these two fields
  (if it's linked, unlinking it lets you set both independently), then
  type `1920` and `1080` (Full HD, 16:9 — YouTube's standard resolution)
  directly. Don't try to resize the on-screen map canvas panel to match —
  QGIS never stretches the map to fit a pixel size; it keeps the map scale
  fixed and grows the *visible extent* outward, symmetrically on every
  side, to match whatever width/height you type. The main map canvas won't
  visually refresh while the export dialog is open, but the extent values
  shown in the dialog itself do update live as you change width/height —
  you can watch them expand equally in every direction from the center you
  had framed.

Because the extent only ever grows outward from what you had framed in
step 1, it can't crop anything that was already comfortably inside — it
only adds empty margin. So as long as you left reasonable margin around
the operation before opening the dialog, you're safe. If you want to be
extra sure, export and open the first and last PNG afterwards; if
anything looks tight, add more margin to the framing and export again.

Click **Export** and QGIS renders one PNG per second of the animation
range into your chosen folder. Open the first and last frame afterwards
and check the whole operation is comfortably inside the frame, with no
portal or field touching the edge.

Next: [`make_video.md`](make_video.md).
