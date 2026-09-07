# Importing the layers into QGIS

You should have `portals.csv`, `links.csv` and `fields.csv` from the
previous step. This guide targets the latest QGIS 3.x (English UI); menu
wording may vary slightly between point releases.

## 1. Add the three layers

Use **Layer > Add Layer > Add Delimited Text Layer...** for each file.

- **portals.csv** — Geometry definition: *Point coordinates*, X field =
  `lon`, Y field = `lat`. Geometry CRS: `EPSG:4326`.
- **links.csv** — Geometry definition: *Well known text (WKT)*, Geometry
  field = `wkt`. Geometry CRS: `EPSG:4326`.
- **fields.csv** — same as links.csv (WKT geometry, field `wkt`,
  `EPSG:4326`).

You should now see three layers: portal points, link lines and field
polygons, all in the right place on the map.

## 2. Enable the Temporal Controller on each layer

For each of the three layers:

1. Open **Layer Properties > Temporal**.
2. Set **Temporal feature source** to *Single field with date/time*.
3. Set the **Field** to `hora`.
4. Tick **Accumulate features over time** (sometimes labelled *"Accumulate
   Features"*) so that once a portal/link/field has appeared it stays on
   the map for the rest of the animation, instead of disappearing again on
   the next frame. This is what gives you the "building up" look rather
   than a blinking one.

## 3. Set the animation range

Open the **Temporal Controller** panel (**View > Panels > Temporal
Controller**, or its icon in the toolbar) and set:

- **Start** to the earliest `hora` value (the first portal's appearance,
  normally the `--base-date` you used, `+0s`).
- **End** to the latest `hora` value across all three layers — the summary
  printed by `op-video-planner` (or shown in the GUI log) tells you this
  timestamp directly.
- A **step** of 1 second, so every second of the operation gets its own
  frame.

Scrub the slider once to confirm portals, links and fields appear in the
right order before moving on to rendering.

Next: [`render_images.md`](render_images.md).
