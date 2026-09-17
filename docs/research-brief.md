# Portable research brief

The two-page PDF accompanies the web project brief. It presents the SF airbag
geographic example and SF injury publication reference, with separate historical
cohorts, conditional uncertainty, limitations and clickable methodology links.
It is an independent project and does not establish causal safety benefits.

## Rebuild and verify

```bash
uv sync --locked --group reports
uv run python scripts/reproduce_study.py --check
uv run python scripts/reproduce_geography.py --check
uv run --group reports python scripts/build_research_brief.py
uv run --group reports python scripts/build_research_brief.py --check
```

The builder reads the verified `web/waymo-project/replication.json` and
`geography.json` reference exports; it does not refit a model or fetch new data.
It writes identical copies to `output/pdf/av-evidence-research-brief.pdf` and
`web/waymo-project/av-evidence-research-brief.pdf`. The edition date is fixed to
September 17, 2026, distinct from each study's stated observation period.

The optional `reports` dependency group pins ReportLab. The PDF embeds the
Bitstream Vera fonts bundled with that dependency so readers do not need local
fonts. Invariant metadata makes the committed bytes reproducible. CI checks both
copies after validating the source exports; the browser check downloads the PDF
and verifies its MIME type, filename and exact bytes.

For a content or layout change, render all pages with Poppler and visually inspect
them before committing. The initial release was inspected at 125 dpi, including
page boundaries, scientific notation, source links and footers. The builder also
rejects text exceeding reserved block heights. The linked HTML brief remains the
responsive, accessible reading option; the PDF is a printable companion.
