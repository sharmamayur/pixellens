"""
CLI interface for PixelLens
Developer-friendly command line tool for validating tracking pixels
"""

import asyncio
import json
from typing import List, Optional

import click
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.validator import (
    TagValidator,
    ValidationConfig,
    ValidationResult,
    ValidationStep,
)

# Load environment variables from .env file
load_dotenv()

console = Console()


@click.command()
@click.option(
    "--test-case",
    "-t",
    help="Test case name from config file (runs all if not specified)",
)
@click.option(
    "--expect",
    "-e",
    help='Comma-separated list of expected pixels (e.g., "ga4,facebook,hotjar")',
)
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to YAML configuration file",
)
@click.option("--timeout", default=30, help="Timeout in seconds (default: 30)")
@click.option(
    "--headless/--no-headless", default=True, help="Run browser in headless mode"
)
@click.option("--save", "-s", type=click.Path(), help="Save results to file")
@click.version_option(version="0.1.0")
def main(
    test_case: Optional[str],
    expect: Optional[str],
    config: Optional[str],
    timeout: int,
    headless: bool,
    save: Optional[str],
):
    """🔍 PixelLens - Developer-focused tracking pixel validation tool"""

    if not config:
        console.print("❌ Config file required.")
        console.print("💡 Use: plens --config sample-config.yml")
        return

    if test_case:
        # Run single test case
        validation_config, test_case_name = _load_test_case(
            config, test_case, expect, timeout, headless
        )

        if not validation_config:
            console.print("❌ Test case not found.")
            return

        # Run validation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Running test case {test_case_name}...", total=None
            )

            validator = TagValidator()
            result = asyncio.run(
                validator.validate_test_case(test_case_name, validation_config)
            )

            progress.remove_task(task)

        # Display results
        _display_results(result, "json")

        # Save results if requested
        if save:
            _save_results(result, save, "json")
            console.print(f"💾 Results saved to {save}")
    else:
        # Run all test cases
        _run_all_test_cases(config, expect, timeout, headless, save)


def _run_all_test_cases(
    config_path: str,
    expect: Optional[str] = None,
    timeout: int = 30,
    headless: bool = True,
    save: Optional[str] = None,
):
    """Run all test cases in the config file"""

    try:
        with open(config_path) as f:
            file_config = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"❌ Config file not found: {config_path}", style="red")
        return
    except Exception as e:
        console.print(f"❌ Error loading config: {e}", style="red")
        return

    test_cases = file_config.get("test_cases", {})
    if not test_cases:
        console.print("❌ No test_cases found in config file", style="red")
        return

    console.print(
        f"🧪 [bold green]Running {len(test_cases)} test cases...[/bold green]"
    )

    all_results = []
    validator = TagValidator()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        main_task = progress.add_task("Running test cases...", total=len(test_cases))

        for i, test_case_name in enumerate(test_cases.keys()):
            progress.update(
                main_task,
                description=f"Running {test_case_name} ({i + 1}/{len(test_cases)})",
            )

            # Load individual test case
            validation_config, _ = _load_test_case(
                config_path, test_case_name, expect, timeout, headless
            )

            if validation_config:
                try:
                    result = asyncio.run(
                        validator.validate_test_case(test_case_name, validation_config)
                    )
                    all_results.append(result)

                    status = "✅" if result.success else "❌"
                    console.print(
                        f"  {status} {test_case_name}: {'PASSED' if result.success else 'FAILED'}"
                    )

                except Exception as e:
                    console.print(f"  ❌ {test_case_name}: ERROR - {e!s}")
            else:
                console.print(f"  ❌ {test_case_name}: CONFIG ERROR")

            progress.advance(main_task)

    # Display summary
    passed = sum(1 for r in all_results if r.success)
    total = len(all_results)
    console.print(f"\n📊 [bold]Summary:[/bold] {passed}/{total} test cases passed")

    if passed == total:
        console.print("🎉 [bold green]All test cases passed![/bold green]")
    else:
        console.print(
            f"⚠️  [bold yellow]{total - passed} test cases failed[/bold yellow]"
        )

    # Save results if requested
    if save:
        _save_all_results(all_results, save)
        console.print(f"💾 Results saved to {save}")


def _save_all_results(results: List[ValidationResult], filename: str):
    """Save all test case results to file"""
    result_list = [_result_to_dict(r) for r in results]
    with open(filename, "w") as f:
        json.dump(result_list, f, indent=2)


def _load_test_case(
    config_path: Optional[str] = None,
    test_case: Optional[str] = None,
    expect: Optional[str] = None,
    timeout: int = 30,
    headless: bool = True,
) -> tuple[Optional[ValidationConfig], Optional[str]]:
    """Load test case configuration from file"""

    if not config_path:
        console.print("❌ Config file is required")
        return None, None

    if not test_case:
        console.print("❌ Test case name is required")
        return None, None

    try:
        with open(config_path) as f:
            file_config = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"❌ Config file not found: {config_path}", style="red")
        return None, None
    except Exception as e:
        console.print(f"❌ Error loading config: {e}", style="red")
        return None, None

    # Check for test_cases
    test_cases = file_config.get("test_cases", {})
    if not test_cases:
        console.print("❌ No test_cases found in config file", style="red")
        return None, None

    if test_case not in test_cases:
        available = list(test_cases.keys())
        console.print(f"❌ Test case '{test_case}' not found", style="red")
        console.print(f"💡 Available test cases: {', '.join(available)}")
        return None, None

    # Load the specific test case
    case_config = test_cases[test_case]

    # Create validation config
    config = ValidationConfig(
        start_url=case_config.get("start_url", ""),
        timeout=timeout,
        headless=headless,
        wait_for_network_idle=True,
        step_delay=2,
    )

    # Apply default config from file
    if "default_config" in file_config:
        defaults = file_config["default_config"]
        config.timeout = defaults.get("timeout", config.timeout)
        config.headless = defaults.get("headless", config.headless)
        config.wait_for_network_idle = defaults.get(
            "wait_for_network_idle", config.wait_for_network_idle
        )
        config.step_delay = defaults.get("step_delay", config.step_delay)

    # Load steps
    steps_data = case_config.get("steps", [])
    for step_data in steps_data:
        step = ValidationStep(
            name=step_data.get("name", ""),
            action=step_data.get("action", ""),
            expect_pixels=step_data.get("expect_pixels", []),
        )
        config.steps.append(step)

    if not config.start_url:
        console.print(f"❌ Test case '{test_case}' has no start_url", style="red")
        return None, None

    console.print(
        f"🧪 [bold green]Test case:[/bold green] {case_config.get('description', test_case)}"
    )
    console.print(f"🔗 [bold blue]URL:[/bold blue] {config.start_url}")
    console.print(f"📋 [bold yellow]Steps:[/bold yellow] {len(config.steps)}")

    return config, test_case


def _display_results(result: ValidationResult, output_format: str):
    """Display validation results"""
    _print_json_results(result)


def _print_json_results(result: ValidationResult):
    """Display results in JSON format"""
    result_dict = {
        "test_case": result.test_case,
        "url": result.url,
        "success": result.success,
        "execution_time": result.execution_time,
        "error": result.error,
        "steps": [],
    }

    for step_result in result.step_results:
        step_dict = {
            "step_name": step_result.step_name,
            "action": step_result.action,
            "success": step_result.success,
            "execution_time": step_result.execution_time,
            "expected_pixels": step_result.expected_pixels,
            "detected_pixels": step_result.detected_pixels,
            "passed_pixels": step_result.passed_pixels,
            "failed_pixels": step_result.failed_pixels,
            "error": step_result.error,
        }
        result_dict["steps"].append(step_dict)

    console.print(json.dumps(result_dict, indent=2))


def _save_results(result: ValidationResult, filename: str, output_format: str):
    """Save results to file"""
    result_dict = _result_to_dict(result)
    with open(filename, "w") as f:
        json.dump(result_dict, f, indent=2)


def _result_to_dict(result: ValidationResult) -> dict:
    """Convert ValidationResult to dictionary"""
    result_dict = {
        "url": result.url,
        "success": result.success,
        "execution_time": result.execution_time,
        "error": result.error,
    }

    if result.summary:
        result_dict["summary"] = {
            "total_requests": result.summary.total_requests,
            "tracking_requests": result.summary.tracking_requests,
            "page_load_pixels": result.summary.page_load_pixels,
            "interaction_pixels": result.summary.interaction_pixels,
            "pixels_by_vendor": {
                k: len(v) for k, v in result.summary.pixels_by_vendor.items()
            },
            "timeline": result.summary.timeline,
        }

    if result.validation:
        result_dict["validation"] = result.validation

    return result_dict


if __name__ == "__main__":
    main()
