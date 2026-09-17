# Bounded background follow-up

Requested by the owner after the v1.4 project brief: keep improving the other aspects
in the background after shipping the current frontend. Work on one item per scheduled
turn. Record completion and evidence here and in PROGRESS.md. Do not silently extend
this queue; pause the automation when all three items are complete.

## 1. Numerical frontend interfaces — complete

Add narrow static type checking to the geographic scenario interface (JSDoc +
TypeScript checkJs is acceptable) and its source-data shape. Keep the existing
JavaScript/esbuild frontend. Do not migrate the UI to a framework or rewrite working
statistics. Preserve the 135-scenario Python parity checks. Document and run the
new type-check command in CI. A type-check dependency is authorized; no paid service.

Implemented in v1.5: strict `npm run typecheck` for the geographic scenario, reading
guide and the actual exported JSON shape. Compile-only negative checks cover wrong
scalar types and missing interval endpoints. Existing 135-scenario parity checks pass.
Linux CI run 35171260900 and production verification passed; delivered in v1.5.

## 2. Frozen-input validation — complete

Review geographic input validation for malformed memberships, nonfinite/negative
exposure, unexpected cohort rows and inconsistent identifiers. Add explicit checks
where a real gap exists, with meaningful invalid-input tests. Keep the frozen source
files and numerical results unchanged. Reproduce both research snapshots and run
Python/JavaScript tests. Record anything intentionally dependent on source judgment.

Implemented semantic checks separate from file hashes, including cohort membership,
calendar validity, numeric domains, source-row coverage, identifier syntax and cross-outcome
consistency. Added 23 rejection tests using altered/rehashed copies; 80 Python tests
and 11 JavaScript suites pass, as do type checks and both unchanged study reproductions.
Linux CI 35189167184 passed, including all browser workflows and accessibility checks.
Both production study payloads exactly match the unchanged verified artifacts.

## 3. Portable research brief — verification in progress

Create a concise, printable PDF companion to the project brief, using the verified
frozen examples and direct methodology links. Read the PDF skill, render and inspect
the artifact, and keep all conditional-uncertainty and independent-project statements.
Link it from the brief and document a reproducible generation command. Do not claim
causal safety benefits or invent credentials, affiliations or new data.

The two-page PDF and web download are implemented and locally verified, including
rendered-page review, deterministic byte checks, responsive layout and accessibility.
Linux CI and production publication are pending.

## Release discipline

- Inspect current git status and PROGRESS.md first; preserve unrelated work.
- Save checked, meaningful changes and push at approximately ten-minute boundaries
  during active work. No empty commits, raw data, secrets or temporary artifacts.
- Keep the app available at the existing vivaran.news/waymo-project routes.
- Run repository-required checks before commits, CI and applicable browser checks
  before deployment. Deploy only a finished, verified increment, then verify live.
- Update this queue and PROGRESS.md with exact checks and limitations.
- Stay quiet on unchanged/routine checkpoints. Notify on a meaningful shipped result,
  a real failure or a required user decision. Respect available usage limits; do not
  redeem credits or change account settings.
