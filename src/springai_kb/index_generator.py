"""
Generates a master index file (SPRING_AI_KB.md) after all PDFs are converted.

This is the file you reference in your CLAUDE.md:
  @docs/spring-ai-kb/SPRING_AI_KB.md

It maps every topic to its markdown file and includes copy-paste
CLAUDE.md snippets.
"""

import re
from pathlib import Path


_CATEGORY_ORDER = [
    "Getting Started",
    "Spring AI API",
    "Chat",
    "Embeddings",
    "Prompts",
    "Structured Output",
    "Tool Calling",
    "Advisors",
    "Chat Memory",
    "RAG",
    "ETL",
    "Vector Store",
    "MCP",
    "Streaming",
    "Multimodality",
    "Testing",
    "Security",
    "Ollama",
    "Azure OpenAI",
    "Spring AI",
]


def _read_frontmatter(md_path: Path) -> dict[str, str]:
    """Parse YAML-style frontmatter from a generated markdown file."""
    text = md_path.read_text(encoding="utf-8")
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---\n", 4)
    if end == -1:
        return fm
    block = text[4:end]
    for line in block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm


def generate_index(output_dir: Path, converted_files: list[Path]) -> Path:
    """
    Writes SPRING_AI_KB.md to output_dir and returns its path.
    """
    # Group files by category
    categorized: dict[str, list[tuple[str, Path]]] = {}
    for md_path in sorted(converted_files):
        fm = _read_frontmatter(md_path)
        title = fm.get("title", md_path.stem.replace("-", " ").title())
        category = fm.get("category", "Spring AI")
        categorized.setdefault(category, []).append((title, md_path))

    lines = [
        "# Spring AI Knowledge Base",
        "",
        "Complete reference index for Claude Code agents.",
        "Generated from official Spring AI documentation PDFs.",
        "",
        "> **Usage in CLAUDE.md:** Reference individual files with `@path/to/file.md`",
        "> or include this index file to give Claude Code the full topic map.",
        "",
        "---",
        "",
        "## Topic Index",
        "",
    ]

    # Write categorized sections in preferred order
    written_categories = []
    for category in _CATEGORY_ORDER:
        if category not in categorized:
            continue
        written_categories.append(category)
        lines.append(f"### {category}")
        lines.append("")
        for title, md_path in sorted(categorized[category]):
            rel = md_path.name
            size_kb = md_path.stat().st_size // 1024
            lines.append(f"- [{title}](./{rel}) `{size_kb} KB`")
        lines.append("")

    # Catch-all for uncategorized
    for category, entries in categorized.items():
        if category in written_categories:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for title, md_path in sorted(entries):
            rel = md_path.name
            size_kb = md_path.stat().st_size // 1024
            lines.append(f"- [{title}](./{rel}) `{size_kb} KB`")
        lines.append("")

    lines += [
        "---",
        "",
        "## How to Use with Claude Code",
        "",
        "### Option 1 — Reference specific files in your project CLAUDE.md",
        "",
        "```markdown",
        "## Spring AI Knowledge Base",
        "Consult these references before writing any Spring AI code.",
        "The files contain official API documentation.",
        "",
        "### MCP",
        "- @docs/spring-ai-kb/mcp-client-boot-starter.md",
        "- @docs/spring-ai-kb/mcp-server-boot-starter.md",
        "- @docs/spring-ai-kb/mcp-annotations.md",
        "- @docs/spring-ai-kb/sse-mcp.md",
        "",
        "### Core API",
        "- @docs/spring-ai-kb/chat-model-api.md",
        "- @docs/spring-ai-kb/tool-calling.md",
        "- @docs/spring-ai-kb/advisors-api.md",
        "- @docs/spring-ai-kb/structured-output-converter.md",
        "- @docs/spring-ai-kb/chat-memory.md",
        "",
        "### RAG / Embeddings",
        "- @docs/spring-ai-kb/retrieval-augmented-generation.md",
        "- @docs/spring-ai-kb/etl-pipeline.md",
        "- @docs/spring-ai-kb/prompts.md",
        "```",
        "",
        "### Option 2 — Global ~/.claude/CLAUDE.md (applies to all projects)",
        "",
        "```markdown",
        "## Spring AI References",
        "When working on any Spring AI project, read from ~/Documents/springai-kb/",
        "before writing Spring AI code. Key files:",
        "- ~/Documents/springai-kb/SPRING_AI_KB.md  (master index)",
        "- ~/Documents/springai-kb/mcp-client-boot-starter.md",
        "- ~/Documents/springai-kb/tool-calling.md",
        "- ~/Documents/springai-kb/advisors-api.md",
        "```",
        "",
        "---",
        "",
        "## Conventions for Claude Code",
        "",
        "These rules apply when building Spring AI projects:",
        "",
        "- Use `ChatClient` (fluent API) for all LLM interactions, not raw `ChatModel`",
        "- Advisors execute in **registration order** on request, **reverse order** on response",
        "- MCP tools are auto-discovered via `McpToolCallbackProvider` — no manual wiring",
        "- Use `@Description` on `Function<>` beans for tool registration",
        "- Structured output uses `.call().entity(MyClass.class)` — never parse JSON manually",
        "- `MessageWindowChatMemory` is the default; use a persistent store for production",
        "- Spring AI BOM manages all version alignment — never set individual artifact versions",
        "",
    ]

    index_path = output_dir / "SPRING_AI_KB.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return index_path