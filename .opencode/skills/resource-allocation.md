# Resource Allocation

## Purpose
This skill governs how the orchestrator selects the skills and tools to allocate for each stage. The Python functions `get_skills_for_stage()`, `get_tools_for_stage()`, and `load_skill_by_name()` in `monkey_devs/orchestrator.py` implement this logic. The skill documents the intent and expected behaviour so the orchestrator — and any developer debugging it — can reason about allocation decisions correctly.

Resource allocation is what makes the system extensible without code changes (NFR-06). New skills and tools are registered in `.opencode/registry.yaml` and immediately become available to the appropriate stages. No stage node definition changes. No code changes. Registry is the only file that needs updating.

## When to Apply

Two moments in the workflow:

1. **At workflow start** — `load_registry()` reads `.opencode/registry.yaml` and validates its structure. A malformed registry raises `ValueError` immediately, before any stage runs.
2. **Before each stage handoff** — `get_skills_for_stage()` and `get_tools_for_stage()` filter the loaded registry for the current stage number. Their output is passed to `compose_handoff()` to build the SKILLS and TOOLS blocks, and to the CLI stage gate renderer to display the allocation to the user.

## The Two Allocation Rules

### Skills

A skill is allocated to a stage if and only if:
1. The stage number is in the skill's `stages` list, **and**
2. `0` is not in the skill's `stages` list

The second condition is the stage 0 guard. It means a skill marked `stages: [0]` is never bulk-allocated to any stage handoff, even if requested for stage 0. Stage 0 skills are orchestrator-internal and are loaded individually by name — never injected in bulk.

Implemented as:
```python
stage in s.get("stages", []) and 0 not in s.get("stages", [])
```

### Tools

A tool is allocated to a stage if the stage number is in the tool's `stages` list. No stage 0 guard applies — tools do not have an orchestrator-only concept.

Implemented as:
```python
stage in t.get("stages", [])
```

## Stage 0: Orchestrator-Only Skills

Stage 0 skills (`stages: [0]`) are never injected into stage node handoffs. They are documentation for the orchestrator's own reasoning — loaded explicitly when the orchestrator needs to perform an internal operation:

- `adversarial-review` — loaded when the orchestrator runs a review pass on stage artifacts
- `stage-gate` — loaded when presenting a gate summary to the user
- `handoff-composer` — loaded when composing a handoff message
- `task-dispatch` — loaded when dispatching Stage 3 implementation tasks
- `resource-allocation` — this file; loaded when the orchestrator reasons about allocation

Load a stage 0 skill by name using `load_skill_by_name(registry, name, base_path)`. This function validates that the resolved path stays within the project root before reading — do not bypass it with a direct file read.

Never include `0` in a skill's `stages` list alongside other stage numbers (e.g., `stages: [0, 3]`). The stage 0 guard excludes any skill that lists `0` from all bulk allocation, regardless of which other stages are listed.

## Validation

**At registry load time** (`load_registry()`):
- The registry file must exist and be valid YAML — raises `ValueError` with the file path if not
- The top-level structure must be a mapping — raises `ValueError` if it is empty or not a dict
- Every skill entry must have a `stages` field that is a list — raises `ValueError` naming the skill if not

**At allocation time** (`get_skills_for_stage()`):
- If the filtered skill list is empty for a non-zero stage, emit a warning — this is unusual and likely a registry misconfiguration, but it is not fatal
- Skill files that are missing at their registered `path` are silently skipped during handoff composition — `compose_handoff()` checks `.exists()` before reading. This is intentional: a missing file does not block the workflow, but the skill content will not appear in the handoff

**On a missing skill file:**
The warning from an empty skill list is the signal to investigate. Check that the `path` field in `registry.yaml` points to an existing file. The path is relative to the project root.

## Output

`get_skills_for_stage(registry, stage)` returns a list of skill dicts matching the registry schema:

```python
[
    {"name": "tdd-implementation", "description": "...", "stages": [3], "path": ".opencode/skills/tdd-implementation.md"},
    {"name": "code-generation", "description": "...", "stages": [3], "path": ".opencode/skills/code-generation.md"},
]
```

`get_tools_for_stage(registry, stage)` returns a list of tool dicts:

```python
[
    {"name": "filesystem", "description": "...", "type": "builtin", "stages": [1,2,3,4,5], "connection": "builtin"},
    {"name": "bash", "description": "...", "type": "builtin", "stages": [3,4], "connection": "builtin"},
]
```

These lists are consumed immediately by two downstream consumers:

| Consumer | Uses the lists for |
|---|---|
| `compose_handoff()` | Reads each skill's `path` and injects the file content into the SKILLS block; injects tool names and descriptions into the TOOLS block |
| CLI stage gate renderer | Displays skill and tool names to the user before they approve or reject the stage |

## Allocation Decisions Are Observable

The stage gate always shows the user which skills and tools were allocated for the stage they are about to approve. If allocation looks wrong — wrong skills, unexpected tools — the user can inspect the registry directly at `.opencode/registry.yaml` and fix the `stages` fields without touching any code.

## Boundaries
- Never read skill file content during allocation — allocation produces lists of registry entries, not file content; `compose_handoff()` reads the files
- Never allocate a stage 0 skill to a stage handoff — load it by name via `load_skill_by_name()` instead
- Never add `0` alongside other stage numbers in a skill's `stages` list — the guard excludes the skill from all bulk allocation
- Never modify stage node code to add skills or tools — update `registry.yaml` only
