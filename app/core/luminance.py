"""Luminance calculation utilities using Rec. 709 standard."""

import numpy as np
from numpy.typing import NDArray

from app.config import settings


def calculate_luminance(rgb_array: NDArray[np.uint8]) -> NDArray[np.float64]:
    """
    Calculate perceptual luminance using Rec. 709 coefficients.

    Args:
        rgb_array: NumPy array of shape (height, width, 3) with RGB values

    Returns:
        2D array of luminance values (0-255 range)
    """
    return (
        settings.REC709_R * rgb_array[:, :, 0].astype(np.float64)
        + settings.REC709_G * rgb_array[:, :, 1].astype(np.float64)
        + settings.REC709_B * rgb_array[:, :, 2].astype(np.float64)
    )


def calculate_average_luminance(luminance: NDArray[np.float64]) -> float:
    """
    Calculate average luminance.

    Args:
        luminance: 2D array of luminance values

    Returns:
        Average luminance value
    """
    return float(luminance.mean())


def calculate_median_luminance(luminance: NDArray[np.float64]) -> float:
    """
    Calculate median luminance.

    Args:
        luminance: 2D array of luminance values

    Returns:
        Median luminance value
    """
    return float(np.median(luminance))


def calculate_brightness_score(average_luminance: float) -> int:
    """
    Convert average luminance to brightness score (0-100).

    Args:
        average_luminance: Average luminance value (0-255)

    Returns:
        Brightness score (0=black, 100=white)
    """
    normalized = average_luminance / settings.LUMINANCE_MAX
    return round(normalized * 100)


def calculate_edge_luminance(
    luminance: NDArray[np.float64], edge_mode: str = "left_right"
) -> NDArray[np.float64]:
    """
    Extract edge regions from luminance array based on edge mode.

    Extracts 10% of the image from specified edges for brightness analysis.
    This is useful for determining background colors that blend well with image edges.

    Args:
        luminance: 2D array of luminance values (height, width)
        edge_mode: Which edges to extract ("left_right", "top_bottom", or "all")

    Returns:
        1D array of luminance values from the specified edges

    Raises:
        ValueError: If edge_mode is not valid
    """
    height, width = luminance.shape
    edge_pixels = []

    # Calculate 10% width and height for edge extraction
    edge_width = max(1, int(width * 0.1))
    edge_height = max(1, int(height * 0.1))

    if edge_mode == "left_right":
        # Left edge (10% from left)
        left_edge = luminance[:, :edge_width]
        edge_pixels.append(left_edge.flatten())

        # Right edge (10% from right)
        right_edge = luminance[:, -edge_width:]
        edge_pixels.append(right_edge.flatten())

    elif edge_mode == "top_bottom":
        # Top edge (10% from top)
        top_edge = luminance[:edge_height, :]
        edge_pixels.append(top_edge.flatten())

        # Bottom edge (10% from bottom)
        bottom_edge = luminance[-edge_height:, :]
        edge_pixels.append(bottom_edge.flatten())

    elif edge_mode == "all":
        # All four edges
        # Left edge
        left_edge = luminance[:, :edge_width]
        edge_pixels.append(left_edge.flatten())

        # Right edge
        right_edge = luminance[:, -edge_width:]
        edge_pixels.append(right_edge.flatten())

        # Top edge (excluding corners already counted)
        top_edge = luminance[:edge_height, edge_width:-edge_width]
        edge_pixels.append(top_edge.flatten())

        # Bottom edge (excluding corners already counted)
        bottom_edge = luminance[-edge_height:, edge_width:-edge_width]
        edge_pixels.append(bottom_edge.flatten())

    else:
        raise ValueError(
            f"Invalid edge_mode '{edge_mode}'. Must be 'left_right', 'top_bottom', or 'all'"
        )

    # Concatenate all edge pixels
    return np.concatenate(edge_pixels)
