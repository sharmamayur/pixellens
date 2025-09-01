"""
Tests for the validator module
"""

from cli.validator import TagValidator, ValidationConfig, ValidationStep


class TestValidationConfig:
    """Test ValidationConfig dataclass"""

    def test_default_values(self):
        config = ValidationConfig()
        assert config.start_url == ""
        assert config.steps == []
        assert config.timeout == 30
        assert config.headless == True
        assert config.wait_for_network_idle == True
        assert config.step_delay == 2


class TestValidationStep:
    """Test ValidationStep dataclass"""

    def test_creation(self):
        step = ValidationStep(
            name="Test Step", 
            action="load_page", 
            expect_pixels={"GA4": {}, "Facebook": {}}
        )
        assert step.name == "Test Step"
        assert step.action == "load_page"
        assert step.expect_pixels == {"GA4": {}, "Facebook": {}}


class TestTagValidator:
    """Test TagValidator class"""

    def test_initialization(self):
        validator = TagValidator()
        assert validator is not None
        assert validator.options == {}

    def test_initialization_with_options(self):
        options = {"headless": False, "timeout": 60}
        validator = TagValidator(options)
        assert validator.options == options


# TODO: Add more comprehensive tests for:
# - validate_test_case method
# - _execute_step_action method
# - _validate_step_pixels method
# - Network monitoring integration
# - AI agent integration
