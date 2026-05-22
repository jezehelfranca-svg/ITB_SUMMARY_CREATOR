"""Converts raw extracted text into clean, structured Markdown.

This module provides functionality to transform raw text (typically extracted
from PDFs or other documents) into well-structured Markdown. It handles:

- Paragraph reconstruction by unwrapping soft line breaks
- Heading detection (ALL CAPS, numbered sections)
- List detection and normalization
- Tabular pattern detection
- Whitespace cleanup

Typical usage::

    from hifi_extractor.markdown_formatter import format_text_to_markdown

    result = format_text_to_markdown(raw_text, page_number=1)
    print(result.markdown)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FormattedPage:
    """A page of formatted Markdown text with metadata.

    Attributes:
        page_number: Zero-based page index from the source document.
        markdown: The fully formatted Markdown string.
        headings_found: List of heading texts detected on this page.
        tables_found: Count of table structures detected on this page.
        lists_found: Count of list blocks detected on this page.
    """

    page_number: int
    markdown: str
    headings_found: list[str] = field(default_factory=list)
    tables_found: int = 0
    lists_found: int = 0


def format_text_to_markdown(
    text: str,
    page_number: int = 0,
    detect_headings: bool = True,
    detect_tables: bool = True,
    detect_lists: bool = True,
    unwrap_lines: bool = True,
) -> FormattedPage:
    """Convert raw extracted text into clean Markdown.

    The conversion pipeline applies the following operations in order:

    1. **Unwrap soft line breaks** — lines that end without sentence-ending
       punctuation are joined to reconstruct paragraphs from column-wrapped
       PDF text.
    2. **Detect headings** — ALL CAPS lines, numbered sections (``1.``,
       ``2.3``), and short bold lines followed by body text are promoted to
       Markdown headings.
    3. **Detect lists** — numbered, bulleted, and lettered list items are
       recognised and normalised to Markdown unordered list syntax.
    4. **Detect tables** — tabular patterns are identified and formatted as
       Markdown tables (future enhancement placeholder).
    5. **Clean whitespace** — runs of three or more blank lines are collapsed
       to a single blank line.

    Args:
        text: The raw text to convert.
        page_number: Zero-based page number for metadata tracking.
        detect_headings: Whether to apply heading detection heuristics.
        detect_tables: Whether to apply table detection heuristics.
        detect_lists: Whether to apply list detection heuristics.
        unwrap_lines: Whether to merge continuation lines into paragraphs.

    Returns:
        A :class:`FormattedPage` containing the Markdown output and
        structural metadata collected during conversion.
    """
    headings_found: list[str] = []
    tables_found: int = 0
    lists_found: int = 0

    lines = text.split("\n")
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines, preserve as paragraph breaks
        if not line.strip():
            if result_lines and result_lines[-1] != "":
                result_lines.append("")
            i += 1
            continue

        stripped = line.strip()

        # --- Heading detection: ALL CAPS lines ---
        if detect_headings and _is_heading_candidate(stripped):
            level = _determine_heading_level(stripped)
            heading = f"{'#' * level} {stripped}"
            headings_found.append(stripped)
            if result_lines and result_lines[-1] != "":
                result_lines.append("")
            result_lines.append(heading)
            result_lines.append("")
            i += 1
            continue

        # --- Heading detection: numbered sections (e.g. "1.", "2.3", "a)") ---
        # Guard: if this line also matches a list pattern *and* the next
        # non-empty line is also a list item, treat the run as a list
        # rather than a heading.
        if detect_headings and _is_numbered_heading(stripped, lines, i) and not (
            detect_lists
            and _is_list_item(stripped)
            and _has_adjacent_list_item(lines, i)
        ):
            heading_text = stripped
            level = _numbered_heading_level(stripped)
            heading = f"{'#' * level} {heading_text}"
            headings_found.append(heading_text)
            if result_lines and result_lines[-1] != "":
                result_lines.append("")
            result_lines.append(heading)
            result_lines.append("")
            i += 1
            continue

        # --- List detection ---
        if detect_lists and _is_list_item(stripped):
            list_items: list[str] = [_format_list_item(stripped)]
            lists_found += 1
            i += 1
            while i < len(lines) and _is_list_item(lines[i].strip()):
                list_items.append(_format_list_item(lines[i].strip()))
                i += 1
            result_lines.extend(list_items)
            result_lines.append("")
            continue

        # --- Default: paragraph unwrapping ---
        if unwrap_lines:
            para_parts: list[str] = [stripped]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    break
                if _is_heading_candidate(next_line) or _is_list_item(next_line):
                    break
                if _is_numbered_heading(next_line, lines, i):
                    break
                if _should_continue_paragraph(para_parts[-1], next_line):
                    para_parts.append(next_line)
                    i += 1
                else:
                    break
            result_lines.append(" ".join(para_parts))
            result_lines.append("")
        else:
            result_lines.append(stripped)
            i += 1

    # Collapse runs of multiple blank lines
    markdown = "\n".join(result_lines)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

    return FormattedPage(
        page_number=page_number,
        markdown=markdown,
        headings_found=headings_found,
        tables_found=tables_found,
        lists_found=lists_found,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _is_heading_candidate(text: str) -> bool:
    """Check whether *text* looks like an ALL CAPS heading.

    A candidate must be between 3 and 100 characters, contain at least three
    alphabetic characters with > 80 % of them upper-case, and must *not* end
    with common sentence-ending or clause-continuing punctuation.
    """
    if len(text) < 3 or len(text) > 100:
        return False
    alpha_chars = sum(1 for c in text if c.isalpha())
    if alpha_chars < 3:
        return False
    upper_ratio = sum(1 for c in text if c.isupper()) / max(alpha_chars, 1)
    return upper_ratio > 0.8 and not text.endswith((".", ",", ";", ":"))


def _determine_heading_level(text: str) -> int:
    """Assign a Markdown heading level based on text length.

    Shorter headings are assumed to be higher-level (``##``), while longer
    headings receive ``###`` or ``####``.
    """
    if len(text) < 20:
        return 2
    if len(text) < 40:
        return 3
    return 4


def _is_numbered_heading(text: str, lines: list[str], index: int) -> bool:
    """Determine whether *text* is a numbered section heading.

    The heuristic matches lines that start with a number-dot pattern
    (e.g. ``1.``, ``2.3``) followed by a capital letter, are reasonably
    short, and are followed by a longer body-text line.
    """
    pattern = r"^\d+(\.\d+)*\.?\s+[A-Z]"
    if not re.match(pattern, text):
        return False
    if len(text) > 120:
        return False
    # Look ahead: if a following non-empty line is longer, this is likely a
    # heading above body text.
    for j in range(index + 1, min(index + 3, len(lines))):
        next_line = lines[j].strip()
        if next_line and len(next_line) > len(text):
            return True
    return len(text) < 80


def _numbered_heading_level(text: str) -> int:
    """Derive heading level from the depth of a numbered pattern.

    ``1.`` → ``##``, ``1.2`` → ``###``, ``1.2.3`` → ``####``, etc.
    The maximum level is capped at 6 to comply with Markdown limits.
    """
    match = re.match(r"^(\d+(\.\d+)*)\.*\s", text)
    if match:
        parts = match.group(1).split(".")
        return min(len(parts) + 1, 6)
    return 3


def _has_adjacent_list_item(lines: list[str], index: int) -> bool:
    """Check whether the next non-empty line after *index* is also a list item.

    This is used to disambiguate numbered headings (``1. Introduction``) from
    numbered lists (``1. Apples``, ``2. Bananas``) — the latter appear in
    consecutive runs.
    """
    for j in range(index + 1, min(index + 3, len(lines))):
        next_line = lines[j].strip()
        if next_line:
            return _is_list_item(next_line)
    return False


def _is_list_item(text: str) -> bool:
    """Return ``True`` if *text* looks like a list item.

    Recognised formats include:
    - Bullet markers: ``-``, ``•``, ``●``, ``◦``, ``▪``
    - Numbered lists: ``1.``, ``1)``, ``1]``
    - Lettered lists: ``a.``, ``a)``
    - Roman numeral lists: ``i.``, ``iv)``
    """
    patterns: list[str] = [
        r"^[-•●◦▪]\s",            # Bullet markers
        r"^\d+[.)\]]\s",           # Numbered lists: "1. ", "1) ", "1] "
        r"^[a-z][.)\]]\s",        # Lettered lists: "a. ", "a) "
        r"^[ivxlcdm]+[.)\]]\s",   # Roman numeral lists
    ]
    return any(re.match(p, text, re.IGNORECASE) for p in patterns)


def _format_list_item(text: str) -> str:
    """Normalise a list item to Markdown unordered list syntax (``- …``).

    All bullet, numbered, lettered, and Roman-numeral prefixes are replaced
    with a uniform ``- `` prefix.
    """
    cleaned = re.sub(r"^[-•●◦▪]\s", "- ", text)
    cleaned = re.sub(r"^\d+[.)\]]\s", "- ", cleaned)
    cleaned = re.sub(r"^[a-z][.)\]]\s", "- ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[ivxlcdm]+[.)\]]\s", "- ", cleaned, flags=re.IGNORECASE)
    return cleaned


def _should_continue_paragraph(prev_line: str, next_line: str) -> bool:
    """Decide whether *next_line* should be merged into the current paragraph.

    The heuristic favours merging when the previous line does not appear to
    end a sentence (no terminal punctuation) or when the next line is a
    plausible continuation (lower-case start, sufficient length).
    """
    # Short line ending with sentence punctuation — likely a complete thought.
    if prev_line.endswith((".", "!", "?", ":")) and len(prev_line) < 60:
        return False
    # New sentence after a period — don't merge.
    if prev_line.endswith(".") and next_line[0:1].isupper():
        return False
    # Mid-sentence continuation (no terminal punctuation).
    if prev_line[-1:] not in ".!?:;":
        return True
    # Merge longer continuation lines that don't start a new sentence.
    return len(next_line) > 20 and not next_line[0:1].isupper()
