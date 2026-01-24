"""Pytest configuration and fixtures."""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

# Path to test fixtures
TEST_FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_IMAGES_DIR = Path(__file__).parent


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def create_test_image():
    """Factory fixture to create test images with specific colors."""

    def _create_image(
        color: tuple[int, int, int] = (128, 128, 128),
        size: tuple[int, int] = (100, 100),
        format: str = "PNG",
    ) -> io.BytesIO:
        """
        Create a test image.

        Args:
            color: RGB tuple (0-255)
            size: (width, height)
            format: Image format (PNG, JPEG)

        Returns:
            BytesIO buffer with the image
        """
        img = Image.new("RGB", size, color)
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer

    return _create_image


@pytest.fixture
def black_image(create_test_image):
    """Create a pure black image."""
    return create_test_image(color=(0, 0, 0))


@pytest.fixture
def white_image(create_test_image):
    """Create a pure white image."""
    return create_test_image(color=(255, 255, 255))


@pytest.fixture
def gray_image(create_test_image):
    """Create a mid-gray image."""
    return create_test_image(color=(128, 128, 128))


@pytest.fixture
def large_image(create_test_image):
    """Create a large image that needs resizing."""
    return create_test_image(size=(2000, 1500))


@pytest.fixture
def jpeg_image(create_test_image):
    """Create a JPEG image."""
    return create_test_image(format="JPEG")


@pytest.fixture
def sample_color_image():
    """Load the sample color image (sample2-536x354.jpg)."""
    image_path = SAMPLE_IMAGES_DIR / "sample2-536x354.jpg"
    if not image_path.exists():
        pytest.skip(f"Sample image not found: {image_path}")
    with open(image_path, "rb") as f:
        return io.BytesIO(f.read())


@pytest.fixture
def sample_grayscale_image():
    """Load the sample grayscale image (sample1-536x354-grayscale.jpg)."""
    image_path = SAMPLE_IMAGES_DIR / "sample1-536x354-grayscale.jpg"
    if not image_path.exists():
        pytest.skip(f"Sample image not found: {image_path}")
    with open(image_path, "rb") as f:
        return io.BytesIO(f.read())
