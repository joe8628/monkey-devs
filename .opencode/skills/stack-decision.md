# Stack Decision

## Purpose
This skill governs how to make the final, binding technology stack selection in Stage 2 and write it to `docs/architecture.md`. It runs first among Stage 2 skills — the system design, ADRs, and task decomposition all depend on the stack being locked before they begin.

This decision is irreversible within the current workflow. Changing the stack after Stage 2 invalidates the system design (component boundaries assume specific libraries), the interface contracts (function signatures depend on framework types), and every implementation task in `.opencode/tasks.yaml`. Treat it with the weight it deserves.

## When to Apply
At the start of Stage 2, before any system design work begins. `docs/stack-candidates.md` from Stage 1 must exist — do not make a stack decision without the evaluation evidence.

## Inputs
Read before deciding:
- `docs/stack-candidates.md` — the weighted comparison, filtered candidates, trade-off narratives, and recommendation note from Stage 1
- `docs/spec.md` — NFRs are the final arbiter; re-verify the chosen stack against each one
- `docs/concept.md` — hard constraints and Non-Goals; a stack that violates either is disqualified regardless of score

## Decision Process

### 1. Read the Recommendation Note
`docs/stack-candidates.md` ends with a Recommendation Note — read it first. It flags cases where the weighted rank diverges from what a single critical criterion demands. The top-ranked candidate is the starting point, not the automatic answer.

### 2. Verify Against Hard Constraints
Before accepting the top-ranked candidate, check it against every hard constraint in `docs/concept.md` and every NFR in `docs/spec.md`. A constraint violation disqualifies a candidate regardless of its weighted score.

Work through each NFR explicitly:
- Does the stack satisfy the measurable target?
- Is there a known gap that requires a workaround? If so, is the workaround acceptable?
- Does the stack introduce a new constraint not anticipated in the spec?

If the top-ranked candidate fails this check, move to the next ranked candidate and repeat. If all candidates fail a constraint, surface this to the user — do not pick a non-compliant stack.

### 3. Make the Decision
Select one candidate. State it clearly:
- Primary language and version
- Every framework and library that is part of the core stack
- Testing framework
- Persistence / storage layer
- Build and packaging tooling
- Any key CLI / tooling dependencies

"We will use Python" is not a complete stack decision. "Python 3.11+, Typer for the CLI, LangGraph for the workflow graph, langgraph-checkpoint-sqlite for persistence, LiteLLM for multi-vendor LLM calls, Pydantic for data validation, PyYAML for config parsing, pytest for testing, uv for packaging" is.

### 4. Write the ADR
The stack decision always warrants ADR-001. Use the `adr-writing` skill format. The ADR must include:
- **Context**: the constraints from `concept.md` and the NFRs that drove the selection criteria
- **Decision**: the full stack named in Step 3 above
- **Rationale**: why this stack satisfies the Context constraints — connect to specific NFRs and evaluation criteria, not generic praise
- **Alternatives Considered**: the other candidates from `stack-candidates.md`, with the specific reason each was not chosen
- **Consequences**: what Stage 3 implementation gains and what it gives up

Reference `docs/stack-candidates.md` in the Alternatives Considered section rather than duplicating the full comparison.

### 5. Write docs/architecture.md
Create `docs/architecture.md` if it does not exist. Write the Technology Stack section using the format below. This is the first section of the file — subsequent Stage 2 skills (`system-design`, `adr-writing`) append their sections after it.

## Output Format

```markdown
# Architecture: [Project Name]

> Stack locked: [Date] — no reconsideration in scope after Stage 2

## Technology Stack

### Language and Runtime
- **[Language]** [version] — [one-line reason it was chosen]

### Frameworks
- **[Framework]**: [role in the system]
- **[Framework]**: [role in the system]

### Persistence
- **[Storage layer]**: [what it stores, where the file/service lives]

### Testing
- **[Test framework]**: [scope — unit, integration, e2e]

### Tooling
- **[Tool]**: [purpose — build, packaging, linting, etc.]

### Key Libraries
- **[Library]**: [specific problem it solves]

---

## Architecture Decision Records

### ADR-001: [Stack Selection Title]
- **Status**: Accepted
- **Context**: [...]
- **Decision**: [...]
- **Rationale**: [...]
- **Alternatives Considered**: [...] See docs/stack-candidates.md for full weighted comparison.
- **Consequences**:
  - Easier: [...]
  - Harder: [...]
```

Leave a blank line after the ADR section — `system-design` will append `## System Design` immediately after.

## After Writing

State clearly that the stack is locked and what each subsequent Stage 2 skill will do with it:
- `system-design` — component boundaries and interface contracts will use the locked frameworks and types
- `task-decomposition` — implementation tasks will target the locked stack; no task should assume a different technology
- Future stage nodes — all LLM calls for Stages 3–5 will include this stack record in their handoff context

If any NFR check in Step 2 produced a concern (gap, workaround, or new constraint), surface it explicitly here so the system-design step can account for it.

## Handling Disagreement

If the user disagrees with the top-ranked candidate's selection and wants a different one:
1. Re-run the NFR verification from Step 2 for their preferred candidate
2. Identify any constraints it violates or gaps it introduces
3. If it passes, proceed — user judgement overrides weighted scores
4. If it fails a hard constraint, surface the specific failure and let the user decide whether to accept the risk or modify the constraint

The user is the final authority. The skill's job is to surface evidence, not to override preference.

## Boundaries
- Do not begin writing `docs/architecture.md` before completing the NFR verification in Step 2
- Do not select a stack that violates a hard constraint without explicit user acknowledgement
- Do not write a partial stack — every layer (language, framework, persistence, testing, tooling) must be named
- Do not skip ADR-001 — the stack decision is always the first and most consequential ADR
- Do not proceed to system design until `docs/architecture.md` contains the Technology Stack section
