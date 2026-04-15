import pytest
import pathlib
from monkey_devs.config import load_config, validate_config, ConfigValidationError


CONFIG_YAML = """\
models:
  concept-spec: google/gemini-2.5-pro
  architecture: google/gemini-2.5-pro
  implementation: anthropic/claude-opus-4-6
  code-fixing: openai/o4-mini
  delivery: anthropic/claude-sonnet-4-6
  reviewer: anthropic/claude-opus-4-6
  fixer: google/gemini-2.5-pro
providers:
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
  openai:
    api_key_env: OPENAI_API_KEY
  google:
    api_key_env: GEMINI_API_KEY
timeouts:
  concept-spec: 120
  architecture: 120
  implementation: 180
  code-fixing: 120
  delivery: 60
  reviewer: 90
  fixer: 120
workflow:
  max_corrections_per_stage: 3
  max_handoff_chars: 400000
  max_intake_turns: 20
  max_tool_iterations: 30
  auto_correction_on_validation_failure: true
review:
  enabled: true
"""


def test_load_config_parses_models(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(CONFIG_YAML)
    cfg = load_config(p)
    assert cfg.models["concept-spec"] == "google/gemini-2.5-pro"
    assert cfg.models["implementation"] == "anthropic/claude-opus-4-6"
    assert cfg.workflow.max_corrections_per_stage == 3
    assert cfg.workflow.max_handoff_chars == 400000
    assert cfg.workflow.max_intake_turns == 20
    assert cfg.workflow.max_tool_iterations == 30
    assert cfg.workflow.auto_correction_on_validation_failure is True
    assert cfg.review["enabled"] is True


def test_load_config_has_all_seven_models(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(CONFIG_YAML)
    cfg = load_config(p)
    for key in ["concept-spec", "architecture", "implementation",
                "code-fixing", "delivery", "reviewer", "fixer"]:
        assert key in cfg.models, f"Missing model key: {key}"


def test_validate_config_blocks_anthropic_key_literal(tmp_path):
    key = "sk-ant-" + "a" * 95   # 95 chars after prefix → matches pattern
    p = tmp_path / "config.yaml"
    p.write_text(f"providers:\n  anthropic:\n    api_key_env: {key}\n")
    with pytest.raises(ConfigValidationError):
        validate_config(p)


def test_validate_config_blocks_openai_key_literal(tmp_path):
    key = "sk-" + "a" * 25   # 25 chars after prefix → matches pattern
    p = tmp_path / "config.yaml"
    p.write_text(f"providers:\n  openai:\n    api_key_env: {key}\n")
    with pytest.raises(ConfigValidationError):
        validate_config(p)


def test_validate_config_blocks_google_key_literal(tmp_path):
    key = "AIza" + "A" * 35   # exactly 35 chars after prefix
    p = tmp_path / "config.yaml"
    p.write_text(f"providers:\n  google:\n    api_key_env: {key}\n")
    with pytest.raises(ConfigValidationError):
        validate_config(p)


def test_validate_config_passes_for_env_var_references(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(CONFIG_YAML)
    validate_config(p)  # must not raise
