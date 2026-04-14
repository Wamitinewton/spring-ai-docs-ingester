"""
Converter orchestrator.

Wires together PDFExtractor → SpringAIDocCleaner → MarkdownRenderer
for a single PDF file. Called by the CLI for each file.
"""

import re
from pathlib import Path

from .cleaner import SpringAIDocCleaner
from .extractor import PDFExtractor
from .renderer import MarkdownRenderer


def _slugify(title: str) -> str:
    """Convert a title like 'Tool Calling' → 'tool-calling'."""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


class ConversionResult:
    def __init__(self, pdf_path: Path, output_path: Path | None, error: str | None):
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None


def convert_pdf(pdf_path: Path, output_dir: Path) -> ConversionResult:
    """
    Convert a single Spring AI reference PDF to a clean markdown file.

    Returns ConversionResult with the output path or error message.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with PDFExtractor(pdf_path) as extractor:
            title = extractor.get_title()
            page_contents = extractor.extract_all_pages()

        cleaner = SpringAIDocCleaner()

        for page in page_contents:
            page.lines = cleaner.process(page.lines)

        renderer = MarkdownRenderer(source_filename=pdf_path.name)
        markdown = renderer.render(title, page_contents)

        slug = _slugify(title)
        output_path = output_dir / f"{slug}.md"
        output_path.write_text(markdown, encoding="utf-8")

        return ConversionResult(pdf_path, output_path, error=None)

    except Exception as exc:
        return ConversionResult(pdf_path, output_path=None, error=str(exc))