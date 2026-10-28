"""Reproducible 2020–2024 Virginia presidential locality analysis.

Input files are direct contest-table downloads from Virginia's official
historical election results site. This script uses only the 'Locality' and
'State' records, excludes precinct lines to avoid double-counting, and checks
that all locality totals reconcile with the state.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = {
    2020: "https://historical.elections.virginia.gov/contest/144567",
    2024: "https://historical.elections.virginia.gov/contest/161256",
}
NOVA_FIVE = {"Fairfax County", "Arlington County", "Alexandria City", "Loudoun County", "Prince William County"}


def read_contest(year: int) -> tuple[dict, dict[str, dict]]:
    path = ROOT / "data" / f"virginia_{year}_president_official.csv"
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    names = rows[0]
    parties = rows[1]
    dem_index = parties.index("Democratic")
    rep_index = parties.index("Republican")
    total_index = names.index("Total Votes Cast")

    def unpack(row: list[str]) -> dict:
        dem, rep, total = (int(row[i].replace(",", "")) for i in (dem_index, rep_index, total_index))
        assert 0 <= dem + rep <= total, (year, row)
        return {"dem": dem, "rep": rep, "total": total, "other": total - dem - rep}

    state_rows = [unpack(r) for r in rows[2:] if r[0] == "State"]
    assert len(state_rows) == 1, f"Expected one state summary in {year}"
    by_locality = {r[1]: unpack(r) for r in rows[2:] if r[0] == "Locality"}
    assert len(by_locality) == 133, f"Unexpected number of Virginia localities in {year}"
    for key in ("dem", "rep", "other", "total"):
        assert sum(v[key] for v in by_locality.values()) == state_rows[0][key], (year, key)
    return state_rows[0], by_locality


def point_margin(v: dict) -> float:
    """Democratic minus Republican share of all votes, in percentage points."""
    return 100 * (v["dem"] - v["rep"]) / v["total"]


def main() -> None:
    state20, loc20 = read_contest(2020)
    state24, loc24 = read_contest(2024)
    assert loc20.keys() == loc24.keys(), {"missing20": sorted(loc24.keys() - loc20.keys()), "missing24": sorted(loc20.keys() - loc24.keys())}
    assert NOVA_FIVE.issubset(loc20), NOVA_FIVE - loc20.keys()

    records = []
    for name in sorted(loc20):
        a, b = loc20[name], loc24[name]
        margin20 = a["dem"] - a["rep"]
        margin24 = b["dem"] - b["rep"]
        records.append({
            "locality": name,
            "year2020": a,
            "year2024": b,
            "margin20votes": margin20,
            "margin24votes": margin24,
            "margin20pp": round(point_margin(a), 4),
            "margin24pp": round(point_margin(b), 4),
            "swingToRpp": round(point_margin(a) - point_margin(b), 4),
            "marginErosionVotes": margin20 - margin24,
            "presVoteChangeVotes": b["total"] - a["total"],
            "presVoteChangePct": round(100 * (b["total"] - a["total"]) / a["total"], 4),
            "novaCore": name in NOVA_FIVE,
        })

    # Compare a weighted statewide result directly, not the average locality swing.
    margin20votes = state20["dem"] - state20["rep"]
    margin24votes = state24["dem"] - state24["rep"]
    erosion = margin20votes - margin24votes
    assert sum(r["marginErosionVotes"] for r in records) == erosion
    assert sum(r["presVoteChangeVotes"] for r in records) == state24["total"] - state20["total"]
    swing_count = Counter("toward_R" if r["swingToRpp"] > 0 else "toward_D" if r["swingToRpp"] < 0 else "no_change" for r in records)
    nova_erosion = sum(r["marginErosionVotes"] for r in records if r["novaCore"])
    nova_votes = sum(r["year2024"]["total"] for r in records if r["novaCore"])
    top_eroders = sorted(records, key=lambda r: -r["marginErosionVotes"])[:10]
    top_pp = sorted(records, key=lambda r: -r["swingToRpp"])[:10]

    output = {
        "sources": {str(y): SOURCE[y] for y in SOURCE},
        "notes": [
            "Official locality-level presidential vote counts; independent cities appear as distinct localities.",
            "Margin = (Democratic votes minus Republican votes) / votes recorded for president. A shift toward Republicans = 2020 Democratic margin minus 2024 Democratic margin, in percentage points. This is not the change in Trump's vote share.",
            "Margins compare Biden (2020) and Harris (2024) against Trump. They do not identify individual voter switching or its cause.",
            "Presidential votes recorded are not all ballots cast, the registered-voter turnout rate, or participation among eligible adults.",
            "The five selected Northern Virginia localities are Fairfax, Arlington, Alexandria, Loudoun, and Prince William. This is not an official statistical geography or all of Northern Virginia.",
            "Changes in raw margins are additive across localities; percentage-point swings are not. Rounding only occurs in display fields.",
        ],
        "state": {
            "year2020": state20,
            "year2024": state24,
            "margin20votes": margin20votes,
            "margin24votes": margin24votes,
            "margin20pp": round(point_margin(state20), 4),
            "margin24pp": round(point_margin(state24), 4),
            "swingToRpp": round(point_margin(state20) - point_margin(state24), 4),
            "marginErosionVotes": erosion,
            "presVoteChangeVotes": state24["total"] - state20["total"],
            "demChangeVotes": state24["dem"] - state20["dem"],
            "repChangeVotes": state24["rep"] - state20["rep"],
            "localitiesTowardR": swing_count["toward_R"],
            "localitiesTowardD": swing_count["toward_D"],
            "localitiesNoChange": swing_count["no_change"],
            "novaMarginErosion": nova_erosion,
            "novaMarginErosionSharePct": round(100 * nova_erosion / erosion, 4),
            "nova2024VoteSharePct": round(100 * nova_votes / state24["total"], 4),
            "novaLocalities": sorted(NOVA_FIVE),
        },
        "topMarginErosion": [r["locality"] for r in top_eroders],
        "topSwingPp": [r["locality"] for r in top_pp],
        "localities": records,
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    with (ROOT / "docs" / "analysis.json").open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
    with (ROOT / "docs" / "analysis.js").open("w", encoding="utf-8") as handle:
        handle.write("window.ELECTION_ANALYSIS = ")
        json.dump(output, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write(";\n")

    with (ROOT / "data" / "virginia_locality_analysis.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["locality", "margin20votes", "margin24votes", "margin20pp", "margin24pp", "swingToRpp", "marginErosionVotes", "presVoteChangeVotes", "presVoteChangePct", "novaCore"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: r[key] for key in fields} for r in records)
    with (ROOT / "docs" / "virginia_locality_analysis.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["locality", "margin20votes", "margin24votes", "margin20pp", "margin24pp", "swingToRpp", "marginErosionVotes", "presVoteChangeVotes", "presVoteChangePct", "novaCore"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: r[key] for key in fields} for r in records)

    print("LOCALITY COVERAGE:", len(records), "2020 / 2024 matched")
    print("STATE 2020:", state20, f"D+ {point_margin(state20):.2f}pp")
    print("STATE 2024:", state24, f"D+ {point_margin(state24):.2f}pp")
    print("STATEWIDE D-MARGIN EROSION:", erosion, "votes")
    print("LOCALITY SWING COUNTS:", dict(swing_count))
    print("FIVE SELECTED NORTHERN VIRGINIA LOCALITIES:", nova_erosion, f"({100*nova_erosion/erosion:.1f}% of total)")
    print("BIGGEST RAW MARGIN EROSION:", [(r["locality"], r["marginErosionVotes"]) for r in top_eroders])
    print("BIGGEST PP SWINGS:", [(r["locality"], round(r["swingToRpp"], 1)) for r in top_pp])


if __name__ == "__main__":
    main()
