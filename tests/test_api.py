"""Tests for the image analysis API endpoint."""

import io
from PIL import Image


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "image-analysis-api"
    
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
            "/v1/image/analysis",
            files={"image": ("test.png", black_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brightness_score"] == 0
        assert data["average_luminance"] == 0.0
        assert data["algorithm"] == "rec709"
    
    def test_analyze_white_image(self, client, white_image):
        """Test analysis of pure white image returns brightness 100."""
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", white_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["brightness_score"] == 100
        assert data["average_luminance"] == 255.0
    
    def test_analyze_gray_image(self, client, gray_image):
        """Test analysis of gray image returns ~50 brightness."""
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", gray_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        # Gray (128, 128, 128) should give ~50% brightness
        assert 49 <= data["brightness_score"] <= 51
    
    def test_analyze_jpeg_image(self, client, jpeg_image):
        """Test analysis works with JPEG format."""
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.jpg", jpeg_image, "image/jpeg")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "brightness_score" in data
    
    def test_response_includes_dimensions(self, client, create_test_image):
        """Test response includes image dimensions."""
        img = create_test_image(size=(200, 150))
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", img, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["width"] == 200
        assert data["height"] == 150
    
    def test_large_image_reports_original_dimensions(self, client, large_image):
        """Test that large images report original dimensions, not resized."""
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", large_image, "image/png")}
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
            "/v1/image/analysis",
            files={"image": ("test.png", gray_image, "image/png")}
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
            files={"image": ("test.png", gray_image, "image/png")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "median_luminance" in data
        assert isinstance(data["median_luminance"], (int, float))
    
    def test_histogram_metric(self, client, gray_image):
        """Test histogram metric."""
        response = client.post(
            "/v1/image/analysis?metrics=histogram",
            files={"image": ("test.png", gray_image, "image/png")}
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
            files={"image": ("test.png", gray_image, "image/png")}
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
            files={"image": ("test.png", gray_image, "image/png")}
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
            "/v1/image/analysis",
            files={"image": ("test.gif", fake_gif, "image/gif")}
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
            "/v1/image/analysis",
            files={"image": ("test.png", large_file, "image/png")}
        )
        assert response.status_code == 413
        data = response.json()
        assert "exceeds maximum" in data["detail"]["error"]
    
    def test_invalid_image_data(self, client):
        """Test invalid image data returns 400."""
        fake_png = io.BytesIO(b"not a real image")
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", fake_png, "image/png")}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
    
    def test_empty_file(self, client):
        """Test empty file returns 400."""
        empty_file = io.BytesIO(b"")
        response = client.post(
            "/v1/image/analysis",
            files={"image": ("test.png", empty_file, "image/png")}
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
            files={"image": ("test1.png", img1, "image/png")}
        )
        response2 = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram",
            files={"image": ("test2.png", img2, "image/png")}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()


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
            "/v1/image/analysis",
            files={"image": ("red.png", red_img, "image/png")}
        )
        green_response = client.post(
            "/v1/image/analysis",
            files={"image": ("green.png", green_img, "image/png")}
        )
        blue_response = client.post(
            "/v1/image/analysis",
            files={"image": ("blue.png", blue_img, "image/png")}
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
            "/v1/image/analysis",
            files={"image": ("test.png", img, "image/png")}
        )
        data = response.json()
        
        # Expected luminance: 0.2126*100 + 0.7152*100 + 0.0722*100 = 100
        expected_luminance = 100.0
        assert abs(data["average_luminance"] - expected_luminance) < 0.01
