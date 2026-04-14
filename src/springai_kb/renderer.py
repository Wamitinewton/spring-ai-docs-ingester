"""
Markdown renderer.

Takes cleaned lines from cleaner.py and produces the final .md file.
Handles:
  - Document frontmatter (title, source, topic category)
  - Heading hierarchy normalization
  - Code block deduplication and language tagging
  - Table injection at correct positions
  - Note/Tip/Warning callout formatting
  - Link stripping (we want content, not nav links)
  - Final whitespace normalization
"""

import re
from pathlib import Path

from .extractor import PageContent


# Callout patterns — Spring AI docs use these heavily
_NOTE_PATTERN = re.compile(r'^(Note|Tip|Warning|Important|Caution)\s*$', re.I)
_NOTE_INLINE = re.compile(r'^(Note|Tip|Warning|Important|Caution):\s+(.+)', re.I)

# Inline link stripping — [text](url) → text
_MD_LINK = re.compile(r'\[([^\]]+)\]\([^)]+\)')

# Bare URL stripping
_BARE_URL = re.compile(r'https?://\S+')

# Sentinel injected by extractor for font-based headings
_HEADING_SENTINEL = re.compile(r'^__HEADING__\s+(.+)')

# Deduplicate heading markers that cleaner may have doubled up
_DOUBLE_HASH = re.compile(r'^(#{1,3})\s+(#{1,3})\s+')


_CALLOUT_EMOJI = {
    "note": "📝",
    "tip": "💡",
    "warning": "⚠️",
    "important": "🔴",
    "caution": "⚠️",
}

# Topic → category mapping for frontmatter
_TOPIC_CATEGORIES = {
    "mcp": "MCP",
    "advisor": "Advisors",
    "chat": "Chat",
    "tool": "Tool Calling",
    "vector": "Vector Store",
    "rag": "RAG",
    "etl": "ETL",
    "embedding": "Embeddings",
    "prompt": "Prompts",
    "structured": "Structured Output",
    "memory": "Chat Memory",
    "ollama": "Ollama",
    "azure": "Azure OpenAI",
    "getting started": "Getting Started",
    "evaluation": "Testing",
    "multimodal": "Multimodality",
    "stream": "Streaming",
    "security": "Security",
}


def _infer_category(title: str) -> str:
    lower = title.lower()
    for keyword, category in _TOPIC_CATEGORIES.items():
        if keyword in lower:
            return category
    return "Spring AI"


def _strip_links(line: str) -> str:
    line = _MD_LINK.sub(r'\1', line)
    line = _BARE_URL.sub('', line)
    return line.strip()


def _normalize_headings(lines: list[str]) -> list[str]:
    """
    Ensures heading hierarchy is sane:
    - Exactly one H1 (the document title)
    - H2 for major sections
    - H3 for subsections
    - Never skip levels
    """
    result = []
    seen_h1 = False

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            if seen_h1:
                # Demote extra H1s to H2
                line = "## " + line[2:]
            else:
                seen_h1 = True
        result.append(line)

    return result


def _merge_adjacent_code_blocks(lines: list[str]) -> list[str]:
    """
    When two code blocks of the same language appear with only blank lines
    between them, merge them. This happens when a page break splits a code
    sample across two PDF pages.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```") and line != "```":
            lang = line[3:].strip()
            block = [line]
            i += 1
            while i < len(lines) and lines[i] != "```":
                block.append(lines[i])
                i += 1
            block.append("```")  # closing fence
            i += 1

            # Check if next non-blank line opens same lang block
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1

            if j < len(lines) and lines[j] == f"```{lang}":
                # Merge: skip closing fence + blank lines + opening fence of next
                block.pop()  # remove closing ```
                block.append("")  # blank separator inside merged block
                i = j + 1  # skip past the next opening fence
                # Continue consuming the next block
                while i < len(lines) and lines[i] != "```":
                    block.append(lines[i])
                    i += 1
                block.append("```")
                i += 1

            result.extend(block)
        else:
            result.append(line)
            i += 1

    return result


class MarkdownRenderer:

    def __init__(self, source_filename: str):
        self.source_filename = source_filename

    def _build_frontmatter(self, title: str) -> list[str]:
        category = _infer_category(title)
        return [
            "---",
            f"title: \"{title}\"",
            f"category: \"{category}\"",
            f"source: \"{self.source_filename}\"",
            "generated_by: \"springai-kb-converter\"",
            "---",
            "",
        ]

    def _process_line(self, line: str) -> str:
        # Resolve heading sentinel from extractor
        m = _HEADING_SENTINEL.match(line)
        if m:
            text = m.group(1).strip()
            return f"## {text}"

        # Fix doubled heading markers
        line = _DOUBLE_HASH.sub(r'\1 ', line)

        # Strip navigation links from prose lines
        if not line.strip().startswith("```") and not line.strip().startswith("|"):
            line = _strip_links(line)

        return line

    def _format_callouts(self, lines: list[str]) -> list[str]:
        """Convert Note/Tip/Warning standalone lines into blockquotes."""
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Pattern: "Note" on its own line followed by content
            if _NOTE_PATTERN.match(line.strip()):
                kind = line.strip().lower()
                emoji = _CALLOUT_EMOJI.get(kind, "📝")
                label = line.strip().title()
                # Consume following lines as callout body until blank
                i += 1
                body_lines = []
                while i < len(lines) and lines[i].strip():
                    body_lines.append(lines[i].strip())
                    i += 1
                if body_lines:
                    result.append(f"> {emoji} **{label}:** {body_lines[0]}")
                    for bl in body_lines[1:]:
                        result.append(f"> {bl}")
                    result.append("")
                else:
                    result.append(f"> {emoji} **{label}**")
                continue

            # Inline: "Note: some text here"
            m = _NOTE_INLINE.match(line.strip())
            if m:
                kind = m.group(1).lower()
                emoji = _CALLOUT_EMOJI.get(kind, "📝")
                label = m.group(1).title()
                body = m.group(2)
                result.append(f"> {emoji} **{label}:** {body}")
                i += 1
                continue

            result.append(line)
            i += 1

        return result

    def render(self, title: str, page_contents: list[PageContent]) -> str:
        """
        Assembles all page contents into a single clean markdown document.
        """
        all_lines: list[str] = []

        # The document title is added as H1 below; skip its first occurrence
        # in the page content so it doesn't appear twice as ## title.
        title_heading_skipped = False

        for page in page_contents:
            for line in page.lines:
                processed = self._process_line(line)
                if not title_heading_skipped and processed == f"## {title}":
                    title_heading_skipped = True
                    continue
                all_lines.append(processed)

            # Inject tables at end of page (they're positionally separate)
            if page.table_lines:
                all_lines.append("")
                all_lines.extend(page.table_lines)

        # Post-processing passes
        all_lines = self._format_callouts(all_lines)
        all_lines = _normalize_headings(all_lines)
        all_lines = _merge_adjacent_code_blocks(all_lines)
        all_lines = self._collapse_blank_lines(all_lines)

        # Assemble final document
        parts = self._build_frontmatter(title)
        parts.append(f"# {title}")
        parts.append("")
        parts.extend(all_lines)

        # Final pass: remove any remaining bare URLs that slipped through
        final = "\n".join(parts)
        final = _BARE_URL.sub('', final)
        final = re.sub(r'\n{3,}', '\n\n', final)

        return final.strip() + "\n"

    def _collapse_blank_lines(self, lines: list[str]) -> list[str]:
        result = []
        blank_count = 0
        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 1:
                    result.append("")
            else:
                blank_count = 0
                result.append(line)
        return result