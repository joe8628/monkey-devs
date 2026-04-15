"""LangGraph workflow state schema for Monkey Devs."""
from typing import TypedDict


class WorkflowState(TypedDict):
    project_name: str
    project_path: str
    current_stage: int                        # 1–5
    workflow_status: str                      # active | completed | interrupted
    stage_statuses: dict[int, str]            # pending | active | complete | approved | rejected
    stage_outputs: dict[int | str, list[str]] # absolute artifact paths per stage/sub-stage
    stage_models: dict[int | str, str]        # model used per stage/sub-stage (audit)
    correction_active: bool
    correction_stage: int | None
    correction_reason: str | None
    tasks: list[str]                          # task IDs from tasks.yaml
    tasks_dispatched: list[str]
    tasks_completed: list[str]
    current_task_index: int                   # index into tasks[] for Stage 3 Send() fan-out
    gate_decisions: dict[int, str]            # approved | fix | rejected
    allocated_skills: dict[int, list[str]]
    allocated_tools: dict[int, list[str]]
    thread_id: str                            # LangGraph thread ID used for interrupt/resume
    correction_counts: dict[int, int]         # number of correction cycles per stage
    review_verdicts: dict[int, str]           # pass | warn | block per stage
    review_brief_paths: dict[int, str]        # absolute path to fix brief per stage
    review_skipped: dict[int, bool]           # True when review verdict was pass
