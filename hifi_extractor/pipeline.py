"""Pipeline orchestrator — wires all extraction modules together.

Provides a unified interface for extracting text from PDFs with configurable
page classification, OCR routing, margin suppression, Markdown formatting,
and token-aware chunking.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path
import json
import time
import fitz  # PyMuPDF

from .page_classifier import (
    PageCategory,
    classify_document,
    DocumentClassification,
)
from .text_extractor import (
    extract_document,
    extract_to_markdown,
    ExtractionResult,
    PageResult,
)
from .margin_suppressor import (
    TextBlock,
    suppress_margins_dbscan,
    suppress_margins_static_zone,
    SuppressionResult,
)
from .markdown_formatter import format_text_to_markdown, FormattedPage
from .token_chunker import chunk_text, Chunk, estimate_tokens


@dataclass
class PipelineConfig:
    """Configuration for the extraction pipeline."""

    # OCR settings
    ocr_language: str = "eng"
    dpi: int = 300
    garbled_threshold: float = 0.05

    # Margin suppression
    suppress_margins: bool = True
    margin_method: str = "static_zone"  # "dbscan" or "static_zone"
    header_zone_pct: float = 0.05
    footer_zone_pct: float = 0.05
    dbscan_eps: float = 30.0
    dbscan_min_samples: int = 3

    # Markdown formatting
    format_markdown: bool = True
    detect_headings: bool = True
    detect_tables: bool = True
    detect_lists: bool = True
    unwrap_lines: bool = True

    # Chunking
    enable_chunking: bool = False
    max_tokens: int = 512
    overlap_tokens: int = 50

    # Output
    output_format: str = "markdown"  # "markdown", "text", "json"
    include_page_numbers: bool = True


@dataclass
class PipelineResult:
    """Complete result from a pipeline run."""

    pdf_path: str
    config: PipelineConfig
    extraction: ExtractionResult
    formatted_pages: list[FormattedPage] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    markdown: str = ""
    elapsed_seconds: float = 0.0
    pages_with_margin_suppression: int = 0

    def summary(self) -> str:
        """Human-readable summary of the pipeline run."""
        lines = [
            f"Pipeline Result: {self.pdf_path}",
            f"  Elapsed: {self.elapsed_seconds:.1f}s",
            f"  Pages processed: {len(self.extraction.pages)}",
            f"  Successful: {self.extraction.success_count}",
            f"  Failed: {self.extraction.failure_count}",
            f"  Total chars: {sum(p.char_count for p in self.extraction.pages):,}",
            f"  Markdown length: {len(self.markdown):,} chars",
        ]
        if self.chunks:
            lines.append(f"  Chunks: {len(self.chunks)}")
            lines.append(
                f"  Avg tokens/chunk: "
                f"{sum(c.token_count for c in self.chunks) / max(len(self.chunks), 1):.0f}"
            )
        if self.extraction.classification:
            lines.append(f"  Classification: {self.extraction.classification.summary()}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serializes the result to a dictionary for JSON export."""
        return {
            "pdf_path": self.pdf_path,
            "elapsed_seconds": self.elapsed_seconds,
            "total_pages": self.extraction.total_pages,
            "pages_processed": len(self.extraction.pages),
            "success_count": self.extraction.success_count,
            "failure_count": self.extraction.failure_count,
            "markdown_length": len(self.markdown),
            "chunk_count": len(self.chunks),
            "pages": [
                {
                    "page_number": p.page_number,
                    "category": p.category.value,
                    "method": p.method_used,
                    "char_count": p.char_count,
                    "success": p.success,
                    "error": p.error,
                }
                for p in self.extraction.pages
            ],
        }


def _suppress_margins_on_page(
    doc: fitz.Document,
    page_index: int,
    page_text: str,
    config: PipelineConfig,
) -> str:
    """Applies margin suppression to a single page's text.

    Extracts spatial text blocks from the PDF page and uses DBSCAN or
    static zone cropping to identify and remove headers/footers.
    """
    page = doc[page_index]
    page_height = page.rect.height

    # Extract text blocks with coordinates
    blocks_raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    text_blocks = []

    for block in blocks_raw.get("blocks", []):
        if block.get("type") == 0:  # Text block
            bbox = block.get("bbox", (0, 0, 0, 0))
            block_text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
                block_text += "\n"
            block_text = block_text.strip()
            if block_text:
                text_blocks.append(
                    TextBlock(
                        x0=bbox[0],
                        y0=bbox[1],
                        x1=bbox[2],
                        y1=bbox[3],
                        text=block_text,
                    )
                )

    if not text_blocks:
        return page_text

    if config.margin_method == "dbscan":
        result = suppress_margins_dbscan(
            text_blocks=text_blocks,
            page_height=page_height,
            eps=config.dbscan_eps,
            min_samples=config.dbscan_min_samples,
            header_zone_pct=config.header_zone_pct,
            footer_zone_pct=config.footer_zone_pct,
        )
    else:
        result = suppress_margins_static_zone(
            text_blocks=text_blocks,
            page_height=page_height,
            header_zone_pct=config.header_zone_pct,
            footer_zone_pct=config.footer_zone_pct,
        )

    if result.body_blocks:
        # Reconstruct text from body blocks, sorted by vertical position
        sorted_blocks = sorted(result.body_blocks, key=lambda b: (b.y0, b.x0))
        return "\n".join(b.text for b in sorted_blocks)

    return page_text


def run_pipeline(
    pdf_path: str,
    config: Optional[PipelineConfig] = None,
    page_range: Optional[tuple[int, int]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> PipelineResult:
    """Runs the full extraction pipeline on a PDF document.

    Pipeline stages:
    1. Page Classification — categorize each page (clean/garbled/image)
    2. Text Extraction — route each page to the appropriate extractor
    3. Margin Suppression — remove headers/footers
    4. Markdown Formatting — structure the text
    5. Token-Aware Chunking — split into bounded chunks (optional)

    Args:
        pdf_path: Path to the PDF file.
        config: Pipeline configuration. Uses defaults if None.
        page_range: Optional (start, end) tuple of 1-indexed page numbers.
        progress_callback: Optional callback for progress reporting.

    Returns:
        PipelineResult with all extraction results, formatted text, and chunks.
    """
    if config is None:
        config = PipelineConfig()

    start_time = time.time()

    # Stage 1 & 2: Classification + Extraction
    if progress_callback:
        progress_callback(0, 1, "Classifying and extracting pages...")

    extraction = extract_document(
        pdf_path=pdf_path,
        page_range=page_range,
        ocr_language=config.ocr_language,
        dpi=config.dpi,
        garbled_threshold=config.garbled_threshold,
        progress_callback=progress_callback,
    )

    # Stage 3: Margin Suppression
    pages_suppressed = 0
    if config.suppress_margins:
        doc = fitz.open(pdf_path)
        for page_result in extraction.pages:
            if page_result.success and page_result.text.strip():
                page_index = page_result.page_number - 1
                if page_index < len(doc):
                    suppressed_text = _suppress_margins_on_page(
                        doc=doc,
                        page_index=page_index,
                        page_text=page_result.text,
                        config=config,
                    )
                    if suppressed_text != page_result.text:
                        page_result.text = suppressed_text
                        page_result.char_count = len(suppressed_text)
                        pages_suppressed += 1
        doc.close()

    # Stage 4: Markdown Formatting
    formatted_pages = []
    if config.format_markdown:
        for page_result in extraction.pages:
            if page_result.success and page_result.text.strip():
                formatted = format_text_to_markdown(
                    text=page_result.text,
                    page_number=page_result.page_number,
                    detect_headings=config.detect_headings,
                    detect_tables=config.detect_tables,
                    detect_lists=config.detect_lists,
                    unwrap_lines=config.unwrap_lines,
                )
                formatted_pages.append(formatted)

    # Assemble full Markdown
    markdown_parts = []
    for fp in formatted_pages:
        if config.include_page_numbers:
            markdown_parts.append(f"<!-- Page {fp.page_number} -->")
        markdown_parts.append(fp.markdown)

    markdown = "\n\n".join(markdown_parts)

    # Stage 5: Token-Aware Chunking
    chunks = []
    if config.enable_chunking:
        chunks = chunk_text(
            text=markdown,
            max_tokens=config.max_tokens,
            overlap_tokens=config.overlap_tokens,
        )

    elapsed = time.time() - start_time

    return PipelineResult(
        pdf_path=pdf_path,
        config=config,
        extraction=extraction,
        formatted_pages=formatted_pages,
        chunks=chunks,
        markdown=markdown,
        elapsed_seconds=elapsed,
        pages_with_margin_suppression=pages_suppressed,
    )


def diagnose(
    pdf_path: str,
    page_range: Optional[tuple[int, int]] = None,
) -> str:
    """Runs classification only and returns a diagnostic report.

    Useful for understanding a PDF's structure before running full extraction.
    """
    classification = classify_document(
        pdf_path=pdf_path,
        page_range=page_range,
    )

    lines = [classification.summary(), ""]

    # Show details for non-clean pages
    problem_pages = [
        p
        for p in classification.pages
        if p.category != PageCategory.CLEAN_TEXT
    ]

    if problem_pages:
        lines.append(f"Problem pages ({len(problem_pages)}):")
        for p in problem_pages[:20]:  # Limit output
            lines.append(
                f"  Page {p.page_number}: {p.category.value} "
                f"(text={p.text_length}, images={p.image_count}, "
                f"garbled={p.garbled_ratio:.2%})"
            )
            if p.sample_text:
                safe_sample = repr(p.sample_text[:80])
                lines.append(f"    Sample: {safe_sample}")
        if len(problem_pages) > 20:
            lines.append(f"  ... and {len(problem_pages) - 20} more")
    else:
        lines.append("All pages have clean native text. No OCR needed.")

    return "\n".join(lines)
