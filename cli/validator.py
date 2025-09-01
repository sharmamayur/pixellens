"""
Pixel Validator - Main validation engine using browser-use AI agent
Orchestrates AI-driven browser interactions with network monitoring
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from browser_use import Agent
from browser_use.llm.anthropic.chat import ChatAnthropic
from playwright.async_api import async_playwright
from rich.console import Console

from cli.network_monitor import NetworkMonitor, ValidationSummary

console = Console()


@dataclass
class UrlParam:
    """URL parameter validation rule"""

    name: str
    value: str


@dataclass
class ExpectedPixel:
    """Expected pixel with optional URL parameter validation"""

    vendor: str
    url_params: List[UrlParam] = field(default_factory=list)


@dataclass
class ValidationStep:
    """Single step in a validation journey"""

    name: str
    action: str
    expect_pixels: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationConfig:
    """Configuration for pixel validation"""

    start_url: str = ""
    steps: List[ValidationStep] = field(default_factory=list)
    timeout: int = 30
    headless: bool = True
    wait_for_network_idle: bool = True
    step_delay: int = 2


@dataclass
class StepResult:
    """Result of a single validation step"""

    step_name: str
    action: str
    expected_pixels: List[str]
    detected_pixels: List[str] = field(default_factory=list)
    passed_pixels: List[str] = field(default_factory=list)
    failed_pixels: List[str] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None
    execution_time: float = 0


@dataclass
class ValidationResult:
    """Result of pixel validation"""

    test_case: str
    url: str
    success: bool
    step_results: List[StepResult] = field(default_factory=list)
    summary: Optional[ValidationSummary] = None
    error: Optional[str] = None
    execution_time: float = 0


class TagValidator:
    """Main pixel validation engine using browser-use AI agent"""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = options or {}
        self.default_config = ValidationConfig(
            headless=self.options.get("headless", True),
            timeout=self.options.get("timeout", 30),
            wait_for_network_idle=self.options.get("wait_for_network_idle", True),
        )

    async def validate_test_case(
        self, test_case_name: str, config: ValidationConfig
    ) -> ValidationResult:
        """Validate pixels for a test case with step-by-step execution"""
        start_time = time.time()
        url = config.start_url

        console.print(
            f"🚀 [bold green]Starting test case:[/bold green] {test_case_name}"
        )
        console.print(f"🔗 [bold blue]URL:[/bold blue] {url}")

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=config.headless)
                context = await browser.new_context()
                page = await context.new_page()

                step_results = []
                all_success = True

                for step in config.steps:
                    console.print(f"📍 [bold yellow]Step:[/bold yellow] {step.name}")

                    step_start_time = time.time()

                    # Set up fresh network monitoring for this step
                    monitor = NetworkMonitor()
                    await monitor.start(page)

                    try:
                        # Execute the step action
                        await self._execute_step_action(page, step, url)

                        # Wait for pixels to fire
                        await asyncio.sleep(config.step_delay)

                        # Get pixels detected during this step
                        step_summary = monitor.stop()
                        detected_vendors = list(step_summary.pixels_by_vendor.keys())

                        # Validate expected pixels for this step
                        step_result = self._validate_step_pixels(
                            step, step_summary, time.time() - step_start_time
                        )

                        step_results.append(step_result)

                        if not step_result.success:
                            all_success = False

                        expected_names = sorted(step_result.expected_pixels)
                        detected_sorted = sorted(detected_vendors)
                        console.print(
                            f"  {'✅' if step_result.success else '❌'} "
                            f"Expected: {expected_names} | "
                            f"Detected: {detected_sorted}"
                        )

                    except Exception as step_error:
                        step_result = StepResult(
                            step_name=step.name,
                            action=step.action,
                            expected_pixels=self._parse_expected_pixels(
                                step.expect_pixels
                            ),
                            success=False,
                            error=str(step_error),
                            execution_time=time.time() - step_start_time,
                        )
                        step_results.append(step_result)
                        all_success = False
                        console.print(f"  ❌ Step failed: {step_error!s}")

                execution_time = time.time() - start_time
                await browser.close()

                return ValidationResult(
                    test_case=test_case_name,
                    url=url,
                    success=all_success,
                    step_results=step_results,
                    execution_time=execution_time,
                )

            except Exception as error:
                execution_time = time.time() - start_time
                console.print(
                    f"❌ [bold red]Error in test case {test_case_name}:[/bold red] "
                    f"{error!s}"
                )

                if "browser" in locals():
                    await browser.close()

                return ValidationResult(
                    test_case=test_case_name,
                    url=url,
                    success=False,
                    error=str(error),
                    execution_time=execution_time,
                )

    async def _execute_step_action(self, page, step: ValidationStep, url: str):
        """Execute a single step action"""
        if step.action.lower() == "load_page":
            # Basic page load - no AI needed
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=30000,
            )
        else:
            # Everything else uses AI agent
            await self._execute_ai_action(page, step.action)

    async def _execute_ai_action(self, page, action_description: str):
        """Execute action using AI agent"""
        try:
            current_url = page.url
            domain = current_url.split("/")[2]

            strict_prompt = f"""
CRITICAL CONSTRAINTS:
- You are a pixel tracking expert. You are given a description of an action
  to take on a website. You are to take that action and that action only.
- NEVER navigate away from {domain} - STAY ON THIS WEBSITE ONLY
- Complete ONLY this specific action: {action_description}
- Do NOT open new tabs or windows
- Do NOT navigate away from {domain}
- Do NOT click on any links that are not part of the action
- Do NOT click on any buttons that are not part of the action
- Do NOT fill out any forms that are not part of the action
- Do NOT interact with any elements that are not part of the action
- Do NOT come up with any other actions to take if the said action is not possible


TASK: {action_description}
"""

            agent = Agent(
                task=strict_prompt,
                browser=page.context.browser,
                llm=ChatAnthropic(model="claude-3-5-haiku-20241022"),
                max_steps=3,
                max_actions_per_step=1,
                max_failures=1,
            )

            await agent.run()

        except Exception as error:
            console.print(f"⚠️  [bold yellow]AI action failed:[/bold yellow] {error!s}")

    def _parse_expected_pixels(
        self, expect_pixels_config: Dict[str, Any]
    ) -> List[ExpectedPixel]:
        """Parse expect_pixels configuration into ExpectedPixel objects"""
        expected_pixels = []
        for vendor, config in expect_pixels_config.items():
            url_params = []
            if config and "url_params" in config:
                for param_config in config["url_params"]:
                    url_params.append(
                        UrlParam(name=param_config["name"], value=param_config["value"])
                    )
            expected_pixels.append(ExpectedPixel(vendor=vendor, url_params=url_params))
        return expected_pixels

    def _validate_step_pixels(
        self, step: ValidationStep, step_summary, execution_time: float
    ) -> StepResult:
        """Validate detected pixels against step expectations"""
        from urllib.parse import parse_qs, urlparse

        expected_pixels = self._parse_expected_pixels(step.expect_pixels)
        detected_vendors = list(step_summary.pixels_by_vendor.keys())
        passed_pixels = []
        failed_pixels = []

        for expected_pixel in expected_pixels:
            # Check if vendor is detected
            vendor_found = any(
                expected_pixel.vendor.lower() in vendor.lower()
                or vendor.lower() in expected_pixel.vendor.lower()
                for vendor in detected_vendors
            )

            if not vendor_found:
                failed_pixels.append(expected_pixel.vendor)
                continue

            # If vendor is found and no URL params specified, it's a pass
            if not expected_pixel.url_params:
                passed_pixels.append(expected_pixel.vendor)
                continue

            # Validate URL parameters
            param_validation_passed = False

            # Find matching vendor's requests
            for vendor_name, requests in step_summary.pixels_by_vendor.items():
                if (
                    expected_pixel.vendor.lower() in vendor_name.lower()
                    or vendor_name.lower() in expected_pixel.vendor.lower()
                ):
                    # Check each request from this vendor
                    for request in requests:
                        parsed_url = urlparse(request.url)
                        url_params = parse_qs(parsed_url.query)

                        # Check if all expected URL parameters match in this request
                        all_params_match = True
                        for expected_param in expected_pixel.url_params:
                            param_values = url_params.get(expected_param.name, [])
                            if expected_param.value not in param_values:
                                all_params_match = False
                                break

                        # If this request matches all expected params, we're good
                        if all_params_match:
                            param_validation_passed = True
                            break

                    if param_validation_passed:
                        break

            if param_validation_passed:
                passed_pixels.append(expected_pixel.vendor)
            else:
                failed_pixels.append(expected_pixel.vendor)

        success = len(failed_pixels) == 0

        expected_pixel_names = [p.vendor for p in expected_pixels]

        return StepResult(
            step_name=step.name,
            action=step.action,
            expected_pixels=expected_pixel_names,
            detected_pixels=detected_vendors,
            passed_pixels=passed_pixels,
            failed_pixels=failed_pixels,
            success=success,
            execution_time=execution_time,
        )
