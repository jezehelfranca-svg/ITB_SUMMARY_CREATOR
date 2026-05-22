"""OpenCV-based image preprocessing for degraded scans.

Provides bilateral filtering, adaptive thresholding, and deskew correction
to prepare page images for downstream OCR engines.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class PreprocessResult:
    """Result container for a single page-image preprocessing pass.

    Attributes:
        image: The processed grayscale (or binary) image.
        skew_angle: Detected skew angle in degrees (0.0 if not measured).
        was_deskewed: Whether deskew correction was actually applied.
        was_denoised: Whether noise filtering was actually applied.
    """

    image: np.ndarray
    skew_angle: float
    was_deskewed: bool
    was_denoised: bool


def preprocess_page_image(
    image: np.ndarray,
    *,
    deskew: bool = True,
    denoise: bool = True,
    binarize: bool = True,
) -> PreprocessResult:
    """Preprocess a page image for OCR.

    The pipeline applies, in order:

    1. **Bilateral filtering** – reduces noise while preserving text edges.
    2. **Adaptive thresholding** – produces a clean binary black-/white image.
    3. **Deskew correction** – detects skew via ``cv2.minAreaRect`` on
       foreground coordinates and rotates the image to compensate.

    Each step can be individually toggled via keyword arguments.

    Args:
        image: Input image as a NumPy array (BGR or grayscale).
        deskew: Whether to apply deskew correction.
        denoise: Whether to apply bilateral noise filtering.
        binarize: Whether to apply adaptive Gaussian thresholding.

    Returns:
        A :class:`PreprocessResult` containing the processed image and
        metadata describing which corrections were applied.
    """
    result_img = image.copy()
    skew_angle: float = 0.0
    was_deskewed: bool = False
    was_denoised: bool = False

    # Convert to grayscale if the input is a colour image.
    if len(result_img.shape) == 3:
        result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2GRAY)

    # Step 1 — Bilateral filtering.
    if denoise:
        result_img = cv2.bilateralFilter(result_img, 9, 75, 75)
        was_denoised = True

    # Step 2 — Adaptive thresholding.
    if binarize:
        result_img = cv2.adaptiveThreshold(
            result_img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )

    # Step 3 — Deskew via minimum-area bounding rectangle.
    if deskew:
        coords = np.column_stack(np.where(result_img > 0))
        if len(coords) > 100:  # Need enough foreground points.
            angle: float = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 0.5:  # Only correct significant skew.
                h, w = result_img.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                result_img = cv2.warpAffine(
                    result_img,
                    rotation_matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
                skew_angle = angle
                was_deskewed = True

    return PreprocessResult(
        image=result_img,
        skew_angle=skew_angle,
        was_deskewed=was_deskewed,
        was_denoised=was_denoised,
    )
