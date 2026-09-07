"""Core conversion logic: operation plan -> QGIS animation layers.

This module has no dependency on how it is invoked (command line or GUI):
:func:`generate_animation_data` is the single entry point both front ends
call.

Timing model (seconds from the start of the video)
----------------------------------------------------
- "The first portal" is the one portal that never acts as a link Origin
  (zero out-degree). It appears at t = 0.
- Every other portal appears ``appear_gap`` seconds after the *end of the
  last action* of the portal introduced immediately before it (in order of
  first use). If that previous portal never launched any link, "its last
  action" is just its own appearance time.
- A portal's first outgoing link fires ``first_link_delay`` seconds after
  the portal appears.
- Each subsequent link from the same portal fires ``link_gap`` seconds
  after the *end* of the previous link's action (end = link time + however
  many fields that link closes: 0, 1 or 2).
- A link's fields appear 1s (and 2s, if it closes a second field) after the
  link itself.

This assumes the plan visits each portal in one contiguous block (all of a
portal's outgoing links happen back-to-back before moving to the next
origin portal), which is typical of manually ordered "no backtracking" op
designs. :func:`generate_animation_data` checks this assumption and reports
a warning through the ``warn`` callback if it is violated, since the timing
model has not been extended to cover that case.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Tuple

Coordinates = Dict[str, Tuple[float, float]]
LinkRecord = Dict[str, object]


def load_portal_coordinates(keys_path: str) -> Coordinates:
    """Read portal names and coordinates from a RESWUE "keys" export.

    Args:
        keys_path: Path to the keys CSV. Must have a "Portal" column and an
            "IITC" column containing an intel.ingress.com URL with a
            ``pll=lat,lon`` query parameter. Other columns are ignored.

    Returns:
        A mapping from portal name to its ``(lat, lon)`` coordinates.
    """
    coords: Coordinates = {}
    with open(keys_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Portal"]
            url = row["IITC"]
            pll = url.split("pll=")[1]
            lat, lon = pll.split(",")
            coords[name] = (float(lat), float(lon))
    return coords


def load_links(links_path: str) -> List[LinkRecord]:
    """Read the ordered link plan from a RESWUE "links" export.

    Args:
        links_path: Path to the links CSV. Must have "Nr", "Origin" and
            "Destination" columns; any other columns (Comment, Fields,
            Length, Keys...) are ignored. Field counts are always
            re-derived from the link graph rather than trusted from a
            "Fields" column, so this works even when that column is
            missing or wrong.

    Returns:
        Link records sorted by execution order (``nr``), each with
        ``nr``, ``origin`` and ``dest`` keys.
    """
    links: List[LinkRecord] = []
    with open(links_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            links.append({
                "nr": int(row["Nr"]),
                "origin": row["Origin"],
                "dest": row["Destination"],
            })
    links.sort(key=lambda r: r["nr"])
    return links


def derive_link_fields(links: List[LinkRecord]) -> Dict[int, List[str]]:
    """Derive which fields (triangles) each link closes, in plan order.

    A link closes a field with every portal that is already linked to both
    of its endpoints at the moment the link is made, so the field set is
    computed incrementally by replaying the plan link by link rather than
    trusted from the source data.

    Args:
        links: Link records in execution order, as returned by
            :func:`load_links`.

    Returns:
        A mapping from link ``nr`` to the (sorted) list of third-portal
        names whose fields that link closes.
    """
    adjacency: Dict[str, set] = {}

    def add_edge(a: str, b: str) -> None:
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    link_fields: Dict[int, List[str]] = {}
    for link in links:
        origin, dest = link["origin"], link["dest"]
        common = sorted(adjacency.get(origin, set()) & adjacency.get(dest, set()))
        link_fields[link["nr"]] = common
        add_edge(origin, dest)
    return link_fields


def identify_first_portal(links: List[LinkRecord], warn: Callable[[str], None]) -> str:
    """Identify the one portal that starts the operation.

    The first portal is defined as the portal that never acts as a link
    Origin (every other portal launches at least one link during the plan).

    Args:
        links: Link records in execution order.
        warn: Callback invoked with a human-readable message if the plan
            does not have exactly one such portal.

    Returns:
        The name of the first portal.
    """
    origins = {link["origin"] for link in links}
    destinations = {link["dest"] for link in links}
    never_origin = destinations - origins
    if len(never_origin) != 1:
        warn(
            f"Expected exactly one never-origin ('first') portal, found "
            f"{len(never_origin)}: {sorted(never_origin)}. Falling back to "
            "the destination of link Nr=1 as the first portal."
        )
        first_link = min(links, key=lambda link: link["nr"])
        return first_link["dest"]
    return next(iter(never_origin))


def group_into_blocks(
    links: List[LinkRecord], warn: Callable[[str], None]
) -> List[Tuple[str, List[LinkRecord]]]:
    """Group consecutive links sharing the same Origin into blocks.

    Args:
        links: Link records in execution order.
        warn: Callback invoked once per portal that resumes as an Origin
            after another portal has already taken over, since the timing
            model assumes each portal's links happen back-to-back.

    Returns:
        A list of ``(origin, links_from_that_origin)`` pairs, in the order
        each origin was first used.
    """
    blocks: List[Tuple[str, List[LinkRecord]]] = []
    for link in links:
        if blocks and blocks[-1][0] == link["origin"]:
            blocks[-1][1].append(link)
        else:
            blocks.append((link["origin"], [link]))

    seen_origins = set()
    for origin, _ in blocks:
        if origin in seen_origins:
            warn(
                f"Portal '{origin}' acts as origin again later in the plan "
                "(non-contiguous). The timing model assumes each portal's "
                "links happen back-to-back; results may be off."
            )
        seen_origins.add(origin)
    return blocks


def compute_timings(
    first_portal: str,
    blocks: List[Tuple[str, List[LinkRecord]]],
    link_fields: Dict[int, List[str]],
    appear_gap: int,
    first_link_delay: int,
    link_gap: int,
) -> Tuple[Dict[str, int], Dict[int, int]]:
    """Compute the appearance time of every portal and the fire time of every link.

    Args:
        first_portal: Name of the portal that appears at t = 0.
        blocks: Per-origin link groups, as returned by
            :func:`group_into_blocks`.
        link_fields: Fields each link closes, as returned by
            :func:`derive_link_fields`.
        appear_gap: Seconds after the previous portal's last action that
            the next portal appears.
        first_link_delay: Seconds after a portal appears that its first
            outgoing link fires.
        link_gap: Seconds after the end of a link's action that the next
            link from the same portal fires.

    Returns:
        A ``(portal_time, link_time)`` pair of second-offsets keyed by
        portal name and link ``nr`` respectively.
    """
    link_time: Dict[int, int] = {}
    portal_time: Dict[str, int] = {first_portal: 0}
    last_action_time: Dict[str, int] = {first_portal: 0}

    prev_portal = first_portal
    for origin, block_links in blocks:
        appear = last_action_time[prev_portal] + appear_gap
        portal_time[origin] = appear

        prev_link_end = None
        for i, link in enumerate(block_links):
            t = appear + first_link_delay if i == 0 else prev_link_end + link_gap
            link_time[link["nr"]] = t
            n_fields = len(link_fields[link["nr"]])
            prev_link_end = t + n_fields

        last_action_time[origin] = prev_link_end
        prev_portal = origin

    return portal_time, link_time


def write_portals_csv(
    out_path: str, coords: Coordinates, portal_time: Dict[str, int], to_timestamp: Callable[[int], str]
) -> None:
    """Write the portals layer, one row per portal ordered by appearance time."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nom", "lat", "lon", "hora"])
        for name in sorted(portal_time, key=lambda p: portal_time[p]):
            lat, lon = coords[name]
            writer.writerow([name, lat, lon, to_timestamp(portal_time[name])])


def write_links_csv(
    out_path: str,
    links: List[LinkRecord],
    coords: Coordinates,
    link_time: Dict[int, int],
    to_timestamp: Callable[[int], str],
) -> None:
    """Write the links layer as WKT ``LINESTRING`` geometries."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nom", "hora", "wkt"])
        for link in links:
            origin, dest = link["origin"], link["dest"]
            lat1, lon1 = coords[origin]
            lat2, lon2 = coords[dest]
            name = f"Link {link['nr']}: {origin} -> {dest}"
            wkt = f"LINESTRING({lon1} {lat1}, {lon2} {lat2})"
            writer.writerow([name, to_timestamp(link_time[link["nr"]]), wkt])


def write_fields_csv(
    out_path: str,
    links: List[LinkRecord],
    coords: Coordinates,
    link_fields: Dict[int, List[str]],
    link_time: Dict[int, int],
    to_timestamp: Callable[[int], str],
) -> List[Tuple[str, int]]:
    """Write the fields layer as WKT ``POLYGON`` geometries.

    Returns:
        The list of ``(field_name, appearance_second)`` pairs written, so
        callers can compute the overall timeline length.
    """
    fields: List[Tuple[str, int, List[str]]] = []
    for link in links:
        link_start = link_time[link["nr"]]
        for i, third in enumerate(link_fields[link["nr"]], start=1):
            origin, dest = link["origin"], link["dest"]
            name = f"Field {origin} - {dest} - {third}"
            fields.append((name, link_start + i, [origin, dest, third]))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nom", "hora", "wkt"])
        for name, appear_second, portal_names in fields:
            ring = [coords[p] for p in portal_names] + [coords[portal_names[0]]]
            wkt_points = ", ".join(f"{lon} {lat}" for lat, lon in ring)
            writer.writerow([name, to_timestamp(appear_second), f"POLYGON(({wkt_points}))"])

    return [(name, appear_second) for name, appear_second, _ in fields]


def generate_animation_data(
    keys_path: str,
    links_path: str,
    out_dir: str,
    base_date: str = "2026-01-01 00:00:00",
    appear_gap: int = 5,
    first_link_delay: int = 2,
    link_gap: int = 3,
    warn: Callable[[str], None] = print,
) -> dict:
    """Convert a RESWUE operation export into three QGIS animation layers.

    Writes ``portals.csv``, ``links.csv`` and ``fields.csv`` to ``out_dir``.

    Args:
        keys_path: Path to the RESWUE "keys" export (portal list).
        links_path: Path to the RESWUE "links" export (ordered link plan).
        out_dir: Directory the three output CSVs are written to; created
            if it does not already exist.
        base_date: Arbitrary reference datetime used as t = 0, formatted
            as ``YYYY-MM-DD HH:MM:SS``.
        appear_gap: Seconds after the previous portal's last action that
            the next portal appears.
        first_link_delay: Seconds after a portal appears that its first
            outgoing link fires.
        link_gap: Seconds after the end of a link's action that the next
            link from the same portal fires.
        warn: Callback used to report non-fatal warnings (e.g. a plan that
            revisits a portal as origin). Defaults to :func:`print`; a GUI
            front end can pass something that appends to a log widget
            instead.

    Returns:
        A summary dict with ``portals``, ``links``, ``fields`` counts and
        the ``start``/``end`` timestamps of the rendered timeline.
    """
    os.makedirs(out_dir, exist_ok=True)
    base = datetime.strptime(base_date, "%Y-%m-%d %H:%M:%S")

    def to_timestamp(seconds: int) -> str:
        return (base + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")

    coords = load_portal_coordinates(keys_path)
    links = load_links(links_path)
    link_fields = derive_link_fields(links)
    first_portal = identify_first_portal(links, warn)
    blocks = group_into_blocks(links, warn)
    portal_time, link_time = compute_timings(
        first_portal, blocks, link_fields, appear_gap, first_link_delay, link_gap
    )

    # Portals that never launch a link (dead ends) never got a portal_time
    # entry from compute_timings, which only walks origins. They are still
    # part of the operation, so default them to t = 0 rather than dropping
    # them from the output.
    for portal in coords:
        portal_time.setdefault(portal, 0)

    write_portals_csv(os.path.join(out_dir, "portals.csv"), coords, portal_time, to_timestamp)
    write_links_csv(os.path.join(out_dir, "links.csv"), links, coords, link_time, to_timestamp)
    fields = write_fields_csv(
        os.path.join(out_dir, "fields.csv"), links, coords, link_fields, link_time, to_timestamp
    )

    field_seconds = [second for _, second in fields]
    total_end = max([*link_time.values(), *field_seconds]) if field_seconds else max(link_time.values())

    return {
        "portals": len(portal_time),
        "links": len(links),
        "fields": len(fields),
        "start": to_timestamp(0),
        "end": to_timestamp(total_end),
        "duration_seconds": total_end,
    }
