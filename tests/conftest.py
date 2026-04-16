"""Shared pytest fixtures for Monkey Devs tests."""
import pytest


@pytest.fixture
def minimal_state(tmp_path):
    """Return a WorkflowState dict with sensible defaults for testing."""
    return {
        "project_name": "test-project",
        "project_path": str(tmp_path),
        "current_stage": 1,
        "workflow_status": "active",
        "stage_statuses": {},
        "stage_outputs": {},
        "stage_models": {},
        "correction_active": False,
        "correction_stage": None,
        "correction_reason": None,
        "tasks": [],
        "tasks_dispatched": [],
        "tasks_completed": [],
        "current_task_index": 0,
        "gate_decisions": {},
        "allocated_skills": {},
        "allocated_tools": {},
        "thread_id": "test-thread-001",
        "correction_counts": {},
        "review_verdicts": {},
        "review_brief_paths": {},
        "review_skipped": {},
    }
