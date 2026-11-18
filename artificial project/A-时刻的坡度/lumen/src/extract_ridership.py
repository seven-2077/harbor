#!/usr/bin/env python3
"""Excerpt 7-line station complexes from Atlas hourly ridership samples and
merge them into timetable.js. Row values are not modified.
"""
from __future__ import annotations

import csv
import json
import shutil
from collections import defaultdict
from pathlib import Path

ATLAS_SAMPLES = Path("/workspace/research/bishe-night/atlas/samples")
OUT_RAW = Path("/workspace/research/bishe-night/lumen/data/raw")
OUT_DATA = Path("/workspace/research/bishe-night/lumen/data")

# GTFS parent stop_id -> official station_complex_id in the ridership file
MAP = [
    ("701", "447", "Flushing-Main St (7)", False, ["7"]),
    ("702", "448", "Mets-Willets Point (7)", False, ["7"]),
    ("705", "449", "111 St (7)", False, ["7"]),
    ("706", "450", "103 St-Corona Plaza (7)", False, ["7"]),
    ("707", "451", "Junction Blvd (7)", False, ["7"]),
    ("708", "452", "90 St-Elmhurst Av (7)", False, ["7"]),
    ("709", "453", "82 St-Jackson Hts (7)", False, ["7"]),
    ("710", "616", "Jackson Hts-Roosevelt Av/74 St-Broadway (7,E,F,M,R)", True, ["7", "E", "F", "M", "R"]),
    ("711", "455", "69 St (7)", False, ["7"]),
    ("712", "456", "61 St-Woodside (7)", False, ["7"]),
    ("713", "457", "52 St (7)", False, ["7"]),
    ("714", "458", "46 St-Bliss St (7)", False, ["7"]),
    ("715", "459", "40 St-Lowery St (7)", False, ["7"]),
    ("716", "460", "33 St-Rawson St (7)", False, ["7"]),
    ("718", "461", "Queensboro Plaza (7,N,W)", True, ["7", "N", "W"]),
    ("719", "606", "Court Sq-23 St (7,E,F,G)", True, ["7", "E", "F", "G"]),
    ("720", "463", "Hunters Point Av (7)", False, ["7"]),
    ("721", "464", "Vernon Blvd-Jackson Av (7)", False, ["7"]),
    ("723", "610", "Grand Central-42 St (4,5,6,7,S)", True, ["4", "5", "6", "7", "S"]),
    ("724", "609", "42 St-Bryant Pk/5 Av (7,B,D,F,M)", True, ["7", "B", "D", "F", "M"]),
    ("725", "611", "Times Sq-42 St/Port Authority Bus Terminal (1,2,3,7,A,C,E,N,Q,R,W,S)", True, ["1", "2", "3", "7", "A", "C", "E", "N", "Q", "R", "W", "S"]),
    ("726", "471", "34 St-Hudson Yards (7)", False, ["7"]),
]
IDS = {cid for _, cid, *_ in MAP}


def main():
    src = ATLAS_SAMPLES / "subway_hourly_ridership_2026-08-03_to_2026-08-09_subway_hourly_totals.csv"
    out_csv = OUT_RAW / "ridership_7_complexes_hourly_totals_2026-08-03_to_2026-08-09.csv"
    kept = []
    with open(src, encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        fields = rdr.fieldnames
        for row in rdr:
            if row["station_complex_id"] in IDS:
                kept.append(row)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in kept:
            w.writerow({k: row[k] for k in fields})

    # copy the small Times Square raw day as-is (fare-class grain)
    shutil.copyfile(
        ATLAS_SAMPLES / "subway_hourly_ridership_times_sq_611_2026-08-03_raw.csv",
        OUT_RAW / "subway_hourly_ridership_times_sq_611_2026-08-03_raw.csv",
    )

    by = defaultdict(lambda: defaultdict(lambda: [0.0] * 24))  # cid -> date -> 24 hours
    dates = set()
    for row in kept:
        ts = row["transit_timestamp"]
        d, t = ts.split("T")
        h = int(t.split(":")[0])
        dates.add(d)
        by[row["station_complex_id"]][d][h] += float(row["ridership"])

    complexes = []
    for sid, cid, name, multi, routes in MAP:
        hourly = {}
        daily = {}
        for d in sorted(dates):
            series = [int(v) if float(v).is_integer() else v for v in by[cid][d]]
            hourly[d] = series
            daily[d] = int(sum(by[cid][d]))
        complexes.append(
            {
                "gtfs_parent": sid,
                "complex_id": cid,
                "complex_name": name,
                "multi_line": multi,
                "routes_in_name": routes,
                "hourly": hourly,
                "daily_sum": daily,
            }
        )

    # load existing js payload
    js_path = OUT_DATA / "timetable.js"
    text = js_path.read_text(encoding="utf-8")
    start = text.index("window.SPECIMEN = ") + len("window.SPECIMEN = ")
    assert text.strip().endswith(";")
    payload = json.loads(text[start:].rstrip().rstrip(";"))

    payload["ridership"] = {
        "source": "Atlas sample: subway_hourly_ridership_2026-08-03_to_2026-08-09_subway_hourly_totals.csv",
        "official_dataset": "MTA Subway Hourly Ridership (Beginning 2025), published on data.ny.gov / OPEN-NY",
        "terms": "OPEN-NY Terms of Use; official dataset overview states “There are no limitations on the data at this time.”",
        "unit": "Station-complex entries. Atlas weekly file already sums fare-class rows into an hourly total (ridership field). This specimen uses those totals unchanged.",
        "dates": sorted(dates),
        "default_date": "2026-08-03",
        "default_date_weekday": "Monday",
        "timezone": "America/New_York",
        "not_the_timetable_day": True,
        "caveat_zh": "客流是 2026-08-03 至 2026-08-09 的官方车站综合体进站量，不是 2026-11-11 时刻表营运日的进站量。综合体若在名称中包含其他线路，进站量不能记作 7 号线独有。",
        "complexes": complexes,
        "rows_excerpted": len(kept),
    }

    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* Derived from data/raw GTFS excerpts and ridership excerpts. See data/SOURCE.md. */\n")
        f.write("window.SPECIMEN = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    meta_path = OUT_DATA / "timetable.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["ridership_summary"] = {
        "dates": sorted(dates),
        "complexes": [
            {
                "gtfs_parent": c["gtfs_parent"],
                "complex_id": c["complex_id"],
                "complex_name": c["complex_name"],
                "multi_line": c["multi_line"],
                "daily_sum": c["daily_sum"],
            }
            for c in complexes
        ],
        "rows_excerpted": len(kept),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("excerpted rows", len(kept), "dates", sorted(dates), "js", js_path.stat().st_size)


if __name__ == "__main__":
    main()
