"""Reconstruct spatial benchmark adjustment from the matched December 2024 release."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from av_safety.geography_validation import validate_geography
from av_safety.stats import poisson_rate_ci

ROOT = Path(__file__).resolve().parents[2]
GEO_DIR = ROOT / "data/processed/geography"
CITIES = {"SAN_FRANCISCO": "San Francisco", "PHOENIX": "Phoenix", "LOS_ANGELES": "Los Angeles"}
METRICS = {
    "airbag": (
        "Airbag deployment",
        "Is Airbag Deployment",
        "Airbag Deployment (non-Dynamic)",
        "Airbag Deployment",
    ),
    "blincoe_any_injury": (
        "Injury · reporting-adjusted",
        "Is Any-Injury-Reported",
        "Any-injury-reported (non-Dynamic)",
        "Any-injury-reported",
    ),
    "observed_any_injury": (
        "Injury · police-observed",
        "Is Any-Injury-Reported",
        "Any-injury-reported (observed, non-Dynamic)",
        "Any-injury-reported (Observed, Dynamic)",
    ),
}


def portable(value: Any) -> Any:
    """Round only exported floats to 12 significant digits for cross-platform reproducibility."""
    if isinstance(value, dict):
        return {key: portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item) for item in value]
    return float(f"{value:.12g}") if isinstance(value, float) else value


def spatial_factor(counts: list[float], human_miles: list[float], av_miles: list[float]) -> float:
    """Return the relative spatial benchmark multiplier on shared geographic support.

    Args: Matched vectors of nonnegative benchmark counts, positive HPMS miles,
        and nonnegative ADS miles. Counts may be geographically allocated fractions.
    Returns: A dimensionless multiplier, not an absolute passenger-vehicle crash rate.
    Formula: [sum(W_i*C_i/H_i)/sum(W_i)] / [sum(C_i)/sum(H_i)].
    Reference: Chen et al., arXiv:2410.08903v1, Equations 1–5 and HPMS calibration.
        Apply this relative multiplier to the published passenger-vehicle benchmark;
        uncalibrated HPMS includes more than passenger-vehicle mileage.
    """
    if not counts or not len(counts) == len(human_miles) == len(av_miles):
        raise ValueError("cell vectors must be nonempty and have equal lengths")
    if any(not math.isfinite(v) or v < 0 for v in [*counts, *av_miles]):
        raise ValueError("counts and ADS miles must be nonnegative and finite")
    if any(not math.isfinite(v) or v <= 0 for v in human_miles):
        raise ValueError("human cell mileage must be positive and finite")
    if math.fsum(counts) <= 0 or math.fsum(av_miles) <= 0:
        raise ValueError("positive total benchmark count and ADS mileage required")
    weighted = math.fsum(w * c / h for c, h, w in zip(counts, human_miles, av_miles, strict=True))
    return weighted / math.fsum(av_miles) / (math.fsum(counts) / math.fsum(human_miles))


def scenario(row: dict, mix: float = 1, stress: float = 1) -> dict:
    """Interpolate mileage distributions and stress benchmark scale, conditional on inputs.

    mix=0 uses HPMS shares, mix=1 uses observed ADS shares. Intermediate distributions
    and stress != 1 are hypothetical. R(mix,stress)=R0*(1+mix*(factor-1))*stress.
    Bounds divide the ADS 95% Garwood interval by that fixed benchmark. They exclude
    uncertainty in the benchmark, mileage, reporting adjustment and spatial weights.
    """
    if not math.isfinite(mix) or not 0 <= mix <= 1:
        raise ValueError("mix must be in [0,1]")
    if not math.isfinite(stress) or stress <= 0:
        raise ValueError("stress must be positive and finite")
    benchmark = row["baseline_ipmm"] * (1 + mix * (row["factor"] - 1)) * stress
    if not math.isfinite(benchmark) or benchmark <= 0:
        raise ValueError("scenario benchmark must be positive and finite")
    ratio = row["waymo_ipmm"] / benchmark
    return {
        "benchmark_ipmm": benchmark,
        "ratio": ratio,
        "ratio_lower": row["waymo_lower"] / benchmark,
        "ratio_upper": row["waymo_upper"] / benchmark,
        "reduction_percent": (1 - ratio) * 100,
        "reduction_lower": (1 - row["waymo_upper"] / benchmark) * 100,
        "reduction_upper": (1 - row["waymo_lower"] / benchmark) * 100,
        "expected_events": benchmark * row["waymo_miles"] / 1e6,
    }


def load_geography(
    directory: Path = GEO_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Validate the frozen inputs before computing anything."""
    manifest = json.loads((directory / "manifest.json").read_text())
    hashes = manifest.get("processed_sha256")
    if not isinstance(hashes, dict) or set(hashes) != {
        "cells.csv",
        "city_inputs.csv",
        "events.csv",
    }:
        raise ValueError("Manifest must hash exactly the three geographic input files")
    for filename, expected in manifest["processed_sha256"].items():
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Geography input hash mismatch: {filename}")
    cells = pd.read_csv(
        directory / "cells.csv", dtype={"cell_id": str}, float_precision="round_trip"
    )
    inputs = pd.read_csv(directory / "city_inputs.csv", float_precision="round_trip")
    events = pd.read_csv(directory / "events.csv", dtype={"report_id": str}, keep_default_na=False)
    validate_geography(cells, inputs, events, set(CITIES), set(METRICS))
    return cells, inputs, events, manifest


def exposure_bands(cells: pd.DataFrame) -> list[dict]:
    """Group cells into five count-balanced bands ordered by local benchmark C/H.

    Bands contain approximately equal numbers of cells, not equal exposure. Ties
    are resolved by cell ID. Bands are a descriptive visualization, not inference
    that an individual cell is intrinsically dangerous.
    """
    ordered = (
        cells.assign(local_rate=cells.benchmark_count / cells.human_miles)
        .sort_values(["local_rate", "cell_id"], kind="stable")
        .reset_index(drop=True)
    )
    human_total, av_total = math.fsum(ordered.human_miles), math.fsum(ordered.waymo_miles)
    groups = []
    for band in range(5):
        group = ordered.iloc[len(ordered) * band // 5 : len(ordered) * (band + 1) // 5]
        groups.append(
            {
                "band": band + 1,
                "cells": len(group),
                "human_share": math.fsum(group.human_miles) / human_total,
                "waymo_share": math.fsum(group.waymo_miles) / av_total,
                "relative_rate_min": float(group.local_rate.min())
                / (math.fsum(cells.benchmark_count) / human_total),
                "relative_rate_max": float(group.local_rate.max())
                / (math.fsum(cells.benchmark_count) / human_total),
            }
        )
    return groups


def build_geography(directory: Path = GEO_DIR) -> dict:
    """Recount events and reconstruct all nine published dynamic benchmark rates."""
    cells, inputs, events, manifest = load_geography(directory)
    results = []
    for entry in inputs.to_dict("records"):
        city, metric = entry["city"], entry["metric"]
        local = cells[(cells.city == city) & (cells.metric == metric)]
        factor = spatial_factor(
            local.benchmark_count.tolist(), local.human_miles.tolist(), local.waymo_miles.tolist()
        )
        event_column = "airbag" if metric == "airbag" else "injury"
        included = events[(events.city == city) & (events[event_column] == 1)]
        rate = poisson_rate_ci(len(included), entry["waymo_miles"])
        benchmark = entry["baseline_ipmm"] * factor
        covered_miles = math.fsum(local.waymo_miles)
        if covered_miles > entry["waymo_miles"]:
            raise ValueError("cell exposure exceeds reported total; review source alignment")
        row = {
            **entry,
            "label": CITIES[city],
            "metric_label": METRICS[metric][0],
            "factor": factor,
            "matched_ipmm": benchmark,
            "events": len(included),
            "waymo_ipmm": rate.rate * 1e6,
            "waymo_lower": rate.lower * 1e6,
            "waymo_upper": rate.upper * 1e6,
            "cells": len(local),
            "cell_miles": covered_miles,
            "coverage": covered_miles / entry["waymo_miles"],
            "unallocated_miles": entry["waymo_miles"] - covered_miles,
            "benchmark_delta": benchmark - entry["published_matched_ipmm"],
            "benchmark_matches": abs(benchmark - entry["published_matched_ipmm"]) < 1e-9,
            "count_matches": len(included) == entry["published_events"],
            "bands": exposure_bands(local),
            "event_rows": included.source_row.tolist(),
        }
        row["unadjusted"] = scenario(row, 0)
        row["matched"] = scenario(row, 1)
        row["scenarios"] = [
            {"mix": mix, "stress": stress, **scenario(row, mix, stress)}
            for mix in [0, 0.25, 0.5, 0.75, 1]
            for stress in [0.5, 1, 1.5]
        ]
        results.append(row)
    return portable(
        {
            "study_id": "spatial-202412",
            "release_date": "2025-03-19",
            "period": "September 2020–December 2024",
            "benchmark_year": 2022,
            "source_manifest": manifest,
            "comparisons": results,
            "audit": {
                "unique_cells": len(cells[["city", "cell_id"]].drop_duplicates()),
                "cell_outcome_rows": len(cells),
                "source_event_rows": len(events),
                "benchmark_checks": sum(r["benchmark_matches"] for r in results),
                "count_checks": sum(r["count_matches"] for r in results),
            },
        }
    )
