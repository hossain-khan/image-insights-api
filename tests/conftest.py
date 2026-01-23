"""Pytest configuration and fixtures."""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


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
        format: str = "PNG"
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
