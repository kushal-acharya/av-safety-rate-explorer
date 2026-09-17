"""Generate the two-page PDF from the verified frozen study exports."""

from __future__ import annotations

import argparse
import json
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/av-evidence-research-brief.pdf"
WEB_OUTPUT = ROOT / "web/waymo-project/av-evidence-research-brief.pdf"
SITE = "https://vivaran.news/waymo-project/"
REPO = "https://github.com/kushal-acharya/av-safety-rate-explorer"
INK, MUTED, GREEN = "#213f34", "#506455", "#1c5e46"


class Brief:
    """Small top-origin drawing helper with explicit text-height checks."""

    def __init__(self, target: BytesIO) -> None:
        fonts = Path(reportlab.__file__).parent / "fonts"
        pdfmetrics.registerFont(TTFont("BriefSans", str(fonts / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("BriefSans-Bold", str(fonts / "VeraBd.ttf")))
        self.page = canvas.Canvas(target, pagesize=(612, 792), invariant=1, pageCompression=1)
        self.page.setTitle("AV Evidence - Research brief")
        self.page.setAuthor("AV Evidence - Independent research project")
        self.page.setSubject("Publication reproduction, geographic exposure and uncertainty")

    def text(
        self,
        content: str,
        x: float,
        top: float,
        width: float = 524,
        size: float = 10,
        color: str = INK,
        font: str = "BriefSans",
        max_height: float = 200,
    ) -> float:
        """Draw wrapped text; fail rather than silently collide with the next block."""
        style = ParagraphStyle(
            "brief", fontName=font, fontSize=size, leading=size * 1.45, textColor=HexColor(color)
        )
        paragraph = Paragraph(content, style)
        _, height = paragraph.wrap(width, max_height)
        if height > max_height:
            raise ValueError(
                f"Text exceeds reserved space ({height} > {max_height}): {content[:60]}"
            )
        paragraph.drawOn(self.page, x, 792 - top - height)
        return top + height

    def box(self, x: float, top: float, width: float, height: float, fill: str = "#edf3e6") -> None:
        """Draw a rounded panel."""
        self.page.setFillColor(HexColor(fill))
        self.page.roundRect(x, 792 - top - height, width, height, 9, stroke=0, fill=1)

    def rule(self, top: float) -> None:
        """Draw a subtle divider."""
        self.page.setStrokeColor(HexColor("#d7e1d1"))
        self.page.line(44, 792 - top, 568, 792 - top)

    def header(self, number: int) -> None:
        """Draw recurring identity and footer."""
        self.text("AV EVIDENCE  /  RESEARCH BRIEF", 44, 25, size=8, color=GREEN)
        self.text("17 SEPTEMBER 2026", 442, 25, width=126, size=8, color=MUTED)
        self.rule(47)
        self.rule(744)
        self.text(
            "Independent project. No affiliation with or endorsement by Waymo.",
            44,
            752,
            width=455,
            size=7.5,
            color=MUTED,
        )
        self.text(f"{number} / 2", 540, 752, width=40, size=8, color=MUTED)

    def link(self, label: str, url: str, top: float, x: float = 44, width: float = 524) -> None:
        """Add a readable label and a real clickable PDF URI annotation."""
        self.text(
            f'<link href="{escape(url, {chr(34): "&quot;"})}" color="{GREEN}">'
            f"<u>{escape(label)}</u></link>",
            x,
            top,
            width,
            size=9,
        )


def build_pdf() -> bytes:
    """Build a deterministic brief from the exported reference values, without refitting."""
    geography = json.loads((ROOT / "web/waymo-project/geography.json").read_text())
    replication = json.loads((ROOT / "web/waymo-project/replication.json").read_text())
    sf = next(
        row
        for row in geography["comparisons"]
        if row["city"] == "SAN_FRANCISCO" and row["metric"] == "airbag"
    )
    paper = next(row for row in replication["comparisons"] if row["id"] == "sf-injury")
    buffer = BytesIO()
    doc = Brief(buffer)
    doc.header(1)
    doc.text(
        "A safety claim is only as strong<br/>as its comparison.",
        44,
        66,
        size=27,
        font="BriefSans",
        max_height=90,
    )
    doc.text(
        "An independent statistics project that reproduces selected Waymo safety "
        "comparisons and shows how geography and assumptions change their interpretation.",
        44,
        165,
        size=11,
        color=MUTED,
        max_height=50,
    )

    doc.box(44, 226, 524, 182, "#234d3c")
    doc.text(
        "THE REFERENCE CHANGES THE RESULT  /  SF AIRBAG",
        62,
        243,
        width=488,
        size=8,
        color="#dfead2",
    )
    doc.text(
        f"{sf['unadjusted']['reduction_percent']:.1f}%  to  "
        f"{sf['matched']['reduction_percent']:.1f}%",
        62,
        261,
        width=488,
        size=35,
        font="BriefSans",
        color="#f5f8ed",
    )
    doc.text(
        "Estimated reduction in Waymo's observed airbag-deployment rate relative to "
        "the human reference, before and after geographic matching.",
        62,
        316,
        width=488,
        size=10,
        color="#edf3e5",
        max_height=35,
    )
    doc.text(
        f"{sf['events']} events / {sf['waymo_miles'] / 1e6:.3f} million rider-only miles. "
        f"The Waymo rate stays at {sf['waymo_ipmm']:.3f} events per million miles; "
        f"the human benchmark moves from {sf['baseline_ipmm']:.3f} to "
        f"{sf['matched_ipmm']:.3f}.",
        62,
        357,
        width=488,
        size=9,
        color="#dfead2",
        max_height=40,
    )

    doc.text(
        "Two investigations. Separate historical cohorts.",
        44,
        430,
        size=19,
        font="BriefSans",
        max_height=35,
    )
    doc.text("01  REPRODUCE A PUBLICATION", 44, 468, width=245, size=8, color=GREEN)
    doc.text(
        "Can we reproduce the paper's numbers?",
        44,
        490,
        width=245,
        size=14,
        font="BriefSans",
        max_height=45,
    )
    doc.text(
        f"For the SF injury reference case, {paper['events']} event over "
        f"{paper['waymo_miles'] / 1e6:.3f} million rider-only miles yields a rate ratio "
        f"of {paper['paper_code']['ratio']:.4f} against the supplied human benchmark. "
        "All four counts match; 12 ratio/endpoint checks differ by less than 0.01 "
        "from the publication.",
        44,
        540,
        width=245,
        size=9.5,
        max_height=95,
    )
    doc.text(
        "Finding: the appendix code and Equation 2 use different tail probabilities "
        "for positive counts. Both conventions are exposed in the app.",
        44,
        636,
        width=245,
        size=9,
        color=MUTED,
        max_height=67,
    )
    doc.text("02  MATCH GEOGRAPHIC EXPOSURE", 313, 468, width=255, size=8, color=GREEN)
    doc.text(
        "Does a fairer reference change the result?",
        313,
        490,
        width=255,
        size=14,
        font="BriefSans",
        max_height=45,
    )
    doc.text(
        "Reconstruct nine published spatial benchmarks from 987 cells across San "
        "Francisco, Phoenix and Los Angeles. Every benchmark and all nine event "
        "counts match. Sliders reveal sensitivity to mileage weighting and benchmark scale.",
        313,
        540,
        width=255,
        size=9.5,
        max_height=95,
    )
    doc.text(
        f"For the SF airbag example, the conditional 95% rate-ratio interval is "
        f"{sf['matched']['ratio_lower']:.4f}-{sf['matched']['ratio_upper']:.4f}. "
        "It includes only Waymo count uncertainty; the human reference is held fixed.",
        313,
        636,
        width=255,
        size=9,
        color=MUTED,
        max_height=67,
    )
    doc.link(
        "Open the project and guided tour: vivaran.news/waymo-project/brief", SITE + "brief", 714
    )
    doc.page.showPage()

    doc.header(2)
    doc.text("How to read the evidence.", 44, 69, size=28, font="BriefSans")
    doc.text(
        "The method, the boundaries, and a route to reproduce the result.",
        44,
        117,
        size=11,
        color=MUTED,
    )
    doc.box(44, 151, 524, 89)
    doc.text("COUNT  /  DISTANCE  /  REFERENCE", 60, 165, width=492, size=8, color=GREEN)
    doc.text(
        "Rate = events / miles. Rate ratio = Waymo rate / human benchmark.<br/>"
        "Estimated reduction = 100 x (1 - rate ratio).",
        60,
        188,
        width=492,
        size=11,
        max_height=40,
    )
    doc.text("Keep these datasets separate", 44, 260, size=17, font="BriefSans")
    entries = [
        (
            "Publication study",
            "arXiv:2312.12675v3; rider-only operations through October 2023. "
            "73 appendix event rows and four reference comparisons. Author-supplied "
            "classifications and human benchmark estimates remain dependencies.",
        ),
        (
            "Geographic study",
            "March 19, 2025 release; rider-only operations through December "
            "2024, with 2022 human benchmarks. Cells cover 99.67%-99.89% of the three cities' "
            "reported miles. Austin has no cell data in this release.",
        ),
        (
            "DMV companion",
            "Historical 2020-2024 testing reports. Disengagements are "
            "interventions, not crashes. Testing miles are never joined to the rider-only "
            "crash cohorts. The experiment planner is hypothetical.",
        ),
    ]
    y = 297
    for label, detail in entries:
        doc.text(label, 44, y, width=110, size=10, font="BriefSans-Bold")
        bottom = doc.text(detail, 167, y, width=401, size=9.3, max_height=65)
        y = bottom + 14
    doc.rule(y)
    y += 17
    doc.text("What this does not establish", 44, y, size=17, font="BriefSans")
    y += 32
    y = (
        doc.text(
            "Geographic matching does not control every difference in driving conditions "
            "and does not establish causality. The displayed geographic intervals include "
            "only Poisson uncertainty in Waymo counts, excluding uncertainty in human "
            "benchmarks, mileage, reporting adjustment and spatial weights. The project "
            "does not claim Waymo is safer everywhere or estimate the risk of your next ride.",
            44,
            y,
            size=9.5,
            max_height=85,
        )
        + 18
    )
    doc.text("Inspect, reproduce, challenge", 44, y, size=17, font="BriefSans")
    y += 30
    doc.link(
        "Publication method and interval-convention audit",
        REPO + "/blob/main/docs/replication-study.md",
        y,
    )
    doc.link(
        "Spatial formula, coverage gaps and source provenance",
        REPO + "/blob/main/docs/geographic-exposure.md",
        y + 18,
    )
    doc.link("Source code, verification runs and local setup", REPO, y + 36)
    doc.text(
        "SHA-256 source manifests, preserved event rows, semantic input checks and "
        "Python/JavaScript reference checks make the work inspectable. Rebuild the "
        "studies using the commands in the linked technical notes. These are historical "
        "snapshots, not a live safety ranking.",
        44,
        y + 65,
        size=9,
        color=MUTED,
        max_height=55,
    )
    if y + 120 > 736:
        raise ValueError("Second-page content would collide with the footer")
    doc.page.save()
    return buffer.getvalue()


def main() -> None:
    """Write both the local deliverable and its deployed copy, or check their bytes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = build_pdf()
    for path in [OUTPUT, WEB_OUTPUT]:
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise ValueError(f"Stale research brief: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(
        f"Two-page research brief {'verified' if args.check else 'built'} ({len(content)} bytes)."
    )


if __name__ == "__main__":
    main()
