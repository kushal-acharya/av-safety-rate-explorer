# Geographic exposure matching

This independent computational reproduction uses the Waymo Safety Impact data release
of **March 19, 2025**, covering rider-only operations **September 2020–December 2024**,
with **2022 human benchmarks**. It reconstructs nine published dynamic benchmark rates
and recounts the corresponding Waymo event cohorts from four matching CSVs.
It is a historical snapshot, not the current Safety Impact dashboard.

[Interactive study](https://vivaran.news/waymo-project/?tab=geography) ·
[Source manifest](../data/processed/geography/manifest.json) ·
[Audit results](../data/processed/geography/results.csv)

## Question and finding

How does the comparison change when human collision benchmarks reflect Waymo's
geographic mileage distribution? All nine city/outcome spatial benchmark reconstructions
agree with the source at absolute tolerance 1e-9 incidents per million miles (IPMM),
before export rounding. All nine Waymo event counts match exactly.

| City | Outcome | Baseline IPMM | Spatial factor | Matched IPMM | Waymo events |
|---|---|---:|---:|---:|---:|
| San Francisco | Airbag | 1.786501 | 1.294795 | 2.313153 | 5 |
| Phoenix | Airbag | 1.320286 | 1.090833 | 1.440212 | 8 |
| Los Angeles | Airbag | 1.165371 | 1.009118 | 1.175997 | 1 |
| San Francisco | Injury, reporting-adjusted | 5.823794 | 1.379784 | 8.035579 | 14 |
| Phoenix | Injury, reporting-adjusted | 1.811546 | 1.170017 | 2.119540 | 21 |
| Los Angeles | Injury, reporting-adjusted | 2.257182 | 1.067196 | 2.408855 | 6 |
| San Francisco | Injury, police-observed | 3.978592 | 1.378962 | 5.486327 | 14 |
| Phoenix | Injury, police-observed | 1.241401 | 1.170060 | 1.452513 | 21 |
| Los Angeles | Injury, police-observed | 1.544620 | 1.066288 | 1.647009 | 6 |

The adjustment raises the SF airbag human benchmark 29.5%, versus 0.9% in LA.
This changes the reference comparison; it does not change the observed Waymo counts
or demonstrate a causal effect of geography on safety.

## Calculation and dependencies

Following the spatial weighting method in
[Chen et al., arXiv:2410.08903v1](https://arxiv.org/pdf/2410.08903v1), define for each
cell its source-allocated benchmark crash count C, HPMS annual vehicle miles H,
and Waymo rider-only miles W. On the shared cell support:

```
local human rate_i = C_i / H_i
factor = [sum(W_i × C_i / H_i) / sum(W_i)] / [sum(C_i) / sum(H_i)]
matched benchmark = published non-Dynamic passenger-vehicle baseline × factor
```

The relative multiplier is reconstructed from 987 cells (123 SF, 629 Phoenix,
235 LA) with three outcomes each, or 2,961 cell/outcome rows. The denominator of
the factor is the human-mileage-weighted rate on the same cell support. HPMS includes
non-passenger vehicle exposure; multiplying the published passenger baseline by the
relative factor retains the publisher's calibration. We do **not** substitute a raw
HPMS absolute rate for a passenger-vehicle benchmark.

The baseline, allocated benchmark counts, mileage and outcome labels remain
publisher-supplied inputs. This does not reconstruct raw police crash records,
passenger-mileage calibration, reporting corrections or crash adjudication.
Reporting-adjusted injury inputs already include the correction; it is not applied twice.
Police-observed human injury benchmarks are an alternative reporting assumption;
the Waymo injury cohort stays the same. They are not a separate Waymo outcome.

## Exposure coverage and event identity

The cell files cover 99.8103% of SF's 16.032 million miles, 99.8879% of Phoenix's
28.331 million, and 99.6664% of LA's 5.165 million. The missing summed exposure is
shown explicitly; its cause is not independently established. CSV1 reports city
mileage rounded to 0.001 million miles. The Waymo rate uses that city total; the
spatial weights normalize on available cell mileage. Differences from source Waymo
rates at the last few digits can arise from that rounded exposure. We do not reverse
engineer mileage from a published rate to force agreement.

Austin has no cell data in this release and is excluded from spatial comparisons.
The downloaded event table retains all 523 original rows, including Austin. Membership
flags restrict the displayed cohorts to injury or airbag events, all in transport.
Two missing SGO IDs and the report ID `30270-9540` repeated across SF and LA are
preserved using their original CSV row numbers. Neither repeated-ID row belongs to
the selected injury or airbag cohorts. No records are invented or silently deduplicated.
S2 identifiers are stored as strings to preserve their 19 digits. Cell mileage is
repeated across outcomes in the source and is never summed across outcomes.

## Interactive sensitivity and conditional uncertainty

The mileage slider interpolates **distributions**, not vehicle counts or total miles:

```
weight_i(lambda) = (1 − lambda) × H_i/sum(H) + lambda × W_i/sum(W)
benchmark(lambda, scale) = baseline × [1 + lambda × (factor − 1)] × scale
rate ratio = (Waymo events / city miles × 1e6) / benchmark
rate reduction = 100 × (1 − rate ratio)
```

Lambda 0 and 1 are the human and observed Waymo geographic shares. Intermediate
values are hypothetical. The 50–150% benchmark scale is a hypothetical stress test,
not a calibrated uncertainty range. Neither control changes the source audit.
The distribution chart groups cells into five approximately equal **cell-count**
bands ordered by C/H, ties by string cell ID. Bands are not equal-mileage quintiles,
and local rates are not evidence of intrinsic road danger.

Each scenario divides the Waymo two-sided 95% Garwood rate endpoints by the fixed
scenario benchmark. This interval includes **only Waymo count uncertainty**, under
Poisson independence and a constant-rate assumption. It excludes uncertainty in
human benchmarks, reporting adjustment, exposure and spatial weights. It is not a
reproduction of the publisher's full rate-ratio interval or spatial bootstrap.
Allocated fractional cell counts are not treated as independent observed integer
crash counts to fabricate a bootstrap.

Spatial matching alone does not address time of day, weather, vehicle mix, road
conditions, changes over time or residual reporting differences. This is an
observational comparison, not a causal safety estimate. It is separate from the
2023 paper cohort and DMV disengagement exposure.

## Reproduce and verify

```bash
uv sync --locked
# No network: recompute from hash-verified, committed inputs.
uv run python scripts/reproduce_geography.py --check
# Network: verify all four archived source hashes and their exact extraction too.
uv run python scripts/reproduce_geography.py --from-source --check
uv run pytest tests/test_geography.py -q
npm test
```

The manifest records source URLs, retrieval time and SHA-256 hashes for source and
normalized inputs. A changed hash fails closed. The build makes audit decisions at
full precision and serializes floats at 12 significant digits for portable exports.
The reference tests include a hand-calculated two-cell example, invariance under
reordering and common count/exposure scaling, invalid data, coverage, identity
preservation, endpoint and stress behavior, and source drift. JavaScript calculations
agree with 135 Python reference scenarios. Browser checks exercise all nine selections,
URL persistence, slider focus, invariant audit, CSV contents, mobile and retry.

The geographic study runs in the custom web interface and Python CLI; the original
Streamlit companion remains the DMV explorer. No additional server or tracking service
is needed.
