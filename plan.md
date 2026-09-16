# AV Safety Rate Explorer — Build Plan

A small, live, interactive tool that estimates autonomous-vehicle (AV) safety/incident rates from public California DMV data with proper uncertainty, and tells you how many miles you'd need to prove one software release is safer than another.

One-line pitch (this is what the finished thing must be able to back up):

> "I built a live tool that estimates autonomous-vehicle safety rates from public crash data and tells you how many miles you'd need to prove a release is safer."

## 1. Goals and non-goals

### Goals

1. **Rare-event rate estimation done right.** Incidents per mile (and per 1,000 miles) with Poisson and Negative-Binomial (overdispersed) confidence intervals, correct handling of zero-event cells (rule of three / exact intervals), and a clearly stated exposure offset.
2. **Exploration.** Filter and compare by manufacturer, year, and (where the data supports it) disengagement initiator / location / cause category. One clean, honest Plotly chart per view — not five noisy ones.
3. **Experiment planner.** "To detect an X% improvement between two releases at α and power 1−β, how many miles do I need?" A two-rate power calculation that accounts for overdispersion.
4. **Shipping signal.** Clean repo, README (problem, method, screenshot, how to run), tests for the statistics, reproducible environment, deployed on Streamlit Community Cloud with a public URL.
5. **Honest methods & limitations section** inside the app (what the DMV data can and cannot say about safety).

### Non-goals (do NOT build these)

- No traffic simulator, no synthetic-scenario generation.
- No database backend. Flat files (CSV/Parquet) in the repo are the data layer.
- No multi-page app, auth, user accounts, or fancy theming.
- No deep learning. This is a statistics-and-measurement tool.
- No scraping of DMV collision PDFs unless Phase 1 finds a machine-readable source; collisions are a stretch goal, disengagements are the core.

## 2. Stack (fixed — do not substitute)

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Env / deps | `uv` (`pyproject.toml` + `uv.lock`); also emit `requirements.txt` for Streamlit Cloud |
| UI | Streamlit (single page, tabs) |
| Data | pandas (Polars/DuckDB not needed at this size) |
| Stats | `scipy.stats`, `statsmodels` (GLM Poisson / NegativeBinomial with offset) |
| Charts | Plotly (`plotly.express` / `graph_objects`) |
| Tests | `pytest` |
| Lint/format | `ruff` |
| Deploy | Streamlit Community Cloud from the GitHub `main` branch |

## 3. Data

### Primary source (core, required)

California DMV Autonomous Vehicle **Disengagement Reports** (annual, published every year since 2015 under the AV Testing Program). Each reporting year has two machine-readable pieces:

1. **Disengagement events** — one row per disengagement: manufacturer, permit number, date, VIN, "vehicle is capable of operating without a driver" (Y/N), driver present (Y/N), disengagement initiated by (AV system / test driver / remote operator / passenger), disengagement location (street, highway, parking facility, ...), free-text description of the facts causing the disengagement.
2. **Autonomous miles** — one row per manufacturer × VIN with monthly autonomous miles driven for the reporting year (Dec → Nov reporting period), i.e. the **exposure** denominator.

Exact column names vary slightly by year; the cleaning layer must normalise them.

### Secondary source (stretch, optional)

- CA DMV **AV Collision Reports** (OL 316) — published as individual PDFs; only include if a pre-parsed CSV is available. Otherwise skip.
- NHTSA **Standing General Order** (SGO) crash data — a public CSV of ADS crash reports; an acceptable alternative "incident" series if the builder wants a second event type. Optional.

### Data handling rules

- `scripts/download_data.py` downloads raw files into `data/raw/<year>/`. URLs live in one config dict at the top of the script; the DMV site reorganises periodically, so if a download fails the script must print the page to look on (`https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/disengagement-reports/`) and exit non-zero rather than silently continuing.
- `src/av_safety/data.py` cleans raw files into two tidy tables and writes `data/processed/events.parquet` and `data/processed/exposure.parquet` (plus CSV copies for readability).
- **Commit the processed files to the repo** so the deployed app and tests never depend on the DMV website being up. Raw files are gitignored.
- Include a `data/README.md` describing source, retrieval date, reporting-period quirk (Dec–Nov), and the cleaning steps.

### Tidy schemas

`events` (one row per disengagement):

| column | type | notes |
|---|---|---|
| `year` | int | reporting year |
| `manufacturer` | str | normalised name (e.g. "Waymo LLC" → "Waymo") |
| `date` | date | |
| `vin` | str | may be redacted/missing in some years |
| `driverless_capable` | bool/NA | |
| `driver_present` | bool/NA | |
| `initiated_by` | category | AV System / Test Driver / Remote Operator / Passenger / Unknown |
| `location` | category | Street / Highway / Freeway / Parking / Rural / Interstate / Unknown |
| `cause_text` | str | free text, kept as-is |
| `cause_category` | category | coarse keyword-rule bucket: Perception / Planning / Hardware-Software / Other-Road-User / Weather-Road / Precautionary / Unknown — document the rules, keep them simple |

`exposure` (one row per manufacturer × year, plus an optional manufacturer × year × month table):

| column | type |
|---|---|
| `year` | int |
| `manufacturer` | str |
| `month` | int (1–12) (monthly table only) |
| `miles` | float |

## 4. Statistics module (`src/av_safety/stats.py`) — the heart of the project

All functions are pure, typed, documented with the formula, and unit-tested. Rates are per mile internally; the UI scales to per-1,000 or per-100,000 miles.

1. `poisson_rate_ci(events, miles, alpha=0.05)` — point estimate `events/miles`; **exact (Garwood) interval** via chi-square quantiles: lower = χ²(α/2, 2k)/(2·miles), upper = χ²(1−α/2, 2k+2)/(2·miles). Handles `events == 0` (lower bound 0, upper = −ln(α/2)/miles ≈ 3.69/miles for the two-sided 95% exact interval).
2. `rule_of_three(miles, conf=0.95)` — the closed-form one-sided zero-event upper bound, −ln(1−conf)/miles ≈ 3/miles at 95%. Exposed separately because it is a talking point; the UI must say which convention (one-sided rule of three vs two-sided exact) a displayed zero-event bound uses.
3. `nb_rate_ci(events_by_unit, miles_by_unit, alpha=0.05)` — fit a Negative-Binomial GLM with `log(miles)` offset and intercept only (statsmodels `NegativeBinomial` or `GLM` with NB family; estimate α by ML), return rate, CI, and the dispersion estimate. Fall back to Poisson with a warning if there are too few units (< 3) or dispersion is not identifiable. Units are typically manufacturer-year or VIN-year rows within the current filter.
4. `dispersion_test(events_by_unit, miles_by_unit)` — simple Poisson deviance/Pearson χ² dispersion ratio so the UI can say "overdispersed, NB interval shown" vs "Poisson adequate."
5. `rate_ratio_ci(k1, m1, k2, m2, alpha=0.05)` — ratio of two Poisson rates with a log-scale Wald CI, plus an exact conditional (binomial) test p-value. Used by the Compare tab.
6. `miles_needed(baseline_rate, relative_reduction, alpha=0.05, power=0.80, dispersion=0.0, allocation=0.5, two_sided=True)` — miles per arm (and total) needed to detect a `relative_reduction` (e.g. 0.10) in rate from `baseline_rate`. Use the two-sample Poisson rate test sample-size formula (normal approximation on rates, or the square-root/variance-stabilised version — pick one, document it, test it against a known table), and inflate variance by `(1 + dispersion · baseline_rate · miles)` style NB overdispersion or a simple design-effect multiplier (document which). Also return the expected number of events per arm, because that number is what makes the answer intuitive ("you need ~X events").
7. `power_curve(baseline_rate, relative_reduction, miles_grid, ...)` — power as a function of miles, for the planner chart.

Tests (`tests/test_stats.py`) must include: Garwood interval against published values (k=0 → upper ≈ 3.689/miles at two-sided 95%; k=5 → [1.623, 11.668]/miles); `rule_of_three(miles)` → 2.996/miles; rate ratio of identical rates ≈ 1 with CI covering 1; `miles_needed` monotone in `relative_reduction` and `power`; NB CI ⊇ Poisson CI when overdispersed; all functions reject negative inputs.

## 5. App (`app.py`) — single page, four tabs

Global sidebar: year multiselect, manufacturer multiselect, rate unit (per 1k / per 100k miles), confidence level (90/95/99), interval method (Poisson exact / Negative-Binomial / auto). A small "data as of <date>" caption.

**Tab 1 — Rates.** Table + one horizontal bar/dot chart: disengagements per N miles by manufacturer (or by year when one manufacturer selected), with error bars = CI. Zero-event rows show the upper bound and a "0 events — upper bound only" marker. Toggle: colour by `initiated_by`. Caption explaining the offset and interval.

**Tab 2 — Compare.** Pick group A and group B (manufacturer×year, or the same manufacturer across two years — the "release A vs release B" analogue). Show both rates with CIs, the rate ratio with CI, p-value, and a one-sentence plain-English conclusion ("B's rate is 23% lower; the 95% interval [8%, 36%] excludes zero"). Show miles and event counts so the reader sees the evidence base.

**Tab 3 — Experiment Planner.** Inputs: baseline rate (pre-filled from the current filter's pooled rate), target relative improvement (default 10%), α, power, dispersion (pre-filled from the NB fit, editable), allocation. Outputs: miles per arm, total miles, expected events per arm, and a power-vs-miles Plotly curve with the chosen point marked. A short note: "At Waymo-scale rates, detecting a 10% change in serious events needs on the order of X million miles — this is why rare-event evaluation is hard."

**Tab 4 — Methods & Limitations.** Markdown: what a disengagement is and is not (it is *not* a crash and is self-reported with inconsistent thresholds across companies); Dec–Nov reporting period; exposure is company-reported; why NB over Poisson; what the planner assumes (independent events, constant rate, two-arm randomisation which Waymo can do but the DMV data cannot); what this tool cannot conclude (company A is "safer" than company B).

UX rules: `st.cache_data` on data loading and expensive fits; every number has units; every chart has a title, axis labels, and a one-line caption; the app must run without error for *any* combination of sidebar selections, including empty selections (show a friendly message, not a traceback).

## 6. Repository layout

```
av-safety-rate-explorer/
├── app.py                      # Streamlit entry point
├── pyproject.toml              # uv project; deps + ruff + pytest config
├── uv.lock
├── requirements.txt            # exported for Streamlit Cloud
├── README.md
├── CLAUDE.md
├── plan.md
├── .gitignore                  # data/raw/, .venv/, __pycache__/, .streamlit/secrets.toml
├── .streamlit/config.toml      # theme + server settings only
├── data/
│   ├── README.md
│   ├── raw/                    # gitignored
│   └── processed/              # committed: events.parquet/.csv, exposure.parquet/.csv
├── scripts/
│   └── download_data.py
├── src/av_safety/
│   ├── __init__.py
│   ├── data.py                 # load/clean/normalise → tidy tables
│   ├── stats.py                # all estimators (pure functions)
│   ├── plots.py                # Plotly figure builders (pure: df → fig)
│   └── text.py                 # long markdown strings (methods, captions)
├── tests/
│   ├── test_stats.py
│   ├── test_data.py
│   └── test_app_smoke.py       # streamlit.testing AppTest: app renders, tabs exist, no exceptions
└── assets/
    └── screenshot.png
```

## 7. Phased execution (with acceptance criteria)

Work in this order. Do not start a phase until the previous phase's criteria pass. Commit at the end of each phase.

### Phase 0 — Scaffold (≈30 min)
- `uv init`, add deps, ruff + pytest config, `.gitignore`, `README.md` stub, `.streamlit/config.toml`, empty package skeleton, a hello-world `app.py`.
- **Done when:** `uv run streamlit run app.py` serves a page; `uv run pytest` passes (one trivial test); `uv run ruff check .` is clean.

### Phase 1 — Data (≈2 h)
- Write `scripts/download_data.py` and `src/av_safety/data.py`. Target the most recent 4–5 reporting years (whatever is available at build time; at minimum three years). Normalise column names, manufacturer names, categoricals; build `cause_category` with documented keyword rules; aggregate exposure.
- Sanity checks that must pass and be asserted in `tests/test_data.py`: no negative miles; every manufacturer with events has exposure (or is flagged and excluded with a logged warning); event dates fall inside the reporting period; total Waymo autonomous miles per year is in a plausible range (six or seven figures — if the number is in the hundreds, a units/column bug exists).
- Commit processed files. Write `data/README.md`.
- **Done when:** `uv run python scripts/download_data.py && uv run python -m av_safety.data` regenerates `data/processed/*` deterministically and `pytest tests/test_data.py` passes.

### Phase 2 — Statistics core (≈2 h)
- Implement every function in §4 with docstrings that state the formula and a reference.
- Write `tests/test_stats.py` per §4. Check `miles_needed` against at least one hand-computed value in a docstring.
- **Done when:** all stats tests pass; a short notebook-free demo script (`python -m av_safety.stats`) prints the pooled Waymo rate with Poisson and NB intervals and the miles needed for a 10% improvement.

### Phase 3 — App (≈3 h)
- Build the four tabs per §5. `plots.py` functions take a DataFrame and return a figure — no Streamlit calls inside them.
- `tests/test_app_smoke.py` with `streamlit.testing.v1.AppTest`: app runs, no exceptions, the four tabs render, and changing the year filter changes the rates table.
- **Done when:** smoke test passes; manual check that every sidebar combination (including "nothing selected") renders without a traceback.

### Phase 4 — Polish, README, deploy (≈1.5 h)
- README: problem → data → method (with the three formulas in plain LaTeX/markdown) → screenshot → how to run (`uv sync && uv run streamlit run app.py`) → limitations → the one-line pitch. Keep it under ~150 lines.
- Take `assets/screenshot.png` (Playwright headless is fine).
- Export `requirements.txt` (`uv export --no-hashes --no-dev > requirements.txt`).
- Push to GitHub; deploy on Streamlit Community Cloud (`app.py`, Python 3.11). Put the live URL at the top of the README.
- **Done when:** the public URL loads, all four tabs work, and a fresh `git clone` + `uv sync` + `uv run pytest` passes on a clean machine.

### Phase 5 — Verification pass (≈45 min)
- Re-derive two numbers by hand (one Poisson CI, one `miles_needed`) and confirm the app shows them.
- Read every caption and the Methods tab as a sceptical statistician would; fix anything overstated.
- `ruff check`, `ruff format --check`, `pytest` all clean. Final commit.

**If time runs short** (the guide's rule): ship Phase 0–2 plus a stripped Tab 1 (rate + CI + one chart) and deploy. A small finished tool beats an ambitious unfinished one.

## 8. Definition of done (whole project)

- [ ] Live public URL on Streamlit Community Cloud
- [ ] GitHub repo with README (problem, method, screenshot, run instructions, limitations, pitch)
- [ ] `uv run pytest` green, `ruff` clean, from a fresh clone
- [ ] Processed data committed; raw download script works or fails loudly
- [ ] Rates tab, Compare tab, Planner tab, Methods tab all functional for every filter combination
- [ ] Zero-event cells handled correctly and labelled
- [ ] NB vs Poisson choice explained in-app
- [ ] The one-line pitch is literally true of the deployed app

## 9. Open questions for the human (answer before Phase 1 if possible; otherwise the builder uses the defaults)

1. Which reporting years to include? **Default:** the most recent five available.
2. Include NHTSA SGO crash data as a second event type? **Default:** no (disengagements only).
3. GitHub repo name / owner and whether the repo should be public from the first commit. **Default:** `av-safety-rate-explorer`, public.
4. Should the app be branded with Richard's name/links (GitHub, Scholar) in the footer? **Default:** yes, a one-line footer.
