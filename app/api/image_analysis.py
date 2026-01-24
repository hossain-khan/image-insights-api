"""Image analysis API endpoint.

Privacy-First Design:
- Images are processed in-memory only, never stored on disk or database
- Image data is immediately discarded after analysis completes
- No user tracking, sessions, or request history
- All processing is stateless and isolated per request
"""

import io
import logging
import time
from typing import Annotated, Any
from urllib.parse import urlparse

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image
from pydantic import BaseModel, Field

from app.config import settings
from app.core import (
    calculate_average_luminance,
    calculate_brightness_score,
    calculate_edge_luminance,
    calculate_histogram,
    calculate_luminance,
    calculate_median_luminance,
    resize_image_if_needed,
    validate_and_download_from_url,
    validate_edge_mode,
    validate_image_upload,
    validate_metrics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/image", tags=["image-analysis"])


def _redact_url_for_logging(url: str) -> str:
    """
    Redact sensitive information from URL for safe logging.

    Removes query parameters and userinfo to prevent leaking credentials or tokens.

    Args:
        url: The URL to redact

    Returns:
        Redacted URL with only scheme, hostname, and path
    """
    try:
        parsed = urlparse(url)
        # Keep only scheme, hostname, and path
        redacted = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return redacted
    except Exception:
        return "[invalid-url]"


class ImageUrlRequest(BaseModel):
    """Request model for URL-based image analysis."""

    url: str = Field(..., description="URL of the image to analyze (JPEG or PNG)")
    metrics: str | None = Field(
        None, description="Comma-separated metrics: brightness, median, histogram"
    )
    edge_mode: str | None = Field(
        None,
        description="Edge-based brightness mode: left_right, top_bottom, or all (analyzes 10% of edges)",
    )


def _process_image_bytes(
    contents: bytes,
    requested_metrics: set[str],
    validated_edge_mode: str | None,
) -> dict[str, Any]:
    """
    Process image bytes and return analysis results.

    **Privacy-First Processing:**
    - Image data exists only in-memory during this function execution
    - No disk writes, database storage, or external uploads
    - All image data is discarded when function returns (garbage collected)
    - Only aggregate metrics are returned, never pixel data

    Args:
        contents: Raw image bytes (immediately discarded after analysis)
        requested_metrics: Set of metrics to calculate
        validated_edge_mode: Validated edge mode (if any)

    Returns:
        Dictionary with analysis results (no image data included)
    """
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

    # Edge-based brightness if requested
    if validated_edge_mode:
        edge_luminance_values = calculate_edge_luminance(luminance, validated_edge_mode)
        edge_avg_luminance = float(edge_luminance_values.mean())
        response["edge_brightness_score"] = calculate_brightness_score(edge_avg_luminance)
        response["edge_average_luminance"] = round(edge_avg_luminance, 2)
        response["edge_mode"] = validated_edge_mode

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

    return response


@router.post(
    "/analysis",
    summary="Analyze Image Brightness",
    response_description="Image analysis results with brightness metrics",
)
async def analyze_image(
    image: Annotated[UploadFile, File(description="JPEG or PNG image to analyze")],
    metrics: Annotated[
        str | None,
        Query(description="Comma-separated metrics: brightness, median, histogram"),
    ] = None,
    edge_mode: Annotated[
        str | None,
        Query(
            description="Edge-based brightness mode: left_right, top_bottom, or all (analyzes 10% of edges)"
        ),
    ] = None,
) -> dict[str, Any]:
    """
    Analyze an uploaded image and return requested metrics.

    **Metrics:**
    - `brightness`: Brightness score (0-100), average luminance
    - `median`: Median luminance value
    - `histogram`: Distribution of luminance values in 10 buckets

    **Edge Mode:**
    - `left_right`: Analyze brightness of left and right edges (10% each)
    - `top_bottom`: Analyze brightness of top and bottom edges (10% each)
    - `all`: Analyze brightness of all four edges (10% each)

    Edge mode is useful for determining background colors that blend well with image edges.

    **Algorithm:** Rec. 709 perceptual luminance formula

    Returns deterministic results for the same input image.
    """
    start_time = time.time()

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(
            f"Image analysis request started - File: {image.filename}, "
            f"Metrics: {metrics}, Edge mode: {edge_mode}"
        )

    # Validate metrics parameter
    requested_metrics = validate_metrics(metrics)

    # Validate edge_mode parameter
    validated_edge_mode = validate_edge_mode(edge_mode)

    # Validate and read image
    contents = await validate_image_upload(image)
    file_size_mb = len(contents) / (1024 * 1024)

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(
            f"File validated - Size: {file_size_mb:.2f}MB, Content-Type: {image.content_type}"
        )

    # Process image and get results
    response = _process_image_bytes(contents, requested_metrics, validated_edge_mode)

    # Calculate and add processing time
    elapsed_time = time.time() - start_time
    processing_time_ms = round(elapsed_time * 1000, 2)
    response["processing_time_ms"] = processing_time_ms

    if settings.ENABLE_DETAILED_LOGGING:
        metrics_used = ", ".join(requested_metrics)
        edge_info = f", Edge mode: {validated_edge_mode}" if validated_edge_mode else ""
        logger.info(
            f"Image analysis completed - Metrics: {metrics_used}{edge_info}, "
            f"Duration: {processing_time_ms}ms, "
            f"Dimensions: {response['width']}x{response['height']}, "
            f"Algorithm: {settings.LUMINANCE_ALGORITHM}"
        )

    return response


@router.post(
    "/analysis/url",
    summary="Analyze Image from URL",
    response_description="Image analysis results with brightness metrics",
)
async def analyze_image_from_url(request: ImageUrlRequest) -> dict[str, Any]:
    """
    Analyze an image from a URL and return requested metrics.

    **Metrics:**
    - `brightness`: Brightness score (0-100), average luminance
    - `median`: Median luminance value
    - `histogram`: Distribution of luminance values in 10 buckets

    **Edge Mode:**
    - `left_right`: Analyze brightness of left and right edges (10% each)
    - `top_bottom`: Analyze brightness of top and bottom edges (10% each)
    - `all`: Analyze brightness of all four edges (10% each)

    Edge mode is useful for determining background colors that blend well with image edges.

    **Algorithm:** Rec. 709 perceptual luminance formula

    Returns deterministic results for the same input image.
    """
    start_time = time.time()

    # Redact URL for safe logging
    redacted_url = _redact_url_for_logging(request.url)

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(
            f"Image analysis request started - URL: {redacted_url}, "
            f"Metrics: {request.metrics}, Edge mode: {request.edge_mode}"
        )

    # Validate metrics parameter
    requested_metrics = validate_metrics(request.metrics)

    # Validate edge_mode parameter
    validated_edge_mode = validate_edge_mode(request.edge_mode)

    # Download and validate image from URL
    contents = await validate_and_download_from_url(request.url)
    file_size_mb = len(contents) / (1024 * 1024)

    if settings.ENABLE_DETAILED_LOGGING:
        logger.info(f"Image downloaded - Size: {file_size_mb:.2f}MB, URL: {redacted_url}")

    # Process image and get results
    response = _process_image_bytes(contents, requested_metrics, validated_edge_mode)

    # Calculate and add processing time
    elapsed_time = time.time() - start_time
    processing_time_ms = round(elapsed_time * 1000, 2)
    response["processing_time_ms"] = processing_time_ms

    if settings.ENABLE_DETAILED_LOGGING:
        metrics_used = ", ".join(requested_metrics)
        edge_info = f", Edge mode: {validated_edge_mode}" if validated_edge_mode else ""
        logger.info(
            f"Image analysis completed - Metrics: {metrics_used}{edge_info}, "
            f"Duration: {processing_time_ms}ms, "
            f"Dimensions: {response['width']}x{response['height']}, "
            f"Algorithm: {settings.LUMINANCE_ALGORITHM}"
        )

    return response
