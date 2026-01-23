"""Tests for core modules."""

import numpy as np
from PIL import Image

from app.config import settings
from app.core.histogram import calculate_histogram
from app.core.luminance import (
    calculate_average_luminance,
    calculate_brightness_score,
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
