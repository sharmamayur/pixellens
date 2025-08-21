"""
Tests for the network_monitor module
"""

from cli.network_monitor import NetworkMonitor, TrackedRequest


class TestNetworkMonitor:
    """Test NetworkMonitor class"""

    def test_initialization(self):
        monitor = NetworkMonitor()
        assert monitor.requests == []
        assert monitor.start_time is None
        assert monitor.current_phase == "page_load"

    def test_is_tracking_request(self):
        monitor = NetworkMonitor()

        # Test tracking URLs
        assert monitor.is_tracking_request("https://www.google-analytics.com/collect")
        assert monitor.is_tracking_request("https://facebook.com/tr")
        assert monitor.is_tracking_request("https://sp.cargurus.com/i?")

        # Test non-tracking URLs
        assert not monitor.is_tracking_request("https://example.com")
        assert not monitor.is_tracking_request("https://cdn.example.com/script.js")

    def test_classify_pixel(self):
        monitor = NetworkMonitor()

        assert (
            monitor.classify_pixel("https://www.google-analytics.com/g/collect")
            == "Google Analytics 4"
        )
        assert monitor.classify_pixel("https://facebook.com/tr") == "Facebook Pixel"
        assert monitor.classify_pixel("https://sp.cargurus.com/i?") == "Snowplow"
        assert monitor.classify_pixel("https://hotjar.com/track") == "Hotjar"
        assert (
            monitor.classify_pixel("https://unknown-tracker.com/pixel")
            == "Generic Tracking"
        )


class TestTrackedRequest:
    """Test TrackedRequest dataclass"""

    def test_creation(self):
        request = TrackedRequest(
            url="https://example.com",
            method="GET",
            headers={"User-Agent": "test"},
            timestamp=1234567890.0,
            phase="page_load",
            resource_type="xhr",
            is_tracking=True,
        )
        assert request.url == "https://example.com"
        assert request.method == "GET"
        assert request.is_tracking == True
        assert request.phase == "page_load"


# TODO: Add more comprehensive tests for:
# - Network request capture
# - Timeline analysis
# - Vendor classification accuracy
# - Phase switching
