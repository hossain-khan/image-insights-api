"""Application configuration settings."""

import os
from dataclasses import dataclass


def _get_logging_config() -> bool:
    """Get logging configuration from environment variable."""
    return os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true"


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

    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_MAX_SIZE: int = 128  # Maximum number of cached results (LRU eviction)
    CACHE_TTL_SECONDS: int = 3600  # Time-to-live for cache entries (1 hour)

    # Logging
    ENABLE_DETAILED_LOGGING: bool = _get_logging_config()


settings = Settings()
