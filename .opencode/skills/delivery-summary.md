# Delivery Summary

## Purpose
This skill governs how to produce `docs/delivery.md` in Stage 5. It is the first artifact written in the delivery stage and the primary document the user reads to understand what was built, whether it works, and how to use it.

The audience is the solo operator who commissioned the workflow. They were not involved in Stages 1–4 and have not read the intermediate artifacts. `docs/delivery.md` is their entry point. Write it so they can evaluate the output and start using it without reading anything else.

## When to Apply
At the start of Stage 5, before `readme-writing`, `api-documentation`, or any other Stage 5 skill. The delivery summary is the executive document — everything else in Stage 5 expands on it.

## Inputs

Read before writing anything:

- `docs/concept.md` — the original goals, scope, and non-goals from Stage 1. What Was Built must be measurable against these goals.
- `docs/spec.md` — the FRs and NFRs. Known Limitations must reference any FR that is not fully implemented.
- `docs/architecture.md` — the locked technology stack. Key Files and How to Run Locally must reflect the actual stack chosen.
- `.opencode/tasks.yaml` — the implementation ledger. Every task with `status: done` was delivered. Any task with `failure_classification` was a problem. Surface both.
- The source directory — read the actual files before listing them in Key Files. Do not describe files from memory or inference.

## Pre-Flight Verification

Before writing any section, verify the state you are about to report:

**1. Run the test suite**

```
uv run pytest
```

Record the exact result: number of tests collected, passed, failed, and skipped. This is the number you will write in the delivery summary. Do not report a test count you did not verify yourself in this session.

**2. Read tasks.yaml completely**

Count tasks by status:
- `done` — implemented and passing
- `in-progress` or `pending` — incomplete (escalate before writing; Stage 5 should not run on incomplete Stage 3/4 work)
- Any `failure_classification` set — a test failure that was classified but not necessarily resolved

If any task remains `pending` or `in-progress`, do not proceed. Surface this to the user — Stage 5 should only begin after Stages 3 and 4 are complete.

**3. Verify the setup commands work**

Run the exact commands you plan to write in "How to Run Locally" in a clean shell context. If a command fails, fix the problem before writing the section. Never write setup instructions you have not verified.

## Writing Each Section

### What Was Built

One paragraph, 4–6 sentences. Answer in order:
1. What does this software do? (name the capability, not the implementation)
2. Who is it for, and what problem does it solve?
3. How does it work at the highest level? (architecture in one sentence)
4. What is the primary way a user interacts with it?

**Weak** (implementation-focused, no user value):
> A Python CLI built with Typer and LangGraph that runs a five-stage workflow using SQLite checkpointing.

**Strong** (user-focused, names the value):
> Monkey Devs is a Python CLI that runs a five-stage AI-assisted development workflow for solo operators who want to produce working software without writing code manually. The user describes what they want to build; the system conducts intake, produces a specification and architecture, implements the code, runs and fixes tests, and delivers a working repository — pausing for user approval at each stage boundary. The workflow persists to SQLite so it can resume after a session crash without losing progress.

### Key Files

A table of the 6–10 most important files. "Important" means: a developer who wants to understand or extend the system would read these first.

| File | Purpose |
|------|---------|
| `relative/path/to/file` | one sentence — what it is and what it does |

Rules:
- Read each file before describing it — do not describe from inference
- Include the main entry point, the core state/model definitions, the primary configuration file, and the test directory
- Exclude generated files, lock files, and files that are derivative of others (e.g., `__pycache__`)
- Use paths relative to the project root

### How to Run Locally

Numbered steps from a clean environment (no prior setup assumed). Include every step, in order:

1. Prerequisites — runtime version, any system dependencies
2. Install — the exact install command
3. Configuration — any environment variables or config files that must exist before running
4. Run — the exact command to start the application

Use a code block for every command. Verify each command works before writing it.

**Do not** include steps that are not required. If the tool installs dependencies automatically, do not add a manual `pip install` step.

### How to Run Tests

The exact command to execute the full test suite, followed by what a passing run looks like:

```bash
uv run pytest
```

Include the test count from the run you performed in Pre-Flight Verification:

> Running the suite as of delivery: **NN passed, 0 failed** (uv run pytest).

If any tests failed and were classified in Stage 4, list them here with their classification and status — do not omit them.

### Known Limitations

An honest list of what was not built, not working, or not production-ready. This section has three sources:

**1. Unimplemented scope** — FRs from `docs/spec.md` with no corresponding completed task in `tasks.yaml`. List each FR ID and a one-line description of what it covers.

**2. Classified failures** — Any task in `tasks.yaml` with `failure_classification` set. For each:
- Task ID and title
- Classification: `code-issue` or `test-issue`
- One-line description of what is not working

**3. Explicit non-goals** — Items from `docs/concept.md` Non-Goals section that a reader might expect to be present. Briefly confirm they are out of scope.

If there are no known limitations in categories 1 and 2, say so explicitly:
> All FRs from `docs/spec.md` are implemented. No test failures remain classified as unresolved.

Do not leave this section empty or write vague statements like "some edge cases may not be handled." Be specific or state there are none.

## Output Format

Write `docs/delivery.md` with this structure:

```markdown
# Delivery: [Project Name]

> Delivered: [Date] | Tests: NN passed, N failed | Tasks: NN/NN completed

## What Was Built
[one paragraph]

## Key Files

| File | Purpose |
|------|---------|
| `path/to/file` | description |

## How to Run Locally

1. **Prerequisites**: [runtime version and system dependencies]
2. **Install**:
   ```bash
   [install command]
   ```
3. **Configure**: [env vars or config files needed, or "No additional configuration required."]
4. **Run**:
   ```bash
   [run command]
   ```

## How to Run Tests

```bash
uv run pytest
```

Running the suite as of delivery: **NN passed, 0 failed**.

## Known Limitations

[list, or explicit statement that there are none]
```

## After Writing

State that `docs/delivery.md` is complete and what follows in Stage 5:
- `readme-writing` — produces `README.md` for the project root; uses the setup steps and project description from `docs/delivery.md` as its source of truth
- `api-documentation`, `developer-guide-writing`, `docstring-writing` — expand specific sections with technical depth

If Known Limitations named unresolved `code-issue` failures, surface them explicitly so the user can decide whether to re-enter Stage 4 before accepting delivery.

## Boundaries
- Do not write any section before completing Pre-Flight Verification
- Do not report a test count you did not verify in this session
- Do not omit tasks with `failure_classification` from Known Limitations
- Do not write "How to Run" steps you have not executed and confirmed
- Do not begin Stage 5 documentation if any task remains `pending` or `in-progress` — surface this to the user first
