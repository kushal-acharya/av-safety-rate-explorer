# Ralph loop prompt for this project

Paste the command below into Claude Code (started in this folder) to run the build
autonomously. Edit the DECISIONS sentence first if you want different choices.
Keep the prompt on one line when pasting; the slash command passes it as arguments.

```
/ralph-loop Read CLAUDE.md and plan.md, then build the AV Safety Rate Explorer by working through plan.md phases 0 to 5 strictly in order. At the start of every iteration inspect git log and the working tree to see where the previous iteration stopped, and continue from there; never redo a finished phase. Before moving to the next phase, run and pass that phase's acceptance commands: uv run ruff check ., uv run ruff format --check ., uv run pytest, and a headless start of uv run streamlit run app.py. Commit at each phase boundary. Real DMV data only: download from https://www.dmv.ca.gov/portal/file/{year}-autonomous-vehicle-disengagement-reports-csv/ and https://www.dmv.ca.gov/portal/file/{year}-autonomous-mileage-reports-csv/ with a browser User-Agent for years 2020 to 2024 (driverless variants use the suffix csvdriverless for 2023 and 2024); if any download fails, stop and report instead of fabricating data. DECISIONS: years 2020 to 2024; disengagements only, no NHTSA SGO; the one-line pitch says public disengagement data, not crash data; VIN-year rows are the units for the dispersion test and Negative-Binomial fit; keep a mode column separating safety-driver testing from driverless testing with a sidebar toggle; the quasi-Poisson dispersion ratio is the design-effect multiplier in miles_needed. Record every other decision in README under Design decisions. Do not create a GitHub repo, push, or deploy: those steps in Phase 4 belong to the human, so do the rest of Phase 4 and all of Phase 5. Output <promise>AV EXPLORER READY TO DEPLOY</promise> only when phases 0 to 3 and 5 are complete, Phase 4 is complete except push and deploy, all tests pass, ruff is clean, and the app runs. --completion-promise "AV EXPLORER READY TO DEPLOY" --max-iterations 30
```

Monitor progress from another terminal:

```
head -10 .claude/ralph-loop.local.md      # iteration counter and settings
git log --oneline                          # phase commits
```

Stop it at any time with `/cancel-ralph` (or delete `.claude/ralph-loop.local.md`).
