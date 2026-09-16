# Versioned California DMV data

Retrieved September 16, 2026 (UTC). Historical reporting years **2020–2024**; this
snapshot intentionally follows the supplied project scope and is not the latest year.
All 14 original CSV URLs, download timestamps and SHA-256 hashes are in
[`source_manifest.json`](source_manifest.json). Sources: California DMV annual
Autonomous Vehicle Disengagement and Autonomous Mileage Reports.

A reporting year covers December 1 of the prior calendar year through November 30.
Safety-driver testing and driverless testing are **different permit series** and are
never combined. Driverless snapshots are included only for 2023–2024. Mileage excludes
commercial deployment, out-of-state operations, simulation and private-road testing.

## Reproduce

`uv run python scripts/download_data.py && uv run python -m av_safety.data`

Raw files are ignored; the application and tests read the committed CSV/Parquet files.
Downloads fail nonzero on HTTP errors or unexpected content. Data is never fabricated.

## Cleaning and audit

- Remove completely blank spreadsheet rows; normalize headings and corporate aliases.
- Parse UTF-8 or Windows-1252; remove thousands separators and whitespace in numbers
  (one source has `830 .04`). Numeric values that remain unrecognized fail the build.
- Reconstruct 47 missing 2023 annual mileage cells from the reported monthly cells.
- Count events using the mileage file's annual counts. **All 128 manufacturer/year/mode
  cells reconcile exactly with the detailed event file counts** in this snapshot.
- Preserve 13 source event dates that cannot be parsed or fall outside the reporting
  period, mark `date_in_period=false`, and retain their reported year and counts.
- Preserve zero-exposure vehicles in `units`, but omit them from NB fitting. One
  vehicle reports an event at zero miles; affected groups use exact Poisson with a
  warning instead of silently fitting a different event count.
- Aggregate repeated manufacturer/year/mode/VIN entries and retain zero-event vehicles.
- Toyotas remain separate entities (Toyota Research Institute vs Woven by Toyota).
- Coarse cause categories use first-match keywords: Perception (perception/detection/
  classification/sensor/localization), Planning (planning/trajectory/path/prediction/
  maneuver), Hardware-Software, Other-Road-User, Weather-Road, Precautionary, Unknown.
  These are illustrative text buckets; boilerplate and negation can misclassify records.
- `audit.csv` records source anomalies; `exposure.csv` includes reported counts,
  detail counts, their difference, and exposure eligibility.

The portal's former disengagement overview URL returned 404 at retrieval time;
original file endpoints remain available. Current portal:
https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/

## Event context views

The dashboard and Streamlit companion group initiator, location and cause categories.
Every category rate uses the **entire selected exposure**, not miles driven on a specific
road type or under a specific condition. Category intervals always use exact Poisson,
independently of the overall chart's NB setting. Event shares describe the composition
of reported events; they are undefined when the selection has zero total events.

The detailed event table retains its case-normalized source labels. Context grouping
uses explicit aliases in `CONTEXT_ALIASES` in `data.py`: driver/soft-stop variants map
to Test Driver; system/emergency-stop/software/ADS variants map to AV System. Ambiguous
Yes, Operator, In-Field Retrieval and mixed driver/system responses map to Unknown
(99 records). Urban and Express Way location responses remain Unknown (201 records);
Interstate (On Ramp), Parking Facility and Rural Road have explicit corresponding groups.
No event is discarded. All declared categories remain visible, including zero counts.
Cause keyword categories retain their documented first-match rules and limitations.

## Geographic exposure study

The separate `processed/geography/` snapshot uses the March 19, 2025 Waymo Safety
Impact release, covering September 2020–December 2024 with 2022 human benchmarks.
Retrieved September 16, 2026 UTC. [Manifest](processed/geography/manifest.json)
records all four source URLs and SHA-256 hashes. It contains 987 unique cells across
SF, Phoenix and LA, three selected outcomes, all 523 source event rows and nine
reference inputs. Austin lacks cell data. These sources are not joined to DMV
mileage or the earlier publication study. [Full methodology](../docs/geographic-exposure.md).
