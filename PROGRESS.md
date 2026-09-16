# Build progress

- Read all supplied project files, including the Claude execution prompt.
- Verified GitHub and Cloudflare access and the 2024 DMV CSV endpoints.
- Scaffolded the reproducible Python project and web deployment tools.
- Initial lint and package smoke test pass; Streamlit server started.
- Next: download and audit all historical datasets; implement exact statistical functions.

## Data and statistical core
- Downloaded all 14 real DMV CSVs for 2020–2024; committed source manifest with hashes.
- Reconciled all 128 annual manufacturer/mode/year event totals with detailed records.
- Processed 22,958 events and 10,092 VIN-year rows; recorded 13 date anomalies and one zero-exposure event unit.
- Implemented Garwood intervals, one-sided zero-event bounds, NB2 with exposure, dispersion diagnostics, exact conditional comparison tests, and the normal-approximate experiment planner.
- Public GitHub repository created; source-only checkpoint pushes underway.

## Paused at user request — September 15, 2026 (EDT)
- Phases 0–2 pushed to GitHub; 26 Python tests pass and core lint is clean.
- Exported 533 statsmodels fit combinations for the future custom web dashboard.
- The custom dashboard UI, full Streamlit companion, browser validation and deployment remain unfinished.
- Nothing deployed to vivaran.news yet. Target path remains /waymo-project.
- Stopped the local Streamlit preview and paused ten-minute checkpoint automation.
- Resume with the dashboard UI and Python/JavaScript statistical parity tests, then app smoke tests, screenshots and Cloudflare publishing.

## Resumed — dashboard and companion built
- Implemented a responsive custom dashboard with four views, shareable filters, CSV export, and explicit zero-event bounds.
- Implemented the four-tab Streamlit companion; 28 Python tests now pass, including widget smoke tests.
- Browser statistics match independent Python reference vectors for Poisson intervals, conditional comparisons and experiment planning.
- Desktop browser interactions pass. Final mobile layout refinements and deployment checks are in progress.
