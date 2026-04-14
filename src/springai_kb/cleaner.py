"""
Text cleaning pipeline for Spring AI reference PDFs.

These PDFs are browser-printed web pages from docs.spring.io.
They contain: site nav, breadcrumbs, footer links, "Edit this page"
buttons, cookie banners, pagination arrows, repeated URL noise,
date/time stamps, and per-page title headers.
This module strips all of that and returns only the technical content.
"""

import re


# ── Patterns that identify noise lines ────────────────────────────────────────

_SITE_NAV_PATTERNS = [
    re.compile(r'^Spring AI\s*$'),
    re.compile(r'^(Overview|Reference|API)\s*$'),
    re.compile(r'^(GitHub|Feedback|Edit this page|Report a bug)\s*$', re.I),
    re.compile(r'^On this page\s*$', re.I),
    re.compile(r'^(Next|Previous|←|→|‹|›)\s*$'),
    re.compile(r'^(Next|Previous)\s*[›»←→]?\s*\w'),
    re.compile(r'^\s*(›|»|«|‹)\s*$'),
    re.compile(r'^Skip to (main )?content\s*$', re.I),
    re.compile(r'^Spring AI Reference\s*$', re.I),
    re.compile(r'^docs\.spring\.io', re.I),
]

_FOOTER_PATTERNS = [
    re.compile(r'Copyright\s*©', re.I),
    re.compile(r'VMware|Broadcom|Pivotal', re.I),
    re.compile(r'Apache License', re.I),
    re.compile(r'Privacy Policy', re.I),
    re.compile(r'Terms of (Use|Service)', re.I),
    re.compile(r'All rights reserved', re.I),
]

# Bare URL lines (long URLs printed at page bottom)
_URL_LINE_PATTERN = re.compile(r'^https?://\S{30,}$')

# Breadcrumb navigation lines (e.g. "Spring AI / Reference / Models / ...")
_BREADCRUMB_PATTERN = re.compile(r'^(Home\s*/|Spring AI\s*/|Reference\s*/)', re.I)

# Page numbers: bare "1", "12", or fraction "1/10", "12/34"
_PAGE_NUMBER_PATTERN = re.compile(r'^\d{1,3}(/\d{1,3})?\s*$')

# Per-page header printed by Chrome: "Azure OpenAI Embeddings :: Spring AI Reference"
_PAGE_TITLE_HEADER = re.compile(r'^.+::\s*Spring AI\b', re.I)

# Date/time stamp printed by Chrome at top-left of every page: "4/14/26, 12:59 PM"
_DATE_HEADER_PATTERN = re.compile(
    r'^\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s*(AM|PM)?\s*$', re.I
)

_EDIT_BUTTON_PATTERN = re.compile(
    r'(Edit this page|Suggest an edit|View on GitHub)', re.I
)

# Language labels that float on code block corners in the printed PDF
# (e.g. "JAVA", "XML", "YAML", "PROPERTIES", "APPLICATION.PROPERTIES")
_CODE_LANG_LABEL = re.compile(
    r'^(JAVA|KOTLIN|XML|YAML|PROPERTIES|GROOVY|GRADLE|BASH|SHELL|'
    r'APPLICATION\.PROPERTIES)\s*$',
    re.I,
)


# ── Code block detection ───────────────────────────────────────────────────────

_JAVA_START = re.compile(
    r'^\s*(import |package |@\w+|public |private |protected |'
    r'class |interface |record |enum |/\*\*|\*\s|\*\/|//\s)'
)

_XML_START = re.compile(r'^\s*<[\w/\?!]')

_YAML_START = re.compile(r'^\s*[\w\-\.]+:\s*\S')

_PROPERTIES_START = re.compile(r'^\s*spring\.\S+\s*=\s*\S')

_SHELL_START = re.compile(r'^\s*(\$\s|mvn |gradle |curl |wget |docker )')


def _detect_lang(lines: list[str]) -> str:
    sample = "\n".join(lines[:10])
    if _XML_START.search(sample):
        return "xml"
    if _PROPERTIES_START.search(sample):
        return "properties"
    if _YAML_START.search(sample) and ":" in sample:
        return "yaml"
    if _SHELL_START.search(sample):
        return "bash"
    if _JAVA_START.search(sample):
        return "java"
    return "java"


# ── Heading detection ──────────────────────────────────────────────────────────

_NUMBERED_HEADING = re.compile(
    r'^(\d+\.?\s+[A-Z][A-Za-z\s]{3,})\s*$'
)

# Lines that LOOK like headings but are just normal sentence starts
_FALSE_HEADING_WORDS = {
    "note", "tip", "warning", "important", "caution",
    "example", "figure", "table", "listing",
}


# ── Main cleaner ───────────────────────────────────────────────────────────────

class SpringAIDocCleaner:
    """
    Strips browser-print noise from Spring AI reference PDFs and
    returns structured, clean text ready for markdown conversion.
    """

    def is_noise(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False

        if _PAGE_NUMBER_PATTERN.match(stripped):
            return True
        if _URL_LINE_PATTERN.match(stripped):
            return True
        if _BREADCRUMB_PATTERN.match(stripped):
            return True
        if _EDIT_BUTTON_PATTERN.search(stripped):
            return True
        if _PAGE_TITLE_HEADER.match(stripped):
            return True
        if _DATE_HEADER_PATTERN.match(stripped):
            return True
        if _CODE_LANG_LABEL.match(stripped):
            return True

        for pat in _SITE_NAV_PATTERNS:
            if pat.match(stripped):
                return True

        for pat in _FOOTER_PATTERNS:
            if pat.search(stripped):
                return True

        # Short lines that are purely navigation fragments
        if len(stripped) < 4 and not stripped[0].isalpha():
            return True

        return False

    def clean_lines(self, raw_lines: list[str]) -> list[str]:
        cleaned = []
        prev_blank = False

        for line in raw_lines:
            if self.is_noise(line):
                continue

            is_blank = line.strip() == ""

            # Collapse consecutive blank lines into one
            if is_blank and prev_blank:
                continue

            cleaned.append(line.rstrip())
            prev_blank = is_blank

        # Strip leading/trailing blanks
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        return cleaned

    def detect_heading_level(self, line: str, prev_lines: list[str]) -> int | None:
        """
        Returns 1, 2, or 3 if the line looks like a heading, else None.
        Spring AI docs use visual size hierarchy (no # markers in PDFs).
        We infer level from line length and context.
        """
        stripped = line.strip()
        if not stripped:
            return None

        # Lines ending in : are often code descriptions, not headings
        if stripped.endswith(":") and len(stripped) > 60:
            return None

        # Must be relatively short for a heading
        if len(stripped) > 80:
            return None

        # Ignore if previous line had content (headings follow blank lines)
        if prev_lines and prev_lines[-1].strip():
            return None

        word = stripped.split()[0].lower().rstrip(":")
        if word in _FALSE_HEADING_WORDS and len(stripped.split()) < 4:
            return None

        # Numbered section → H2
        if _NUMBERED_HEADING.match(stripped):
            return 2

        # Title-case multi-word → candidate heading
        words = stripped.split()
        if len(words) >= 2 and all(
            w[0].isupper() or w.lower() in {"a", "an", "the", "and", "or", "of", "in", "to", "for", "with", "on"}
            for w in words if w
        ):
            # Short title-case = probably H2; longer = H3
            return 2 if len(words) <= 5 else 3

        return None

    def detect_code_blocks(self, lines: list[str]) -> list[str]:
        """
        Wraps sequences of code-looking lines in fenced code blocks.
        Handles Java, XML, YAML, properties, and bash.
        """
        result = []
        code_buffer: list[str] = []
        in_code = False

        CODE_STARTERS = (_JAVA_START, _XML_START, _YAML_START,
                         _PROPERTIES_START, _SHELL_START)

        def _flush_code():
            if not code_buffer:
                return
            # Drop if it's just 1-2 lines with no punctuation (likely a heading fragment)
            content = "\n".join(code_buffer).strip()
            if len(code_buffer) <= 2 and not any(c in content for c in "{}();=:<>@"):
                result.extend(code_buffer)
            else:
                lang = _detect_lang(code_buffer)
                result.append(f"```{lang}")
                result.extend(code_buffer)
                result.append("```")
            code_buffer.clear()

        for line in lines:
            stripped = line.strip()
            is_code_line = any(p.match(line) for p in CODE_STARTERS)

            if is_code_line and not in_code:
                in_code = True
                code_buffer.append(line)
            elif in_code:
                # Continue code block if: line has content, or blank line
                # followed by more code. Stop if clearly prose.
                if stripped == "":
                    # Lookahead not possible here; buffer the blank
                    code_buffer.append(line)
                elif is_code_line or line.startswith("  ") or line.startswith("\t"):
                    code_buffer.append(line)
                else:
                    # Trailing blanks in buffer → remove before closing
                    while code_buffer and not code_buffer[-1].strip():
                        code_buffer.pop()
                    _flush_code()
                    in_code = False
                    result.append(line)
            else:
                result.append(line)

        if in_code:
            while code_buffer and not code_buffer[-1].strip():
                code_buffer.pop()
            _flush_code()

        return result

    def process(self, raw_lines: list[str]) -> list[str]:
        """Full pipeline: clean → heading detection → code block wrapping."""
        cleaned = self.clean_lines(raw_lines)
        with_code = self.detect_code_blocks(cleaned)

        # Inject markdown heading markers
        result = []
        for line in with_code:
            prev = result[-5:] if result else []
            level = self.detect_heading_level(line, prev)
            if level and not line.strip().startswith("```"):
                result.append("")
                result.append(f"{'#' * level} {line.strip()}")
                result.append("")
            else:
                result.append(line)

        return result
