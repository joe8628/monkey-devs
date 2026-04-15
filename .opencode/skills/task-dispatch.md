# Task Dispatch

Before dispatching Stage 3 implementation tasks:

1. Load `.opencode/tasks.yaml`
2. Run topological sort on the `depends_on` fields to determine execution order
3. Validate: no cycles in dependencies; all `depends_on` IDs exist; all tasks have `status: pending`
4. If a cycle is detected, raise `TaskCycleError` and surface it to the user before any dispatch
5. Emit one `Send("implementation_node", {"task_id": tid})` per task in sorted order

Each dispatched task receives its `task_id` in the handoff CONTEXT block and operates independently.
