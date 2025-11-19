"""Unit tests for configuration."""

import pytest

from camera_analytics.config.settings import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default settings are loaded."""
        settings = Settings()
        assert settings.api_port == 8000
        assert settings.default_fps == 15
        assert settings.log_level == "INFO"

    def test_resolution_validation(self):
        """Test resolution format validation."""
        # Valid resolution
        settings = Settings(default_resolution="1280x720")
        assert settings.default_resolution == "1280x720"

        # Invalid resolution
        with pytest.raises(ValueError, match="Invalid resolution format"):
            Settings(default_resolution="invalid")

        with pytest.raises(ValueError):
            Settings(default_resolution="0x0")

    def test_port_range_validation(self):
        """Test port number validation."""
        # Valid port
        settings = Settings(api_port=8080)
        assert settings.api_port == 8080

        # Invalid ports (pydantic validates this)
        with pytest.raises(ValueError):
            Settings(api_port=0)

        with pytest.raises(ValueError):
            Settings(api_port=70000)
