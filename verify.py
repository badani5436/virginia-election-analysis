"""Independent audit of the archived Virginia presidential CSVs and outputs.

This check intentionally parses the input files separately from analyze.py.
It does not import that module or rely on its totals.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
GROUP = {
    "Fairfax County", "Arlington County", "Alexandria City",
    "Loudoun County", "Prince William County",
}
EXPECTED_SHA256 = {
    2020: "e3289bba8e9e0fce24cd06de2c4f9dbe091e14d3c3c710eee560aec145cae84a",
    2024: "f4e54c7fc691cc253ba2026cc37eb81945513600ad0fdef5fde50a3de50671c8",
}


def read_year(year: int) -> tuple[dict, dict]:
    path = BASE / "data" / f"virginia_{year}_president_official.csv"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA256[year], f"Input CSV changed for {year}; verify source version"
    with path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        raw = list(csv.reader(f))
    dem_col, rep_col = raw[1].index("Democratic"), raw[1].index("Republican")
    total_col = raw[0].index("Total Votes Cast")
    values = {}
    state = None
    for line in raw[2:]:
        if line[0] not in ("State", "Locality"):
            continue
        item = tuple(int(line[k]) for k in (dem_col, rep_col, total_col))
        if line[0] == "State":
            assert state is None
            state = item
        else:
            assert line[1] not in values
            values[line[1]] = item
    assert state is not None and len(values) == 133
    assert tuple(sum(v[k] for v in values.values()) for k in range(3)) == state
    return {"dem": state[0], "rep": state[1], "total": state[2]}, values


def verify() -> None:
    state20, v20 = read_year(2020)
    state24, v24 = read_year(2024)
    assert v20.keys() == v24.keys() and GROUP <= v20.keys()
    assert (state20["dem"], state20["rep"], state20["total"]) == (2413568, 1962430, 4460524)
    assert (state24["dem"], state24["rep"], state24["total"]) == (2335395, 2075085, 4505941)

    per_place = {}
    for name in v20:
        d0, r0, t0 = v20[name]
        d1, r1, t1 = v24[name]
        vote_margin_change = (d0 - r0) - (d1 - r1)
        margin_point_change = 100 * ((d0 - r0) / t0 - (d1 - r1) / t1)
        per_place[name] = (vote_margin_change, margin_point_change, t1 - t0)

    decline = sum(x[0] for x in per_place.values())
    group_decline = sum(per_place[name][0] for name in GROUP)
    assert decline == 190828
    assert group_decline == 100111
    assert per_place["Fairfax County"][0] == 46999
    assert sum(v[1] > 0 for v in per_place.values()) == 120
    assert sum(v[1] < 0 for v in per_place.values()) == 13
    assert sum(v[2] for v in per_place.values()) == 45417

    output = json.loads((BASE / "docs" / "analysis.json").read_text(encoding="utf-8"))
    assert len(output["localities"]) == len(per_place)
    state = output["state"]
    assert state["marginErosionVotes"] == decline
    assert state["presVoteChangeVotes"] == 45417
    assert state["novaMarginErosion"] == group_decline
    assert abs(state["novaMarginErosionSharePct"] - 100 * group_decline / decline) < 0.0001
    assert state["localitiesTowardR"] == 120
    assert state["localitiesTowardD"] == 13
    for item in output["localities"]:
        eroded, point_shift, vote_delta = per_place[item["locality"]]
        assert item["marginErosionVotes"] == eroded
        assert item["presVoteChangeVotes"] == vote_delta
        assert abs(item["swingToRpp"] - point_shift) < 0.0001
    print("PASS: 133 localities; all statewide totals, shift counts, margins,")
    print("      five-locality decomposition, and displayed locality metrics verified.")


if __name__ == "__main__":
    verify()
