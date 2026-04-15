import pathlib
import pytest
from monkey_devs.orchestrator import (
    load_registry,
    get_skills_for_stage,
    get_tools_for_stage,
    load_skill_by_name,
)

REGISTRY_YAML = """\
skills:
  - name: conversational-intake
    description: "Forge-style intake"
    stages: [1]
    path: .opencode/skills/conversational-intake.md
  - name: system-design
    description: "System design"
    stages: [2]
    path: .opencode/skills/system-design.md
  - name: adversarial-review
    description: "Adversarial critique"
    stages: [0]
    path: .opencode/skills/adversarial-review.md
tools:
  - name: filesystem
    description: "Read/write access"
    type: builtin
    stages: [1, 2, 3, 4, 5]
    connection: builtin
  - name: bash
    description: "Shell execution"
    type: builtin
    stages: [3, 4]
    connection: builtin
"""


@pytest.fixture
def registry(tmp_path):
    p = tmp_path / "registry.yaml"
    p.write_text(REGISTRY_YAML)
    return load_registry(p)


@pytest.fixture
def skill_files(tmp_path, registry):
    """Create skill markdown files at expected paths relative to tmp_path."""
    for skill in registry["skills"]:
        skill_path = tmp_path / skill["path"]
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(f"# Skill: {skill['name']}\nContent here.")
    return tmp_path


def test_load_registry_returns_dict(tmp_path):
    p = tmp_path / "registry.yaml"
    p.write_text(REGISTRY_YAML)
    reg = load_registry(p)
    assert "skills" in reg
    assert "tools" in reg
    assert len(reg["skills"]) == 3
    assert len(reg["tools"]) == 2


def test_get_skills_for_stage_1(registry):
    skills = get_skills_for_stage(registry, 1)
    assert len(skills) == 1
    assert skills[0]["name"] == "conversational-intake"


def test_get_skills_for_stage_2(registry):
    skills = get_skills_for_stage(registry, 2)
    assert len(skills) == 1
    assert skills[0]["name"] == "system-design"


def test_get_skills_for_stage_excludes_stage_0(registry):
    # stage 0 = orchestrator-only; never injected into normal stage handoffs
    skills = get_skills_for_stage(registry, 1)
    names = [s["name"] for s in skills]
    assert "adversarial-review" not in names


def test_get_tools_for_stage_3_has_bash(registry):
    tools = get_tools_for_stage(registry, 3)
    names = [t["name"] for t in tools]
    assert "filesystem" in names
    assert "bash" in names


def test_get_tools_for_stage_1_no_bash(registry):
    tools = get_tools_for_stage(registry, 1)
    names = [t["name"] for t in tools]
    assert "filesystem" in names
    assert "bash" not in names


def test_load_skill_by_name_returns_content(registry, skill_files):
    content = load_skill_by_name(registry, "conversational-intake", skill_files)
    assert "conversational-intake" in content


def test_load_skill_by_name_raises_for_unknown(registry, tmp_path):
    with pytest.raises(KeyError):
        load_skill_by_name(registry, "nonexistent-skill", tmp_path)
