"""Configuration loader and validator for Monkey Devs."""
import pathlib
import re

import yaml
from pydantic import BaseModel


class WorkflowConfig(BaseModel):
    max_corrections_per_stage: int = 3
    max_handoff_chars: int = 400000
    max_intake_turns: int = 20
    max_tool_iterations: int = 30
    auto_correction_on_validation_failure: bool = True


class AppConfig(BaseModel):
    models: dict[str, str]
    providers: dict[str, dict] = {}
    timeouts: dict[str, int] = {}
    workflow: WorkflowConfig = WorkflowConfig()
    review: dict[str, bool] = {"enabled": True}


_KEY_PATTERNS: list[re.Pattern] = [
    re.compile(r"sk-[a-zA-Z0-9\-_]{20,}"),           # OpenAI
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),            # Google
    re.compile(r"sk-ant-[a-zA-Z0-9\-_]{90,}"),        # Anthropic
]


class ConfigValidationError(Exception):
    """Raised when config.yaml contains an API key literal."""


def load_config(path: pathlib.Path) -> AppConfig:
    """Parse config.yaml and return a validated AppConfig."""
    data = yaml.safe_load(path.read_text())
    return AppConfig(**data)


def validate_config(path: pathlib.Path) -> None:
    """Scan config.yaml for accidental API key literals. Raises ConfigValidationError if found."""
    text = path.read_text()
    for pattern in _KEY_PATTERNS:
        if pattern.search(text):
            raise ConfigValidationError(
                f"API key literal detected in {path}. Store keys as environment variable names only."
            )
