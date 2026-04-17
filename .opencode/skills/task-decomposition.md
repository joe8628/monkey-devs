# Task Decomposition

## Purpose
This skill governs how to produce `.opencode/tasks.yaml` in Stage 2. The file it creates is the work order for Stage 3: every implementation task that runs is drawn from this list, dispatched in topological order, and tracked through to completion.

A task is the unit of parallel work. Getting decomposition right means Stage 3 agents can work independently without stepping on each other. Getting it wrong — overlapping responsibilities, missing dependencies, tasks that are too large — creates integration failures and wasted work that the code-fixing stage then has to untangle.

## When to Apply
After `docs/architecture.md` contains both the Technology Stack section (written by `stack-decision`) and the System Design section (written by `system-design`). Component boundaries and interface contracts from the system design are the direct input — do not decompose from a spec alone.

## Inputs
Read before beginning:
- `docs/architecture.md` — component definitions, interface contracts, and data models from the system design. Each component is a candidate task unit.
- `docs/spec.md` — FRs provide the verification criteria for each task's description
- `.opencode/tasks.yaml` if it already exists — extend rather than overwrite; note any changes

## Schema

Every task must have all six required fields. The schema is enforced by `validate_tasks_yaml` at the end of Stage 2 — a malformed file will trigger an automatic correction cycle:

```yaml
project: [project-name]
tasks:
  - id: T-01                          # format: T-NN, zero-padded, sequential
    title: "Imperative verb + noun"   # short, actionable — max ~6 words
    description: |
      What to build: <specific component or behaviour>
      Interface: <inputs, outputs, file paths, or function signatures it must satisfy>
      How to verify: <concrete test or observable outcome>
    status: pending                   # pending | in-progress | done — always pending when written
    stage: 3                          # 3 for implementation; set explicitly
    depends_on: []                    # list of T-NN IDs this task cannot start before
    failure_classification: null      # null when written; filled by Stage 4 code-fixing
```

**Field discipline:**
- `title` — imperative form ("Add config loader", not "Config loader" or "Adding config loader")
- `description` — must answer three questions: what to build, what interface it must satisfy, and how to verify it. A description that only says what to build is incomplete.
- `depends_on` — every ID listed must exist in the same file. The runtime will reject unknown references.
- `failure_classification` — always `null` when you write it; Stage 4 fills this in if the task fails.

## Process

### 1. Map Components to Tasks

Start from the Components section in `docs/architecture.md`. Each component with a distinct interface contract is a candidate task. Apply these rules:

**One component → one task** when:
- The component is small and its interface is simple (one or two functions/files)
- It has no meaningful sub-responsibilities

**One component → multiple tasks** when:
- The component has separable concerns (e.g., "data model" vs. "loader logic" vs. "validation")
- Different parts have different dependencies — splitting lets unblocked parts proceed sooner

**Multiple components → one task** when:
- Two components are so tightly coupled that testing one requires the other
- Both are trivial alone but meaningful together

Name each task after the component and the specific work: "Add WorkflowState schema", "Implement registry loader", "Write RunLogger with rotation" — not vague names like "Backend work" or "Data layer".

### 2. Order by Dependency

Ask for each task: "Can this be implemented using only its interface contracts, without reading another task's implementation?" If not, it has a dependency.

Common dependency patterns:
- **Data models first** — any task that stores or retrieves data depends on the model task
- **Foundation before features** — config loaders, loggers, and state schemas before anything that uses them
- **Interface before consumer** — if task B calls a function defined in task A, B depends on A
- **No circular deps** — if A depends on B and B depends on A, the shared interface needs its own task that both depend on

Draw the dependency graph mentally before writing it. Verify it is a DAG (directed acyclic graph) — any cycle will cause `topological_sort` to raise `TaskCycleError` and block Stage 3 dispatch.

### 3. Write Verification Criteria

The `description` field's "how to verify" line is what the Stage 4 code-fixing agent uses to classify a failure as a code issue or a test issue. Be specific:

**Weak** (untestable):
```
description: "Implement the config loader"
```

**Strong** (testable):
```
description: |
  What to build: Config loader that parses config.yaml into AppConfig (Pydantic model)
  Interface: load_config(path: Path) -> AppConfig; raises ValueError with filename on parse error
  How to verify: pytest tests/test_config.py passes — load valid YAML, reject empty file,
    reject missing required model keys, reject API key literals
```

Every verification criterion should be specific enough that a developer can write the test before writing the implementation.

### 4. Cover All FRs

After drafting the task list, cross-check against `docs/spec.md`. Every FR must be implementable through the union of all tasks. If an FR has no task that covers it, either:
- Add a task, or
- Note it explicitly as covered implicitly by an existing task (and say which one)

Uncovered FRs left silent become gaps discovered in Stage 4, after implementation is already done.

### 5. Validate Before Writing

Before writing the file, verify:
- All required fields are present on every task
- All `depends_on` IDs exist in the task list
- No cycles: trace every dependency chain to its root; no chain should loop back
- All statuses are `pending`
- All `failure_classification` values are `null`

## Output

Write to `.opencode/tasks.yaml`. If the file already exists, read it first and preserve any tasks with `status: in-progress` or `done` — only modify `pending` tasks or append new ones.

```yaml
project: [project-name]
tasks:
  - id: T-01
    title: "..."
    description: |
      What to build: ...
      Interface: ...
      How to verify: ...
    status: pending
    stage: 3
    depends_on: []
    failure_classification: null

  - id: T-02
    title: "..."
    description: |
      ...
    status: pending
    stage: 3
    depends_on: [T-01]
    failure_classification: null
```

After writing, state the task count, the maximum dependency depth (longest chain from root to leaf), and any FRs whose coverage depends on multiple tasks working together.

## Boundaries
- Do not write tasks for work outside Stage 3 implementation (no "deploy" or "document" tasks — those belong to Stage 5)
- Do not set `status` to anything other than `pending` when writing
- Do not invent tasks with no corresponding component or FR
- Do not leave `depends_on` empty if a real dependency exists — missing edges cause Stage 3 agents to start work before its prerequisites are ready
- Do not write a task whose description cannot answer "how to verify it"
