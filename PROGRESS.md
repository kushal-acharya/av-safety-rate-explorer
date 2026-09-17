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

## Publication reproduction — research checkpoint
- Selected Kusano et al. arXiv:2312.12675v3 (2024-10-24), covering rider-only operations through October 2023.
- Primary result: San Francisco any-injury-reported comparison; three companion checks reproduce the Appendix A.3 reference cases.
- Re-extracted all 73 appendix event rows, preserved the two pre-SGO events, and froze PDF/input SHA-256 hashes.
- Recalculated counts and rate-ratio intervals independently from event rows and benchmark inputs: 16/16 reference checks pass using the source's <0.01 tolerance.
- Identified and explicitly separated Equation 2 (2.5% tails) from Listing 1 (1.25% tails for positive counts); no silent confidence relabeling.
- The paper's labels and rounded benchmark estimates remain source inputs, not independently adjudicated facts. No DMV miles or newer crash records are joined to this cohort.
- Next: build the interactive study view, document limitations, verify desktop/mobile and publish.
- Built the separate publication view with source-linked event IDs, published-vs-reproduced audit, both interval conventions, and downloadable inputs/results.
- Added the technical note and source-page references; Python 43 tests and all 9 existing JavaScript suites pass.
- Browser, mobile and accessibility checks are in progress; the publication view is not yet deployed.
- All five web views pass automated accessibility scans; both existing and publication browser workflows pass, including export contents, shared state, filter isolation and failed-request recovery.
- Linux CI exposed last-bit numerical differences around 1e-15. Study exports now use 12 decimal places after full-precision calculations and audit decisions, preserving deterministic artifacts across platforms.
- Cloudflare dry run passes. Waiting for the updated Linux CI before production deployment.

## Publication reproduction delivered — September 16, 2026
- Live study: https://vivaran.news/waymo-project/?tab=replication&study=sf-injury&tails=paper_code
- Cloudflare deployment: 19a5521d-1da4-444b-bb4c-87a450a5845d.
- Linux GitHub Actions run 35119389161 passed on code commit 59d9395, including 43 Python tests, 9 JavaScript suites, deterministic study checks and both browser workflows.
- Production browser workflows and automated accessibility scans across all five views passed. All five downloadable study files exactly match verified local artifacts.
- Primary result: 1 SF injury event / 1.755 million rider-only miles; rate ratio 0.097904 versus published 0.10. All four counts match exactly; 12 ratio/endpoint checks pass the publication's <0.01 tolerance.
- The web study and Python CLI preserve separate paper-code and Equation 2 intervals, downloadable source rows, SHA-256 provenance, and a technical note. Author-supplied memberships and benchmark estimates are explicit dependencies.
- Final screenshots refreshed. Ten-minute build checkpoint timer paused after delivery.

## Geographic exposure matching — build checkpoint
- Reconstructed all nine dynamic benchmarks from the matched March 19, 2025 release (through December 2024, 2022 human benchmarks). All nine event counts match.
- Preserved 987 geographic cells, source row identities, cell-mileage coverage gaps and publisher baseline dependencies.
- Added a sixth web view with distribution interpolation, benchmark stress testing, conditional count intervals, exposure-band charts and a fixed source audit.
- Added reproducible source extraction, hash verification, downloadable data, technical documentation and 135 Python/JavaScript scenario comparisons.
- Python: 57 tests pass. JavaScript: 11 suites pass. Browser and accessibility verification in progress; not deployed yet.

## Geographic exposure matching delivered — September 16, 2026
- Live: https://vivaran.news/waymo-project/?tab=geography
- Cloudflare version: 817ddb05-072b-4b23-8dfd-f109daaf45d3. Code commit: 91bc624.
- GitHub Actions run 35144962422 passed on Linux: 57 Python tests, 11 JavaScript suites, both frozen-study artifact checks, all three browser workflows and six-view accessibility scanning.
- Production browser workflows and all six automated accessibility scans passed. The six geography JSON/CSV downloads match local artifacts byte for byte.
- Source refetch verified all four archived CSV hashes and exact normalized extraction.
- SF airbag benchmark increases 29.5% under geographic matching; observed rate reduction changes from 82.5% to 86.5% (+4.0 percentage points). The displayed 95% interval includes only Waymo count uncertainty.
- Refreshed desktop/mobile screenshots and documentation. All progress pushed; build checkpoint timer paused at delivery.

## Version 1.4 — project brief and frontend polish
- Added a standalone, no-JavaScript project brief with an evidence example, three-minute research tour and methodology links.
- Added a Project brief link to every analysis view, improved mobile header space and retained the existing analysis defaults.
- Reformatted all CSS as readable source, pinned Prettier and added CSS-format checks to CI. Kept the modular JavaScript/esbuild frontend.
- Local validation: 57 Python tests, 11 JavaScript suites, all four browser workflows, six-view accessibility checks, and brief accessibility/layout at 320/390/768/1440 px pass.
- Documented frontend structure and a three-item background queue for typed numerical interfaces, input validation and a portable PDF brief. Deployment verification follows.

## Version 1.4 delivered — September 17, 2026
- Live project brief: https://vivaran.news/waymo-project/brief (brief.html redirects to this canonical URL).
- Cloudflare version: 6be29c18-b62e-4652-b88b-3e1a4ebad3c1. Code commit: 2ae9a72.
- Linux CI run 35169686580 passed: 57 Python tests, 11 JavaScript suites, frozen-artifact checks, CSS formatting, all four browser workflows and dashboard accessibility.
- Live brief passes no-JavaScript rendering, 320/390/768/1440 layout and accessibility checks, and links into all three working research views. All six production analysis views pass accessibility checks.
- Background heartbeat is ACTIVE every ten minutes for the bounded queue in docs/BACKGROUND_QUEUE.md, with checked GitHub checkpoints and notifications for meaningful shipped work or failures. It will pause when the three queued improvements are complete.

## Version 1.5 — explain the analysis and check its interfaces
- Responded to the owner’s confusion by adding a plain-English introduction and five-term glossary to the project brief.
- Added an expandable walkthrough of the current geographic comparison: events and miles → rate → human benchmark → ratio → percentage. It updates with city/outcome/sliders and keeps the uncertainty limits visible.
- Added a direct beginner link, preserved URL fragments, and retained the open guide when controls change.
- Added strict TypeScript checkJs around geographic scenario inputs/results and the reading guide, with a compile-time contract against the real exported JSON; no framework migration or changed numerical formula.
- Type checking passes. Regression, browser and deployment verification in progress. Background queue item 1 implementation is ready; items 2 and 3 remain pending.

## Version 1.5 delivered — September 17, 2026
- Beginner guide: https://vivaran.news/waymo-project/brief#start-here
- Live arithmetic walkthrough: https://vivaran.news/waymo-project/?tab=geography#geo-reading-guide
- Cloudflare version: 2e40506a-c7ab-4d8d-af0a-f7dbb89b9d8f. Code commit: 002f95f.
- Linux CI 35171260900 passed all checks, including strict TypeScript, 57 Python tests, 11 JavaScript suites, both frozen reproductions, four browser workflows, six-view accessibility and the expanded guide.
- Production geography and brief browser workflows pass, including all nine comparisons, guide updates, deep-link focus, exports and mobile. All six live views plus the expanded guide pass automated accessibility checks.
- Background queue item 1 is complete. Items 2 (input validation) and 3 (portable PDF brief) remain pending; the ten-minute background heartbeat remains active.

## Frozen-input validation — implementation checkpoint
- Added semantic validation alongside SHA-256 checks: complete hash coverage, schemas, numeric domains, calendar months, binary memberships, in-transport eligibility, fixed event-row coverage, identifier syntax and cross-outcome exposure consistency.
- Retained the two missing report IDs and repeated report ID from the source; report IDs are not deduplicated.
- Added 23 rejection tests using modified and rehashed inputs. All 80 Python tests, 11 JavaScript suites, type checks and both frozen reproductions pass.
- No changes to source snapshots, statistical formulas or deployed assets. CI verification is next; no Cloudflare asset redeployment is needed for this offline pipeline change.

## Frozen-input validation delivered — September 17, 2026
- Pipeline code committed in ecc5150. Linux CI run 35189167184 passed: 80 Python tests, 11 JavaScript suites, type checks, both study reproductions, all browser workflows and automated accessibility checks.
- Production geography.json and replication.json match the verified local artifacts byte for byte. Numerical results, frozen inputs and deployed UI assets are unchanged; this improvement is in the reproducible analysis pipeline on GitHub.
- Background queue item 2 is complete. Only the portable PDF research brief remains pending; the scheduled follow-up stays active.

## Portable research brief — implementation checkpoint
- Built a deterministic two-page PDF from the verified study exports, with embedded fonts, cohort dates, conditional uncertainty, independence statements and four clickable methodology/project links.
- Added the download to the no-JavaScript project brief and documented reproduction through the optional pinned ReportLab dependency group. CI verifies both committed PDF copies.
- Both pages rendered and visually inspected at 125 dpi. PDF text/link checks pass. Browser verification passes exact download bytes/MIME/filename, four responsive sizes, accessibility and the three research entry points.
- Local checks pass: Ruff, 80 Python tests, 11 JavaScript tests, strict TypeScript, CSS formatting, both study reproductions and the deterministic PDF check. Linux CI and deployment verification follow.
