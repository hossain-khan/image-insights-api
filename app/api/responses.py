"""Response models for image analysis API with OpenAPI examples."""

from pydantic import BaseModel, Field


class HistogramBucket(BaseModel):
    """A single bucket in the brightness histogram."""

    range: str = Field(..., description="Luminance range (e.g., '0-24')")
    percent: float = Field(..., description="Percentage of pixels in this range")


class BrightnessAnalysisResponse(BaseModel):
    """Response for brightness analysis of an image."""

    brightness_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Brightness score from 0 (black) to 100 (white)",
    )
    average_luminance: float = Field(
        ..., ge=0, le=255, description="Average luminance value (0-255)"
    )
    width: int = Field(..., description="Original image width in pixels")
    height: int = Field(..., description="Original image height in pixels")
    algorithm: str = Field(..., description="Algorithm used for luminance calculation")
    processing_time_ms: float = Field(
        ..., description="Time taken to process the image in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brightness_score": 57,
                "average_luminance": 146.28,
                "width": 536,
                "height": 354,
                "algorithm": "rec709",
                "processing_time_ms": 45.23,
            }
        }


class MedianAnalysisResponse(BrightnessAnalysisResponse):
    """Response including median luminance."""

    median_luminance: float = Field(
        ..., ge=0, le=255, description="Median luminance value (0-255)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brightness_score": 57,
                "average_luminance": 146.28,
                "median_luminance": 165.88,
                "width": 536,
                "height": 354,
                "algorithm": "rec709",
                "processing_time_ms": 48.5,
            }
        }


class HistogramAnalysisResponse(MedianAnalysisResponse):
    """Response including histogram distribution."""

    histogram: list[HistogramBucket] = Field(
        ..., description="Distribution of luminance values across 10 buckets"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brightness_score": 57,
                "average_luminance": 146.28,
                "median_luminance": 165.88,
                "histogram": [
                    {"range": "0-24", "percent": 0.2},
                    {"range": "25-50", "percent": 13.1},
                    {"range": "51-75", "percent": 15.6},
                    {"range": "76-101", "percent": 3.0},
                    {"range": "102-127", "percent": 3.3},
                    {"range": "128-152", "percent": 11.5},
                    {"range": "153-178", "percent": 11.9},
                    {"range": "179-203", "percent": 24.8},
                    {"range": "204-229", "percent": 15.5},
                    {"range": "230-255", "percent": 4.5},
                ],
                "width": 536,
                "height": 354,
                "algorithm": "rec709",
                "processing_time_ms": 50.1,
            }
        }


class EdgeAnalysisResponse(BrightnessAnalysisResponse):
    """Response including edge-based brightness analysis."""

    edge_brightness_score: int = Field(
        ..., ge=0, le=100, description="Brightness score (0-100) for the specified edges"
    )
    edge_average_luminance: float = Field(
        ..., ge=0, le=255, description="Average luminance value (0-255) for the specified edges"
    )
    edge_mode: str = Field(
        ..., description="Edge mode used (left_right, top_bottom, or all)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "brightness_score": 57,
                "average_luminance": 146.28,
                "edge_brightness_score": 51,
                "edge_average_luminance": 130.18,
                "edge_mode": "all",
                "width": 536,
                "height": 354,
                "algorithm": "rec709",
                "processing_time_ms": 52.3,
            }
        }


class FullAnalysisResponse(HistogramAnalysisResponse, EdgeAnalysisResponse):
    """Response with all metrics and edge analysis."""

    class Config:
        json_schema_extra = {
            "example": {
                "brightness_score": 57,
                "average_luminance": 146.28,
                "median_luminance": 165.88,
                "histogram": [
                    {"range": "0-24", "percent": 0.2},
                    {"range": "25-50", "percent": 13.1},
                    {"range": "51-75", "percent": 15.6},
                    {"range": "76-101", "percent": 3.0},
                    {"range": "102-127", "percent": 3.3},
                    {"range": "128-152", "percent": 11.5},
                    {"range": "153-178", "percent": 11.9},
                    {"range": "179-203", "percent": 24.8},
                    {"range": "204-229", "percent": 15.5},
                    {"range": "230-255", "percent": 4.5},
                ],
                "edge_brightness_score": 51,
                "edge_average_luminance": 130.18,
                "edge_mode": "all",
                "width": 536,
                "height": 354,
                "algorithm": "rec709",
                "processing_time_ms": 61.06,
            }
        }
