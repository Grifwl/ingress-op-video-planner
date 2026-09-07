# Ingress Operation Video Planner

Turn an Ingress fielding-operation plan into a timed, animated video: a
small Python tool converts your operation export into three timestamped
layers, QGIS's Temporal Controller animates them and renders a frame
sequence, and `ffmpeg` stitches those frames into an MP4 (with background
music, if you want it).

No AI, no cloud service, nothing running in the background — everything
here happens locally, once, on files you already have.

## The pipeline

```
RESWUE export (two CSVs)
        |
        v
op-video-planner  ->  portals.csv, links.csv, fields.csv
        |
        v
QGIS (Temporal Controller)  ->  PNG frame sequence
        |
        v
ffmpeg  ->  final MP4 (+ background music)
```

## Requirements

You'll need three things installed:

1. **Python 3.9+** — to run `op-video-planner` from source, or skip this
   entirely and use the prebuilt executable from the
   [Releases](../../releases) page instead.
   Download: https://www.python.org/downloads/
2. **QGIS 3.x** — to render the animation frames.
   Download: https://qgis.org/download/
3. **ffmpeg** — to encode the frames into a video.
   Download: https://ffmpeg.org/download.html

## 1. Get your matches out of RESWUE

Open the app, head to **Import/Export**, and pull your two exports:
contacts (**Keys** to my Heart) and your working order for them (Matches
**Plan**).

- **Keys** to my Heart — your portal roster: columns `Portal, IITC, keys
  required, keys farmed`.
- Matches **Plan** — the order you're going to work through them: columns
  `Nr, Origin, Destination, ...`.

Both are plain CSV files — keep them somewhere handy, you'll point the tool
at them next.

## 2. Generate the QGIS layers

### Option A — GUI (no terminal needed)

Download the executable for your OS from the [Releases](../../releases)
page and run it. Pick your two RESWUE exports, pick an output folder, hit
**Generate**. That's it — you now have `portals.csv`, `links.csv` and
`fields.csv` in the output folder.

### Option B — command line

```bash
pip install .
op-video-planner --keys keys_export.csv --links links_export.csv --out ./layers
```

Useful flags (all optional — the defaults match a comfortable default
pacing):

| Flag | Meaning | Default |
| --- | --- | --- |
| `--base-date` | Reference datetime used as t = 0 | `2026-01-01 00:00:00` |
| `--appear-gap` | Seconds before the next portal appears after the previous one's last action | `5` |
| `--first-link-delay` | Seconds after a portal appears before its first link fires | `2` |
| `--link-gap` | Seconds between the end of one link's action and the next link from the same portal | `3` |

### What you get

- `portals.csv` — one row per portal, with its coordinates and the second
  it first appears (`nom, lat, lon, hora`).
- `links.csv` — one row per link, as a WKT `LINESTRING`, timestamped to
  when it fires (`nom, hora, wkt`).
- `fields.csv` — one row per field closed, as a WKT `POLYGON`, timestamped
  to just after the link that closes it (`nom, hora, wkt`).

## 3. Import into QGIS and render frames

See [`docs/qgis_import.md`](docs/qgis_import.md) for loading the three CSVs
and setting up the Temporal Controller, and
[`docs/render_images.md`](docs/render_images.md) for exporting the PNG
frame sequence.

## 4. Build the video

See [`docs/make_video.md`](docs/make_video.md) for the `ffmpeg` commands —
one for a plain silent video, one for adding background music.

## License

MIT — see [LICENSE](LICENSE).
