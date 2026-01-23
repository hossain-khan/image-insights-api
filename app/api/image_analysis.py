"""Image analysis API endpoint."""

import io
import logging
import time
from typing import Annotated, Any

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image

from app.config import settings
from app.core import (
    calculate_average_luminance,
    calculate_brightness_score,
    calculate_histogram,
    calculate_luminance,
    calculate_median_luminance,
    resize_image_if_needed,
    validate_image_upload,
    validate_metrics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/image", tags=["image-analysis"])


@router.post("/analysis")
async def analyze_image(
    image: Annotated[UploadFile, File(description="JPEG or PNG image to analyze")],
    metrics: Annotated[
        str | None,
        Query(description="Comma-separated metrics: brightness, median, histogram"),
    ] = None,
) -> dict[str, Any]:
    """
    Analyze an image and return requested metrics.

    **Metrics:**
    - `brightness`: Brightness score (0-100), average luminance
    - `median`: Median luminance value
    - `histogram`: Distribution of luminance values in 10 buckets

    **Algorithm:** Rec. 709 perceptual luminance formula

    Returns deterministic results for the same input image.
    """
    start_time = time.time()

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(f"Image analysis request started - File: {image.filename}, Metrics: {metrics}")

    # Validate metrics parameter
    requested_metrics = validate_metrics(metrics)

    # Validate and read image
    contents = await validate_image_upload(image)
    file_size_mb = len(contents) / (1024 * 1024)

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(f"File validated - Size: {file_size_mb:.2f}MB, Content-Type: {image.content_type}")

    # Parse image
    try:
        img = Image.open(io.BytesIO(contents))

        # Convert to RGB (handles RGBA, grayscale, etc.)
        img = img.convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid or corrupted image file", "details": str(e)},
        ) from e

    # Store original dimensions
    original_width, original_height = img.size

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(f"Image loaded - Original dimensions: {original_width}x{original_height}")

    # Resize if needed for performance
    img = resize_image_if_needed(img)

    if img.size != (original_width, original_height) and settings.ENABLE_DETAILED_LOGGING:
        logger.info(f"Image resized - New dimensions: {img.size[0]}x{img.size[1]}")

    # Convert to numpy array
    rgb_array = np.array(img)

    # Calculate luminance
    luminance = calculate_luminance(rgb_array)

    # Build response with requested metrics
    response: dict[str, Any] = {}

    # Brightness is always included with brightness metric
    if "brightness" in requested_metrics:
        avg_luminance = calculate_average_luminance(luminance)
        response["brightness_score"] = calculate_brightness_score(avg_luminance)
        response["average_luminance"] = round(avg_luminance, 2)

    # Median luminance
    if "median" in requested_metrics:
        response["median_luminance"] = round(calculate_median_luminance(luminance), 2)

    # Histogram
    if "histogram" in requested_metrics:
        response["histogram"] = calculate_histogram(luminance)

    # Always include metadata
    response["width"] = original_width
    response["height"] = original_height
    response["algorithm"] = settings.LUMINANCE_ALGORITHM

    # Log completion with timing
    elapsed_time = time.time() - start_time
    if settings.ENABLE_DETAILED_LOGGING:
        metrics_used = ", ".join(requested_metrics)
        logger.info(
            f"Image analysis completed - Metrics: {metrics_used}, "
            f"Duration: {elapsed_time*1000:.2f}ms, "
            f"Dimensions: {original_width}x{original_height}, "
            f"Algorithm: {settings.LUMINANCE_ALGORITHM}"
        )

    return response
