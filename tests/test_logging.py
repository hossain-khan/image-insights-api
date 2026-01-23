"""Tests for detailed application logging functionality."""

import logging
import time


class TestLoggingWhenEnabled:
    """Test logging behavior when ENABLE_DETAILED_LOGGING is True."""

    def test_logs_request_start(self, client, white_image, caplog):
        """Test that request start is logged when enabled."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness",
                files={"image": ("test.png", white_image, "image/png")},
            )

        # Check for request start log
        log_messages = [record.message for record in caplog.records]
        assert any("Image analysis request started" in msg for msg in log_messages)

    def test_logs_request_start_with_filename(self, client, white_image, caplog):
        """Test that request start log includes filename."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness",
                files={"image": ("photo.jpg", white_image, "image/jpeg")},
            )

        log_messages = [record.message for record in caplog.records]
        assert any(
            "photo.jpg" in msg and "Image analysis request started" in msg for msg in log_messages
        )

    def test_logs_request_start_with_metrics(self, client, white_image, caplog):
        """Test that request start log includes requested metrics."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness,median,histogram",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        assert any(
            "brightness,median,histogram" in msg and "Image analysis request started" in msg
            for msg in log_messages
        )

    def test_logs_file_validation(self, client, white_image, caplog):
        """Test that file validation is logged."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        assert any("File validated" in msg and "Size:" in msg for msg in log_messages)

    def test_logs_file_content_type(self, client, white_image, caplog):
        """Test that file content type is logged."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        assert any("image/png" in msg for msg in log_messages)

    def test_logs_image_dimensions(self, client, white_image, caplog):
        """Test that image dimensions are logged."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        # Check for dimensions in the format "256x256" or similar
        assert any("Image loaded" in msg and "x" in msg for msg in log_messages)

    def test_logs_analysis_completion(self, client, white_image, caplog):
        """Test that analysis completion is logged."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        assert any("Image analysis completed" in msg for msg in log_messages)

    def test_logs_processing_duration(self, client, white_image, caplog):
        """Test that processing duration is logged in milliseconds."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        completion_logs = [msg for msg in log_messages if "Image analysis completed" in msg]
        assert any("Duration:" in msg and "ms" in msg for msg in completion_logs)

    def test_logs_metrics_used(self, client, white_image, caplog):
        """Test that metrics used are logged in completion message."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness,median",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        completion_logs = [msg for msg in log_messages if "Image analysis completed" in msg]
        assert any("Metrics:" in msg for msg in completion_logs)

    def test_logs_algorithm_used(self, client, white_image, caplog):
        """Test that algorithm is logged."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        log_messages = [record.message for record in caplog.records]
        completion_logs = [msg for msg in log_messages if "Image analysis completed" in msg]
        assert any("Algorithm: rec709" in msg for msg in completion_logs)

    def test_logging_uses_correct_logger(self, client, white_image, caplog):
        """Test that logging uses the correct logger name."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        # Check that logs come from the image_analysis module
        logger_names = [record.name for record in caplog.records]
        assert any("image_analysis" in name for name in logger_names)


class TestLoggingLogLevels:
    """Test that logging uses appropriate log levels."""

    def test_all_logs_are_info_level(self, client, white_image, caplog):
        """Test that all image analysis logs use INFO level."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness",
                files={"image": ("test.png", white_image, "image/png")},
            )

        image_analysis_logs = [
            record for record in caplog.records if "image_analysis" in record.name
        ]
        assert len(image_analysis_logs) > 0

        # All should be INFO level
        for record in image_analysis_logs:
            assert record.levelname == "INFO"

    def test_no_error_logs_on_successful_request(self, client, white_image, caplog):
        """Test that successful requests do not generate error logs."""
        with caplog.at_level(logging.DEBUG):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        error_logs = [
            record for record in caplog.records if record.levelname in ["ERROR", "CRITICAL"]
        ]
        assert len(error_logs) == 0


class TestLogMessageContent:
    """Test the content and format of log messages."""

    def test_duration_is_reasonable(self, client, white_image, caplog):
        """Test that logged duration is a reasonable value in milliseconds."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness",
                files={"image": ("test.png", white_image, "image/png")},
            )

        completion_logs = [
            record.message
            for record in caplog.records
            if "Image analysis completed" in record.message
        ]
        assert len(completion_logs) > 0

        # Extract duration from log message
        import re

        log_msg = completion_logs[0]
        duration_match = re.search(r"Duration: ([\d.]+)ms", log_msg)
        assert duration_match is not None

        duration = float(duration_match.group(1))
        # Duration should be reasonable (between 0.1ms and 1000ms)
        assert 0.1 <= duration < 1000

    def test_file_size_logged_correctly(self, client, white_image, caplog):
        """Test that file size is logged in MB format."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis",
                files={"image": ("test.png", white_image, "image/png")},
            )

        file_logs = [
            record.message for record in caplog.records if "File validated" in record.message
        ]
        assert len(file_logs) > 0

        # Check that size is in MB format
        import re

        log_msg = file_logs[0]
        size_match = re.search(r"Size: ([\d.]+)MB", log_msg)
        assert size_match is not None

    def test_all_metrics_logged_correctly(self, client, white_image, caplog):
        """Test that all requested metrics are shown in completion log."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness,median,histogram",
                files={"image": ("test.png", white_image, "image/png")},
            )

        completion_logs = [
            record.message
            for record in caplog.records
            if "Image analysis completed" in record.message
        ]
        assert len(completion_logs) > 0

        log_msg = completion_logs[0]
        # All three metrics should be mentioned
        assert "brightness" in log_msg
        assert "median" in log_msg
        assert "histogram" in log_msg


class TestLoggingPerformance:
    """Test performance impact of logging."""

    def test_logging_performance_acceptable(self, client, white_image):
        """Test that analysis completes quickly with logging enabled."""
        start = time.time()
        response = client.post(
            "/v1/image/analysis?metrics=brightness,median,histogram",
            files={"image": ("test.png", white_image, "image/png")},
        )
        duration = time.time() - start

        assert response.status_code == 200
        # Should complete well under 1 second with logging overhead
        assert duration < 1.0

    def test_all_metrics_logged_completion(self, client, white_image, caplog):
        """Test that all metrics are logged in completion for all metric types."""
        with caplog.at_level(logging.INFO):
            client.post(
                "/v1/image/analysis?metrics=brightness,median,histogram",
                files={"image": ("test.png", white_image, "image/png")},
            )

        completion_logs = [
            record.message
            for record in caplog.records
            if "Image analysis completed" in record.message
        ]
        assert len(completion_logs) > 0

        log_msg = completion_logs[0]
        # All three metrics should be mentioned
        assert "brightness" in log_msg
        assert "median" in log_msg
        assert "histogram" in log_msg
