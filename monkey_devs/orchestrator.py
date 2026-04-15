"""Orchestrator functions: registry loading, skill/tool selection, handoff composition."""
import pathlib

import yaml


def load_registry(path: pathlib.Path) -> dict:
    """Load and return the raw registry YAML as a dict."""
    return yaml.safe_load(path.read_text())


def get_skills_for_stage(registry: dict, stage: int) -> list[dict]:
    """Return skills whose stages list includes the given stage number.

    Stage 0 is reserved for orchestrator-only reference skills and is never
    returned by this function for normal stage handoffs.
    """
    return [
        s for s in registry.get("skills", [])
        if stage in s.get("stages", []) and stage != 0
    ]


def get_tools_for_stage(registry: dict, stage: int) -> list[dict]:
    """Return tools whose stages list includes the given stage number."""
    return [t for t in registry.get("tools", []) if stage in t.get("stages", [])]


def load_skill_by_name(registry: dict, name: str, base_path: pathlib.Path) -> str:
    """Load a skill file by name, resolving its path relative to base_path.

    Used for stage-0 (orchestrator-only) skills like adversarial-review that
    are never injected via get_skills_for_stage().

    Raises:
        KeyError: if the skill name is not found in the registry.
    """
    for skill in registry.get("skills", []):
        if skill["name"] == name:
            return (base_path / skill["path"]).read_text()
    raise KeyError(f"Skill '{name}' not found in registry")
