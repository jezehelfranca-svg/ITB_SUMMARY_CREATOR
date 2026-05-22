"""Token-aware semantic chunking for extracted document text."""

from dataclasses import dataclass, field
from typing import Optional, Callable
import re


@dataclass
class Chunk:
    """A token-bounded text chunk with metadata."""
    text: str
    chunk_index: int
    token_count: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    heading: Optional[str] = None


def estimate_tokens(text: str) -> int:
    """Estimates token count using the ~4 chars per token heuristic."""
    return max(1, len(text) // 4)


def create_precise_token_counter(model_name: str = "bert-base-uncased") -> Callable[[str], int]:
    """
    Creates a precise token counter using a HuggingFace tokenizer.
    Falls back to estimation if transformers is not available.
    """
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        return lambda text: len(tokenizer.encode(text, add_special_tokens=False))
    except ImportError:
        return estimate_tokens


def chunk_text(
    text: str,
    max_tokens: int = 512,
    overlap_tokens: int = 50,
    token_counter: Optional[Callable[[str], int]] = None,
    respect_paragraphs: bool = True,
    respect_headings: bool = True
) -> list[Chunk]:
    """
    Splits text into token-bounded chunks that respect structural boundaries.

    Strategy:
    1. Split text into paragraphs (double newlines).
    2. Group paragraphs into chunks without exceeding max_tokens.
    3. If a single paragraph exceeds max_tokens, split it at sentence boundaries.
    4. Never split mid-sentence if possible.
    5. Apply overlap at paragraph/sentence boundaries for context continuity.

    Args:
        text: The full text to chunk.
        max_tokens: Maximum tokens per chunk.
        overlap_tokens: Number of tokens to overlap between adjacent chunks.
        token_counter: Function that counts tokens. Defaults to ~4 chars/token estimate.
        respect_paragraphs: If True, avoids splitting within paragraphs.
        respect_headings: If True, starts a new chunk at each heading (# lines).

    Returns:
        List of Chunk objects with text, token count, and metadata.
    """
    if token_counter is None:
        token_counter = estimate_tokens

    if not text.strip():
        return []

    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text.strip())

    chunks: list[Chunk] = []
    current_parts: list[str] = []
    current_tokens = 0
    current_heading: Optional[str] = None
    chunk_idx = 0

    def flush_chunk():
        nonlocal chunk_idx, current_parts, current_tokens, current_heading
        if not current_parts:
            return
        chunk_text_str = "\n\n".join(current_parts)
        chunks.append(Chunk(
            text=chunk_text_str,
            chunk_index=chunk_idx,
            token_count=token_counter(chunk_text_str),
            heading=current_heading
        ))
        chunk_idx += 1

        # Handle overlap: keep the last paragraph if it fits within overlap budget
        if overlap_tokens > 0 and len(current_parts) > 1:
            last_part = current_parts[-1]
            last_tokens = token_counter(last_part)
            if last_tokens <= overlap_tokens:
                current_parts = [last_part]
                current_tokens = last_tokens
            else:
                current_parts = []
                current_tokens = 0
        else:
            current_parts = []
            current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Detect headings
        is_heading = para.startswith('#') if respect_headings else False
        if is_heading:
            # Start a new chunk at each heading
            flush_chunk()
            current_heading = para.split('\n')[0].strip()

        para_tokens = token_counter(para)

        if para_tokens > max_tokens:
            # Split oversized paragraph at sentence boundaries
            flush_chunk()
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sent_tokens = token_counter(sentence)
                if current_tokens + sent_tokens > max_tokens:
                    flush_chunk()
                current_parts.append(sentence)
                current_tokens += sent_tokens
        elif current_tokens + para_tokens > max_tokens:
            flush_chunk()
            current_parts.append(para)
            current_tokens = para_tokens
        else:
            current_parts.append(para)
            current_tokens += para_tokens

    flush_chunk()
    return chunks
