from monkey_devs.state import WorkflowState


def test_state_schema_has_required_fields():
    fields = WorkflowState.__annotations__
    for f in [
        "project_name", "project_path", "current_stage", "workflow_status",
        "stage_statuses", "stage_outputs", "stage_models", "correction_active",
        "correction_stage", "correction_reason", "tasks", "tasks_dispatched",
        "tasks_completed", "current_task_index", "gate_decisions",
        "allocated_skills", "allocated_tools", "thread_id", "correction_counts",
        "review_verdicts", "review_brief_paths", "review_skipped",
    ]:
        assert f in fields, f"Missing field: {f}"
