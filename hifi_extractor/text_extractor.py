"""Core text extraction engine with tiered OCR routing.

Implements the three-tier extraction strategy:
- CLEAN_TEXT pages: Direct text extraction via PyMuPDF (fast, no OCR).
- GARBLED_TEXT pages: Force-OCR via PyMuPDF4LLM to bypass corrupt font layers.
- IMAGE_ONLY pages: Rasterize → preprocess with OpenCV → OCR.

Supports both per-page and full-document extraction modes.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path
import fitz  # PyMuPDF

from .page_classifier import (
    PageCategory,
    PageClassification,
    classify_page,
    classify_document,
    DocumentClassification,
)


@dataclass
class PageResult:
    """Extraction result for a single page."""
    page_number: int
    text: str
    category: PageCategory
    method_used: str  # "direct", "force_ocr", "image_ocr", "pymupdf4llm_markdown"
    char_count: int
    garbled_ratio: float
    success: bool
    error: Optional[str] = None


@dataclass
class ExtractionResult:
    """Aggregate extraction result for a document."""
    pdf_path: str
    total_pages: int
    pages: list[PageResult] = field(default_factory=list)
    classification: Optional[DocumentClassification] = None

    @property
    def full_text(self) -> str:
        """Concatenates all page texts with page separators."""
        parts = []
        for page in self.pages:
            if page.text.strip():
                parts.append(page.text.strip())
        return "\n\n".join(parts)

    @property
    def success_count(self) -> int:
        return sum(1 for p in self.pages if p.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for p in self.pages if not p.success)

    def summary(self) -> str:
        """Returns a human-readable summary of the extraction."""
        methods = {}
        for p in self.pages:
            methods[p.method_used] = methods.get(p.method_used, 0) + 1
        method_str = ", ".join(f"{k}: {v}" for k, v in sorted(methods.items()))
        total_chars = sum(p.char_count for p in self.pages)
        return (
            f"Extraction: {self.pdf_path}\n"
            f"  Pages processed: {len(self.pages)} / {self.total_pages}\n"
            f"  Successful: {self.success_count}, Failed: {self.failure_count}\n"
            f"  Total characters: {total_chars:,}\n"
            f"  Methods used: {method_str}"
        )


def _extract_direct(page: fitz.Page) -> str:
    """Extracts text directly from a page's native text layer."""
    return page.get_text("text").strip()


def _extract_force_ocr_page(
    doc: fitz.Document,
    page_index: int,
    ocr_language: str = "eng",
    dpi: int = 300,
) -> str:
    """Forces OCR on a single page by rasterizing and running Tesseract.

    Uses PyMuPDF's built-in OCR capabilities via page.get_textpage_ocr().
    Falls back to pymupdf4llm if available.
    """
    page = doc[page_index]

    try:
        # Try using PyMuPDF's built-in OCR
        tp = page.get_textpage_ocr(
            flags=fitz.TEXT_PRESERVE_WHITESPACE,
            language=ocr_language,
            dpi=dpi,
            full=True,  # Force full OCR (ignore existing text)
        )
        text = page.get_text("text", textpage=tp).strip()
        if text:
            return text
    except Exception:
        pass

    # Fallback: rasterize and use image preprocessing + OCR
    try:
        from .image_preprocessor import preprocess_page_image
        import numpy as np

        # Rasterize at high DPI
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)

        # Convert to numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width
        )

        # Preprocess
        result = preprocess_page_image(img, deskew=True, denoise=True, binarize=True)

        # Try OCR on preprocessed image via PyMuPDF
        # Create a temporary PDF page from the preprocessed image
        import cv2

        _, encoded = cv2.imencode(".png", result.image)
        img_bytes = encoded.tobytes()

        temp_doc = fitz.open()
        img_rect = fitz.Rect(0, 0, result.image.shape[1], result.image.shape[0])
        temp_page = temp_doc.new_page(width=img_rect.width, height=img_rect.height)
        temp_page.insert_image(img_rect, stream=img_bytes)

        tp = temp_page.get_textpage_ocr(
            flags=fitz.TEXT_PRESERVE_WHITESPACE,
            language=ocr_language,
            dpi=dpi,
            full=True,
        )
        text = temp_page.get_text("text", textpage=tp).strip()
        temp_doc.close()

        return text
    except Exception:
        return ""


def extract_page(
    doc: fitz.Document,
    page_index: int,
    classification: Optional[PageClassification] = None,
    ocr_language: str = "eng",
    dpi: int = 300,
    garbled_threshold: float = 0.05,
) -> PageResult:
    """Extracts text from a single page using the appropriate method.

    Args:
        doc: Open PyMuPDF Document.
        page_index: 0-indexed page number.
        classification: Pre-computed page classification. If None, classifies
            the page on-the-fly.
        ocr_language: Language code for OCR (e.g., "eng", "eng+hin").
        dpi: DPI for page rasterization when OCR is needed.
        garbled_threshold: Ratio threshold for garbled text detection.

    Returns:
        PageResult with extracted text and metadata.
    """
    page = doc[page_index]
    page_number = page_index + 1

    # Classify the page if not provided
    if classification is None:
        classification = classify_page(
            page=page,
            page_number=page_number,
            garbled_threshold=garbled_threshold,
        )

    try:
        if classification.category == PageCategory.CLEAN_TEXT:
            text = _extract_direct(page)
            method = "direct"

        elif classification.category == PageCategory.GARBLED_TEXT:
            text = _extract_force_ocr_page(
                doc=doc,
                page_index=page_index,
                ocr_language=ocr_language,
                dpi=dpi,
            )
            method = "force_ocr"

            # If OCR also failed, try direct extraction as a last resort
            if not text.strip():
                text = _extract_direct(page)
                method = "force_ocr_fallback_direct"

        elif classification.category == PageCategory.IMAGE_ONLY:
            text = _extract_force_ocr_page(
                doc=doc,
                page_index=page_index,
                ocr_language=ocr_language,
                dpi=dpi,
            )
            method = "image_ocr"

        else:  # EMPTY
            text = ""
            method = "empty"

        return PageResult(
            page_number=page_number,
            text=text,
            category=classification.category,
            method_used=method,
            char_count=len(text),
            garbled_ratio=classification.garbled_ratio,
            success=True,
        )

    except Exception as e:
        return PageResult(
            page_number=page_number,
            text="",
            category=classification.category,
            method_used="error",
            char_count=0,
            garbled_ratio=classification.garbled_ratio,
            success=False,
            error=str(e),
        )


def extract_document(
    pdf_path: str,
    page_range: Optional[tuple[int, int]] = None,
    ocr_language: str = "eng",
    dpi: int = 300,
    garbled_threshold: float = 0.05,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> ExtractionResult:
    """Extracts text from an entire PDF document using tiered routing.

    Args:
        pdf_path: Path to the PDF file.
        page_range: Optional (start, end) tuple of 1-indexed page numbers.
        ocr_language: Language code for OCR engine.
        dpi: DPI for rasterization when OCR is needed.
        garbled_threshold: Ratio threshold for garbled text detection.
        progress_callback: Optional function called with
            (current_page, total_pages, status_message).

    Returns:
        ExtractionResult with per-page results and aggregate statistics.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if page_range:
        start = max(1, page_range[0]) - 1
        end = min(total_pages, page_range[1])
    else:
        start = 0
        end = total_pages

    # Phase 1: Classify all pages
    doc_classification = classify_document(
        pdf_path=pdf_path,
        page_range=(start + 1, end) if page_range else None,
        garbled_threshold=garbled_threshold,
    )

    # Build a lookup from page number to classification
    classification_map = {c.page_number: c for c in doc_classification.pages}

    result = ExtractionResult(
        pdf_path=pdf_path,
        total_pages=total_pages,
        classification=doc_classification,
    )

    # Phase 2: Extract text page by page
    pages_to_process = end - start
    for i in range(start, end):
        page_number = i + 1
        classification = classification_map.get(page_number)

        if progress_callback:
            category_str = classification.category.value if classification else "unknown"
            progress_callback(
                i - start + 1,
                pages_to_process,
                f"Page {page_number}: {category_str}",
            )

        page_result = extract_page(
            doc=doc,
            page_index=i,
            classification=classification,
            ocr_language=ocr_language,
            dpi=dpi,
            garbled_threshold=garbled_threshold,
        )
        result.pages.append(page_result)

    doc.close()
    return result


def extract_to_markdown(
    pdf_path: str,
    page_range: Optional[tuple[int, int]] = None,
    ocr_language: str = "eng",
    suppress_headers_footers: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> str:
    """High-level convenience function: extract PDF to clean Markdown.

    Uses pymupdf4llm for clean-text documents for optimal Markdown formatting.
    Falls back to the tiered extraction engine for mixed documents.

    Args:
        pdf_path: Path to the PDF file.
        page_range: Optional (start, end) tuple of 1-indexed page numbers.
        ocr_language: Language code for OCR.
        suppress_headers_footers: Whether to strip headers/footers.
        progress_callback: Optional progress callback.

    Returns:
        Clean Markdown string.
    """
    try:
        import pymupdf4llm

        # First, classify to check if we can use pymupdf4llm directly
        doc_class = classify_document(pdf_path, page_range=page_range)
        garbled_or_image = doc_class.garbled_count + doc_class.image_only_count
        total = len(doc_class.pages)

        if total > 0 and garbled_or_image / total < 0.1:
            # Document is mostly clean — use pymupdf4llm for best Markdown
            pages_arg = None
            if page_range:
                pages_arg = list(range(page_range[0] - 1, page_range[1]))

            markdown = pymupdf4llm.to_markdown(
                doc=pdf_path,
                pages=pages_arg,
                page_chunks=False,
            )
            return markdown

    except ImportError:
        pass

    # Fallback: use the tiered extraction engine
    extraction = extract_document(
        pdf_path=pdf_path,
        page_range=page_range,
        ocr_language=ocr_language,
        progress_callback=progress_callback,
    )

    return extraction.full_text
