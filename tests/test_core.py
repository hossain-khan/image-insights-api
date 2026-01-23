"""Tests for core modules."""

import numpy as np
import pytest
from PIL import Image

from app.config import settings
from app.core.histogram import calculate_histogram
from app.core.luminance import (
    calculate_average_luminance,
    calculate_brightness_score,
    calculate_edge_luminance,
    calculate_luminance,
    calculate_median_luminance,
)
from app.core.resize import resize_image_if_needed


class TestLuminance:
    """Test luminance calculation functions."""

    def test_calculate_luminance_black(self):
        """Test luminance of black pixels is 0."""
        black = np.zeros((10, 10, 3), dtype=np.uint8)
        luminance = calculate_luminance(black)
        assert luminance.shape == (10, 10)
        assert np.all(luminance == 0)

    def test_calculate_luminance_white(self):
        """Test luminance of white pixels is 255."""
        white = np.ones((10, 10, 3), dtype=np.uint8) * 255
        luminance = calculate_luminance(white)
        assert np.allclose(luminance, 255.0)

    def test_calculate_luminance_rec709(self):
        """Test Rec. 709 coefficients are correctly applied."""
        # Create array with known values
        arr = np.zeros((1, 1, 3), dtype=np.uint8)
        arr[0, 0] = [100, 150, 50]  # R, G, B

        luminance = calculate_luminance(arr)

        # Expected: 0.2126*100 + 0.7152*150 + 0.0722*50 = 21.26 + 107.28 + 3.61 = 132.15
        expected = 0.2126 * 100 + 0.7152 * 150 + 0.0722 * 50
        assert abs(luminance[0, 0] - expected) < 0.01

    def test_calculate_average_luminance(self):
        """Test average luminance calculation."""
        luminance = np.array([[100, 200], [150, 150]], dtype=np.float64)
        avg = calculate_average_luminance(luminance)
        assert avg == 150.0

    def test_calculate_median_luminance(self):
        """Test median luminance calculation."""
        luminance = np.array([[10, 20], [30, 100]], dtype=np.float64)
        median = calculate_median_luminance(luminance)
        # Sorted: 10, 20, 30, 100 -> median = (20 + 30) / 2 = 25
        assert median == 25.0

    def test_calculate_brightness_score_black(self):
        """Test brightness score for black is 0."""
        assert calculate_brightness_score(0.0) == 0

    def test_calculate_brightness_score_white(self):
        """Test brightness score for white is 100."""
        assert calculate_brightness_score(255.0) == 100

    def test_calculate_brightness_score_mid(self):
        """Test brightness score for mid-gray."""
        # 127.5 / 255 * 100 = 50
        assert calculate_brightness_score(127.5) == 50


class TestResize:
    """Test image resizing functions."""

    def test_no_resize_needed(self):
        """Test that small images are not resized."""
        img = Image.new("RGB", (100, 100))
        result = resize_image_if_needed(img)
        assert result.size == (100, 100)

    def test_resize_wide_image(self):
        """Test resizing a wide image."""
        img = Image.new("RGB", (1000, 500))
        result = resize_image_if_needed(img)
        assert result.width == settings.MAX_DIMENSION
        assert result.height == 256  # Aspect ratio preserved

    def test_resize_tall_image(self):
        """Test resizing a tall image."""
        img = Image.new("RGB", (500, 1000))
        result = resize_image_if_needed(img)
        assert result.width == 256
        assert result.height == settings.MAX_DIMENSION

    def test_resize_preserves_aspect_ratio(self):
        """Test that aspect ratio is preserved."""
        img = Image.new("RGB", (800, 600))
        result = resize_image_if_needed(img)

        original_ratio = 800 / 600
        result_ratio = result.width / result.height

        assert abs(original_ratio - result_ratio) < 0.01

    def test_exact_boundary(self):
        """Test image at exact MAX_DIMENSION boundary."""
        img = Image.new("RGB", (512, 512))
        result = resize_image_if_needed(img)
        assert result.size == (512, 512)


class TestHistogram:
    """Test histogram calculation functions."""

    def test_histogram_bucket_count(self):
        """Test histogram returns correct number of buckets."""
        luminance = np.random.uniform(0, 255, (100, 100))
        histogram = calculate_histogram(luminance)
        assert len(histogram) == settings.HISTOGRAM_BUCKETS

    def test_histogram_percentages_sum_to_100(self):
        """Test histogram percentages sum to approximately 100."""
        luminance = np.random.uniform(0, 255, (100, 100))
        histogram = calculate_histogram(luminance)
        total = sum(bucket["percent"] for bucket in histogram)
        assert abs(total - 100.0) < 2.0  # Allow for rounding across 10 buckets

    def test_histogram_uniform_distribution(self):
        """Test histogram of uniformly distributed values."""
        # Create values evenly distributed across range
        values = np.linspace(0, 255, 10000).reshape(100, 100)
        histogram = calculate_histogram(values)

        # Each bucket should have roughly 10%
        for bucket in histogram:
            assert 5 <= bucket["percent"] <= 15

    def test_histogram_concentrated(self):
        """Test histogram with concentrated values."""
        # All values in middle range
        luminance = np.full((100, 100), 128.0)
        histogram = calculate_histogram(luminance)

        # Find the bucket containing 128
        for bucket in histogram:
            start, end = bucket["range"].split("-")
            if int(start) <= 128 <= int(end):
                assert bucket["percent"] == 100.0
                break

    def test_histogram_bucket_ranges(self):
        """Test histogram bucket ranges are correct."""
        luminance = np.zeros((10, 10))
        histogram = calculate_histogram(luminance)

        # First bucket should start at 0
        assert histogram[0]["range"].startswith("0-")
        # Last bucket should end at 255
        assert histogram[-1]["range"].endswith("255")

    def test_histogram_empty_image(self):
        """Test histogram handles empty arrays gracefully."""
        luminance = np.array([]).reshape(0, 0)
        histogram = calculate_histogram(luminance)
        assert histogram == []


class TestEdgeLuminance:
    """Test edge-based luminance calculation functions."""

    def test_edge_luminance_left_right(self):
        """Test left and right edge extraction."""
        # Create a 100x100 image where left is dark (0) and right is bright (255)
        luminance = np.zeros((100, 100), dtype=np.float64)
        luminance[:, 50:] = 255.0

        edge_values = calculate_edge_luminance(luminance, "left_right")

        # Should extract 10 pixels from left (all 0) and 10 from right (all 255)
        # Left edge: 100 rows * 10 cols = 1000 pixels of value 0
        # Right edge: 100 rows * 10 cols = 1000 pixels of value 255
        # Average should be around 127.5
        avg = edge_values.mean()
        assert 120 < avg < 135

    def test_edge_luminance_top_bottom(self):
        """Test top and bottom edge extraction."""
        # Create a 100x100 image where top is dark (0) and bottom is bright (255)
        luminance = np.zeros((100, 100), dtype=np.float64)
        luminance[50:, :] = 255.0

        edge_values = calculate_edge_luminance(luminance, "top_bottom")

        # Should extract 10 rows from top and 10 from bottom
        avg = edge_values.mean()
        assert 120 < avg < 135

    def test_edge_luminance_all(self):
        """Test all edges extraction."""
        # Create a 100x100 image with bright edges
        luminance = np.zeros((100, 100), dtype=np.float64)
        # Top edge
        luminance[:10, :] = 255.0
        # Bottom edge
        luminance[-10:, :] = 255.0
        # Left edge
        luminance[:, :10] = 255.0
        # Right edge
        luminance[:, -10:] = 255.0

        edge_values = calculate_edge_luminance(luminance, "all")

        # All edge pixels should be bright
        avg = edge_values.mean()
        assert avg == 255.0

    def test_edge_luminance_invalid_mode(self):
        """Test invalid edge mode raises ValueError."""
        luminance = np.zeros((100, 100), dtype=np.float64)

        with pytest.raises(ValueError):
            calculate_edge_luminance(luminance, "invalid_mode")

    def test_edge_luminance_small_image(self):
        """Test edge extraction on very small images."""
        # 10x10 image - 10% would be 1 pixel
        luminance = np.ones((10, 10), dtype=np.float64) * 128.0

        edge_values = calculate_edge_luminance(luminance, "left_right")

        # Should still work with 1 pixel width
        assert len(edge_values) > 0
        assert edge_values.mean() == 128.0

    def test_edge_luminance_uniform_image(self):
        """Test edge extraction on uniform image."""
        # All pixels same value
        luminance = np.full((100, 100), 200.0, dtype=np.float64)

        for mode in ["left_right", "top_bottom", "all"]:
            edge_values = calculate_edge_luminance(luminance, mode)
            assert edge_values.mean() == 200.0

    def test_edge_luminance_percentage_extraction(self):
        """Test that exactly 10% of width/height is extracted."""
        # 200x100 image
        luminance = np.zeros((100, 200), dtype=np.float64)

        # Left/right mode: should extract 20 pixels width (10% of 200)
        edge_values = calculate_edge_luminance(luminance, "left_right")
        # Left: 100 rows * 20 cols = 2000
        # Right: 100 rows * 20 cols = 2000
        # Total: 4000 pixels
        assert len(edge_values) == 4000

        # Top/bottom mode: should extract 10 pixels height (10% of 100)
        edge_values = calculate_edge_luminance(luminance, "top_bottom")
        # Top: 10 rows * 200 cols = 2000
        # Bottom: 10 rows * 200 cols = 2000
        # Total: 4000 pixels
        assert len(edge_values) == 4000
