# Task Dispatch

## Purpose
This skill governs how the orchestrator loads, validates, sorts, and dispatches implementation tasks at the start of Stage 3. Its output is a sequence of `Send("implementation_node", {"task_id": tid})` calls — one per task — that drive the Stage 3 parallel fan-out.

The Python functions in `monkey_devs/tasks.py` implement this logic: `validate_tasks_yaml()`, `load_tasks()`, `topological_sort()`, and `update_task_status()`. The skill documents the intent and required sequence so the orchestrator reasons correctly about ordering, status tracking, and failure handling.

## When to Apply
Once, at the entry of Stage 3, before any implementation node is invoked. The task file (`.opencode/tasks.yaml`) must exist and be produced by `task-decomposition` in Stage 2. Do not dispatch if the file is absent — surface the missing file to the user and block the stage.

## Dispatch Sequence

Run these steps in order. Do not proceed past a failure.

### Step 1: Validate the Task File

Call `validate_tasks_yaml(path)` before loading anything. This checks:
- All required fields are present on every task: `id`, `title`, `description`, `status`, `depends_on`, `failure_classification`
- All `status` values are one of `pending`, `in-progress`, `done`
- All `depends_on` IDs reference tasks that exist in the same file

If validation raises `ValueError`, surface the error to the user with the specific task ID and missing field. Do not proceed to dispatch. The tasks file was produced by `task-decomposition` and validated there — a validation failure here means the file was modified after Stage 2 or the schema changed.

### Step 2: Load Tasks

Call `load_tasks(path)` to get the list of task dicts. At this point, all tasks should have `status: pending`. If any task has `status: in-progress` or `done`, a previous Stage 3 run was interrupted:

- `done` tasks: skip dispatch — do not re-run work that completed successfully
- `in-progress` tasks: reset to `pending` via `update_task_status()` before dispatching — the implementation was interrupted and may be incomplete

### Step 3: Topological Sort

Call `topological_sort(tasks)` on the full task list (including tasks that will be skipped). The sort uses Kahn's algorithm — it processes tasks with no unmet dependencies first, then progressively unlocks dependents.

If the sort raises `TaskCycleError`, a dependency cycle exists in the task graph. Surface this to the user immediately:

```
TaskCycleError: Cycle detected in task depends_on
Dispatch blocked — tasks.yaml contains a circular dependency.
Check the depends_on fields in .opencode/tasks.yaml and remove the cycle.
```

Do not attempt to dispatch any tasks after a `TaskCycleError`. The cycle must be resolved in `.opencode/tasks.yaml` before Stage 3 can proceed.

The sorted order is the dispatch order. Tasks that appear earlier in the sorted list have no unmet dependencies at that point — they can begin immediately. Tasks that appear later depend on earlier tasks completing first.

### Step 4: Dispatch Tasks

For each task in sorted order, skipping those already `done`:

1. Mark the task `in-progress` via `update_task_status(path, task_id, "in-progress")`
2. Emit `Send("implementation_node", {"task_id": task_id})`
3. Record the task ID in `state["tasks_dispatched"]`

The `Send()` call triggers LangGraph's fan-out — multiple implementation nodes may run concurrently when their dependencies are satisfied. The topological order of dispatch ensures that no task is dispatched before its dependency has been dispatched, but concurrent execution among independent tasks is expected and correct.

### Step 5: Track Completion

Each implementation node is responsible for calling `update_task_status(path, task_id, "done")` when it finishes successfully. The orchestrator records the task ID in `state["tasks_completed"]` when the node returns.

If an implementation node fails (exception, timeout, or blocking error):
- Do not mark the task `done`
- Leave it as `in-progress` or reset to `pending`
- Record the failure in the stage gate before presenting to the user
- The user can reject Stage 3 with a correction reason — the correction handoff re-enters the dispatch loop, skipping `done` tasks and retrying incomplete ones

## Atomic Status Updates

Never write `.opencode/tasks.yaml` directly with a file write. Always use `update_task_status(path, task_id, status)`, which:
1. Acquires `_lock` (asyncio) — prevents concurrent writes from corrupting the file
2. Reads the current file
3. Updates the target task's status
4. Writes to a `.yaml.tmp` file first
5. Renames `.yaml.tmp` → `.yaml` atomically via `os.replace()`

This sequence ensures that a crash mid-write leaves the original file intact, not a partial write. If you bypass `update_task_status` and write the YAML directly, a concurrent status update from another task will corrupt the file.

## Dispatch State in WorkflowState

The orchestrator maintains task progress in `WorkflowState`:

| Field | Set when |
|---|---|
| `state["tasks"]` | Populated with all task IDs before dispatch begins |
| `state["tasks_dispatched"]` | Each task ID added as `Send()` is emitted |
| `state["tasks_completed"]` | Each task ID added when its node returns successfully |
| `state["current_task_index"]` | Tracks position in the sorted list for resumption |

These fields are read by the Stage 3 stage gate renderer to show task progress:
```
Tasks   12 / 15 completed
```

## Connection to Handoff Composer

Each dispatched task ID is used by `compose_handoff()` to build a per-task handoff. The handoff-composer skill specifies what goes into each Stage 3 handoff — in particular, the `task_id` and `task_description` fields in the CONTEXT block. Dispatch provides the `task_id`; the handoff-composer reads the task description from tasks.yaml.

The implementation node receives only its own task's context. It does not receive other tasks' descriptions, implementations, or results.

## Boundaries
- Do not dispatch any task before `validate_tasks_yaml()` passes
- Do not dispatch any task after `TaskCycleError` — surface and block
- Do not re-dispatch tasks with `status: done` — skip them
- Do not write tasks.yaml directly — always use `update_task_status()`
- Do not dispatch Stage 3 if tasks.yaml does not exist — surface the missing file and block
- Do not modify `depends_on` or `id` fields during dispatch — only `status` and `failure_classification` are updated at runtime
