#!/usr/bin/env python3
"""
springai-kb — Spring AI PDF → Claude Code Knowledge Base Converter

Usage:
    python main.py --input ~/Documents/springai/ --output ~/Documents/springai-kb/
    python main.py --input "~/Documents/springai/Tool Calling __ Spring AI Reference.pdf"
"""

import argparse
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text
from rich import box

from src.springai_kb.converter import convert_pdf, ConversionResult
from src.springai_kb.index_generator import generate_index


console = Console()


def collect_pdfs(input_path: Path) -> list[Path]:
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    if input_path.is_dir():
        pdfs = sorted(input_path.glob("*.pdf"))
        if not pdfs:
            pdfs = sorted(input_path.rglob("*.pdf"))
        return pdfs
    console.print(f"[red]Error:[/red] {input_path} is not a PDF file or directory")
    sys.exit(1)


def print_banner():
    console.print(Panel(
        "[bold cyan]Spring AI KB Converter[/bold cyan]\n"
        "[dim]PDF → Clean Markdown for Claude Code agents[/dim]",
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    console.print()


def run_conversion(pdfs: list[Path], output_dir: Path, workers: int) -> list[ConversionResult]:
    results: list[ConversionResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"[cyan]Converting {len(pdfs)} PDF(s)...", total=len(pdfs)
        )

        if workers == 1:
            for pdf in pdfs:
                short_name = pdf.stem[:50] + "..." if len(pdf.stem) > 50 else pdf.stem
                progress.update(task, description=f"[cyan]{short_name}")
                result = convert_pdf(pdf, output_dir)
                results.append(result)
                progress.advance(task)
        else:
            futures = {}
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for pdf in pdfs:
                    future = executor.submit(convert_pdf, pdf, output_dir)
                    futures[future] = pdf

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    progress.advance(task)

    return results


def print_results(results: list[ConversionResult], output_dir: Path):
    console.print()

    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    # Summary table
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    table.add_column("File", style="cyan", no_wrap=False, max_width=45)
    table.add_column("Output", style="green", no_wrap=False, max_width=35)
    table.add_column("Size", justify="right", style="dim")
    table.add_column("Status", justify="center")

    for r in sorted(results, key=lambda x: x.pdf_path.name):
        pdf_name = r.pdf_path.stem[:44] + "…" if len(r.pdf_path.stem) > 45 else r.pdf_path.stem
        if r.success:
            size_kb = r.output_path.stat().st_size // 1024
            out_name = r.output_path.name
            table.add_row(pdf_name, out_name, f"{size_kb} KB", "[green]✓[/green]")
        else:
            table.add_row(pdf_name, "—", "—", "[red]✗[/red]")

    console.print(table)

    if failures:
        console.print()
        console.print("[bold red]Failures:[/bold red]")
        for r in failures:
            console.print(f"  [red]✗[/red] {r.pdf_path.name}")
            console.print(f"    [dim]{r.error}[/dim]")

    console.print()
    console.print(
        f"[bold green]✓ {len(successes)}/{len(results)} converted[/bold green]"
        f"  →  [cyan]{output_dir}/[/cyan]"
    )


def print_next_steps(index_path: Path, output_dir: Path):
    console.print()
    console.print(Panel(
        "[bold]Next Steps[/bold]\n\n"
        f"1. [cyan]Review the index:[/cyan]\n"
        f"   cat {index_path}\n\n"
        f"2. [cyan]Add to your project CLAUDE.md:[/cyan]\n"
        f"   Copy the snippet from [dim]SPRING_AI_KB.md → 'How to Use' section[/dim]\n\n"
        f"3. [cyan]Or set up global access:[/cyan]\n"
        f"   echo '- @{output_dir}/SPRING_AI_KB.md' >> ~/.claude/CLAUDE.md\n\n"
        f"4. [cyan]Test:[/cyan]\n"
        f"   cd your-spring-ai-project && claude",
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def main():
    parser = argparse.ArgumentParser(
        description="Convert Spring AI reference PDFs to Claude Code markdown knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all PDFs in a folder
  python main.py --input ~/Documents/springai/

  # Convert to a specific output directory
  python main.py --input ~/Documents/springai/ --output ~/Documents/springai-kb/

  # Convert a single PDF
  python main.py --input ~/Documents/springai/Tool\\ Calling\\ __\\ Spring\\ AI\\ Reference.pdf

  # Use parallel processing (faster for many files)
  python main.py --input ~/Documents/springai/ --workers 4
        """,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="Path to a single PDF or a directory of PDFs",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./springai-kb"),
        help="Output directory for markdown files (default: ./springai-kb)",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=1,
        help="Parallel workers for batch conversion (default: 1, try 4 for speed)",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip generating the SPRING_AI_KB.md index file",
    )

    args = parser.parse_args()

    print_banner()

    pdfs = collect_pdfs(args.input)
    if not pdfs:
        console.print(f"[yellow]No PDFs found in {args.input}[/yellow]")
        sys.exit(0)

    console.print(f"[dim]Found {len(pdfs)} PDF(s) in {args.input}[/dim]")
    console.print(f"[dim]Output → {args.output.resolve()}[/dim]")
    console.print()

    start = time.perf_counter()
    results = run_conversion(pdfs, args.output, args.workers)
    elapsed = time.perf_counter() - start

    print_results(results, args.output)

    successes = [r for r in results if r.success]

    if successes and not args.no_index:
        index_path = generate_index(
            args.output,
            [r.output_path for r in successes],
        )
        console.print(f"[dim]Index → {index_path.name}[/dim]")
        print_next_steps(index_path, args.output.resolve())

    console.print(f"\n[dim]Completed in {elapsed:.1f}s[/dim]")


if __name__ == "__main__":
    main()