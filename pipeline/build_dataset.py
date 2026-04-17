"""Core pipeline: roster data + AP polls → cfb_nfl_talent.csv + web JSON.

Implements the PRD's "simplification option":

  For each distinct NFL player, determine an anchor year (draft year if
  available, otherwise first NFL season). Their estimated college window is
  the 5 CFB seasons ending the year before the anchor. The player is
  credited to every top-25 appearance of their college within that window.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import fetch_nflverse
from .ap_poll import load_all as load_ap_all
from .normalize import flush_unmatched, normalize_college

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_CSV = ROOT / "data" / "output" / "cfb_nfl_talent.csv"
WEB_DATA_DIR = ROOT / "web" / "data"

YEARS = range(2000, 2026)  # 2000..2025 inclusive

CAVEATS = [
    "Recent CFB seasons are structurally incomplete: a player is only credited once they reach an NFL roster, and we look up to 5 NFL seasons forward. The most recent 4–5 CFB years will grow as future NFL seasons are played. For example, CFB 2024 only counts players whose first NFL season is 2025 or later.",
    "College name matching is approximate — players with unusual name spellings or multiple college stints may be miscategorized.",
    "Pre-2015 coverage is ~70–85%. Players without a gsis_id match in draft_picks.csv are excluded from early seasons.",
    "Undrafted free agents are included when they appear on a 53-man active roster (status == 'ACT').",
    "Practice-squad players are excluded by design.",
    "AP poll data is fetched from public sources when available; a hardcoded fallback is used otherwise and is unverified.",
    "College-season year is estimated from NFL draft year / first-seen year — no direct CFB roster data is used.",
]


def _load_rosters(years) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for y in years:
        path = fetch_nflverse.roster_path(y)
        if not path.exists():
            log.warning("roster file missing for %d at %s — skipping", y, path)
            continue
        df = pd.read_csv(path, low_memory=False)
        # Some older files use slightly different column names. Normalize a few.
        if "player_id" in df.columns and "gsis_id" not in df.columns:
            df = df.rename(columns={"player_id": "gsis_id"})
        if "full_name" not in df.columns:
            for cand in ("player_name", "name"):
                if cand in df.columns:
                    df = df.rename(columns={cand: "full_name"})
                    break
        if "season" not in df.columns:
            df["season"] = y
        # Keep only what we need.
        wanted = [c for c in ["gsis_id", "full_name", "college", "status", "season"] if c in df.columns]
        df = df[wanted].copy()
        # Filter to active 53-man roster
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.upper() == "ACT"]
        frames.append(df)
    if not frames:
        raise RuntimeError("no roster files loaded — run the fetcher first")
    rosters = pd.concat(frames, ignore_index=True)
    # Dedupe within each season on gsis_id (weekly snapshots may repeat).
    rosters = rosters.dropna(subset=["gsis_id"])
    rosters = rosters.drop_duplicates(subset=["season", "gsis_id"])
    return rosters


def _load_draft_picks() -> pd.DataFrame:
    path = fetch_nflverse.draft_picks_path()
    if not path.exists():
        raise RuntimeError(f"draft_picks.csv not found at {path}")
    dp = pd.read_csv(path, low_memory=False)
    # Harmonize column names.
    rename = {}
    if "pfr_player_name" in dp.columns and "full_name" not in dp.columns:
        rename["pfr_player_name"] = "full_name"
    if "season" in dp.columns:
        rename["season"] = "draft_year"
    if rename:
        dp = dp.rename(columns=rename)
    keep = [c for c in ["gsis_id", "full_name", "college", "draft_year", "probowls", "allpro"] if c in dp.columns]
    dp = dp[keep].copy()
    # Some rows in draft_picks have no gsis_id (older undrafted/pre-2000). Drop those.
    dp = dp.dropna(subset=["gsis_id"]).drop_duplicates(subset=["gsis_id"])
    return dp


def _backfill_college(rosters: pd.DataFrame, draft: pd.DataFrame) -> pd.DataFrame:
    # Add draft's college under a separate column, then coalesce.
    draft_cols = draft[["gsis_id", "college"]].rename(columns={"college": "college_draft"})
    merged = rosters.merge(draft_cols, on="gsis_id", how="left")
    merged["college"] = merged["college"].where(merged["college"].notna() & (merged["college"].astype(str) != ""), merged["college_draft"])
    merged = merged.drop(columns=["college_draft"])
    return merged


def _players_table(rosters: pd.DataFrame, draft: pd.DataFrame) -> pd.DataFrame:
    """One row per distinct player: gsis_id, name, college, anchor_year, probowls, allpro."""
    first_seen = rosters.groupby("gsis_id", as_index=False)["season"].min().rename(columns={"season": "first_nfl_season"})
    # Best college per player: most frequent non-null college across their roster rows.
    def pick_college(s: pd.Series) -> str | None:
        vals = s.dropna().astype(str)
        vals = vals[vals != ""]
        if vals.empty:
            return None
        return vals.value_counts().idxmax()

    player_college = rosters.groupby("gsis_id", as_index=False)["college"].agg(pick_college)
    player_name = rosters.groupby("gsis_id", as_index=False)["full_name"].agg(lambda s: s.dropna().astype(str).iloc[0] if not s.dropna().empty else None)

    players = player_college.merge(player_name, on="gsis_id").merge(first_seen, on="gsis_id")
    players = players.merge(
        draft[[c for c in ["gsis_id", "draft_year", "probowls", "allpro"] if c in draft.columns]],
        on="gsis_id",
        how="left",
    )
    # Anchor year = draft_year if present, else first NFL season.
    if "draft_year" in players.columns:
        players["anchor_year"] = players["draft_year"].fillna(players["first_nfl_season"]).astype("Int64")
    else:
        players["anchor_year"] = players["first_nfl_season"].astype("Int64")
    # Fill probowls/allpro with 0 for undrafted players (not in draft_picks).
    for c in ("probowls", "allpro"):
        if c not in players.columns:
            players[c] = 0
        players[c] = pd.to_numeric(players[c], errors="coerce").fillna(0).astype(int)
    # Normalize college on the player table.
    players["college_norm"] = players["college"].apply(normalize_college)
    return players


def _build_top25_index(ap_polls: dict[int, list[str]]) -> dict[str, dict[int, int]]:
    """college_norm -> { cfb_season: ap_rank } across all years."""
    idx: dict[str, dict[int, int]] = defaultdict(dict)
    for year, teams in ap_polls.items():
        for rank, name in enumerate(teams, start=1):
            idx[name][year] = rank
    return idx


def build(
    years=YEARS,
    *,
    allow_network: bool = True,
    only_year: int | None = None,
) -> pd.DataFrame:
    log.info("loading rosters for %d seasons", len(list(years)))
    rosters = _load_rosters(years)
    log.info("loaded %d roster rows", len(rosters))

    log.info("loading draft picks")
    draft = _load_draft_picks()
    log.info("loaded %d draft rows", len(draft))

    # Step 3: backfill missing college from draft picks.
    rosters = _backfill_college(rosters, draft)
    missing_college = rosters["college"].isna().sum() + (rosters["college"].astype(str) == "").sum()
    log.info("after backfill: %d roster rows still missing college", missing_college)

    # Step 4: normalize college names on the per-season roster frame (for logging unmatched).
    rosters["college_norm"] = rosters["college"].apply(normalize_college)

    # Build one-row-per-player table used for credit attribution.
    players = _players_table(rosters, draft)
    log.info("derived %d distinct players", len(players))

    # Step 5: AP poll data.
    log.info("loading AP Top 25 polls (network=%s)", allow_network)
    ap_polls = load_ap_all(years, allow_network=allow_network)

    # Build index from normalized college -> {year: rank}.
    top25_index = _build_top25_index({y: [normalize_college(n) for n in t] for y, t in ap_polls.items()})

    # Step 6/7: attribute players to (cfb_season, college) rows.
    # For each player, for each year in [anchor-5, anchor-1], if their college
    # was top-25 that year, credit them.
    credits: dict[tuple[int, str], dict] = defaultdict(lambda: {
        "ap_rank": None,
        "players": [],  # list of (gsis_id, name, probowls, allpro)
    })

    for row in players.itertuples(index=False):
        anchor = row.anchor_year
        if pd.isna(anchor):
            continue
        anchor = int(anchor)
        window_start = anchor - 5
        window_end = anchor - 1
        college = row.college_norm
        if not college or college == "No College":
            continue
        program_years = top25_index.get(college)
        if not program_years:
            continue
        for cfb_year, rank in program_years.items():
            if window_start <= cfb_year <= window_end:
                if only_year is not None and cfb_year != only_year:
                    continue
                key = (cfb_year, college)
                bucket = credits[key]
                bucket["ap_rank"] = rank
                bucket["players"].append(
                    (row.gsis_id, row.full_name or "", int(row.probowls), int(row.allpro))
                )

    # Materialize into a DataFrame.
    rows = []
    for (cfb_season, college), bucket in credits.items():
        unique_players = {}
        for gid, name, pb, ap in bucket["players"]:
            # Dedupe per (gsis_id) per (cfb_season, college) — they should already be unique,
            # but guard against accidental double-credit.
            unique_players[gid] = (name, pb, ap)
        names = sorted(v[0] for v in unique_players.values() if v[0])
        rows.append({
            "cfb_season": cfb_season,
            "college": college,
            "ap_rank": bucket["ap_rank"],
            "nfl_players": len(unique_players),
            "pro_bowls": sum(v[1] for v in unique_players.values()),
            "all_pros": sum(v[2] for v in unique_players.values()),
            "player_list": "|".join(names),
        })

    # Also emit rows for top-25 program-seasons with zero credited players so the
    # Year view shows every top-25 team, even ones with no NFL alumni in the dataset.
    seen = {(r["cfb_season"], r["college"]) for r in rows}
    for year, teams in ap_polls.items():
        if only_year is not None and year != only_year:
            continue
        for rank, name in enumerate((normalize_college(n) for n in teams), start=1):
            if (year, name) not in seen:
                rows.append({
                    "cfb_season": year,
                    "college": name,
                    "ap_rank": rank,
                    "nfl_players": 0,
                    "pro_bowls": 0,
                    "all_pros": 0,
                    "player_list": "",
                })

    out = pd.DataFrame(rows).sort_values(["cfb_season", "ap_rank"]).reset_index(drop=True)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_CSV, index=False)
    log.info("wrote %d rows to %s", len(out), OUTPUT_CSV)

    # Persist JSON for the web app.
    _write_web_json(out, players, ap_polls)

    # Flush unmatched college names for review.
    flush_unmatched()
    return out


def _write_web_json(out: pd.DataFrame, players: pd.DataFrame, ap_polls: dict[int, list[str]]) -> None:
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Player lookup (gsis_id -> {name, probowls, allpro, nfl_seasons}).
    # nfl_seasons is unavailable at this level without reaggregating — we'll
    # skip it here and let the frontend display pro_bowls/all_pros per player.
    player_lookup = players.set_index("gsis_id")[[
        "full_name", "probowls", "allpro", "college_norm"
    ]].to_dict(orient="index")

    # leaderboard.json — program-level rollup across all years.
    leaderboard: dict[str, dict] = {}
    for row in out.itertuples(index=False):
        rec = leaderboard.setdefault(row.college, {
            "program": row.college,
            "top25_seasons": 0,
            "nfl_players_total": 0,
            "pro_bowls_total": 0,
            "all_pros_total": 0,
            "years": {},
        })
        rec["top25_seasons"] += 1 if row.ap_rank is not None else 0
        rec["nfl_players_total"] += int(row.nfl_players)
        rec["pro_bowls_total"] += int(row.pro_bowls)
        rec["all_pros_total"] += int(row.all_pros)
        rec["years"][str(int(row.cfb_season))] = {
            "ap_rank": int(row.ap_rank) if row.ap_rank is not None and not pd.isna(row.ap_rank) else None,
            "nfl_players": int(row.nfl_players),
            "pro_bowls": int(row.pro_bowls),
            "all_pros": int(row.all_pros),
        }
    leaderboard_list = sorted(leaderboard.values(), key=lambda r: (-r["nfl_players_total"], r["program"]))
    (WEB_DATA_DIR / "leaderboard.json").write_text(
        json.dumps(leaderboard_list, indent=2), encoding="utf-8"
    )

    # by_year.json — per-year top-25 detail.
    by_year: dict[str, list[dict]] = {}
    for row in out.itertuples(index=False):
        by_year.setdefault(str(int(row.cfb_season)), []).append({
            "program": row.college,
            "ap_rank": int(row.ap_rank) if row.ap_rank is not None and not pd.isna(row.ap_rank) else None,
            "nfl_players": int(row.nfl_players),
            "pro_bowls": int(row.pro_bowls),
            "all_pros": int(row.all_pros),
            "player_list": row.player_list.split("|") if row.player_list else [],
        })
    for year_str in by_year:
        by_year[year_str].sort(key=lambda r: (r["ap_rank"] if r["ap_rank"] is not None else 99))
    (WEB_DATA_DIR / "by_year.json").write_text(
        json.dumps(by_year, indent=2), encoding="utf-8"
    )

    # by_program.json — per-program timeline + player list per season.
    by_program: dict[str, dict] = {}
    name_by_gid = {gid: info.get("full_name") or "" for gid, info in player_lookup.items()}
    probowls_by_gid = {gid: int(info.get("probowls") or 0) for gid, info in player_lookup.items()}
    allpro_by_gid = {gid: int(info.get("allpro") or 0) for gid, info in player_lookup.items()}

    # Build a (program, season) -> [gsis_id] map.
    prog_season_gids: dict[tuple[str, int], list[str]] = defaultdict(list)
    # Re-derive by walking players with their anchor window against ap_polls.
    normalized_ap = {y: [normalize_college(n) for n in t] for y, t in ap_polls.items()}
    for row in players.itertuples(index=False):
        anchor = row.anchor_year
        if pd.isna(anchor):
            continue
        anchor = int(anchor)
        college = row.college_norm
        if not college or college == "No College":
            continue
        for cfb_year in range(anchor - 5, anchor):
            if college in normalized_ap.get(cfb_year, []):
                prog_season_gids[(college, cfb_year)].append(row.gsis_id)

    for (college, season), gids in prog_season_gids.items():
        rec = by_program.setdefault(college, {"program": college, "years": {}})
        rank = None
        for r, n in enumerate(normalized_ap.get(season, []), start=1):
            if n == college:
                rank = r
                break
        rec["years"][str(season)] = {
            "ap_rank": rank,
            "nfl_players": len(set(gids)),
            "players": sorted(
                ({
                    "name": name_by_gid.get(g, ""),
                    "pro_bowls": probowls_by_gid.get(g, 0),
                    "all_pros": allpro_by_gid.get(g, 0),
                } for g in set(gids)),
                key=lambda p: (-p["pro_bowls"], p["name"]),
            ),
        }
    # Include programs that only have 0-player top-25 entries so the UI can still render them.
    for row in out.itertuples(index=False):
        rec = by_program.setdefault(row.college, {"program": row.college, "years": {}})
        year_key = str(int(row.cfb_season))
        if year_key not in rec["years"]:
            rec["years"][year_key] = {
                "ap_rank": int(row.ap_rank) if row.ap_rank is not None and not pd.isna(row.ap_rank) else None,
                "nfl_players": int(row.nfl_players),
                "players": [],
            }
    (WEB_DATA_DIR / "by_program.json").write_text(
        json.dumps(by_program, indent=2), encoding="utf-8"
    )

    # meta.json
    meta = {
        "year_range": [min(ap_polls.keys()) if ap_polls else 2000, max(ap_polls.keys()) if ap_polls else 2024],
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "caveats": CAVEATS,
        "programs": sorted(leaderboard.keys()),
    }
    (WEB_DATA_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
