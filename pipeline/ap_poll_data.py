"""Hardcoded final AP Top 25 rankings by year (fallback only).

This module is the fallback used when `ap_poll.fetch_from_wikipedia()` fails
for a given year.

IMPORTANT: These values are seeded from model knowledge and marked UNVERIFIED.
They should be audited against the canonical sources before being trusted:

    https://www.sports-reference.com/cfb/years/{year}-polls.html
    https://en.wikipedia.org/wiki/{year}_NCAA_Division_I_FBS_football_rankings

Rankings reflect the *final post-bowl AP poll* for each season. The list for
each year is ordered 1 through 25.

College names here should already match the normalized form that
`pipeline.normalize` produces (e.g. "Ohio State", "USC", "Mississippi",
"Miami" for the Florida school).
"""
from __future__ import annotations

# ruff: noqa: E501
# UNVERIFIED — audit against sports-reference.com before relying on these
FINAL_AP_TOP_25: dict[int, list[str]] = {
    2000: [
        "Oklahoma", "Miami", "Washington", "Oregon State", "Florida State",
        "Virginia Tech", "Oregon", "Nebraska", "Kansas State", "Florida",
        "Notre Dame", "Purdue", "Colorado", "Texas", "Clemson",
        "TCU", "Georgia Tech", "Michigan", "South Carolina", "LSU",
        "Texas A&M", "Mississippi State", "Northwestern", "NC State", "Auburn",
    ],
    2001: [
        "Miami", "Oregon", "Florida", "Tennessee", "Texas",
        "Oklahoma", "LSU", "Nebraska", "Colorado", "Washington State",
        "Maryland", "Illinois", "South Carolina", "Syracuse", "Florida State",
        "Stanford", "Louisville", "Virginia Tech", "Washington", "Michigan",
        "Boston College", "Georgia", "Toledo", "Georgia Tech", "BYU",
    ],
    2002: [
        "Ohio State", "Miami", "Georgia", "USC", "Oklahoma",
        "Texas", "Kansas State", "Iowa", "Michigan", "Washington State",
        "NC State", "Maryland", "Auburn", "Boise State", "Penn State",
        "Notre Dame", "Virginia Tech", "Pittsburgh", "Colorado", "Florida State",
        "Virginia", "TCU", "Marshall", "West Virginia", "Alabama",
    ],
    2003: [
        "USC", "LSU", "Oklahoma", "Ohio State", "Miami",
        "Michigan", "Georgia", "Iowa", "Washington State", "Miami (OH)",
        "Florida State", "Texas", "Mississippi", "Kansas State", "Tennessee",
        "Boise State", "Purdue", "Nebraska", "Minnesota", "Utah",
        "Clemson", "Bowling Green", "Florida", "TCU", "Maryland",
    ],
    2004: [
        "USC", "Auburn", "Oklahoma", "Utah", "Texas",
        "Louisville", "Georgia", "Iowa", "California", "Virginia Tech",
        "Miami", "Boise State", "Tennessee", "Michigan", "Florida State",
        "LSU", "Wisconsin", "Texas Tech", "Arizona State", "Ohio State",
        "Boston College", "Virginia", "Pittsburgh", "Fresno State", "Navy",
    ],
    2005: [
        "Texas", "USC", "Penn State", "Ohio State", "West Virginia",
        "LSU", "Virginia Tech", "Alabama", "Notre Dame", "Georgia",
        "TCU", "Oregon", "Miami", "Auburn", "Wisconsin",
        "UCLA", "Texas Tech", "Louisville", "Clemson", "Oklahoma",
        "Florida", "Florida State", "Boston College", "Nebraska", "Michigan State",
    ],
    2006: [
        "Florida", "Ohio State", "LSU", "USC", "Boise State",
        "Louisville", "Wisconsin", "Michigan", "Auburn", "West Virginia",
        "Oklahoma", "Rutgers", "Texas", "California", "Arkansas",
        "BYU", "Notre Dame", "Wake Forest", "Virginia Tech", "Boston College",
        "Oregon State", "TCU", "Georgia", "Penn State", "Tennessee",
    ],
    2007: [
        "LSU", "Georgia", "USC", "Missouri", "Ohio State",
        "West Virginia", "Kansas", "Oklahoma", "Virginia Tech", "Texas",
        "Boston College", "Tennessee", "Hawaii", "Illinois", "Arizona State",
        "Auburn", "BYU", "Clemson", "Michigan", "Wisconsin",
        "Florida", "Texas Tech", "Cincinnati", "Oregon", "South Florida",
    ],
    2008: [
        "Florida", "Utah", "USC", "Texas", "Oklahoma",
        "Alabama", "TCU", "Penn State", "Ohio State", "Oregon",
        "Boise State", "Texas Tech", "Georgia", "Mississippi", "Virginia Tech",
        "Oregon State", "Missouri", "Cincinnati", "Michigan State", "BYU",
        "Oklahoma State", "Georgia Tech", "Iowa", "West Virginia", "Florida State",
    ],
    2009: [
        "Alabama", "Texas", "Florida", "Boise State", "Ohio State",
        "TCU", "Iowa", "Cincinnati", "Penn State", "Virginia Tech",
        "LSU", "Oregon", "Georgia Tech", "BYU", "Miami",
        "Wisconsin", "Utah", "Nebraska", "Pittsburgh", "USC",
        "Mississippi", "West Virginia", "Arizona", "Central Michigan", "Texas Tech",
    ],
    2010: [
        "Auburn", "TCU", "Oregon", "Stanford", "Ohio State",
        "Oklahoma", "Wisconsin", "LSU", "Boise State", "Alabama",
        "Michigan State", "Arkansas", "Oklahoma State", "Missouri", "Nevada",
        "Mississippi State", "Virginia Tech", "Nebraska", "Utah", "South Carolina",
        "Texas A&M", "Florida State", "West Virginia", "Hawaii", "Tulsa",
    ],
    2011: [
        "Alabama", "LSU", "Oklahoma State", "Oregon", "USC",
        "Arkansas", "Boise State", "Kansas State", "South Carolina", "Wisconsin",
        "Michigan State", "Michigan", "Oklahoma", "Baylor", "TCU",
        "Stanford", "West Virginia", "Houston", "Georgia", "Southern Miss",
        "Virginia Tech", "Cincinnati", "Florida State", "Auburn", "Nebraska",
    ],
    2012: [
        "Alabama", "Oregon", "Ohio State", "Notre Dame", "Georgia",
        "Texas A&M", "Stanford", "South Carolina", "Florida", "Florida State",
        "Clemson", "LSU", "Oklahoma", "Kansas State", "Northern Illinois",
        "Oregon State", "Louisville", "Nebraska", "Boise State", "Michigan",
        "San Jose State", "Utah State", "Northwestern", "Vanderbilt", "Kent State",
    ],
    2013: [
        "Florida State", "Auburn", "Michigan State", "South Carolina", "Missouri",
        "Oklahoma", "Alabama", "Clemson", "Oregon", "UCF",
        "Stanford", "Ohio State", "Baylor", "LSU", "Louisville",
        "UCLA", "Oklahoma State", "Texas A&M", "USC", "Arizona State",
        "Wisconsin", "Notre Dame", "Duke", "Vanderbilt", "Washington",
    ],
    2014: [
        "Ohio State", "Oregon", "TCU", "Alabama", "Michigan State",
        "Florida State", "Baylor", "Georgia Tech", "Georgia", "UCLA",
        "Kansas State", "Mississippi State", "Arizona State", "Mississippi", "Arizona",
        "Boise State", "Utah", "Auburn", "Wisconsin", "LSU",
        "Clemson", "USC", "Louisville", "Missouri", "Minnesota",
    ],
    2015: [
        "Alabama", "Clemson", "Stanford", "Michigan State", "Oklahoma",
        "Ohio State", "TCU", "Houston", "Mississippi", "Notre Dame",
        "Michigan", "Florida State", "Iowa", "Tennessee", "Northwestern",
        "Oklahoma State", "LSU", "Navy", "Utah", "North Carolina",
        "Baylor", "Washington State", "Wisconsin", "Western Kentucky", "Temple",
    ],
    2016: [
        "Clemson", "Alabama", "USC", "Washington", "Oklahoma",
        "Ohio State", "Penn State", "Florida State", "Wisconsin", "Oklahoma State",
        "Michigan", "Florida", "Stanford", "Western Michigan", "LSU",
        "Miami", "Virginia Tech", "Utah", "Louisville", "Colorado",
        "Auburn", "West Virginia", "Tennessee", "Pittsburgh", "Air Force",
    ],
    2017: [
        "Alabama", "Georgia", "Oklahoma", "Clemson", "Ohio State",
        "UCF", "Wisconsin", "Auburn", "Penn State", "Notre Dame",
        "USC", "TCU", "Miami", "Oklahoma State", "Washington",
        "Stanford", "LSU", "Memphis", "Michigan State", "Mississippi State",
        "Northwestern", "Iowa State", "NC State", "Boise State", "South Florida",
    ],
    2018: [
        "Clemson", "Alabama", "Ohio State", "Oklahoma", "Notre Dame",
        "LSU", "Georgia", "Florida", "Kentucky", "Washington",
        "Texas", "Penn State", "Washington State", "West Virginia", "UCF",
        "Michigan", "Texas A&M", "Mississippi State", "Syracuse", "Iowa State",
        "Army", "Utah", "Iowa", "Auburn", "Boise State",
    ],
    2019: [
        "LSU", "Clemson", "Ohio State", "Georgia", "Oregon",
        "Florida", "Oklahoma", "Alabama", "Penn State", "Minnesota",
        "Wisconsin", "Notre Dame", "Baylor", "Auburn", "Iowa",
        "Utah", "Memphis", "Michigan", "Appalachian State", "Navy",
        "Cincinnati", "Air Force", "Boise State", "UCF", "Texas",
    ],
    2020: [
        "Alabama", "Clemson", "Ohio State", "Texas A&M", "Oklahoma",
        "Georgia", "Notre Dame", "Cincinnati", "Iowa State", "Northwestern",
        "Indiana", "Coastal Carolina", "BYU", "Florida", "Louisiana",
        "USC", "Miami", "North Carolina", "Iowa", "NC State",
        "Texas", "Oklahoma State", "Mississippi", "Washington", "San Jose State",
    ],
    2021: [
        "Georgia", "Alabama", "Michigan", "Cincinnati", "Baylor",
        "Ohio State", "Oklahoma State", "Notre Dame", "Michigan State", "Oklahoma",
        "Mississippi", "Utah", "Pittsburgh", "Clemson", "Wake Forest",
        "Kentucky", "Iowa", "Houston", "NC State", "Arkansas",
        "San Diego State", "UTSA", "Louisiana", "Air Force", "Oregon",
    ],
    2022: [
        "Georgia", "TCU", "Michigan", "Ohio State", "Alabama",
        "Tennessee", "Clemson", "Utah", "Penn State", "Washington",
        "Florida State", "USC", "Tulane", "Kansas State", "LSU",
        "Oregon", "Notre Dame", "UCLA", "Troy", "Mississippi State",
        "Oregon State", "South Carolina", "UTSA", "Pittsburgh", "Duke",
    ],
    2023: [
        "Michigan", "Washington", "Texas", "Alabama", "Georgia",
        "Ohio State", "Oregon", "Missouri", "Mississippi", "Oklahoma",
        "Arizona", "LSU", "Notre Dame", "Louisville", "Penn State",
        "Kansas State", "NC State", "Tennessee", "Clemson", "SMU",
        "Kansas", "Oklahoma State", "Iowa", "West Virginia", "James Madison",
    ],
    2024: [
        "Ohio State", "Oregon", "Notre Dame", "Texas", "Penn State",
        "Georgia", "Tennessee", "Arizona State", "Boise State", "BYU",
        "Indiana", "SMU", "Alabama", "Mississippi", "Clemson",
        "South Carolina", "Miami", "Iowa State", "Illinois", "Syracuse",
        "Army", "Louisville", "Missouri", "Memphis", "UNLV",
    ],
}


def get(year: int) -> list[str] | None:
    """Return the Top-25 list for `year`, or None if unknown."""
    return FINAL_AP_TOP_25.get(year)
