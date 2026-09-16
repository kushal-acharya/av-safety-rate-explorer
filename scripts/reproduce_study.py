"""Regenerate the publication study offline, or verify its event extraction from the PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
import requests

from av_safety.replication import PAPER_SHA256, PAPER_URL, ROOT, STUDY_DIR, reproduce_study


def verify_source_pdf() -> None:
    """Re-download the pinned PDF and independently re-extract the appendix memberships."""
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise SystemExit(
            "Use: uv run --group research python scripts/reproduce_study.py --from-source"
        ) from error
    response = requests.get(PAPER_URL, timeout=60)
    response.raise_for_status()
    if hashlib.sha256(response.content).hexdigest() != PAPER_SHA256:
        raise ValueError("Published PDF bytes changed; review the version before proceeding")
    raw = ROOT / "data/raw/replication/kusano-7m-v3.pdf"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(response.content)
    reader = PdfReader(BytesIO(response.content))
    records = []
    pattern = re.compile(
        r"(30270-\d+|NA)\s+(?:(\d+|NA)\s+)?(PHX|SFO|LA)\s+"
        r"((?:True|False)(?:\s+(?:True|False)){4})"
    )
    for index in [18, 19]:
        for line in reader.pages[index].extract_text().splitlines():
            match = pattern.fullmatch(line.strip())
            if not match:
                continue
            sgo, early, city, flags = match.groups()
            values = [int(v == "True") for v in flags.split()]
            records.append(
                {
                    "event_id": sgo if sgo != "NA" else f"victor-2023-{early}",
                    "sgo_report_id": sgo if sgo != "NA" else "",
                    "early_event_number": early if early and early != "NA" else "",
                    "location": city,
                    "sgo_reportable": values[0],
                    "in_transport_impacted": values[1],
                    "above_low_delta_v": values[2],
                    "police_reported": values[3],
                    "any_injury": values[4],
                    "source_page": index + 1,
                }
            )
    expected = pd.read_csv(STUDY_DIR / "events.csv", keep_default_na=False)
    pd.testing.assert_frame_equal(pd.DataFrame(records), expected)
    print(f"Source verified: SHA-256 matches; all {len(records)} event rows re-extracted exactly.")


def artifacts(study: dict) -> dict[Path, str]:
    """Serialize the same Python calculation for the website, CSV export and offline audit."""
    table = []
    for row in study["comparisons"]:
        for check in row["checks"]:
            table.append({"comparison": row["id"], **check})
    csv_buffer = StringIO()
    pd.DataFrame(table).to_csv(csv_buffer, index=False)
    serialized = json.dumps(study, indent=2, allow_nan=False) + "\n"
    return {
        ROOT / "web/waymo-project/replication.json": serialized,
        STUDY_DIR / "results.csv": csv_buffer.getvalue(),
        ROOT / "web/waymo-project/replication-results.csv": csv_buffer.getvalue(),
        ROOT / "web/waymo-project/replication-events.csv": (STUDY_DIR / "events.csv").read_text(),
        ROOT / "web/waymo-project/replication-inputs.csv": (
            STUDY_DIR / "comparisons.csv"
        ).read_text(),
        ROOT / "web/waymo-project/replication-manifest.json": (
            STUDY_DIR / "manifest.json"
        ).read_text(),
    }


def main() -> None:
    """Fail on input drift or mismatched references; optionally require committed outputs match."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-source", action="store_true", help="Fetch/hash PDF and verify extraction"
    )
    parser.add_argument("--check", action="store_true", help="Verify outputs without writing them")
    args = parser.parse_args()
    if args.from_source:
        verify_source_pdf()
    study = reproduce_study()
    if study["audit"]["checks_passed"] != study["audit"]["checks_total"]:
        raise ValueError("Published reference mismatch; inspect calculated deltas")
    for path, content in artifacts(study).items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise ValueError(f"Generated artifact is stale: {path.relative_to(ROOT)}")
        else:
            path.write_text(content)
    primary = study["comparisons"][0]
    print(
        f"{study['audit']['checks_passed']}/{study['audit']['checks_total']} reference checks pass."
    )
    print(f"SF injury: {primary['events']} event / {primary['waymo_miles']:,.0f} rider-only miles.")
    print(
        f"Rate ratio {primary['paper_code']['ratio']:.6f}; "
        f"{primary['reduction_percent']:.2f}% lower."
    )
    print("Paper-code tails: 1.25% each. Equation 2 tails: 2.5% each. Both are exported.")
    print("Benchmark inputs and outcome labels are author-supplied, not independently adjudicated.")


if __name__ == "__main__":
    main()
