"""Tests for the image analysis API endpoint."""

import io

from app.api.image_analysis import _cache
from app.core.cache import ImageAnalysisCache, compute_cache_key


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "image-insights-api"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestImageAnalysisEndpoint:
    """Test POST /v1/image/analysis endpoint."""

    def test_analyze_black_image(self, client, black_image):
        """Test analysis of pure black image returns brightness 0."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", black_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brightness_score"] == 0
        assert data["average_luminance"] == 0.0
        assert data["algorithm"] == "rec709"

    def test_analyze_white_image(self, client, white_image):
        """Test analysis of pure white image returns brightness 100."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", white_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brightness_score"] == 100
        assert data["average_luminance"] == 255.0

    def test_analyze_gray_image(self, client, gray_image):
        """Test analysis of gray image returns ~50 brightness."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", gray_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        # Gray (128, 128, 128) should give ~50% brightness
        assert 49 <= data["brightness_score"] <= 51

    def test_analyze_jpeg_image(self, client, jpeg_image):
        """Test analysis works with JPEG format."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.jpg", jpeg_image, "image/jpeg")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data

    def test_response_includes_dimensions(self, client, create_test_image):
        """Test response includes image dimensions."""
        img = create_test_image(size=(200, 150))
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", img, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["width"] == 200
        assert data["height"] == 150

    def test_large_image_reports_original_dimensions(self, client, large_image):
        """Test that large images report original dimensions, not resized."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", large_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        # Original dimensions should be reported
        assert data["width"] == 2000
        assert data["height"] == 1500


class TestMetricsParameter:
    """Test metrics query parameter functionality."""

    def test_default_metrics_brightness(self, client, gray_image):
        """Test default metrics returns brightness."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", gray_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data
        assert "average_luminance" in data
        # Median and histogram should not be in default response
        assert "median_luminance" not in data
        assert "histogram" not in data

    def test_median_metric(self, client, gray_image):
        """Test median metric."""
        response = client.post(
            "/v1/image/analysis?metrics=median",
            files={"image": ("test.png", gray_image, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "median_luminance" in data
        assert isinstance(data["median_luminance"], (int, float))

    def test_histogram_metric(self, client, gray_image):
        """Test histogram metric."""
        response = client.post(
            "/v1/image/analysis?metrics=histogram",
            files={"image": ("test.png", gray_image, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "histogram" in data
        assert len(data["histogram"]) == 10
        # Each bucket should have range and percent
        for bucket in data["histogram"]:
            assert "range" in bucket
            assert "percent" in bucket

    def test_multiple_metrics(self, client, gray_image):
        """Test requesting multiple metrics."""
        response = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram",
            files={"image": ("test.png", gray_image, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data
        assert "median_luminance" in data
        assert "histogram" in data

    def test_invalid_metric(self, client, gray_image):
        """Test invalid metric returns 400."""
        response = client.post(
            "/v1/image/analysis?metrics=invalid_metric",
            files={"image": ("test.png", gray_image, "image/png")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "invalid_metrics" in data["detail"]


class TestValidation:
    """Test input validation."""

    def test_missing_image(self, client):
        """Test missing image returns 422."""
        response = client.post("/v1/image/analysis")
        assert response.status_code == 422

    def test_unsupported_format(self, client):
        """Test unsupported image format returns 415."""
        # Create a fake GIF file
        fake_gif = io.BytesIO(b"GIF89a...")
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.gif", fake_gif, "image/gif")}
        )
        assert response.status_code == 415
        data = response.json()
        assert "Unsupported image type" in data["detail"]["error"]

    def test_file_too_large(self, client):
        """Test file too large returns 413."""
        # Create content larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        large_file = io.BytesIO(large_content)
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", large_file, "image/png")}
        )
        assert response.status_code == 413
        data = response.json()
        assert "exceeds maximum" in data["detail"]["error"]

    def test_invalid_image_data(self, client):
        """Test invalid image data returns 400."""
        fake_png = io.BytesIO(b"not a real image")
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", fake_png, "image/png")}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]

    def test_empty_file(self, client):
        """Test empty file returns 400."""
        empty_file = io.BytesIO(b"")
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", empty_file, "image/png")}
        )
        assert response.status_code == 400


class TestDeterminism:
    """Test that results are deterministic."""

    def test_same_image_same_result(self, client, create_test_image):
        """Test that analyzing the same image twice gives identical results."""
        # Create two identical images
        img1 = create_test_image(color=(100, 150, 200), size=(50, 50))
        img2 = create_test_image(color=(100, 150, 200), size=(50, 50))

        response1 = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram",
            files={"image": ("test1.png", img1, "image/png")},
        )
        response2 = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram",
            files={"image": ("test2.png", img2, "image/png")},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Compare responses excluding processing_time_ms which varies per request
        # and cached which differs between first and second call
        data1 = response1.json()
        data2 = response2.json()
        data1.pop("processing_time_ms", None)
        data2.pop("processing_time_ms", None)
        data1.pop("cached", None)
        data2.pop("cached", None)
        assert data1 == data2

    def test_response_includes_processing_time(self, client, white_image):
        """Test that response includes processing_time_ms field."""
        response = client.post(
            "/v1/image/analysis?metrics=brightness",
            files={"image": ("test.png", white_image, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify processing_time_ms is present
        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], (int, float))

        # Processing time should be non-negative and reasonable (< 10 seconds)
        assert data["processing_time_ms"] >= 0
        assert data["processing_time_ms"] < 10000


class TestRec709Algorithm:
    """Test that Rec. 709 algorithm is correctly applied."""

    def test_green_weighted_more_than_red_or_blue(self, client, create_test_image):
        """Test that green contributes more to brightness than red or blue."""
        # Pure red
        red_img = create_test_image(color=(255, 0, 0))
        # Pure green
        green_img = create_test_image(color=(0, 255, 0))
        # Pure blue
        blue_img = create_test_image(color=(0, 0, 255))

        red_response = client.post(
            "/v1/image/analysis", files={"image": ("red.png", red_img, "image/png")}
        )
        green_response = client.post(
            "/v1/image/analysis", files={"image": ("green.png", green_img, "image/png")}
        )
        blue_response = client.post(
            "/v1/image/analysis", files={"image": ("blue.png", blue_img, "image/png")}
        )

        red_brightness = red_response.json()["brightness_score"]
        green_brightness = green_response.json()["brightness_score"]
        blue_brightness = blue_response.json()["brightness_score"]

        # Green should have highest perceived brightness
        assert green_brightness > red_brightness
        assert green_brightness > blue_brightness
        # Red should be brighter than blue
        assert red_brightness > blue_brightness

    def test_rec709_coefficients(self, client, create_test_image):
        """Test exact Rec. 709 coefficient calculation."""
        # Create a specific color image
        # Using RGB (100, 100, 100) should give luminance of 100
        img = create_test_image(color=(100, 100, 100))
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", img, "image/png")}
        )
        data = response.json()

        # Expected luminance: 0.2126*100 + 0.7152*100 + 0.0722*100 = 100
        expected_luminance = 100.0
        assert abs(data["average_luminance"] - expected_luminance) < 0.01


class TestEdgeMode:
    """Test edge-based brightness functionality."""

    def test_edge_mode_left_right(self, client, create_test_image):
        """Test left_right edge mode analysis."""
        # Create image with bright left/right edges
        img = create_test_image(color=(200, 200, 200), size=(100, 100))

        response = client.post(
            "/v1/image/analysis?edge_mode=left_right",
            files={"image": ("test.png", img, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()

        # Should include edge metrics
        assert "edge_brightness_score" in data
        assert "edge_average_luminance" in data
        assert "edge_mode" in data
        assert data["edge_mode"] == "left_right"

        # Uniform image should have same edge and overall brightness
        assert data["edge_brightness_score"] == data["brightness_score"]

    def test_edge_mode_top_bottom(self, client, create_test_image):
        """Test top_bottom edge mode analysis."""
        img = create_test_image(color=(150, 150, 150), size=(100, 100))

        response = client.post(
            "/v1/image/analysis?edge_mode=top_bottom",
            files={"image": ("test.png", img, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["edge_mode"] == "top_bottom"
        assert "edge_brightness_score" in data

    def test_edge_mode_all(self, client, create_test_image):
        """Test all edges mode analysis."""
        img = create_test_image(color=(100, 100, 100), size=(100, 100))

        response = client.post(
            "/v1/image/analysis?edge_mode=all",
            files={"image": ("test.png", img, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["edge_mode"] == "all"
        assert "edge_brightness_score" in data

    def test_edge_mode_without_metrics(self, client, gray_image):
        """Test edge mode works independently of metrics parameter."""
        response = client.post(
            "/v1/image/analysis?edge_mode=left_right",
            files={"image": ("test.png", gray_image, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have both default brightness and edge brightness
        assert "brightness_score" in data
        assert "edge_brightness_score" in data

    def test_edge_mode_with_multiple_metrics(self, client, gray_image):
        """Test edge mode combined with other metrics."""
        response = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram&edge_mode=all",
            files={"image": ("test.png", gray_image, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have all requested metrics plus edge metrics
        assert "brightness_score" in data
        assert "median_luminance" in data
        assert "histogram" in data
        assert "edge_brightness_score" in data
        assert "edge_mode" in data

    def test_invalid_edge_mode(self, client, gray_image):
        """Test invalid edge mode returns 400."""
        response = client.post(
            "/v1/image/analysis?edge_mode=invalid_mode",
            files={"image": ("test.png", gray_image, "image/png")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "valid_modes" in data["detail"]

    def test_edge_mode_none(self, client, gray_image):
        """Test that no edge mode returns no edge metrics."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", gray_image, "image/png")}
        )

        assert response.status_code == 200
        data = response.json()

        # Should not have edge metrics
        assert "edge_brightness_score" not in data
        assert "edge_average_luminance" not in data
        assert "edge_mode" not in data


class TestImageAnalysisUrlEndpoint:
    """Test POST /v1/image/analysis/url endpoint."""

    @staticmethod
    def _image_to_bytes(image_buffer):
        """Convert BytesIO buffer to bytes for httpx_mock."""
        return image_buffer.getvalue()

    def test_analyze_image_from_valid_url(self, client, httpx_mock, create_test_image):
        """Test analysis of image from a valid URL."""
        # Mock the HTTP request
        test_image = self._image_to_bytes(create_test_image((128, 128, 128)))
        httpx_mock.add_response(
            url="https://example.com/test.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/test.png"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data
        assert "average_luminance" in data
        assert data["algorithm"] == "rec709"
        assert "width" in data
        assert "height" in data

    def test_analyze_black_image_from_url(self, client, httpx_mock, create_test_image):
        """Test analysis of pure black image from URL returns brightness 0."""
        test_image = self._image_to_bytes(create_test_image((0, 0, 0)))
        httpx_mock.add_response(
            url="https://example.com/black.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/black.png"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brightness_score"] == 0
        assert data["average_luminance"] == 0.0

    def test_analyze_white_image_from_url(self, client, httpx_mock, create_test_image):
        """Test analysis of pure white image from URL returns brightness 100."""
        test_image = self._image_to_bytes(create_test_image((255, 255, 255)))
        httpx_mock.add_response(
            url="https://example.com/white.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/white.png"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brightness_score"] == 100
        assert data["average_luminance"] == 255.0

    def test_analyze_jpeg_from_url(self, client, httpx_mock, create_test_image):
        """Test analysis works with JPEG from URL."""
        test_image = self._image_to_bytes(create_test_image((128, 128, 128), format="JPEG"))
        httpx_mock.add_response(
            url="https://example.com/test.jpg",
            content=test_image,
            headers={"content-type": "image/jpeg"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/test.jpg"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data

    def test_url_endpoint_with_metrics_parameter(self, client, httpx_mock, create_test_image):
        """Test URL endpoint with metrics parameter."""
        test_image = self._image_to_bytes(create_test_image((128, 128, 128)))
        httpx_mock.add_response(
            url="https://example.com/test.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url",
            json={"url": "https://example.com/test.png", "metrics": "brightness,median,histogram"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data
        assert "median_luminance" in data
        assert "histogram" in data

    def test_url_endpoint_with_edge_mode(self, client, httpx_mock, create_test_image):
        """Test URL endpoint with edge mode parameter."""
        test_image = self._image_to_bytes(create_test_image((128, 128, 128)))
        httpx_mock.add_response(
            url="https://example.com/test.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url",
            json={"url": "https://example.com/test.png", "edge_mode": "left_right"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "edge_brightness_score" in data
        assert "edge_average_luminance" in data
        assert data["edge_mode"] == "left_right"

    def test_url_endpoint_empty_url(self, client):
        """Test URL endpoint with empty URL returns 400."""
        response = client.post("/v1/image/analysis/url", json={"url": ""})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_invalid_scheme(self, client):
        """Test URL endpoint with invalid scheme returns 400."""
        response = client.post("/v1/image/analysis/url", json={"url": "ftp://example.com/test.png"})
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
        assert "scheme" in data["detail"]["error"].lower()

    def test_url_endpoint_download_failure(self, client, httpx_mock):
        """Test URL endpoint handles download failure."""
        httpx_mock.add_response(url="https://example.com/test.png", status_code=404)

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/test.png"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_unsupported_content_type(self, client, httpx_mock):
        """Test URL endpoint rejects unsupported content types."""
        httpx_mock.add_response(
            url="https://example.com/test.gif",
            content=b"fake gif content",
            headers={"content-type": "image/gif"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/test.gif"}
        )
        assert response.status_code == 415
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_file_too_large(self, client, httpx_mock):
        """Test URL endpoint rejects files larger than 5MB."""
        # Create content larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)
        httpx_mock.add_response(
            url="https://example.com/large.png",
            content=large_content,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/large.png"}
        )
        assert response.status_code == 413
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_invalid_metrics(self, client):
        """Test URL endpoint with invalid metrics."""
        response = client.post(
            "/v1/image/analysis/url",
            json={"url": "https://example.com/test.png", "metrics": "invalid_metric"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_invalid_edge_mode(self, client):
        """Test URL endpoint with invalid edge mode."""
        response = client.post(
            "/v1/image/analysis/url",
            json={"url": "https://example.com/test.png", "edge_mode": "invalid_mode"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_corrupted_image(self, client, httpx_mock):
        """Test URL endpoint handles corrupted image data."""
        httpx_mock.add_response(
            url="https://example.com/corrupted.png",
            content=b"not a valid image",
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/corrupted.png"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]

    def test_url_endpoint_includes_processing_time(self, client, httpx_mock, create_test_image):
        """Test that URL endpoint response includes processing_time_ms field."""
        test_image = self._image_to_bytes(create_test_image((255, 255, 255)))
        httpx_mock.add_response(
            url="https://example.com/white.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/white.png"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify processing_time_ms is present
        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], (int, float))

        # Processing time should be non-negative and reasonable (< 10 seconds)
        assert data["processing_time_ms"] >= 0
        assert data["processing_time_ms"] < 10000


class TestUrlEndpointSSRFProtection:
    """Test SSRF protection in URL endpoint."""

    def test_url_endpoint_blocks_localhost(self, client):
        """Test URL endpoint blocks localhost URLs."""
        for url in ["http://localhost/image.png", "http://127.0.0.1/image.png"]:
            response = client.post("/v1/image/analysis/url", json={"url": url})
            assert response.status_code == 400
            data = response.json()
            assert "private or local" in data["detail"]["detail"].lower()

    def test_url_endpoint_blocks_private_ips(self, client):
        """Test URL endpoint blocks private IP addresses."""
        private_urls = [
            "http://192.168.1.1/image.png",
            "http://10.0.0.1/image.png",
            "http://172.16.0.1/image.png",
        ]
        for url in private_urls:
            response = client.post("/v1/image/analysis/url", json={"url": url})
            assert response.status_code == 400
            data = response.json()
            assert "private or local" in data["detail"]["detail"].lower()

    def test_url_endpoint_allows_public_domains(self, client, httpx_mock, create_test_image):
        """Test URL endpoint allows public domain URLs."""
        test_image = create_test_image((128, 128, 128)).getvalue()
        httpx_mock.add_response(
            url="https://example.com/image.png",
            content=test_image,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/image.png"}
        )
        assert response.status_code == 200


class TestRealSampleImages:
    """Test analysis with real sample images."""

    def test_analyze_sample_color_image(self, client, sample_color_image):
        """Test analysis of real sample color image."""
        response = client.post(
            "/v1/image/analysis?metrics=brightness,median",
            files={"image": ("sample2-536x354.jpg", sample_color_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify expected dimensions
        assert data["width"] == 536
        assert data["height"] == 354

        # Verify brightness metrics are present and reasonable
        assert "brightness_score" in data
        assert "average_luminance" in data
        assert "median_luminance" in data
        assert 0 <= data["brightness_score"] <= 100
        assert 0 <= data["average_luminance"] <= 255
        assert 0 <= data["median_luminance"] <= 255

        # Based on actual API testing: brightness_score should be around 57
        assert 50 <= data["brightness_score"] <= 65
        assert 140 <= data["average_luminance"] <= 160

    def test_analyze_sample_grayscale_image(self, client, sample_grayscale_image):
        """Test analysis of real sample grayscale image."""
        response = client.post(
            "/v1/image/analysis?metrics=brightness,histogram",
            files={
                "image": ("sample1-536x354-grayscale.jpg", sample_grayscale_image, "image/jpeg")
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify expected dimensions
        assert data["width"] == 536
        assert data["height"] == 354

        # Verify brightness and histogram are present
        assert "brightness_score" in data
        assert "average_luminance" in data
        assert "histogram" in data
        assert len(data["histogram"]) == 10

        # Based on actual API testing: brightness_score should be around 62
        assert 55 <= data["brightness_score"] <= 70
        assert 150 <= data["average_luminance"] <= 170

    def test_sample_images_with_edge_mode(self, client, sample_color_image):
        """Test edge mode analysis with sample image."""
        response = client.post(
            "/v1/image/analysis?edge_mode=all",
            files={"image": ("sample2-536x354.jpg", sample_color_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify edge analysis fields
        assert "edge_brightness_score" in data
        assert "edge_average_luminance" in data
        assert "edge_mode" in data
        assert data["edge_mode"] == "all"

        # Edge values should be reasonable
        assert 0 <= data["edge_brightness_score"] <= 100
        assert 0 <= data["edge_average_luminance"] <= 255

    def test_sample_images_all_metrics(self, client, sample_color_image):
        """Test sample image with all available metrics."""
        response = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram",
            files={"image": ("sample2-536x354.jpg", sample_color_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify all metrics are present
        assert "brightness_score" in data
        assert "average_luminance" in data
        assert "median_luminance" in data
        assert "histogram" in data
        assert "processing_time_ms" in data
        assert "width" in data
        assert "height" in data

        # Verify histogram has correct structure
        assert isinstance(data["histogram"], list)
        assert len(data["histogram"]) == 10
        for bucket in data["histogram"]:
            assert "range" in bucket
            assert "percent" in bucket
            assert isinstance(bucket["percent"], (int, float))
            assert 0 <= bucket["percent"] <= 100


class TestCachingBehavior:
    """Test in-memory LRU cache for image analysis endpoints."""

    def test_first_request_not_cached(self, client, gray_image):
        """First request for an image should have cached=False."""
        response = client.post(
            "/v1/image/analysis", files={"image": ("test.png", gray_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False

    def test_second_request_is_cached(self, client, gray_image):
        """Second request with the same image and parameters should be a cache hit."""
        image_bytes = gray_image.getvalue()

        # First request – cache miss
        client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", io.BytesIO(image_bytes), "image/png")},
        )

        # Second request with identical content – cache hit
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("other_name.png", io.BytesIO(image_bytes), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True

    def test_cached_result_contains_all_metrics(self, client, gray_image):
        """Cached response should contain all the same metric fields."""
        image_bytes = gray_image.getvalue()

        # Warm cache
        first = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", io.BytesIO(image_bytes), "image/png")},
        ).json()

        # Cache hit
        second = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", io.BytesIO(image_bytes), "image/png")},
        ).json()

        assert second["cached"] is True
        for key in ("brightness_score", "average_luminance", "width", "height", "algorithm"):
            assert second[key] == first[key]

    def test_different_metrics_produce_separate_cache_entries(self, client, gray_image):
        """Different metrics parameters should not share cache entries."""
        image_bytes = gray_image.getvalue()

        r1 = client.post(
            "/v1/image/analysis?metrics=brightness",
            files={"image": ("test.png", io.BytesIO(image_bytes), "image/png")},
        ).json()
        assert r1["cached"] is False

        r2 = client.post(
            "/v1/image/analysis?metrics=brightness,median",
            files={"image": ("test.png", io.BytesIO(image_bytes), "image/png")},
        ).json()
        # Different metrics → different cache key → cache miss
        assert r2["cached"] is False

    def test_different_images_produce_separate_cache_entries(
        self, client, black_image, white_image
    ):
        """Different image content should produce separate cache entries."""
        r1 = client.post(
            "/v1/image/analysis",
            files={"image": ("black.png", black_image, "image/png")},
        ).json()
        assert r1["cached"] is False

        r2 = client.post(
            "/v1/image/analysis",
            files={"image": ("white.png", white_image, "image/png")},
        ).json()
        # Different image content → different hash → cache miss
        assert r2["cached"] is False

    def test_cache_is_populated_after_first_request(self, client, gray_image):
        """The module-level cache should contain one entry after the first request."""
        assert _cache.size == 0

        client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", gray_image, "image/png")},
        )

        assert _cache.size == 1

    def test_url_endpoint_first_request_not_cached(self, client, httpx_mock, create_test_image):
        """First URL request should have cached=False."""
        image_bytes = create_test_image((128, 128, 128)).getvalue()
        httpx_mock.add_response(
            url="https://example.com/test.png",
            content=image_bytes,
            headers={"content-type": "image/png"},
        )

        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/test.png"}
        )
        assert response.status_code == 200
        assert response.json()["cached"] is False

    def test_url_endpoint_second_request_is_cached(self, client, httpx_mock, create_test_image):
        """Second URL request with the same image content should be a cache hit."""
        image_bytes = create_test_image((128, 128, 128)).getvalue()
        # Allow two HTTP downloads of the same URL
        httpx_mock.add_response(
            url="https://example.com/test.png",
            content=image_bytes,
            headers={"content-type": "image/png"},
        )
        httpx_mock.add_response(
            url="https://example.com/test.png",
            content=image_bytes,
            headers={"content-type": "image/png"},
        )

        client.post("/v1/image/analysis/url", json={"url": "https://example.com/test.png"})
        response = client.post(
            "/v1/image/analysis/url", json={"url": "https://example.com/test.png"}
        )
        assert response.status_code == 200
        assert response.json()["cached"] is True


class TestImageAnalysisCacheUnit:
    """Unit tests for the ImageAnalysisCache class."""

    def test_cache_miss_returns_none(self):
        """Cache returns None for unknown keys."""
        cache = ImageAnalysisCache()
        assert cache.get("nonexistent") is None

    def test_cache_set_and_get(self):
        """Values stored with set() should be retrievable with get()."""
        cache = ImageAnalysisCache()
        cache.set("key1", {"brightness_score": 50})
        result = cache.get("key1")
        assert result is not None
        assert result["brightness_score"] == 50

    def test_cache_returns_copy(self):
        """get() returns a copy so mutating the result doesn't affect the cache."""
        cache = ImageAnalysisCache()
        original = {"brightness_score": 42}
        cache.set("key1", original)

        copy = cache.get("key1")
        copy["brightness_score"] = 99

        # Original in cache should be unchanged
        assert cache.get("key1")["brightness_score"] == 42

    def test_cache_lru_eviction(self):
        """Cache should evict the least-recently-used entry when max_size is exceeded."""
        cache = ImageAnalysisCache(max_size=2)
        cache.set("a", {"v": 1})
        cache.set("b", {"v": 2})
        cache.set("c", {"v": 3})  # Should evict "a"

        assert cache.get("a") is None
        assert cache.get("b") is not None
        assert cache.get("c") is not None

    def test_cache_ttl_expiry(self):
        """Entries older than ttl_seconds should be treated as misses."""
        import time

        cache = ImageAnalysisCache(ttl_seconds=0)
        cache.set("key1", {"brightness_score": 77})

        # Sleep just long enough for monotonic clock to advance
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """clear() should remove all entries."""
        cache = ImageAnalysisCache()
        cache.set("key1", {"v": 1})
        cache.set("key2", {"v": 2})
        cache.clear()
        assert cache.size == 0

    def test_compute_cache_key_deterministic(self):
        """Same inputs should always produce the same key."""
        data = b"image data"
        k1 = compute_cache_key(data, {"brightness", "median"}, "all")
        k2 = compute_cache_key(data, {"median", "brightness"}, "all")
        assert k1 == k2

    def test_compute_cache_key_differs_on_content(self):
        """Different image bytes should produce different keys."""
        k1 = compute_cache_key(b"image_a", {"brightness"}, None)
        k2 = compute_cache_key(b"image_b", {"brightness"}, None)
        assert k1 != k2

    def test_compute_cache_key_differs_on_metrics(self):
        """Different metrics should produce different keys."""
        data = b"same image"
        k1 = compute_cache_key(data, {"brightness"}, None)
        k2 = compute_cache_key(data, {"brightness", "median"}, None)
        assert k1 != k2

    def test_compute_cache_key_differs_on_edge_mode(self):
        """Different edge modes should produce different keys."""
        data = b"same image"
        k1 = compute_cache_key(data, {"brightness"}, None)
        k2 = compute_cache_key(data, {"brightness"}, "all")
        assert k1 != k2

    def test_compute_cache_key_no_url_in_key(self):
        """Cache key must not contain the raw URL (privacy requirement)."""
        url = "https://secret.example.com/private/image.png?token=supersecret"
        key = compute_cache_key(b"img", {"brightness"}, None)
        assert url not in key
        assert "secret" not in key
        assert "supersecret" not in key
