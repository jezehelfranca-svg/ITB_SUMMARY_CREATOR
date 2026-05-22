"""Command-line interface for the HiFi PDF Extraction Pipeline."""

import argparse
import json
import sys
import os
from pathlib import Path


def _setup_encoding():
    """Ensures UTF-8 output on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def _progress_callback(current: int, total: int, message: str = "") -> None:
    """Prints a progress bar to stderr."""
    pct = current / max(total, 1) * 100
    bar_len = 30
    filled = int(bar_len * current / max(total, 1))
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  [{bar}] {pct:5.1f}% ({current}/{total}) {message[:50]}", end="", file=sys.stderr)
    if current >= total:
        print("", file=sys.stderr)


def cmd_diagnose(args):
    """Run page classification diagnostics on a PDF."""
    from .pipeline import diagnose

    print(f"Diagnosing: {args.input}", file=sys.stderr)
    page_range = _parse_page_range(args.pages) if args.pages else None
    report = diagnose(args.input, page_range=page_range)
    print(report)


def cmd_extract(args):
    """Run the full extraction pipeline."""
    from .pipeline import run_pipeline, PipelineConfig

    config = PipelineConfig(
        ocr_language=args.ocr_lang,
        dpi=args.dpi,
        suppress_margins=not args.no_margins,
        margin_method=args.margin_method,
        header_zone_pct=args.header_zone / 100.0,
        footer_zone_pct=args.footer_zone / 100.0,
        format_markdown=True,
        enable_chunking=args.chunk_size > 0,
        max_tokens=args.chunk_size if args.chunk_size > 0 else 512,
        overlap_tokens=args.overlap,
        include_page_numbers=not args.no_page_numbers,
    )

    page_range = _parse_page_range(args.pages) if args.pages else None

    print(f"Extracting: {args.input}", file=sys.stderr)
    result = run_pipeline(
        pdf_path=args.input,
        config=config,
        page_range=page_range,
        progress_callback=_progress_callback if not args.quiet else None,
    )

    # Output
    if args.output:
        output_path = Path(args.output)
        if args.format == "json":
            output_path.write_text(
                json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            output_path.write_text(result.markdown, encoding="utf-8")
        print(f"Output saved to: {args.output}", file=sys.stderr)
    else:
        if args.format == "json":
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(result.markdown)

    # Summary
    if not args.quiet:
        print(f"\n{result.summary()}", file=sys.stderr)


def cmd_batch(args):
    """Process multiple PDF files."""
    from .pipeline import run_pipeline, PipelineConfig

    config = PipelineConfig(
        ocr_language=args.ocr_lang,
        suppress_margins=True,
        format_markdown=True,
        include_page_numbers=True,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = []
    for pattern in args.inputs:
        if "*" in pattern or "?" in pattern:
            parent = Path(pattern).parent
            glob_pattern = Path(pattern).name
            pdf_files.extend(parent.glob(glob_pattern))
        else:
            pdf_files.append(Path(pattern))

    print(f"Processing {len(pdf_files)} files...", file=sys.stderr)

    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] {pdf_path.name}", file=sys.stderr)
        try:
            result = run_pipeline(
                pdf_path=str(pdf_path),
                config=config,
                progress_callback=_progress_callback if not args.quiet else None,
            )

            output_name = pdf_path.stem + ".md"
            output_file = output_dir / output_name
            output_file.write_text(result.markdown, encoding="utf-8")
            print(f"  → {output_file} ({len(result.markdown):,} chars)", file=sys.stderr)

        except Exception as e:
            print(f"  ✗ Error: {e}", file=sys.stderr)


def _parse_page_range(page_str: str) -> tuple[int, int]:
    """Parses '10-50' into (10, 50), or '5' into (5, 5)."""
    if "-" in page_str:
        parts = page_str.split("-")
        return (int(parts[0].strip()), int(parts[1].strip()))
    else:
        page = int(page_str.strip())
        return (page, page)


def main():
    """Main entry point for the CLI."""
    _setup_encoding()

    parser = argparse.ArgumentParser(
        prog="hifi_extractor",
        description="HiFi PDF Extraction Pipeline — High-fidelity, layout-aware text extraction.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- diagnose ---
    diag_parser = subparsers.add_parser(
        "diagnose",
        help="Run page classification diagnostics on a PDF.",
    )
    diag_parser.add_argument("input", help="Path to the PDF file.")
    diag_parser.add_argument("--pages", help="Page range (e.g., '1-50' or '10').")

    # --- extract ---
    ext_parser = subparsers.add_parser(
        "extract",
        help="Extract text from a PDF using the full pipeline.",
    )
    ext_parser.add_argument("input", help="Path to the PDF file.")
    ext_parser.add_argument("-o", "--output", help="Output file path. Prints to stdout if omitted.")
    ext_parser.add_argument("--pages", help="Page range (e.g., '1-50').")
    ext_parser.add_argument("--ocr-lang", default="eng", help="OCR language (default: eng).")
    ext_parser.add_argument("--dpi", type=int, default=300, help="DPI for OCR rasterization (default: 300).")
    ext_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format.")
    ext_parser.add_argument("--chunk-size", type=int, default=0, help="Enable chunking with max token count (0=disabled).")
    ext_parser.add_argument("--overlap", type=int, default=50, help="Token overlap between chunks.")
    ext_parser.add_argument("--margin-method", choices=["static_zone", "dbscan"], default="static_zone", help="Margin suppression method.")
    ext_parser.add_argument("--header-zone", type=float, default=5.0, help="Header zone percentage (default: 5%%).")
    ext_parser.add_argument("--footer-zone", type=float, default=5.0, help="Footer zone percentage (default: 5%%).")
    ext_parser.add_argument("--no-margins", action="store_true", help="Disable margin suppression.")
    ext_parser.add_argument("--no-page-numbers", action="store_true", help="Omit page number comments.")
    ext_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output.")

    # --- batch ---
    batch_parser = subparsers.add_parser(
        "batch",
        help="Process multiple PDF files.",
    )
    batch_parser.add_argument("inputs", nargs="+", help="PDF file paths or glob patterns.")
    batch_parser.add_argument("-o", "--output-dir", required=True, help="Output directory.")
    batch_parser.add_argument("--ocr-lang", default="eng", help="OCR language.")
    batch_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output.")

    args = parser.parse_args()

    if args.command == "diagnose":
        cmd_diagnose(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "batch":
        cmd_batch(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
