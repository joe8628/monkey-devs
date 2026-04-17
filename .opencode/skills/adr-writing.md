# ADR Writing

## Purpose
This skill governs how to write Architecture Decision Records (ADRs) in Stage 2. ADRs are appended to `docs/architecture.md` under the `## Architecture Decision Records` section, alongside the system design.

An ADR records a single decision: what was decided, why it was chosen over the alternatives, and what it makes easier or harder going forward. Its value is not in the decision itself — it is in the reasoning that cannot be recovered later. Stage 3 implementers, Stage 4 debuggers, and Stage 5 documentation writers all encounter the consequences of architectural decisions without knowing why they were made. ADRs are the answer to "why is it like this?"

## When to Write an ADR

Write an ADR whenever a decision meets any of these conditions:

- **Non-obvious** — a reasonable developer would ask "why not the straightforward approach?"
- **Trade-off-bearing** — the chosen option gives something up; there was no clearly dominant choice
- **Plausible alternative ruled out** — another option was considered and rejected; the rejection reasoning should be preserved
- **Constraining** — the decision limits what future stages can do (technology lock-in, data format choices, interface conventions)
- **Revisit-prone** — without documentation, someone will relitigate this decision in Stage 3 or Stage 4

The stack decision written by `stack-decision` always warrants an ADR. Component boundary choices, persistence strategy, inter-process communication patterns, and error-handling conventions typically do too.

## When NOT to Write an ADR

Do not write an ADR for:
- Decisions that follow trivially from the chosen stack ("we use pytest because we chose Python")
- Implementation details that are easily changed without cascading effects
- Personal style choices with no architectural consequence
- Decisions with no real alternatives (there was only one viable option)
- Anything already fully documented in `docs/spec.md`

Over-documentation dilutes the ADR set. If every decision gets an ADR, the important ones get lost.

## Numbering

ADRs are numbered sequentially: ADR-001, ADR-002, ADR-003. Never reuse a number, even if an ADR is deprecated. If `docs/architecture.md` already has ADRs, read the highest existing number and continue from there.

## Writing Each Field

### Status
Use exactly one of:
- `Accepted` — the decision is active and in effect
- `Proposed` — under consideration, not yet finalised
- `Deprecated` — superseded by a later ADR (add "Superseded by ADR-NNN")

All ADRs written during Stage 2 are `Accepted` unless explicitly deferred.

### Context
Describe the forces that made this decision necessary — the constraints, requirements, and pressures that created the situation. This is not background; it is the problem the decision solves.

**Weak context** (background, not forces):
> We needed a way to persist workflow state between runs.

**Strong context** (forces that constrained the decision):
> The workflow must survive process crashes and resume from the last completed stage gate without data loss (NFR-03). LangGraph's native checkpointing requires a backing store. The store must be portable — no external service, no Docker dependency — and must be queryable by thread ID so the CLI can load a specific workflow run.

Reference FR/NFR IDs where they drove the decision.

### Decision
State what was decided in one or two sentences. Use active voice and be specific — name the technology, pattern, or boundary exactly.

**Weak decision:**
> We will use a database for state persistence.

**Strong decision:**
> We will use SQLite via `langgraph-checkpoint-sqlite` as the LangGraph checkpointer, storing all workflow state in `.opencode/workflow-state.db` relative to the project root.

### Rationale
Explain why this option over the alternatives. Do not list the alternatives here — that goes in Alternatives Considered. Focus on what properties of the chosen option satisfy the constraints from Context.

Connect back to specific criteria: performance characteristics, portability, ecosystem maturity, team familiarity, NFR fit. A rationale that doesn't reference the Context is not a rationale — it is a preference.

### Alternatives Considered
List the real alternatives that were evaluated and why each was rejected. These must be genuine alternatives, not strawmen set up to be knocked down.

For each alternative: name it, describe it in one sentence, and give the specific reason it was rejected.

```
- **PostgreSQL**: Full-featured relational store with excellent LangGraph support.
  Rejected: requires a running server process, violating the portability constraint.
- **JSON files**: Simple file-per-checkpoint approach, zero dependencies.
  Rejected: no atomic multi-key updates; concurrent writes risk corruption on crash.
```

If the evaluation was more thorough (e.g., a `stack-candidates.md` exists for the decision), reference it: "See docs/stack-candidates.md for the full weighted comparison."

### Consequences
Be honest about what this decision makes harder, not just easier. One-sided consequences are a sign the author is advocating, not documenting.

Format as two lists:

```
Easier:
- Resumable workflows with zero external dependencies (NFR-03 satisfied)
- Thread-based isolation: multiple parallel workflows share one file

Harder:
- SQLite write concurrency limited to one writer; parallel stage execution
  must serialise checkpoint writes
- No built-in migration tooling; schema changes require manual migration scripts
```

## Full ADR Format

```markdown
### ADR-NNN: [Short Decision Title — noun phrase, not a question]

- **Status**: Accepted
- **Context**: [The forces. Reference FR/NFR IDs. Explain the constraints that created the need for a decision.]
- **Decision**: [What was decided. Active voice. Specific technology, pattern, or boundary named.]
- **Rationale**: [Why this option satisfies the Context constraints. No alternatives here.]
- **Alternatives Considered**:
  - **[Option A]**: [one sentence]. Rejected: [specific reason].
  - **[Option B]**: [one sentence]. Rejected: [specific reason].
- **Consequences**:
  - Easier: [what this makes simpler or unlocks]
  - Harder: [what this constrains or complicates]
```

## Placement in docs/architecture.md

ADRs go in the `## Architecture Decision Records` section, after the System Design section. Append each new ADR in sequence — do not insert between existing ADRs.

```markdown
## Architecture Decision Records

### ADR-001: [Title]
...

### ADR-002: [Title]
...
```

## Deprecating an ADR

When a later decision supersedes an earlier one, update the earlier ADR's Status field only:

```
- **Status**: Deprecated — superseded by ADR-007
```

Do not delete or rewrite the deprecated ADR. The original reasoning is historical record — removing it erases the context that explains why ADR-007 was needed.

## Boundaries
- Write one ADR per decision — do not bundle multiple decisions into one
- Do not write ADRs for implementation details or easily reversible choices
- Do not leave Alternatives Considered empty — if there were no real alternatives, the decision does not need an ADR
- Do not write one-sided Consequences — every significant decision has costs
- Do not renumber or delete ADRs once written
