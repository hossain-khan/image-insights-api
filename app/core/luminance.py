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
        settings.REC709_R * rgb_array[:, :, 0].astype(np.float64) +
        settings.REC709_G * rgb_array[:, :, 1].astype(np.float64) +
        settings.REC709_B * rgb_array[:, :, 2].astype(np.float64)
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
