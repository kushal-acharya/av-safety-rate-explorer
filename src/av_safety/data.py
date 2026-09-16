"""Normalize the DMV's historical CSVs once; expose audited tidy tables downstream."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KEYS = ["year", "mode", "manufacturer"]
# 2020–2024 use the same substantive headings, with whitespace/newline variation.
# 2021 adds an empty column; 2023–24 contain thousands of blank event rows.
COLUMN_MAP = {
    "manufacturer": "manufacturer",
    "vin number": "vin",
    "date": "date",
    "annual total": "miles",
    "annual total of disengagements": "reported_events",
    "description of facts causing disengagement": "cause_text",
}
NAME_PREFIXES = {
    "aimotive": "aiMotive",
    "apollo": "Apollo",
    "apple": "Apple",
    "argo": "Argo AI",
    "aurora": "Aurora",
    "autox": "AutoX",
    "bmw": "BMW",
    "bosch": "Bosch",
    "cruise": "Cruise",
    "deeproute": "DeepRoute",
    "didi": "DiDi",
    "easymile": "EasyMile",
    "gatik": "Gatik",
    "ghost": "Ghost Autonomy",
    "imagry": "Imagry",
    "intel": "Intel",
    "lyft": "Lyft",
    "mercedes": "Mercedes-Benz",
    "motional": "Motional",
    "nissan": "Nissan",
    "nullmax": "Nullmax",
    "nuro": "Nuro",
    "nvidia": "NVIDIA",
    "pony": "Pony.ai",
    "qcraft": "Qcraft",
    "qualcomm": "Qualcomm",
    "ridecell": "Ridecell",
    "sf motors": "SF Motors",
    "telenav": "Telenav",
    "toyota": "Toyota Research Institute",
    "udelv": "Udelv",
    "valeo": "Valeo",
    "vueron": "Vueron",
    "waymo": "Waymo",
    "weride": "WeRide",
    "woven": "Woven by Toyota",
    "zoox": "Zoox",
}
CAUSE_RULES = [
    ("Perception", r"perception|detect|classif|sensor|localiz"),
    ("Planning", r"plann|trajectory|path|prediction|maneuver"),
    ("Hardware-Software", r"hardware|software|system|comput|fault"),
    ("Other-Road-User", r"pedestrian|cyclist|other vehicle|road user"),
    ("Weather-Road", r"rain|snow|weather|construction|road surface"),
    ("Precautionary", r"precaution|comfort|caution|safety driver"),
]


def manufacturer_name(value: str) -> str:
    """Normalize case and known corporate aliases without merging distinct Toyota entities."""
    clean = re.sub(r"\s+", " ", str(value)).strip()
    for prefix, name in NAME_PREFIXES.items():
        if clean.lower().startswith(prefix):
            return name
    return clean


def cause_category(value: str) -> str:
    """Assign the first matching coarse keyword bucket; this is not an adjudication."""
    for label, pattern in CAUSE_RULES:
        if re.search(pattern, value, re.IGNORECASE):
            return label
    return "Unknown"


def _read(path: Path) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        frame = pd.read_csv(path, encoding="cp1252", dtype=str)
    names = {}
    for column in frame.columns:
        normalized = re.sub(r"\s+", " ", column).strip().lower()
        target = COLUMN_MAP.get(normalized, normalized)
        for prefix, value in [
            ("vehicle is capable", "driverless_capable"),
            ("driver present", "driver_present"),
            ("disengagement initiated", "initiated_by"),
            ("disengagement location", "location"),
        ]:
            if normalized.startswith(prefix):
                target = value
        names[column] = target
    frame = frame.rename(columns=names).dropna(how="all")
    frame = frame[frame.manufacturer.notna()].copy()
    frame["manufacturer"] = frame.manufacturer.map(manufacturer_name)
    frame["vin"] = frame.vin.fillna("").str.strip().str.upper()
    return frame


def _numeric(series: pd.Series) -> pd.Series:
    clean = series.str.replace(",", "", regex=False).str.replace(r"\s+", "", regex=True)
    result = pd.to_numeric(clean, errors="coerce")
    invalid = result.isna() & clean.notna() & ~clean.isin(["", "N/A", "NA", "-"])
    if invalid.any():
        raise ValueError(f"Unrecognized numeric values: {clean[invalid].unique()}")
    return result


def build(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Read original reports and return deterministic tables plus an explicit audit."""
    raw_dir = raw_dir or ROOT / "data/raw"
    events, vehicles, audit = [], [], []
    for path in sorted(raw_dir.glob("*/*-mileage.csv")):
        year = int(path.parent.name)
        mode = path.name.removesuffix("-mileage.csv")
        frame = _read(path)
        months = [
            c for c in frame if re.match(r"^(dec|jan|feb|mar|apr|may|jun|july|aug|sep|oct|nov) ", c)
        ]
        annual = _numeric(frame.miles)
        month_values = frame[months].apply(_numeric)
        reconstructed = annual.isna() & month_values.notna().any(axis=1)
        annual = annual.fillna(month_values.sum(axis=1, min_count=1))
        frame["miles"] = annual
        frame["reported_events"] = _numeric(frame.reported_events)
        missing = frame.miles.isna() | frame.reported_events.isna()
        audit.append(
            {
                "year": year,
                "mode": mode,
                "issue": "annual miles from monthly sum",
                "rows": int(reconstructed.sum()),
            }
        )
        audit.append(
            {
                "year": year,
                "mode": mode,
                "issue": "missing exposure/count excluded",
                "rows": int(missing.sum()),
            }
        )
        frame = frame[~missing].copy()
        if (frame.miles < 0).any() or (frame.reported_events < 0).any():
            raise ValueError(f"Negative count/exposure in {path}")
        frame["year"], frame["mode"] = year, mode
        vehicles.append(frame[KEYS + ["vin", "miles", "reported_events"]])
        detail = _read(path.with_name(f"{mode}-events.csv"))
        detail["year"], detail["mode"] = year, mode
        dates = detail.date.str.strip().str.replace(r"\.(?=\s|$)", "", regex=True)
        detail["date"] = pd.to_datetime(dates, format="mixed", errors="coerce")
        valid = detail.date.between(
            pd.Timestamp(year - 1, 12, 1), pd.Timestamp(year, 11, 30, 23, 59, 59)
        )
        audit.append(
            {
                "year": year,
                "mode": mode,
                "issue": "unparseable/out-of-period detail date",
                "rows": int((~valid).sum()),
            }
        )
        # Retain the reported year and explicitly flag source date anomalies.
        detail["date_in_period"] = valid
        for c in ["driverless_capable", "driver_present"]:
            detail[c] = (
                detail[c].str.strip().str.lower().map({"yes": True, "no": False}).astype("boolean")
            )
        detail["initiated_by"] = detail.initiated_by.fillna("Unknown").str.strip().str.title()
        detail["initiated_by"] = detail.initiated_by.replace({"Av System": "AV System"})
        detail["location"] = detail.location.fillna("Unknown").str.strip().str.title()
        detail["cause_text"] = detail.cause_text.fillna("")
        detail["cause_category"] = detail.cause_text.map(cause_category)
        events.append(
            detail[
                KEYS
                + [
                    "date",
                    "date_in_period",
                    "vin",
                    "driverless_capable",
                    "driver_present",
                    "initiated_by",
                    "location",
                    "cause_text",
                    "cause_category",
                ]
            ]
        )
    if not vehicles:
        raise ValueError("No raw DMV files found; run scripts/download_data.py first")
    units = pd.concat(vehicles, ignore_index=True)
    units = units.groupby(KEYS + ["vin"], as_index=False).sum(numeric_only=True)
    if (units.reported_events % 1 != 0).any():
        raise ValueError("Non-integer reported annual count")
    units["reported_events"] = units.reported_events.astype(int)
    event_table = pd.concat(events, ignore_index=True).sort_values(KEYS + ["date", "vin"])
    annual = units.groupby(KEYS, as_index=False)[["miles", "reported_events"]].sum()
    detail_counts = event_table.groupby(KEYS).size().rename("detail_events")
    annual = annual.merge(detail_counts, on=KEYS, how="left").fillna({"detail_events": 0})
    annual["detail_events"] = annual.detail_events.astype(int)
    annual["event_difference"] = annual.reported_events - annual.detail_events
    annual["events"] = annual.reported_events
    annual["eligible"] = annual.miles > 0
    zero = units.miles == 0
    if (units.loc[zero, "reported_events"] > 0).any():
        logging.warning("Zero-exposure VIN rows with events are excluded from NB fits; see audit.")
    audit.append(
        {
            "year": 0,
            "mode": "all",
            "issue": "zero-mile VINs with positive events",
            "rows": int((zero & (units.reported_events > 0)).sum()),
        }
    )
    return {
        "events": event_table.reset_index(drop=True),
        "exposure": annual,
        "units": units,
        "audit": pd.DataFrame(audit),
    }


def load_processed() -> dict[str, pd.DataFrame]:
    """Load the committed offline data tables."""
    return {
        name: pd.read_parquet(ROOT / f"data/processed/{name}.parquet")
        for name in ["events", "exposure", "units", "audit"]
    }


def main() -> None:
    """Write reproducible CSV and Parquet snapshots with transparent discrepancy records."""
    tables = build()
    out = ROOT / "data/processed"
    out.mkdir(exist_ok=True, parents=True)
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S")
        frame.to_parquet(out / f"{name}.parquet", index=False)
    print(json.dumps({k: len(v) for k, v in tables.items()}))
    print(tables["exposure"].query('manufacturer == "Waymo"').to_string(index=False))
    print(tables["exposure"].query("event_difference != 0").to_string(index=False))
    print(tables["audit"].query("rows > 0").to_string(index=False))


if __name__ == "__main__":
    main()
