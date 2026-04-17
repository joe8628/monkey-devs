"""Orchestrator functions: registry loading, skill/tool selection, handoff composition."""
import pathlib
import warnings

import yaml


def load_registry(path: pathlib.Path) -> dict:
    """Load and return the raw registry YAML as a dict."""
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse registry file {path}: {exc}") from exc
    if data is None:
        raise ValueError(f"Registry file {path} is empty.")
    if not isinstance(data, dict):
        raise ValueError(f"Registry file {path} must contain a top-level mapping.")

    for skill in data.get("skills", []):
        if not isinstance(skill.get("stages"), list):
            skill_name = skill.get("name", "<unnamed skill>")
            raise ValueError(
                f"Registry file {path} has invalid stages for skill '{skill_name}': expected a list."
            )
    return data


def get_skills_for_stage(registry: dict, stage: int) -> list[dict]:
    """Return skills whose stages list includes the given stage number.

    Stage 0 is reserved for orchestrator-only reference skills. Any skill whose
    stages list includes 0 is excluded, regardless of what stage is requested.
    """
    skills = [
        s for s in registry.get("skills", [])
        if stage in s.get("stages", []) and 0 not in s.get("stages", [])
    ]
    if stage != 0 and not skills:
        warnings.warn(f"Registry returned no skills for stage {stage}.", stacklevel=2)
    return skills


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
    base_root = base_path.resolve()
    for skill in registry.get("skills", []):
        if skill["name"] == name:
            skill_path = (base_path / skill["path"]).resolve()
            try:
                skill_path.relative_to(base_root)
            except ValueError as exc:
                raise ValueError(
                    f"Skill '{name}' resolves outside project root: {skill['path']}"
                ) from exc
            return skill_path.read_text()
    raise KeyError(f"Skill '{name}' not found in registry")


def compose_handoff(state, stage: int, registry: dict, skills_base, config,
                    task_id: str | None = None, prior_paths: dict | None = None,
                    sub_stage: str | None = None) -> str:
    """Compose a structured handoff prompt for a given stage.

    Returns a string with four blocks: CONTEXT, SKILLS, TOOLS, INSTRUCTIONS.
    """
    max_chars: int = getattr(config, "max_handoff_chars", 400000)

    skills = get_skills_for_stage(registry, stage)
    tools = get_tools_for_stage(registry, stage)

    skill_parts = []
    chars_used = 0
    for s in skills:
        skill_path = pathlib.Path(skills_base) / s["path"]
        if not skill_path.exists():
            warnings.warn(f"Skill file not found: {skill_path}", stacklevel=2)
            continue
        part = f"---\n## Skill: {s['name']}\n{skill_path.read_text()}"
        if chars_used + len(part) > max_chars:
            break
        skill_parts.append(part)
        chars_used += len(part)
    skills_block = "\n".join(skill_parts)

    prior_block = ""
    for s_key, paths in (prior_paths or {}).items():
        for p in paths:
            content = pathlib.Path(p).read_text() if pathlib.Path(p).exists() else ""
            chunk = f'\n<prior-stage-output stage="{s_key}">\n{content}\n</prior-stage-output>'
            if chars_used + len(chunk) > max_chars:
                break
            prior_block += chunk
            chars_used += len(chunk)

    tools_block = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
    return (f"## HANDOFF: Stage {stage}\n\n### CONTEXT\nproject: {state['project_name']}\n"
            f"stage: {sub_stage or stage}\ntask_id: {task_id or 'all'}\n{prior_block}\n\n"
            f"### SKILLS\n{skills_block}\n\n### TOOLS\n{tools_block}\n\n### INSTRUCTIONS\n"
            f"[Stage {stage} directive: produce required artifacts and emit <artifact path=\"...\">...</artifact> blocks.]")
