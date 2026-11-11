#!/usr/bin/env python3
"""Build the public case-study PDF and Markdown from one JSON source.

Python 3.10+; install reportlab and pypdf. Fonts are bundled in ../assets.
Run from any working directory. No network, private input or account is used.
"""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import json

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from pypdf import PdfReader, PdfWriter


PUBLIC = Path(__file__).resolve().parent.parent
CASE_DIR = PUBLIC / "04_case_studies"
DATA_FILE = CASE_DIR / "case_studies.json"
PDF_FILE = CASE_DIR / "Selected_Case_Studies.pdf"
MD_FILE = CASE_DIR / "Selected_Case_Studies.md"
WIDTH, HEIGHT = 612, 792
MARGIN = 44
CONTENT_WIDTH = WIDTH - MARGIN * 2
INK = HexColor("#172331")
BLUE = HexColor("#4355db")
MUTED = HexColor("#5c6878")
LINE = HexColor("#e1e5ed")
NOTICE = "Client identities and monetary terms are withheld."


def load_cases():
    cases = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) != 5:
        raise ValueError("Expected five case records")
    expected_ids = ["01", "02", "03", "04", "05"]
    if [case.get("n") for case in cases] != expected_ids:
        raise ValueError("Case IDs must remain in their documented order")
    required = ("title", "context", "body", "outcome", "featured_summary")
    for case in cases:
        if any(not isinstance(case.get(key), str) or not case[key].strip() for key in required):
            raise ValueError(f"Case {case['n']} has an empty required field")
        if case.get("result_label") not in ("Outcome", "Contribution"):
            raise ValueError(f"Case {case['n']} has an unsupported result label")
    return cases


def register_fonts():
    for family, filename in (
        ("CaseBody", "Inter-Regular.ttf"),
        ("CaseSemi", "Inter-SemiBold.ttf"),
        ("CaseBold", "Inter-Bold.ttf"),
        ("CaseDisplay", "Inter-Medium.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(family, str(PUBLIC / "assets" / filename)))
    pdfmetrics.registerFontFamily(
        "CaseBody", normal="CaseBody", bold="CaseBold", italic="CaseBody", boldItalic="CaseBold"
    )


class CasePDF:
    def __init__(self):
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=(WIDTH, HEIGHT), pageCompression=1, invariant=1, initialFontName='CaseBody')
        self.page = 0

    def paragraph(self, text, top, size=10.8, leading=14.6, font="CaseBody", color=INK):
        paragraph = Paragraph(
            text,
            ParagraphStyle(
                "case", fontName=font, fontSize=size, leading=leading,
                textColor=color, splitLongWords=False,
            ),
        )
        _, height = paragraph.wrap(CONTENT_WIDTH, 1500)
        if top + height > 738:
            raise ValueError(f"Page {self.page} content exceeds its text area")
        paragraph.drawOn(self.canvas, MARGIN, HEIGHT - top - height)
        return top + height

    def start_page(self, title, subtitle):
        self.page += 1
        self.paragraph("Ingrid Kao / Selected case studies", 27, 8.6, 11.5, "CaseSemi", INK)
        self.canvas.setFont("CaseSemi", 8.4)
        self.canvas.setFillColor(MUTED)
        self.canvas.drawRightString(WIDTH - MARGIN, HEIGHT - 35.4, "NOVEMBER 2026")
        self.canvas.setStrokeColor(LINE)
        self.canvas.setLineWidth(0.6)
        self.canvas.line(MARGIN, HEIGHT - 49, WIDTH - MARGIN, HEIGHT - 49)
        self.canvas.setStrokeColor(BLUE)
        self.canvas.setLineWidth(2)
        self.canvas.line(MARGIN, HEIGHT - 63, MARGIN + 28, HEIGHT - 63)
        end = self.paragraph(escape(title), 77, 25, 28.5, "CaseDisplay")
        end = self.paragraph(escape(subtitle), end + 10, 10.6, 14.2, color=MUTED)
        return end + 18

    def case(self, case, top):
        top = self.paragraph(
            escape(case["n"] + " / " + case["context"]), top, 8.6, 11.5, "CaseSemi", BLUE
        )
        top = self.paragraph(escape(case["title"]), top + 7, 14, 17.5, "CaseSemi")
        top = self.paragraph(escape(case["body"]), top + 8)
        top = self.paragraph(
            "<b>" + escape(case["result_label"]) + ":</b> " + escape(case["outcome"]), top + 8,
            size=10.7, leading=14.4, color=INK,
        )
        self.canvas.setStrokeColor(LINE)
        self.canvas.setLineWidth(0.5)
        self.canvas.line(MARGIN, HEIGHT-top-10, WIDTH-MARGIN, HEIGHT-top-10)
        return top + 20

    def finish_page(self):
        self.canvas.setStrokeColor(LINE)
        self.canvas.line(MARGIN, 37, WIDTH - MARGIN, 37)
        self.canvas.setFillColor(MUTED)
        self.canvas.setFont("CaseBody", 8.2)
        self.canvas.drawString(MARGIN, 24, "Ingrid Kao | Representative matters")
        self.canvas.drawRightString(WIDTH - MARGIN, 24, f"{self.page} / 2")
        self.canvas.showPage()

    def save(self):
        self.canvas.save()
        self.buffer.seek(0)
        reader = PdfReader(self.buffer)
        if len(reader.pages) != 2:
            raise ValueError("The case-study document must remain two pages")
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        writer.metadata = None
        writer.add_metadata({
            "/Title": "Selected Case Studies | Ingrid Kao",
            "/Author": "Ingrid Kao",
            "/Creator": "Ingrid Kao",
            "/Subject": "Representative matters in licensing, commercial remedies, equipment procurement, transactions and legal data",
        })
        with PDF_FILE.open("wb") as output:
            writer.write(output)


def write_markdown(cases):
    parts = ["# Selected case studies", "Ingrid Kao", NOTICE]
    for case in cases:
        parts.extend([
            "## " + case["title"], case["context"], case["body"],
            "**" + case["result_label"] + ":** " + case["outcome"],
        ])
    MD_FILE.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def main():
    cases = load_cases()
    register_fonts()
    document = CasePDF()
    top = document.start_page("Representative matters", NOTICE)
    for case in cases[:3]:
        top = document.case(case, top)
    document.finish_page()
    top = document.start_page("Transactions and legal technology", NOTICE)
    for case in cases[3:]:
        top = document.case(case, top)
    document.finish_page()
    document.save()
    write_markdown(cases)
    print("Built Selected_Case_Studies.pdf (2 pages) and Selected_Case_Studies.md from case_studies.json")


if __name__ == "__main__":
    main()
