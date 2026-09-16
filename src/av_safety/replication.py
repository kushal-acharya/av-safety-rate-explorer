"""Reproduce a frozen publication, keeping reported values separate from calculations."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pandas as pd
from scipy.stats import betaprime

from av_safety.stats import poisson_rate_ci

ROOT = Path(__file__).resolve().parents[2]
STUDY_DIR = ROOT / "data/processed/replication"
PAPER_URL = "https://arxiv.org/pdf/2312.12675v3"
PAPER_SHA256 = "f25356e8ad1b1ff01f158f0bcce6e863aedbf52f84928268972e57dcc60ede5e"
LOCATIONS = {"SFO": "San Francisco", "PHX": "Phoenix", "LA": "Los Angeles"}
OUTCOMES = {"any_injury": "Any injury reported", "police_reported": "Police reported"}


def _portable_snapshot(value):
    """Serialize results to 12 decimals, ignoring platform differences around 1e-15.

    Calculations and tolerance decisions occur before this export-only rounding.
    Twelve decimals substantially exceed the precision of the published inputs.
    """
    if isinstance(value, dict):
        return {key: _portable_snapshot(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable_snapshot(item) for item in value]
    return round(value, 12) if isinstance(value, float) else value


def nelson_interval(
    events: int,
    miles: float,
    benchmark_ipmm: float,
    benchmark_miles: float,
    *,
    convention: str = "equation",
) -> dict:
    """Return the publication's beta-prime ratio interval under an explicit convention.

    Args: An integer ADS count, positive exposures, and a positive human rate per
        million miles. `equation` uses Equation 2; `paper_code` reproduces Listing 1.
    Returns: Ratio, endpoints, tail probability and model central probability.
    Formula: (s/t) * beta_prime_quantile(q, Y, X+1) and
        (s/t) * beta_prime_quantile(1-q, Y+1, X), X = benchmark_ipmm*s/1e6.
    Reference: Kusano et al., arXiv:2312.12675v3, Equation 2 and Appendix A.3.
        Listing 1 halves alpha before halving again for positive counts, so q=.0125.
        Reconstructed X can be fractional; this reproduces published arithmetic,
        not an exact-coverage guarantee for adjusted human benchmark estimates.
    """
    if not math.isfinite(events) or events < 0 or int(events) != events:
        raise ValueError("events must be a nonnegative integer")
    if any(not math.isfinite(v) or v <= 0 for v in [miles, benchmark_ipmm, benchmark_miles]):
        raise ValueError("exposures and benchmark rate must be positive and finite")
    if convention not in {"equation", "paper_code"}:
        raise ValueError("unknown interval convention")
    tail = 0.0125 if convention == "paper_code" and events > 0 else 0.025
    benchmark_count = benchmark_ipmm * benchmark_miles / 1e6
    scale = benchmark_miles / miles
    return {
        "ratio": (events / miles * 1e6) / benchmark_ipmm,
        "lower": float(scale * betaprime.ppf(tail, events, benchmark_count + 1)) if events else 0,
        "upper": float(scale * betaprime.ppf(1 - tail, events + 1, benchmark_count)),
        "tail_probability": tail,
        "central_probability": 1 - 2 * tail,
        "benchmark_count": benchmark_count,
    }


def load_study_inputs(directory: Path = STUDY_DIR) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load and validate frozen inputs; source labels are retained, never re-adjudicated."""
    manifest = json.loads((directory / "manifest.json").read_text())
    for filename, expected in manifest["processed_sha256"].items():
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Frozen input hash mismatch: {filename}")
    events = pd.read_csv(directory / "events.csv", keep_default_na=False)
    comparisons = pd.read_csv(directory / "comparisons.csv")
    if events.event_id.duplicated().any():
        raise ValueError("Duplicate event identifier")
    for col in ["sgo_reportable", "in_transport_impacted", "police_reported", "any_injury"]:
        if not events[col].isin([0, 1]).all():
            raise ValueError(f"Invalid membership flag: {col}")
    if not events.location.isin(LOCATIONS).all():
        raise ValueError("Unknown study location")
    if ((events.any_injury | events.police_reported) > events.in_transport_impacted).any():
        raise ValueError("Outcome outside in-transport/impacted cohort")
    if comparisons.id.duplicated().any():
        raise ValueError("Duplicate comparison")
    return events, comparisons, manifest


def reproduce_study(directory: Path = STUDY_DIR) -> dict:
    """Count appendix events, compute estimates, and audit against separate Table 7 values."""
    events, inputs, manifest = load_study_inputs(directory)
    results = []
    for row in inputs.to_dict("records"):
        city_events = events[events.location == row["location"]]
        included = city_events[
            (city_events.in_transport_impacted == 1) & (city_events[row["outcome"]] == 1)
        ]
        count = len(included)
        arguments = (count, row["waymo_miles"], row["benchmark_ipmm"], row["benchmark_miles"])
        paper = nelson_interval(*arguments, convention="paper_code")
        equation = nelson_interval(*arguments)
        rate = poisson_rate_ci(count, row["waymo_miles"])
        # Listing 2 itself specifies absolute tolerance 1e-2 for rounded reference values.
        checks = [
            {
                "quantity": "Included events",
                "published": row["published_count"],
                "reproduced": count,
                "delta": count - row["published_count"],
                "tolerance": 0,
                "matches": count == row["published_count"],
            }
        ]
        for name in ["ratio", "lower", "upper"]:
            expected = row[f"published_{name}"]
            checks.append(
                {
                    "quantity": {
                        "ratio": "Rate ratio",
                        "lower": "Ratio lower limit",
                        "upper": "Ratio upper limit",
                    }[name],
                    "published": expected,
                    "reproduced": paper[name],
                    "delta": paper[name] - expected,
                    "tolerance": 0.01,
                    "matches": abs(paper[name] - expected) < 0.01,
                }
            )
        results.append(
            {
                **row,
                "location_label": LOCATIONS[row["location"]],
                "outcome_label": OUTCOMES[row["outcome"]],
                "events": count,
                "waymo_ipmm": rate.rate * 1e6,
                "rate_lower": rate.lower * 1e6,
                "rate_upper": rate.upper * 1e6,
                "expected_at_benchmark": row["benchmark_ipmm"] * row["waymo_miles"] / 1e6,
                "reduction_percent": (1 - paper["ratio"]) * 100,
                "paper_code": paper,
                "equation": equation,
                "checks": checks,
                "event_ids": included.event_id.tolist(),
                "cohort": {
                    "listed": len(city_events),
                    "in_transport_impacted": int(city_events.in_transport_impacted.sum()),
                    "excluded_transport_or_contact": int(
                        (city_events.in_transport_impacted == 0).sum()
                    ),
                    "excluded_outcome": int(city_events.in_transport_impacted.sum()) - count,
                    "included": count,
                },
            }
        )
    return _portable_snapshot(
        {
            "study_id": "kusano-7m-v3",
            "primary_comparison": "sf-injury",
            "title": "Reproducing a published safety result",
            "publication": "Kusano et al. · 7.1 million rider-only miles",
            "version": "arXiv v3 · October 24, 2024",
            "period": "Through October 2023",
            "paper_url": PAPER_URL,
            "doi_url": "https://doi.org/10.1080/15389588.2024.2380786",
            "scope": "Four city/outcome comparisons from Table 7 and Appendix A.3. "
            "Primary: San Francisco, any-injury-reported, Blincoe-adjusted benchmark.",
            "source_manifest": manifest,
            "audit": {
                "listed_events": len(events),
                "in_transport_impacted": int(events.in_transport_impacted.sum()),
                "any_injury": int(events.any_injury.sum()),
                "police_reported": int(events.police_reported.sum()),
                "pre_sgo_events": int((events.sgo_report_id == "").sum()),
                "checks_passed": sum(c["matches"] for r in results for c in r["checks"]),
                "checks_total": sum(len(r["checks"]) for r in results),
            },
            "comparisons": results,
            "events": events.to_dict("records"),
        }
    )
