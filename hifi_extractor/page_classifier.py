"""Page-by-page quality classification for PDF documents.

Inspects each page of a PDF and classifies it into one of three categories:
- CLEAN_TEXT: Native digital text with good quality
- GARBLED_TEXT: Native text exists but is corrupt (garbled font encodings)
- IMAGE_ONLY: No native text layer; page contains embedded images

This classification drives the downstream extraction routing decisions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import fitz  # PyMuPDF


class PageCategory(Enum):
    """Classification category for a PDF page."""
    CLEAN_TEXT = "clean_text"
    GARBLED_TEXT = "garbled_text"
    IMAGE_ONLY = "image_only"
    EMPTY = "empty"


@dataclass
class PageClassification:
    """Result of classifying a single PDF page."""
    page_number: int  # 1-indexed
    category: PageCategory
    text_length: int
    image_count: int
    garbled_ratio: float  # Ratio of non-printable/control characters
    confidence: float  # 0.0 to 1.0
    sample_text: str = ""  # First 200 chars of extracted text for diagnostics


@dataclass
class DocumentClassification:
    """Aggregate classification for an entire PDF document."""
    pdf_path: str
    total_pages: int
    pages: list[PageClassification] = field(default_factory=list)

    @property
    def clean_count(self) -> int:
        return sum(1 for p in self.pages if p.category == PageCategory.CLEAN_TEXT)

    @property
    def garbled_count(self) -> int:
        return sum(1 for p in self.pages if p.category == PageCategory.GARBLED_TEXT)

    @property
    def image_only_count(self) -> int:
        return sum(1 for p in self.pages if p.category == PageCategory.IMAGE_ONLY)

    @property
    def empty_count(self) -> int:
        return sum(1 for p in self.pages if p.category == PageCategory.EMPTY)

    def summary(self) -> str:
        """Returns a human-readable summary string."""
        return (
            f"Document: {self.pdf_path}\n"
            f"  Total pages: {self.total_pages}\n"
            f"  Clean text:  {self.clean_count} ({self.clean_count / max(self.total_pages, 1) * 100:.1f}%)\n"
            f"  Garbled:     {self.garbled_count} ({self.garbled_count / max(self.total_pages, 1) * 100:.1f}%)\n"
            f"  Image-only:  {self.image_only_count} ({self.image_only_count / max(self.total_pages, 1) * 100:.1f}%)\n"
            f"  Empty:       {self.empty_count} ({self.empty_count / max(self.total_pages, 1) * 100:.1f}%)"
        )


def _compute_garbled_ratio(text: str) -> float:
    """Computes the ratio of non-printable/control characters in text.

    Control characters (0x00–0x1F excluding tab, newline, carriage return)
    and replacement characters indicate corrupt font encodings.
    """
    if not text:
        return 0.0

    control_chars = 0
    for ch in text:
        code = ord(ch)
        # Count non-printable control chars (excluding \t, \n, \r, space)
        if code < 0x20 and code not in (0x09, 0x0A, 0x0D):
            control_chars += 1
        # Count Unicode replacement character
        elif code == 0xFFFD:
            control_chars += 1

    return control_chars / len(text)


def classify_page(
    page: fitz.Page,
    page_number: int,
    min_text_length: int = 50,
    garbled_threshold: float = 0.05,
) -> PageClassification:
    """Classifies a single PDF page.

    Args:
        page: A PyMuPDF Page object.
        page_number: 1-indexed page number.
        min_text_length: Minimum character count to consider a page as having text.
        garbled_threshold: If more than this fraction of characters are
            non-printable control characters, the page is classified as garbled.

    Returns:
        PageClassification with the determined category and metadata.
    """
    text = page.get_text("text").strip()
    images = page.get_images(full=True)
    text_length = len(text)
    image_count = len(images)
    garbled_ratio = _compute_garbled_ratio(text)
    sample_text = text[:200] if text else ""

    if text_length < min_text_length:
        if image_count > 0:
            category = PageCategory.IMAGE_ONLY
            confidence = 0.95
        else:
            category = PageCategory.EMPTY
            confidence = 1.0
    elif garbled_ratio > garbled_threshold:
        category = PageCategory.GARBLED_TEXT
        confidence = min(1.0, garbled_ratio * 10)  # Higher garble = higher confidence
    else:
        category = PageCategory.CLEAN_TEXT
        confidence = 1.0 - garbled_ratio  # Small amounts of noise reduce confidence

    return PageClassification(
        page_number=page_number,
        category=category,
        text_length=text_length,
        image_count=image_count,
        garbled_ratio=garbled_ratio,
        confidence=confidence,
        sample_text=sample_text,
    )


def classify_document(
    pdf_path: str,
    page_range: Optional[tuple[int, int]] = None,
    min_text_length: int = 50,
    garbled_threshold: float = 0.05,
    progress_callback: Optional[callable] = None,
) -> DocumentClassification:
    """Classifies all pages of a PDF document.

    Args:
        pdf_path: Path to the PDF file.
        page_range: Optional (start, end) tuple of 1-indexed page numbers.
            If None, classifies all pages.
        min_text_length: Minimum character count to consider as having text.
        garbled_threshold: Ratio threshold for garbled text detection.
        progress_callback: Optional callback function called with
            (current_page, total_pages) for progress reporting.

    Returns:
        DocumentClassification with per-page results and aggregate statistics.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if page_range:
        start_page = max(1, page_range[0]) - 1  # Convert to 0-indexed
        end_page = min(total_pages, page_range[1])
    else:
        start_page = 0
        end_page = total_pages

    result = DocumentClassification(
        pdf_path=pdf_path,
        total_pages=total_pages,
    )

    for i in range(start_page, end_page):
        page = doc[i]
        classification = classify_page(
            page=page,
            page_number=i + 1,
            min_text_length=min_text_length,
            garbled_threshold=garbled_threshold,
        )
        result.pages.append(classification)

        if progress_callback:
            progress_callback(i - start_page + 1, end_page - start_page)

    doc.close()
    return result
