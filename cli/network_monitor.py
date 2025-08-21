"""
Network Monitor - Core tracking pixel detection system
Monitors HTTP requests to identify and classify tracking pixels
"""

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class TrackedRequest:
    """Represents a captured network request"""

    url: str
    method: str
    headers: Dict[str, str]
    timestamp: float
    phase: str
    resource_type: str
    is_tracking: bool
    status_code: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    successful: Optional[bool] = None


@dataclass
class ValidationSummary:
    """Summary of pixel validation results"""

    total_requests: int
    tracking_requests: int
    page_load_pixels: int
    interaction_pixels: int
    pixels_by_vendor: Dict[str, List[TrackedRequest]]
    timeline: List[Dict[str, Any]]


class NetworkMonitor:
    """Monitors network traffic to detect tracking pixels"""

    def __init__(self):
        self.requests: List[TrackedRequest] = []
        self.start_time: Optional[float] = None
        self.phases = {"page_load": "page_load", "user_interaction": "user_interaction"}
        self.current_phase = self.phases["page_load"]

        # Tracking pixel patterns
        self.tracking_patterns = [
            # Google Analytics & Tag Manager
            re.compile(r"google-analytics\.com"),
            re.compile(r"googletagmanager\.com"),
            re.compile(r"gtag/js"),
            re.compile(r"collect\?"),
            # Facebook/Meta
            re.compile(r"facebook\.com/tr"),
            re.compile(r"connect\.facebook\.net"),
            # Other major platforms
            re.compile(r"hotjar\.com"),
            re.compile(r"segment\.(io|com)"),
            re.compile(r"mixpanel\.com"),
            re.compile(r"amplitude\.com"),
            re.compile(r"klaviyo\.com"),
            re.compile(r"pinterest\.com.*\/pixel"),
            re.compile(r"tiktok\.com.*\/pixel"),
            re.compile(r"linkedin\.com.*\/px"),
            re.compile(r"twitter\.com.*\/i\/adsct"),
            re.compile(r"snapchat\.com.*\/tr"),
            # Snowplow
            re.compile(r"sp\.cargurus\.com"),
            re.compile(r"snowplowanalytics\.com"),
            re.compile(r"\/i\?"),  # Snowplow tracking endpoint
            # Generic tracking patterns
            re.compile(r"\/track\?"),
            re.compile(r"\/pixel\?"),
            re.compile(r"\/analytics\?"),
            re.compile(r"\/events\?"),
            re.compile(r"\/beacon"),
            # Common tracking parameters
            re.compile(r"[?&]utm_"),
            re.compile(r"[?&]gclid="),
            re.compile(r"[?&]fbclid="),
        ]

    async def start(self, page):
        """Initialize network monitoring for a Playwright page"""
        self.start_time = time.time()
        self.page = page

        # Capture all network requests
        page.on("request", self._capture_request)
        page.on("response", self._capture_response)

        console.print("🔍 [bold green]Network monitoring started...[/bold green]")

    def _capture_request(self, request):
        """Capture and analyze network requests"""
        request_data = TrackedRequest(
            url=request.url,
            method=request.method,
            headers=dict(request.headers),
            timestamp=time.time(),
            phase=self.current_phase,
            resource_type=request.resource_type,
            is_tracking=self.is_tracking_request(request.url),
        )

        self.requests.append(request_data)

        # Log tracking requests in real-time
        if request_data.is_tracking:
            pixel_type = self.classify_pixel(request.url)
            console.print(
                f"📊 [bold yellow]Tracking pixel detected:[/bold yellow] {pixel_type} - {request.url}"
            )

    def _capture_response(self, response):
        """Capture response data for analysis"""
        url = response.url
        if self.is_tracking_request(url):
            # Find corresponding request and add response data
            for request in reversed(self.requests):
                if request.url == url and request.status_code is None:
                    request.status_code = response.status
                    request.response_headers = dict(response.headers)
                    request.successful = response.ok
                    break

    def is_tracking_request(self, url: str) -> bool:
        """Determine if a URL is a tracking request"""
        return any(pattern.search(url) for pattern in self.tracking_patterns)

    def classify_pixel(self, url: str) -> str:
        """Classify pixel by vendor/platform"""
        classifications = {
            "Google Analytics 4": re.compile(
                r"gtag|google-analytics\.com.*\/g\/collect"
            ),
            "Universal Analytics": re.compile(
                r"google-analytics\.com.*\/collect(?!.*\/g\/)"
            ),
            "Google Tag Manager": re.compile(r"googletagmanager\.com"),
            "Facebook Pixel": re.compile(
                r"facebook\.com\/tr|connect\.facebook\.net.*fbevents"
            ),
            "Hotjar": re.compile(r"hotjar\.com"),
            "Segment": re.compile(r"segment\.(io|com)|cdn\.segment\.com"),
            "Mixpanel": re.compile(r"mixpanel\.com"),
            "Amplitude": re.compile(r"amplitude\.com"),
            "Klaviyo": re.compile(r"klaviyo\.com"),
            "Pinterest": re.compile(r"pinterest\.com.*\/pixel"),
            "TikTok": re.compile(r"tiktok\.com.*\/pixel"),
            "LinkedIn": re.compile(r"linkedin\.com.*\/px"),
            "Twitter": re.compile(r"twitter\.com.*\/i\/adsct"),
            "Snapchat": re.compile(r"snapchat\.com.*\/tr"),
            "Snowplow": re.compile(r"sp\.cargurus\.com|snowplowanalytics\.com|\/i\?"),
        }

        for vendor, pattern in classifications.items():
            if pattern.search(url):
                return vendor

        return "Generic Tracking"

    def start_interaction_phase(self):
        """Switch to user interaction phase"""
        self.current_phase = self.phases["user_interaction"]
        console.print(
            "👆 [bold cyan]Switched to user interaction monitoring...[/bold cyan]"
        )

    def get_tracking_requests(self) -> List[TrackedRequest]:
        """Get all tracking requests"""
        return [req for req in self.requests if req.is_tracking]

    def get_tracking_requests_by_phase(self, phase: str) -> List[TrackedRequest]:
        """Get tracking requests by phase"""
        return [req for req in self.get_tracking_requests() if req.phase == phase]

    def get_summary(self) -> ValidationSummary:
        """Get summary of detected pixels"""
        tracking_requests = self.get_tracking_requests()
        page_load_pixels = self.get_tracking_requests_by_phase(self.phases["page_load"])
        interaction_pixels = self.get_tracking_requests_by_phase(
            self.phases["user_interaction"]
        )

        # Group by vendor
        pixels_by_vendor = {}
        for req in tracking_requests:
            vendor = self.classify_pixel(req.url)
            if vendor not in pixels_by_vendor:
                pixels_by_vendor[vendor] = []
            pixels_by_vendor[vendor].append(req)

        return ValidationSummary(
            total_requests=len(self.requests),
            tracking_requests=len(tracking_requests),
            page_load_pixels=len(page_load_pixels),
            interaction_pixels=len(interaction_pixels),
            pixels_by_vendor=pixels_by_vendor,
            timeline=self._get_timeline(),
        )

    def _get_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of pixel fires"""
        tracking_requests = self.get_tracking_requests()
        timeline = []

        for req in sorted(tracking_requests, key=lambda x: x.timestamp):
            timeline.append(
                {
                    "timestamp": (
                        req.timestamp - self.start_time if self.start_time else 0
                    ),
                    "vendor": self.classify_pixel(req.url),
                    "url": req.url,
                    "phase": req.phase,
                    "successful": req.successful,
                }
            )

        return timeline

    def stop(self) -> ValidationSummary:
        """Stop monitoring and return results"""
        console.print("⏹️  [bold red]Network monitoring stopped[/bold red]")
        return self.get_summary()
