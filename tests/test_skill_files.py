import pathlib
import yaml

SKILLS = [
    "conversational-intake", "requirements-writing", "stack-evaluation",
    "system-design", "task-decomposition", "adr-writing", "stack-decision",
    "tdd-implementation", "code-generation", "test-categorization",
    "systematic-debugging", "delivery-summary", "readme-writing",
    "resource-allocation", "stage-gate", "handoff-composer", "task-dispatch",
    "adversarial-review", "api-documentation", "developer-guide-writing",
    "docstring-writing",
]

BASE = pathlib.Path(".opencode")


def test_all_skill_files_exist():
    for name in SKILLS:
        p = BASE / "skills" / f"{name}.md"
        assert p.exists(), f"Missing: {p}"
        assert len(p.read_text().strip()) >= 100, f"Too short: {p}"


def test_registry_yaml_schema():
    data = yaml.safe_load((BASE / "registry.yaml").read_text())
    assert "skills" in data and "tools" in data
    skill_names = {s["name"] for s in data["skills"]}
    for name in SKILLS:
        assert name in skill_names, f"Missing skill in registry: {name}"
    for skill in data["skills"]:
        assert "name" in skill
        assert "stages" in skill
        assert "path" in skill
        assert isinstance(skill["stages"], list)


def test_registry_tool_entries():
    data = yaml.safe_load((BASE / "registry.yaml").read_text())
    tool_names = {t["name"] for t in data["tools"]}
    for name in ["filesystem", "bash", "web-search"]:
        assert name in tool_names, f"Missing tool: {name}"


def test_config_yaml_has_all_model_keys():
    data = yaml.safe_load((BASE / "config.yaml").read_text())
    for key in ["concept-spec", "architecture", "implementation",
                "code-fixing", "delivery", "reviewer", "fixer"]:
        assert key in data["models"], f"Missing model key: {key}"


def test_config_yaml_has_no_key_literals():
    import re
    text = (BASE / "config.yaml").read_text()
    patterns = [
        re.compile(r"sk-[a-zA-Z0-9\-_]{20,}"),
        re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        re.compile(r"sk-ant-[a-zA-Z0-9\-_]{90,}"),
    ]
    for p in patterns:
        assert not p.search(text), "API key literal found in config.yaml"
