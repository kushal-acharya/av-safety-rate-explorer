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

## Publication checkpoint
- Finished mobile filter/layout fixes and responsive charts.
- Passed 28 Python tests, 6 JavaScript suites, all-view browser interactions and an automated WCAG A/AA scan across all four views.
- Added GitHub Actions, screenshots, source documentation, security headers and install requirements.
- Cloudflare deployment dry run passed; publishing and live verification are next.

## Delivered — September 16, 2026
- Published https://vivaran.news/waymo-project/ on Cloudflare Worker av-evidence.
- Deployment version: db66a6f2-e853-4ad3-b662-11e30e42d0f8.
- Requested path redirects to the canonical trailing-slash URL; production returns HTTP 200.
- Production browser interactions and all four automated accessibility scans pass.
- Fresh GitHub clone passes 28 Python tests and the JavaScript reference suites.
- GitHub Actions run 35070357578 passed, including Linux Chromium interaction tests.
- Build checkpoint automation paused after delivery; all source and progress saved to GitHub.
- Scope: versioned 2020–2024 disengagement data, not crash data or live safety rankings. Hosted UI is the custom dashboard; the Streamlit companion runs from the same repository.

## Version 1.1 — event context exploration
- Added initiator, reported-location and cause-keyword context to the web and Streamlit interfaces.
- Context retains every event, zero-event category and ambiguous Unknown label. Road-type-specific mileage is never inferred.
- Added shareable context selection and CSV export with full exposure, confidence and zero-count conventions.
- Validated 31 Python tests, 9 JavaScript suites, browser interactions and all four accessibility scans.
- Ready to publish this update to the existing Cloudflare path.
- Published v1.1 at the existing URL; Cloudflare deployment ab9b1c16-1e6d-4429-ba69-4d51094381b7.
- Production browser checks passed, including context selection, share-link persistence, exports and zero-event behavior.
- Captured the live event-context panel and refreshed screenshots. Build timer paused after this delivery.
