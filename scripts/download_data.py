"""Download the versioned DMV source files, failing explicitly on any missing source."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DMV_PAGE = "https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/"
SOURCES = {
    (year, mode, kind): (
        f"https://www.dmv.ca.gov/portal/file/{year}-autonomous-"
        f"{'vehicle-disengagement' if kind == 'events' else 'mileage'}-reports-"
        f"csv{'driverless' if mode == 'driverless' else ''}/"
    )
    for year in range(2020, 2025)
    for mode in (["safety-driver", "driverless"] if year >= 2023 else ["safety-driver"])
    for kind in ["events", "mileage"]
}


def download(item: tuple) -> dict:
    """Fetch a CSV and record its URL, hash and UTC retrieval time."""
    (year, mode, kind), url = item
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=90)
    response.raise_for_status()
    if b"Manufacturer" not in response.content[:1000]:
        raise ValueError(f"Not a manufacturer CSV: {url}")
    path = ROOT / "data/raw" / str(year) / f"{mode}-{kind}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    print(f"Downloaded {year} {mode} {kind}: {len(response.content):,} bytes")
    return {
        "year": year,
        "mode": mode,
        "kind": kind,
        "url": url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sha256": hashlib.sha256(response.content).hexdigest(),
    }


def main() -> None:
    """Download all required files or stop with the source page for investigation."""
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            manifest = list(pool.map(download, SOURCES.items()))
    except (requests.RequestException, ValueError) as exc:
        raise SystemExit(f"DMV download failed: {exc}. Check {DMV_PAGE}") from exc
    (ROOT / "data/source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
