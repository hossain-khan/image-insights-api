"""Application configuration settings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings with production-safe defaults."""
    
    # Image processing
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    MAX_DIMENSION: int = 512  # Max width or height in pixels
    ALLOWED_CONTENT_TYPES: tuple = ("image/jpeg", "image/png")
    
    # Processing
    REQUEST_TIMEOUT: float = 2.0  # seconds
    
    # Luminance algorithm
    LUMINANCE_ALGORITHM: str = "rec709"
    
    # Rec. 709 coefficients
    REC709_R: float = 0.2126
    REC709_G: float = 0.7152
    REC709_B: float = 0.0722
    
    # Histogram settings
    HISTOGRAM_BUCKETS: int = 10
    LUMINANCE_MAX: int = 255


settings = Settings()
