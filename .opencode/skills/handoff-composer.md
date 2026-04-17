# Handoff Message Composition

## Purpose
This skill governs how the orchestrator composes the handoff message for each stage node invocation. The handoff is the stage node's complete system prompt — the node has no other context. What is not in the handoff does not exist for that node.

`compose_handoff()` in `monkey_devs/orchestrator.py` implements this logic. The skill documents the intent and composition strategy so the orchestrator reasons correctly about what each stage needs and what it must never receive.

## When to Apply
Before every stage node invocation:
- Once per stage for Stages 1, 2, 4, and 5
- Once per task for Stage 3 — each implementation task gets its own handoff with its own `task_id` and task description in CONTEXT

## The Four Blocks

The handoff is always exactly four blocks in this order. Never omit a block; never add a fifth.

---

### Block 1: CONTEXT

```
### CONTEXT
project: [project_name from WorkflowState]
stage: [sub_stage key or stage number]
task_id: [T-NN or "all"]
[prior stage outputs]
```

**`project`** — `state["project_name"]`. Identifies which project the node is working on.

**`stage`** — The `sub_stage` parameter if provided (e.g., `"3-T-01"` for a specific implementation task), otherwise the integer stage number. The sub-stage key appears in `stage_outputs` for per-task tracking in Stage 3.

**`task_id`** — The specific task ID for Stage 3 per-task handoffs (e.g., `"T-03"`), or `"all"` for stages that process the full scope at once.

**Prior stage outputs** — Each prior artifact is wrapped in a delimiter:

```
<prior-stage-output stage="1">
[full file content of docs/concept.md]
</prior-stage-output>

<prior-stage-output stage="1">
[full file content of docs/spec.md]
</prior-stage-output>
```

Use the `stage` attribute to identify which stage produced the artifact. One `<prior-stage-output>` block per file — do not bundle multiple files into one block. If a file does not exist at its registered path, include an empty block rather than omitting it, so the node knows the path was attempted.

**Prior output selection by stage** — Include only what the node needs to do its work. More is not better; large prior outputs consume context that the node needs for reasoning.

| Stage | Include as prior outputs |
|---|---|
| 1 — Concept & Spec | None — first stage |
| 2 — Architecture | Stage 1: `docs/concept.md`, `docs/spec.md`, `docs/stack-candidates.md` |
| 3 — Implementation (per task) | Stage 2: `docs/architecture.md`, `.opencode/tasks.yaml`; the specific task description extracted from tasks.yaml |
| 4 — Code Fixing | Stage 2: `docs/architecture.md`; Stage 3 test output summary (not all source files — they are on disk and the node can read them) |
| 5 — Delivery | Stage 2: `docs/architecture.md`; Stage 4: `.opencode/tasks.yaml` with classifications; Stage 3/4 test summary |

For Stage 3, also append the specific task's full description block from `.opencode/tasks.yaml` as a named field in CONTEXT:

```
task_description: |
  What to build: [...]
  Interface: [...]
  How to verify: [...]
```

This makes the task description immediately visible without requiring the node to parse the full tasks.yaml.

---

### Block 2: SKILLS

```
### SKILLS
---
## Skill: tdd-implementation
[full content of .opencode/skills/tdd-implementation.md]
---
## Skill: code-generation
[full content of .opencode/skills/code-generation.md]
```

`get_skills_for_stage(registry, stage)` returns the filtered skill list. For each skill:
1. Emit a `---` separator
2. Emit `## Skill: [name]` as a heading
3. Read the skill file at its registered `path` and emit the full content

Skills whose file does not exist at their registered path are silently skipped — `compose_handoff()` checks `.exists()` before reading. If the SKILLS block is empty for a non-zero stage, a warning was emitted by `get_skills_for_stage()` — investigate the registry before proceeding.

Do not summarise or truncate skill content. The node receives the full skill text — that is the point of skill injection.

---

### Block 3: TOOLS

```
### TOOLS
- filesystem: Read/write access to local filesystem
- bash: Shell command execution (allowlisted commands only)
```

`get_tools_for_stage(registry, stage)` returns the filtered tool list. For each tool: emit `- [name]: [description]`.

The TOOLS block lists names and descriptions only. The tool JSON schema (the OpenAI function-calling format) is passed separately to the LLM API call by LiteLLM — it is not part of the handoff message. The TOOLS block tells the node *what is available*; the API call gives it *how to invoke*.

If no tools are allocated for a stage, emit the block header with the word `none`:

```
### TOOLS
none
```

Never omit the TOOLS block — its absence would be ambiguous.

---

### Block 4: INSTRUCTIONS

```
### INSTRUCTIONS
[Stage-specific directive — what to produce, what artifacts to emit, completion signal]
```

The INSTRUCTIONS block is where the orchestrator tells the node what to do with its allocated skills and tools. It must be:
- **Specific** — name the artifacts to produce and their paths
- **Bounded** — state what the node must not do (e.g., "do not make a final stack decision — propose candidates only")
- **Complete** — include the artifact emission protocol

**Artifact emission protocol** — every stage node signals completion by emitting artifact blocks in its response. The orchestrator scans the node's output for these blocks and records the paths in `stage_outputs`:

```
<artifact path="docs/concept.md">
[file content]
</artifact>
```

The INSTRUCTIONS block must tell the node to use this format. Example for Stage 2:

```
### INSTRUCTIONS
Produce the following artifacts for Stage 2 — Architecture:
- docs/architecture.md — Technology Stack section (stack-decision skill), then
  System Design section (system-design skill), then ADR section (adr-writing skill)
- .opencode/tasks.yaml — task breakdown (task-decomposition skill)

Write each file to disk and emit it as:
  <artifact path="relative/path">content</artifact>

Do not advance to Stage 3. Do not write implementation code. Signal completion
by emitting all artifact blocks above.
```

**Security rule** — never concatenate unvalidated user text into the INSTRUCTIONS block. User-supplied text (project descriptions, rejection reasons, task descriptions from tasks.yaml) belongs in the CONTEXT block, wrapped in delimiters. If user text reached INSTRUCTIONS without wrapping, an adversarial project description could override the stage directive with injected instructions.

## Correction Handoffs

When `state["correction_active"]` is True, the node is being re-invoked after a user rejection. The correction handoff differs from the initial handoff in one place: the CONTEXT block gains a correction field:

```
### CONTEXT
project: [project_name]
stage: [stage]
task_id: all
correction: true
correction_reason: |
  [verbatim text from state["correction_reason"]]
[prior outputs — same as the initial handoff for this stage]
```

The correction reason is the user's verbatim instruction. Do not paraphrase it. Wrap it under the `correction_reason:` key so the node can locate it without parsing the full CONTEXT block.

The SKILLS, TOOLS, and INSTRUCTIONS blocks are identical to the initial handoff for the same stage — the node uses its same skills and tools, directed by the same stage directive. The correction reason in CONTEXT is what tells it to approach the work differently.

## Stage 3 Per-Task Handoff

Stage 3 dispatches one handoff per implementation task. Each handoff is scoped to a single task:

```
### CONTEXT
project: my-project
stage: 3-T-03
task_id: T-03
task_description: |
  What to build: Config loader that parses config.yaml into AppConfig
  Interface: load_config(path: Path) -> AppConfig; raises ValueError on parse error
  How to verify: pytest tests/test_config.py passes
<prior-stage-output stage="2">
[docs/architecture.md content]
</prior-stage-output>
```

Do not include other tasks' descriptions in a per-task handoff. The task boundary is the isolation guarantee — the node for T-03 must not know about T-04's implementation details.

## Boundaries
- Never omit a block — all four blocks are always present
- Never concatenate user text into the INSTRUCTIONS block — it belongs in CONTEXT under a named key
- Never summarise or truncate skill file content in the SKILLS block
- Never include source code files as prior outputs for Stage 4 — they are on disk; the node reads them via the filesystem tool
- Never include Stage 0 skills in the SKILLS block — they are orchestrator-internal and loaded separately via `load_skill_by_name()`
- Never include another task's description in a Stage 3 per-task handoff
