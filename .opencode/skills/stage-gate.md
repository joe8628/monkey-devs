# Stage Gate Presentation

## Purpose
This skill governs how the orchestrator renders the stage gate summary at each stage boundary. The gate is the user's decision point — they read it to decide whether to approve the stage output and advance, reject and redirect with a reason, or expand the full allocation log for more detail.

The gate must be compact and scannable. The user is making an approval decision, not reading documentation. Every line must earn its place.

## When to Apply
After each stage node completes and before the next stage begins. The orchestrator calls `interrupt()` at this point, which pauses LangGraph execution and hands control to the CLI for gate rendering. Five gates total — one per stage, always.

## Source Data

Read from `WorkflowState` before rendering:

| Field | Used for |
|---|---|
| `current_stage` | Stage number and name in the header |
| `stage_models[stage]` | Model line |
| `allocated_skills[stage]` | Skills Injected line |
| `allocated_tools[stage]` | Tools Granted line |
| `stage_outputs[stage]` | Artifacts Produced list |
| `review_verdicts[stage]` | Review Verdict line |
| `review_brief_paths[stage]` | Fix brief path if verdict is warn or block |
| `correction_counts[stage]` | Correction cycle indicator in the header |
| `tasks_completed`, `tasks_dispatched` | Stage 3 task progress |

For Stage 4: also read `.opencode/tasks.yaml` to retrieve failure classifications and rationale. `WorkflowState` does not store the classification rationale — only the tasks file does.

## Gate Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STAGE GATE — Stage N: [Stage Name]
 Project: [project_name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model       [model name from stage_models]
Skills      [skill-name-1], [skill-name-2], ...
Tools       [tool-name-1], [tool-name-2], ...

Artifacts
  • [relative/path/to/artifact-1]
  • [relative/path/to/artifact-2]

[Stage-specific section — see below]

Review      [verdict] [— path/to/fix-brief.md if warn or block]

Actions
  monkey-devs approve              — advance to Stage N+1
  monkey-devs reject --reason "…"  — trigger correction branch
  monkey-devs details              — expand full allocation log
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Formatting rules:
- Artifact paths are relative to `project_path` — strip the absolute prefix for readability
- Skill and tool names are comma-separated on one line; do not list descriptions
- The Review line is omitted if `review_skipped[stage]` is True
- If `correction_counts[stage]` is greater than 0, append `(correction N)` to the stage name in the header

## Stage-Specific Sections

Each stage has a short section between Artifacts and Review that surfaces the most important result of that stage's work.

---

### Stage 1 — Concept & Spec

```
Spec        [FR count] functional requirements, [NFR count] non-functional requirements
Stack       [N] candidates evaluated — see docs/stack-candidates.md
```

Count FRs and NFRs by scanning `docs/spec.md`. State the candidate count from `docs/stack-candidates.md`. No decision has been made yet — Stage 1 proposes, Stage 2 decides.

---

### Stage 2 — Architecture

```
Stack       [Language] [version] + [primary frameworks] — locked
Tasks       [N] implementation tasks written to .opencode/tasks.yaml
            Max dependency depth: [D]
```

Read the stack from `docs/architecture.md`. Read task count and dependency depth from `.opencode/tasks.yaml`. The word "locked" is important — it signals to the user that the stack decision is binding.

---

### Stage 3 — Implementation

```
Tasks       [N completed] / [N total] completed
Tests       [N passed], [N failed] — uv run pytest
```

Read task counts from `WorkflowState` fields `tasks_completed` and `tasks_dispatched`. Run `uv run pytest --tb=no -q` to get the test summary line and extract the pass/fail count. Do not report a test count you did not verify in this session.

If any tests failed, list the failing test names:

```
Failed      tests/test_config.py::test_load_invalid_key
            tests/test_tools.py::test_bash_boundary
```

---

### Stage 4 — Code Fixing

This stage has the most important stage-specific section. FR-19 requires that failure classifications are presented to the user at the gate with rationale. Present every classified failure:

```
Failures    [N classified]

  T-03  test-issue  test_load_invalid_key asserts ValueError but Interface
                    specifies RuntimeError — test definition mismatch
  T-07  code-issue  validate_path returns None for symlink targets instead
                    of raising FilesystemBoundaryError
```

Format each entry as: `[task-id]  [classification]  [one-sentence rationale]`

If a task's rationale spans two lines, indent the continuation to align with the first line of the rationale.

If all failures were resolved (no `failure_classification` remains set on any incomplete task), say:

```
Failures    None — all tests pass
```

Do not omit the Failures section even when clean. The user needs explicit confirmation that Stage 4 resolved everything before approving.

---

### Stage 5 — Delivery

```
Docs        docs/delivery.md, README.md, docs/api-reference.md,
            docs/developer-guide.md
Tests       [N passed], 0 failed — uv run pytest
```

List the Stage 5 documents that were produced (read from `stage_outputs[5]`). Run the test suite one final time and confirm the count. This is the last gate — the user is approving the final deliverable.

---

## The Three Actions

**`monkey-devs approve`**

Sets `gate_decisions[stage] = "approved"` and advances the workflow to the next stage node. If this is Stage 5, sets `workflow_status = "completed"`.

**`monkey-devs reject --reason "..."`**

Sets `gate_decisions[stage] = "rejected"`, stores the reason in `correction_reason`, sets `correction_stage` to the current stage, and activates the correction branch. The correction branch re-invokes the same stage node with the rejection reason prepended to the handoff CONTEXT block. The workflow resumes from the same stage — not from Stage 1 (FR-23).

The reason is the user's specific instruction. Surface it verbatim in the correction handoff — do not paraphrase.

**`monkey-devs details`**

Expands the full allocation log: all skills with their descriptions, all tools with their types and connection strings, all prior artifact paths, and the full review brief if one exists. This does not change workflow state.

## Correction Cycle Indicator

If `correction_counts[stage]` is greater than 0, the user has already rejected this stage at least once. Append `(correction N)` to the stage name in the header so the user knows this is a retry:

```
 STAGE GATE — Stage 2: Architecture (correction 1)
```

If the correction count reaches 3 for the same stage, add a note below the Failures or stage-specific section:

```
⚠  This stage has been corrected 3 times. Consider rejecting with a more
   specific reason, or approve with known limitations noted in delivery.md.
```

## Boundaries
- Do not include artifact file content in the gate — paths only
- Do not include full skill content — names only
- Do not include the full review brief — path and verdict only; the user runs `details` to expand
- Do not skip the Failures section in Stage 4 even if there are none — show explicit confirmation
- Do not report test counts without running the suite in the current session
- Do not advance the workflow without an explicit `approve` command — the gate always requires user action
