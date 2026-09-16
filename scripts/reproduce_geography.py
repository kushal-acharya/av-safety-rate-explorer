"""Normalize and reproduce the frozen spatial study; default mode needs no network."""

from __future__ import annotations

import argparse
import hashlib
import json
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from av_safety.geography import CITIES, GEO_DIR, METRICS, ROOT, build_geography

BASE = "https://storage.googleapis.com/waymo-uploads/files/documents/safety/safety-impact-data/"
FILES = {
    "miles": "CSV1 - RO Miles per Location 202009-202412-2022benchmark.csv",
    "events": "CSV2 - Crashes with SGO ID and Group Membership 202009-202412-2022benchmark.csv",
    "comparisons": (
        "CSV3 - Collision Counts and Comparison to Benchmarks 202009-202412-2022benchmark.csv"
    ),
    "cells": (
        "CSV4 - Miles and Benchmark Crashes for Dynamic Benchmark 202009-202412-2022benchmark.csv"
    ),
}


def normalized_inputs(raw_directory: Path) -> dict[str, str]:
    """Select supported outcomes and retain source rows without deduplicating SGO IDs."""
    raw = {
        key: pd.read_csv(raw_directory / name, dtype={"S2 Cell": str}, float_precision="round_trip")
        for key, name in FILES.items()
    }
    cells = raw["cells"]
    cells = (
        cells[cells.Location.isin(CITIES) & cells.Outcome.isin(METRICS)]
        .rename(
            columns={
                "Location": "city",
                "Outcome": "metric",
                "S2 Cell": "cell_id",
                "Benchmark Crash Count": "benchmark_count",
                "HPMS Yearly Vehicle Miles Traveled": "human_miles",
                "Waymo RO Miles": "waymo_miles",
            }
        )
        .sort_values(["city", "metric", "cell_id"])
    )
    refs = raw["comparisons"]
    rows = []
    for city in CITIES:
        miles = (
            raw["miles"].loc[raw["miles"]["Ops Depot"] == city, "Waymo RO Miles (Millions)"].item()
            * 1e6
        )
        for metric, (_, _, baseline, matched) in METRICS.items():
            unadjusted = refs[(refs.Location == city) & (refs["Benchmark Comparison"] == baseline)]
            adjusted = refs[(refs.Location == city) & (refs["Benchmark Comparison"] == matched)]
            if len(unadjusted) != 1 or len(adjusted) != 1:
                raise ValueError(f"Expected one source comparison for {city}/{metric}")
            rows.append(
                {
                    "city": city,
                    "metric": metric,
                    "waymo_miles": miles,
                    "baseline_ipmm": unadjusted.iloc[0]["Benchmark IPMM"],
                    "published_matched_ipmm": adjusted.iloc[0]["Benchmark IPMM"],
                    "published_events": int(adjusted.iloc[0]["Waymo Count"]),
                }
            )
    events = (
        raw["events"]
        .reset_index()
        .rename(
            columns={
                "index": "source_row",
                "SGO Report ID": "report_id",
                "Year Month": "year_month",
                "Location": "city",
                "Is NHTSA Reportable In-Transport": "in_transport",
                "Is Any-Injury-Reported": "injury",
                "Is Airbag Deployment": "airbag",
            }
        )
    )
    events.source_row += 2  # Header is source CSV row 1.
    if not events.year_month.between(202009, 202412).all():
        raise ValueError("Event outside the frozen source window")
    for col in ["in_transport", "injury", "airbag"]:
        if not events[col].isin([True, False]).all():
            raise ValueError(f"Unknown source membership: {col}")
        events[col] = events[col].astype(int)
    if ((events.injury == 1) | (events.airbag == 1)).any() and (
        events.loc[(events.injury == 1) | (events.airbag == 1), "in_transport"] != 1
    ).any():
        raise ValueError("Outcome outside in-transport source cohort")
    events = events[
        ["source_row", "report_id", "year_month", "city", "in_transport", "injury", "airbag"]
    ]
    return {
        "cells.csv": cells.to_csv(index=False),
        "city_inputs.csv": pd.DataFrame(rows).to_csv(index=False),
        "events.csv": events.to_csv(index=False),
    }


def verify_sources() -> None:
    """Fetch all four pinned sources, verify hashes, and reproduce normalized input files."""
    manifest = json.loads((GEO_DIR / "manifest.json").read_text())
    raw = ROOT / "data/raw/geography"
    raw.mkdir(parents=True, exist_ok=True)
    for item in manifest["sources"]:
        response = requests.get(item["url"], timeout=60)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != item["sha256"]:
            raise ValueError(f"Source bytes changed: {item['filename']}; review before updating")
        (raw / item["filename"]).write_bytes(response.content)
    for name, content in normalized_inputs(raw).items():
        if content != (GEO_DIR / name).read_text():
            raise ValueError(f"Source extraction differs from frozen {name}")
    print("All four source hashes and all normalized input rows verified.")


def main() -> None:
    """Build website data and audit CSV, or check existing artifacts without changing files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-source", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.from_source:
        verify_sources()
    study = build_geography()
    if study["audit"]["benchmark_checks"] != 9 or study["audit"]["count_checks"] != 9:
        raise ValueError("Published benchmark/count mismatch; review the audit before publishing")
    columns = [
        "city",
        "metric",
        "events",
        "waymo_miles",
        "baseline_ipmm",
        "factor",
        "matched_ipmm",
        "published_matched_ipmm",
        "benchmark_delta",
        "benchmark_matches",
        "count_matches",
        "cell_miles",
        "coverage",
        "unallocated_miles",
    ]
    buffer = StringIO()
    pd.DataFrame(study["comparisons"])[columns].to_csv(buffer, index=False)
    outputs = {
        ROOT / "web/waymo-project/geography.json": json.dumps(study, indent=2, allow_nan=False)
        + "\n",
        GEO_DIR / "results.csv": buffer.getvalue(),
        ROOT / "web/waymo-project/geography-results.csv": buffer.getvalue(),
    }
    for source, target in [
        ("cells.csv", "cells.csv"),
        ("events.csv", "events.csv"),
        ("city_inputs.csv", "inputs.csv"),
        ("manifest.json", "manifest.json"),
    ]:
        outputs[ROOT / f"web/waymo-project/geography-{target}"] = (GEO_DIR / source).read_text()
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise ValueError(f"Stale geography artifact: {path.relative_to(ROOT)}")
        else:
            path.write_text(content)
    print(
        "9/9 spatial benchmarks and 9/9 source counts match; "
        f"{study['audit']['unique_cells']} cells."
    )
    for row in study["comparisons"]:
        print(
            f"{row['city']}/{row['metric']}: multiplier {row['factor']:.6f}; "
            f"coverage {row['coverage']:.4%}"
        )


if __name__ == "__main__":
    main()
