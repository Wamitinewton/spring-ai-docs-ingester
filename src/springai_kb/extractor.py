"""
PDF content extractor.

Strategy:
  - pdfplumber  → primary text extraction (handles font spacing well)
  - PyMuPDF     → fallback and for extracting text blocks with bbox data
  - pdfplumber  → table detection (more reliable than PyMuPDF for tables)

Spring AI reference PDFs are text-based (not scanned), so no OCR needed.
"""

import re
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber


# Minimum point size for a text span to be considered a real heading.
# Chrome-printed Spring AI PDFs: body text ~12pt, TOC items ~10-11pt,
# H3 ~18pt, H2 ~21pt. 18.0 catches H2/H3 without false-positives.
_HEADING_FONT_THRESHOLD = 18.0

# Lines shorter than this that appear alone are likely nav fragments
_MIN_MEANINGFUL_LINE = 3


class PageContent:
    """Holds extracted content for one PDF page."""

    def __init__(self, page_num: int):
        self.page_num = page_num
        self.lines: list[str] = []
        self.table_lines: list[str] = []
        self.has_tables: bool = False


class PDFExtractor:
    """
    Extracts text and tables from a Spring AI reference PDF.
    Uses pdfplumber as primary, PyMuPDF for font-size heading hints.
    """

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self._plumber = None
        self._fitz_doc = None

    def __enter__(self):
        self._plumber = pdfplumber.open(self.pdf_path)
        self._fitz_doc = fitz.open(str(self.pdf_path))
        return self

    def __exit__(self, *_):
        if self._plumber:
            self._plumber.close()
        if self._fitz_doc:
            self._fitz_doc.close()

    @property
    def page_count(self) -> int:
        return len(self._plumber.pages)

    def _get_font_sized_lines(self, page_index: int) -> set[str]:
        """
        Uses PyMuPDF to find text that appears in a large font size.
        These are headings in the Spring AI website layout.
        Returns a set of stripped text strings that are headings.
        """
        heading_texts = set()
        fitz_page = self._fitz_doc[page_index]
        blocks = fitz_page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") != 0:  # 0 = text block
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    text = span.get("text", "").strip()
                    if size >= _HEADING_FONT_THRESHOLD and len(text) > 3:
                        heading_texts.add(text)

        return heading_texts

    def _extract_page_lines(self, plumber_page, page_index: int) -> list[str]:
        """
        Extract lines from a single page using pdfplumber.
        Uses word-level extraction to handle spacing issues common in
        browser-printed PDFs (words sometimes have gaps).
        """
        # Try words-based reconstruction first (better for printed web pages)
        words = plumber_page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=True,
        )

        if words:
            lines = self._reconstruct_lines_from_words(words)
        else:
            # Fallback to standard text extraction
            raw = plumber_page.extract_text(
                x_tolerance=2,
                y_tolerance=2,
                layout=False,
            )
            lines = raw.split("\n") if raw else []

        return lines

    def _reconstruct_lines_from_words(self, words: list[dict]) -> list[str]:
        """
        Groups words into lines based on their y-position (top coordinate).
        This is more reliable than pdfplumber's default line grouping for
        web-printed PDFs where line spacing can be inconsistent.
        """
        if not words:
            return []

        # Group by y-coordinate (rounded to nearest 2px to handle sub-pixel diffs)
        line_map: dict[int, list[dict]] = {}
        for word in words:
            y_key = round(word["top"] / 2) * 2
            line_map.setdefault(y_key, []).append(word)

        lines = []
        for y_key in sorted(line_map.keys()):
            line_words = sorted(line_map[y_key], key=lambda w: w["x0"])
            line_text = " ".join(w["text"] for w in line_words)
            lines.append(line_text)

        return lines

    def extract_page(self, page_index: int) -> PageContent:
        content = PageContent(page_index + 1)

        plumber_page = self._plumber.pages[page_index]

        # Get heading hints from font sizes
        heading_hints = self._get_font_sized_lines(page_index)

        # Extract main text lines
        lines = self._extract_page_lines(plumber_page, page_index)

        # Annotate lines that are headings (so cleaner can use this)
        annotated = []
        for line in lines:
            stripped = line.strip()
            if stripped in heading_hints and len(stripped) > 3:
                # Mark with a sentinel that cleaner.py will recognize
                annotated.append(f"__HEADING__ {line}")
            else:
                annotated.append(line)

        content.lines = annotated

        # Extract tables separately
        table_lines = self._extract_tables(plumber_page)
        content.table_lines = table_lines
        content.has_tables = bool(table_lines)

        return content

    def _extract_tables(self, plumber_page) -> list[str]:
        """
        Extract tables using pdfplumber and convert to GFM markdown.
        Tries strict line detection first, falls back to text analysis.
        """
        tables = None

        # Strategy 1: explicit line-based table detection
        try:
            tables = plumber_page.extract_tables({
                "vertical_strategy": "lines_strict",
                "horizontal_strategy": "lines_strict",
            })
        except Exception:
            pass

        # Strategy 2: relaxed detection
        if not tables:
            try:
                tables = plumber_page.extract_tables()
            except Exception:
                pass

        if not tables:
            return []

        md_lines = []
        for table in tables:
            if not table or len(table) < 2:
                continue

            rows = []
            for row in table:
                cells = [
                    re.sub(r'\s+', ' ', str(cell or "")).strip()
                    for cell in row
                ]
                rows.append(cells)

            # Normalize column count across all rows
            max_cols = max(len(r) for r in rows)
            rows = [r + [""] * (max_cols - len(r)) for r in rows]

            header = rows[0]
            md_lines.append("")
            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("|" + " --- |" * max_cols)
            for row in rows[1:]:
                md_lines.append("| " + " | ".join(row) + " |")
            md_lines.append("")

        return md_lines

    def extract_all_pages(self) -> list[PageContent]:
        pages = []
        for i in range(self.page_count):
            pages.append(self.extract_page(i))
        return pages

    def get_title(self) -> str:
        """
        Extract the document title from the PDF filename or first page.
        Spring AI PDFs are named like: 'Tool Calling __ Spring AI Reference.pdf'
        """
        stem = self.pdf_path.stem
        # Pattern: 'Topic Name __ Spring AI Reference'
        match = re.match(r'^(.+?)\s*__\s*Spring AI', stem)
        if match:
            return match.group(1).strip()

        # Fallback: clean up the stem
        title = stem.replace("__", " ").replace("_", " ").strip()
        # Remove trailing reference noise
        title = re.sub(r'\s*Spring AI Reference\s*$', '', title, flags=re.I).strip()
        return title