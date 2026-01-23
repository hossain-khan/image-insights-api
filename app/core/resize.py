"""Image resizing utilities."""

from PIL import Image

from app.config import settings


def resize_image_if_needed(img: Image.Image) -> Image.Image:
    """
    Resize image if it exceeds maximum dimensions.

    Preserves aspect ratio using high-quality LANCZOS resampling.

    Args:
        img: PIL Image object

    Returns:
        Resized image (or original if within bounds)
    """
    max_dim = settings.MAX_DIMENSION
    width, height = img.size

    # Check if resizing is needed
    if width <= max_dim and height <= max_dim:
        return img

    # Calculate new dimensions preserving aspect ratio
    if width > height:
        new_width = max_dim
        new_height = int(height * (max_dim / width))
    else:
        new_height = max_dim
        new_width = int(width * (max_dim / height))

    # Ensure minimum dimension of 1 pixel
    new_width = max(1, new_width)
    new_height = max(1, new_height)

    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
