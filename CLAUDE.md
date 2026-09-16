# CLAUDE.md — AV Safety Rate Explorer

You are building a small, deployable Streamlit tool that estimates autonomous-vehicle incident rates per mile (with proper rare-event uncertainty) from public California DMV disengagement data and includes a power-calculation "experiment planner." The full specification is in `plan.md` — **read it first and follow its phases in order.** This file holds the standing rules you apply on every step.

## Why this exists (keep it in mind)

The owner is a transportation-safety statistician preparing for a Waymo Data Scientist interview. The tool is a portfolio artifact: it must be *correct*, *small*, *honest*, and *shippable* — in that order. It will be screen-shared to statisticians. Statistical sloppiness is worse than a missing feature. Flashy UI earns nothing.

## Commands

```bash
uv sync                                  # install everything (creates .venv)
uv run streamlit run app.py              # run the app locally
uv run pytest                            # run all tests
uv run pytest tests/test_stats.py -q     # stats only (fast)
uv run ruff check . && uv run ruff format --check .
uv run python scripts/download_data.py   # fetch raw DMV files → data/raw/
uv run python -m av_safety.data          # rebuild data/processed/ from data/raw/
uv export --no-hashes --no-dev > requirements.txt   # refresh for Streamlit Cloud
```

Before every commit: `ruff check`, `ruff format`, `pytest` — all clean.

## Stack (fixed)

Python 3.11+, `uv`, Streamlit, pandas, scipy, statsmodels, Plotly, pytest, ruff. Do not add Polars, DuckDB, SQL databases, FastAPI, React, Docker, or any ML library. If you think you need something else, stop and explain why in your summary instead of adding it.

## Architecture rules

- `src/av_safety/stats.py` — **pure functions only.** No pandas dependency beyond accepting arrays/Series; no Streamlit imports; every function has a docstring with the formula and a reference; every function validates inputs (negative miles/events → `ValueError`).
- `src/av_safety/plots.py` — pure `DataFrame → plotly Figure` builders. No Streamlit calls.
- `src/av_safety/data.py` — the only place raw DMV quirks are handled. Downstream code sees only the tidy schemas in `plan.md` §3.
- `app.py` — layout, widgets, caching, and glue. Keep it thin; if a block of logic in `app.py` exceeds ~15 lines, move it into `src/`.
- Use `st.cache_data` on data loading and on NB fits keyed by the filter selection.
- Single page with `st.tabs`. No `pages/` directory.

## Statistics rules (non-negotiable)

1. Rates always use an **exposure offset** (miles). Never present raw counts as a safety comparison.
2. Zero-event cells get an **upper bound, never "rate = 0."** Use the exact Poisson (Garwood) interval; expose the rule-of-three number explicitly.
3. Default interval method is **"auto"**: run the dispersion check; if overdispersed and ≥3 units, show the Negative-Binomial interval and say so; otherwise Poisson. Always label which one is shown.
4. Every displayed number carries **units** (per 1,000 miles, per 100,000 miles) and a **confidence level**.
5. The planner reports **expected events per arm**, not just miles — that is the intuitive quantity.
6. Any approximation (normal-approx sample size, Wald log-ratio CI) is named in the caption and in the Methods tab.
7. Never write copy that claims one company is "safer" than another. Disengagements are self-reported with inconsistent thresholds; say so wherever a cross-manufacturer comparison is displayed.
8. When you implement a formula, add a test with a hand-computed or published reference value. Golden numbers to check against: two-sided exact 95% Poisson interval for k=0 has upper = −ln(0.025)/miles ≈ 3.689/miles; the one-sided "rule of three" bound is −ln(0.05)/miles ≈ 2.996/miles; for k=5 the exact 95% interval is ≈ [1.623, 11.668]/miles. Label which convention any zero-event bound uses.

## Data rules

- Raw files: `data/raw/` (gitignored). Processed: `data/processed/` (**committed**, both `.parquet` and `.csv`). The app reads only `data/processed/`.
- The download script must **fail loudly** (non-zero exit, clear message with the DMV page URL) if any download fails. Never silently fabricate or "fill in" data. If you cannot obtain real data, stop and report — do not invent a sample dataset and present it as real. (A clearly labelled `data/sample/` synthetic fixture for tests is fine, but the app must never load it by default.)
- Column names differ across DMV years. Handle them in one normalisation map in `data.py` with a comment per year.
- Sanity assertions in `tests/test_data.py` per `plan.md` §7 Phase 1 (no negative miles, exposure exists for every manufacturer with events, plausible Waymo mileage).
- Record the retrieval date and source URLs in `data/README.md`.

## Code style

- Type hints on all public functions. `from __future__ import annotations`.
- Small functions, descriptive names, no clever one-liners. Readable > clever (this code will be read aloud in an interview).
- Docstrings: one-line summary, then Args/Returns, then the formula for stats functions.
- No dead code, no commented-out blocks, no TODOs left in `main`.
- Log with `logging`, not `print`, except in CLI scripts.
- Ruff config in `pyproject.toml`: line length 100, rules `E, F, I, B, UP, N`.

## Testing

- `tests/test_stats.py` — reference values, monotonicity, edge cases (k=0, tiny miles, huge miles), input validation.
- `tests/test_data.py` — schema, sanity assertions, deterministic rebuild.
- `tests/test_app_smoke.py` — `streamlit.testing.v1.AppTest`: app runs with no exception; all four tabs present; changing the year filter changes the rates output; empty filter selection shows a message, not an error.
- Tests must not hit the network.

## Working style for the agent

- Follow `plan.md` phases strictly; finish and verify each phase (run the acceptance commands) before starting the next. Commit at each phase boundary with a message like `phase 2: statistics core + tests`.
- **Iterate until it's right before reporting back.** Run the app, run the tests, fix what breaks. Do not hand over a phase with known failures.
- Be economical: do not spawn subagents for this project unless a phase is genuinely parallelisable (Phase 2 stats and Phase 1 data are the only reasonable candidates). Do not rewrite working modules for style.
- If a decision is not covered by `plan.md`, choose the simplest option that keeps the statistics correct, note it in `README.md` under "Design decisions," and continue. Only stop to ask when the choice is irreversible or touches the open questions in `plan.md` §9.
- If the DMV data cannot be downloaded, that is a blocker — report it; do not work around it with fabricated data.
- Timebox: this is a weekend project. If a feature is taking much longer than its phase estimate, ship the stripped version described at the end of `plan.md` §7 and say so.

## Definition of done

See `plan.md` §8. In short: live Streamlit Cloud URL, green tests from a fresh clone, clean README with screenshot and limitations, every tab works for every filter combination, and the one-line pitch is literally true.

## Do not

- Do not add features beyond `plan.md` (no simulator, no DB, no multipage, no ML models, no LLM features).
- Do not hide uncertainty, drop zero-event rows, or round intervals to make them look tighter.
- Do not commit raw data, secrets, or `.venv`.
- Do not use `print` debugging left in code, bare `except:`, or global mutable state in `app.py`.
