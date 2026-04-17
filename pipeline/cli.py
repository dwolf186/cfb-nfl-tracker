"""CLI entrypoint: `python -m pipeline.cli`."""
from __future__ import annotations

import argparse
import logging

from . import build_dataset, fetch_nflverse


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CFB → NFL talent dataset")
    parser.add_argument("--year", type=int, help="Run pipeline for a single CFB season (useful for testing)")
    parser.add_argument("--refresh-cache", action="store_true", help="Force re-download of nflverse CSVs")
    parser.add_argument("--skip-fetch", action="store_true", help="Use cached CSVs only — no network for nflverse")
    parser.add_argument("--no-ap-network", action="store_true", help="Skip AP poll web scraping; use hardcoded fallback")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    years = list(build_dataset.YEARS)

    if not args.skip_fetch:
        fetch_nflverse.ensure_all(years, refresh=args.refresh_cache)

    build_dataset.build(
        years=years,
        allow_network=not args.no_ap_network,
        only_year=args.year,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
