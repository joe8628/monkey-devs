"""Tests for compose_handoff in monkey_devs.orchestrator (IU-06)."""
from monkey_devs.orchestrator import compose_handoff


def test_compose_handoff_contains_four_blocks(tmp_path, minimal_state):
    result = compose_handoff(minimal_state, stage=1, registry={}, skills_base=tmp_path, config=None)
    for block in ["### CONTEXT", "### SKILLS", "### TOOLS", "### INSTRUCTIONS"]:
        assert block in result


def test_compose_handoff_wraps_prior_output(tmp_path, minimal_state):
    doc = tmp_path / "docs" / "concept.md"
    doc.parent.mkdir(); doc.write_text("# Concept")
    minimal_state["stage_outputs"] = {}
    result = compose_handoff(minimal_state, stage=2, prior_paths={"1": [str(doc)]},
                             registry={}, skills_base=tmp_path, config=None)
    assert '<prior-stage-output stage="1">' in result
