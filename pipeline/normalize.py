"""College-name normalization.

Maps the messy variants found in nflverse roster CSVs (and AP poll sources)
to a canonical form. Unmatched raw values are written to
`data/logs/unmatched_colleges.log` so the map can be extended over time.
"""
from __future__ import annotations

import html
import json
import logging
import math
from collections import Counter
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = Path(__file__).resolve().parent / "college_name_map.json"
LOG_PATH = ROOT / "data" / "logs" / "unmatched_colleges.log"

_MAP: dict[str, str] | None = None
_UNMATCHED: Counter[str] = Counter()


def _load_map() -> dict[str, str]:
    global _MAP
    if _MAP is None:
        with MAP_PATH.open(encoding="utf-8") as f:
            raw = json.load(f)
        _MAP = {k: v for k, v in raw.items() if not k.startswith("_")}
    return _MAP


def normalize_college(raw: str | None) -> str:
    """Return the canonical name for a raw college string.

    Unknown values are passed through unchanged after stripping whitespace
    and tallied for later review via `flush_unmatched`.
    """
    if raw is None:
        return "No College"
    # pandas NaN floats arrive here as float('nan')
    if isinstance(raw, float) and math.isnan(raw):
        return "No College"
    s = html.unescape(str(raw)).strip()
    if not s or s.lower() == "nan":
        return "No College"
    # nflverse players.csv uses semicolon-delimited multi-college strings
    # for transfers/JUCO paths (e.g. "Miami; Lackawanna JC"). Convention:
    # primary 4-year school first. Collapse to that primary school.
    if ";" in s:
        s = s.split(";", 1)[0].strip() or s
    m = _load_map()
    if s in m:
        return m[s]
    # Try case-insensitive match as a cheap fallback.
    low = s.lower()
    for k, v in m.items():
        if k.lower() == low:
            return v
    if s:
        _UNMATCHED[s] += 1
    return s or "No College"


def flush_unmatched() -> None:
    if not _UNMATCHED:
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        for name, count in sorted(_UNMATCHED.items(), key=lambda kv: -kv[1]):
            f.write(f"{count}\t{name}\n")
    log.info(
        "wrote %d unmatched college names to %s", len(_UNMATCHED), LOG_PATH
    )
    _UNMATCHED.clear()
