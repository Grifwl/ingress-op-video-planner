"""Command-line front end for the operation-to-QGIS-layers conversion."""

from __future__ import annotations

import argparse

from op_video_planner.convert import generate_animation_data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the ``op-video-planner`` CLI.

    Args:
        argv: Argument list to parse; defaults to ``sys.argv[1:]`` when
            ``None`` (the normal case, overridable for tests).

    Returns:
        The parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate portals.csv, links.csv and fields.csv for an "
        "Ingress fielding-operation animation, ready to import into QGIS "
        "with the Temporal Controller."
    )
    parser.add_argument("--keys", required=True, help="Path to the RESWUE keys export (portal list)")
    parser.add_argument("--links", required=True, help="Path to the RESWUE links export (ordered link plan)")
    parser.add_argument("--out", default=".", help="Output directory for portals.csv / links.csv / fields.csv")
    parser.add_argument(
        "--base-date",
        default="2026-01-01 00:00:00",
        help="Arbitrary reference datetime for t=0 (format: 'YYYY-MM-DD HH:MM:SS')",
    )
    parser.add_argument(
        "--appear-gap",
        type=int,
        default=5,
        help="Seconds after the previous portal's last action that a new portal appears",
    )
    parser.add_argument(
        "--first-link-delay",
        type=int,
        default=2,
        help="Seconds after a portal appears that its first outgoing link fires",
    )
    parser.add_argument(
        "--link-gap",
        type=int,
        default=3,
        help="Seconds after the end of a link's action that the next link from the same portal fires",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``op-video-planner`` console script."""
    args = parse_args(argv)
    summary = generate_animation_data(
        keys_path=args.keys,
        links_path=args.links,
        out_dir=args.out,
        base_date=args.base_date,
        appear_gap=args.appear_gap,
        first_link_delay=args.first_link_delay,
        link_gap=args.link_gap,
    )
    print(f"Portals: {summary['portals']}  Links: {summary['links']}  Fields: {summary['fields']}")
    print(
        f"Timeline: {summary['start']} -> {summary['end']} "
        f"({summary['duration_seconds']} seconds)"
    )


if __name__ == "__main__":
    main()
