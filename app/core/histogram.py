"""Histogram calculation utilities."""

from typing import TypedDict

import numpy as np
from numpy.typing import NDArray

from app.config import settings


class HistogramBucket(TypedDict):
    """Type definition for histogram bucket."""
    range: str
    percent: float


def calculate_histogram(luminance: NDArray[np.float64]) -> list[HistogramBucket]:
    """
    Calculate histogram buckets for luminance distribution.
    
    Divides luminance values into equal-sized buckets and returns
    the percentage of pixels in each bucket.
    
    Args:
        luminance: 2D array of luminance values (0-255)
        
    Returns:
        List of histogram buckets with range and percentage
    """
    num_buckets = settings.HISTOGRAM_BUCKETS
    max_val = settings.LUMINANCE_MAX
    
    # Calculate bucket edges
    bucket_size = (max_val + 1) / num_buckets
    
    # Flatten the array for histogram calculation
    flat_luminance = luminance.flatten()
    total_pixels = len(flat_luminance)
    
    if total_pixels == 0:
        return []
    
    histogram: list[HistogramBucket] = []
    
    for i in range(num_buckets):
        start = int(i * bucket_size)
        end = int((i + 1) * bucket_size) - 1
        
        # For the last bucket, include the max value
        if i == num_buckets - 1:
            end = max_val
            count = np.sum((flat_luminance >= start) & (flat_luminance <= end))
        else:
            count = np.sum((flat_luminance >= start) & (flat_luminance < (i + 1) * bucket_size))
        
        percent = round((count / total_pixels) * 100, 1)
        
        histogram.append({
            "range": f"{start}-{end}",
            "percent": percent
        })
    
    return histogram
