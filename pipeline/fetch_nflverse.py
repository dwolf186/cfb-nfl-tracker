"""Download and cache nflverse roster + draft-picks CSVs.

Files are kept under data/cache/ and only re-downloaded when missing
or when refresh=True.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

log = logging.getLogger(__name__)

ROSTER_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/rosters/"
    "roster_{year}.csv"
)
DRAFT_PICKS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "draft_picks/draft_picks.csv"
)
PLAYERS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "players/players.csv"
)

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "cache"


def _download(url: str, dest: Path, timeout: int = 60, retries: int = 3) -> None:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            log.info("downloading %s (attempt %d)", url, attempt)
            r = requests.get(url, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            log.info("saved %s (%d bytes)", dest.name, len(r.content))
            return
        except requests.RequestException as e:
            last_err = e
            log.warning("download failed (%s); retrying in %ds", e, 2 * attempt)
            time.sleep(2 * attempt)
    raise RuntimeError(f"failed to download {url} after {retries} attempts: {last_err}")


def roster_path(year: int) -> Path:
    return CACHE_DIR / f"roster_{year}.csv"


def draft_picks_path() -> Path:
    return CACHE_DIR / "draft_picks.csv"


def players_path() -> Path:
    return CACHE_DIR / "players.csv"


def ensure_roster(year: int, refresh: bool = False) -> Path:
    path = roster_path(year)
    if path.exists() and not refresh:
        return path
    _download(ROSTER_URL.format(year=year), path)
    return path


def ensure_draft_picks(refresh: bool = False) -> Path:
    path = draft_picks_path()
    if path.exists() and not refresh:
        return path
    _download(DRAFT_PICKS_URL, path)
    return path


def ensure_players(refresh: bool = False) -> Path:
    path = players_path()
    if path.exists() and not refresh:
        return path
    _download(PLAYERS_URL, path)
    return path


def ensure_all(years: range | list[int], refresh: bool = False) -> None:
    for y in years:
        ensure_roster(y, refresh=refresh)
    ensure_draft_picks(refresh=refresh)
    ensure_players(refresh=refresh)
