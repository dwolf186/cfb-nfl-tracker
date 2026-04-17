"""AP Top 25 retrieval.

Tries to fetch the final post-bowl AP poll for a given season from a public
source; falls back to the hardcoded dict in `ap_poll_data.py`.

Strategy (in order):
  1. Sports Reference `years/{year}-polls.html` — has a stable table with a
     `Final` column that is exactly the final AP poll post-bowl.
  2. Wikipedia season rankings article — variable structure; a best-effort
     pandas.read_html scrape.
  3. Hardcoded fallback (`ap_poll_data.py`).

Any successful fetch is run through `normalize` so returned names match the
same canonical forms produced by the roster pipeline.
"""
from __future__ import annotations

import logging
import re
import time
from io import StringIO
from typing import Callable

import pandas as pd
import requests

from . import ap_poll_data
from .normalize import normalize_college

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (cfb-nfl-tracker/0.1; +https://github.com/local/cfb-nfl-tracker)"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}


def _get(url: str, timeout: int = 20) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
        log.debug("GET %s -> %d", url, r.status_code)
    except requests.RequestException as e:
        log.debug("GET %s failed: %s", url, e)
    return None


def _fetch_sports_reference(year: int) -> list[str] | None:
    url = f"https://www.sports-reference.com/cfb/years/{year}-polls.html"
    html = _get(url)
    if html is None:
        return None
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError:
        return None
    # The polls page has one large table per poll. Pick the AP table — it's the
    # first on the page and contains a "Final" column (post-bowl rank).
    for t in tables:
        cols = {str(c).strip() for c in t.columns.get_level_values(-1)}
        if {"School", "Final"}.issubset(cols):
            df = t.copy()
            df.columns = [str(c[-1]).strip() for c in df.columns.to_flat_index()] if isinstance(df.columns, pd.MultiIndex) else [str(c).strip() for c in df.columns]
            df = df[df["Final"].notna() & (df["Final"].astype(str).str.strip() != "")]
            try:
                df["Final"] = pd.to_numeric(df["Final"], errors="coerce")
            except Exception:
                return None
            df = df.dropna(subset=["Final"]).sort_values("Final")
            df = df[df["Final"] <= 25]
            names = [normalize_college(str(s)) for s in df["School"].tolist()]
            if len(names) >= 20:
                return names[:25]
    return None


_WIKI_SEASON_URL = (
    "https://en.wikipedia.org/wiki/{year}_NCAA_Division_I_FBS_football_rankings"
)


_WIKI_NAME_CLEAN = re.compile(r"\s*\((?:\d+|no\.\s*\d+|tied?)\)\s*$", re.IGNORECASE)


def _clean_wiki_name(s: str) -> str:
    s = re.sub(r"\[.*?\]", "", str(s)).strip()
    # Strip trailing "(NN)" first-place-vote / point counts: e.g. "Alabama (54)".
    s = _WIKI_NAME_CLEAN.sub("", s).strip()
    # Strip leading ranking numbers like "1. " or "1 ".
    s = re.sub(r"^\d+\.?\s+", "", s).strip()
    return s


def _fetch_wikipedia(year: int) -> list[str] | None:
    html = _get(_WIKI_SEASON_URL.format(year=year))
    if html is None:
        return None
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError:
        return None
    # Wikipedia rankings articles have one table per week plus a final table.
    # The FINAL post-bowl AP poll is the last matching table on the page, so
    # iterate in reverse and return the first one we find with 25 distinct names.
    for t in reversed(tables):
        if t.shape[0] < 20 or t.shape[0] > 35:
            continue
        text_cols = [c for c in t.columns if t[c].dtype == object]
        for col in text_cols:
            series = t[col].astype(str).map(_clean_wiki_name)
            non_numeric = series[~series.str.match(r"^\d+$", na=False) & (series != "")]
            if len(non_numeric) >= 20:
                names = [normalize_college(s) for s in non_numeric.tolist()[:25]]
                if len(set(names)) >= 20:
                    return names
    return None


_FETCHERS: list[Callable[[int], list[str] | None]] = [
    _fetch_sports_reference,
    _fetch_wikipedia,
]


def top25_for(year: int, *, allow_network: bool = True) -> tuple[list[str] | None, str]:
    """Return (ranked list of 25 colleges, source tag) for a season.

    Priority: hardcoded (auditable) first. Network sources are used only as a
    fallback for years the hardcoded dict doesn't cover. Scraping AP polls
    from Wikipedia is fragile because the per-year article structure varies,
    so we treat any curated dict as more trustworthy.

    Source tag is one of: "hardcoded", "sports-reference", "wikipedia", "none".
    """
    fallback = ap_poll_data.get(year)
    if fallback:
        return [normalize_college(n) for n in fallback], "hardcoded"
    if allow_network:
        for fetcher in _FETCHERS:
            try:
                result = fetcher(year)
            except Exception as e:
                log.warning("ap-poll fetcher failed for %d: %s", year, e)
                result = None
            time.sleep(0.25)  # gentle rate-limiting
            if result:
                return result, fetcher.__name__.replace("_fetch_", "").replace("_", "-")
    return None, "none"


def load_all(years, *, allow_network: bool = True) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for y in years:
        teams, source = top25_for(y, allow_network=allow_network)
        if teams:
            log.info("AP Top 25 %d: loaded from %s", y, source)
            out[y] = teams
        else:
            log.warning("AP Top 25 %d: no data available", y)
    return out
