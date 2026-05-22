"""DBSCAN-based header/footer detection and removal.

Uses density-based clustering to separate body text from margin noise
(headers, footers, page numbers) with a static-zone fallback for
pages that lack sufficient text blocks.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.cluster import DBSCAN


@dataclass
class TextBlock:
    """Axis-aligned bounding box around a detected text region.

    Attributes:
        x0: Left edge coordinate.
        y0: Top edge coordinate.
        x1: Right edge coordinate.
        y1: Bottom edge coordinate.
        text: The recognised text content of this block.
        block_type: Semantic label — one of ``"body"``, ``"header"``,
            ``"footer"``, or ``"margin"``.
    """

    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_type: str = "body"


@dataclass
class SuppressionResult:
    """Outcome of a margin-suppression pass on a single page.

    Attributes:
        body_blocks: Text blocks classified as body content.
        suppressed_blocks: Text blocks classified as margin noise.
        method_used: ``"dbscan"`` or ``"static_zone"``.
    """

    body_blocks: list[TextBlock]
    suppressed_blocks: list[TextBlock]
    method_used: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def suppress_margins_dbscan(
    text_blocks: list[TextBlock],
    page_height: float,
    *,
    eps: float = 30.0,
    min_samples: int = 3,
    header_zone_pct: float = 0.08,
    footer_zone_pct: float = 0.08,
) -> SuppressionResult:
    """Identify and separate body text from margin noise using DBSCAN.

    **Strategy**

    1. Build feature vectors ``[x_center, y_center, text_length]`` for each
       block.
    2. Cluster the feature vectors with DBSCAN.
    3. The largest cluster is treated as body text.  Smaller clusters whose
       blocks fall inside the top or bottom page zones are classified as
       headers / footers and suppressed.
    4. Falls back to :func:`suppress_margins_static_zone` when DBSCAN cannot
       form any cluster (e.g. too few blocks).

    Args:
        text_blocks: Detected text blocks for one page.
        page_height: Total page height in the same coordinate units as the
            block bounding boxes.
        eps: DBSCAN neighbourhood radius.
        min_samples: DBSCAN minimum cluster size.
        header_zone_pct: Fraction of page height (from the top) considered
            the header zone.
        footer_zone_pct: Fraction of page height (from the bottom) considered
            the footer zone.

    Returns:
        A :class:`SuppressionResult` with body and suppressed blocks.
    """
    if not text_blocks:
        return SuppressionResult([], [], "dbscan")

    # Build feature matrix.
    features: list[list[float]] = []
    for block in text_blocks:
        x_center = (block.x0 + block.x1) / 2
        y_center = (block.y0 + block.y1) / 2
        features.append([x_center, y_center, float(len(block.text))])

    features_array = np.array(features)

    if len(features_array) < min_samples:
        return suppress_margins_static_zone(
            text_blocks, page_height, header_zone_pct, footer_zone_pct
        )

    # Run DBSCAN.
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels: np.ndarray = db.fit_predict(features_array)

    # Identify the largest (body) cluster.
    unique_labels = set(labels.tolist())
    unique_labels.discard(-1)  # Remove the noise label.

    if not unique_labels:
        return suppress_margins_static_zone(
            text_blocks, page_height, header_zone_pct, footer_zone_pct
        )

    cluster_sizes = {label: int(np.sum(labels == label)) for label in unique_labels}
    body_label = max(cluster_sizes, key=cluster_sizes.get)  # type: ignore[arg-type]

    body_blocks: list[TextBlock] = []
    suppressed_blocks: list[TextBlock] = []

    header_threshold = page_height * header_zone_pct
    footer_threshold = page_height * (1.0 - footer_zone_pct)

    for block, label in zip(text_blocks, labels):
        if label == body_label:
            block.block_type = "body"
            body_blocks.append(block)
        elif block.y0 < header_threshold:
            block.block_type = "header"
            suppressed_blocks.append(block)
        elif block.y1 > footer_threshold:
            block.block_type = "footer"
            suppressed_blocks.append(block)
        else:
            # Non-body cluster that is NOT in a margin zone — keep it.
            block.block_type = "body"
            body_blocks.append(block)

    return SuppressionResult(body_blocks, suppressed_blocks, "dbscan")


def suppress_margins_static_zone(
    text_blocks: list[TextBlock],
    page_height: float,
    header_zone_pct: float = 0.05,
    footer_zone_pct: float = 0.05,
) -> SuppressionResult:
    """Fallback margin suppression using fixed page zones.

    Removes blocks whose vertical centre falls in the top or bottom *N %*
    of the page.

    Args:
        text_blocks: Detected text blocks for one page.
        page_height: Total page height (same units as block coordinates).
        header_zone_pct: Fraction of page height treated as the header zone.
        footer_zone_pct: Fraction of page height treated as the footer zone.

    Returns:
        A :class:`SuppressionResult` with body and suppressed blocks.
    """
    header_threshold = page_height * header_zone_pct
    footer_threshold = page_height * (1.0 - footer_zone_pct)

    body_blocks: list[TextBlock] = []
    suppressed_blocks: list[TextBlock] = []

    for block in text_blocks:
        y_center = (block.y0 + block.y1) / 2
        if y_center < header_threshold:
            block.block_type = "header"
            suppressed_blocks.append(block)
        elif y_center > footer_threshold:
            block.block_type = "footer"
            suppressed_blocks.append(block)
        else:
            block.block_type = "body"
            body_blocks.append(block)

    return SuppressionResult(body_blocks, suppressed_blocks, "static_zone")
