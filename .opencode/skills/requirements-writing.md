# Requirements Writing

## Purpose
This skill governs how to write `docs/spec.md` at the end of Stage 1. The `conversational-intake` skill drives the Q&A process; this skill defines what a well-formed spec looks like and how to derive one from the intake output.

A good spec is the architecture stage's contract. It says exactly what the system must do and how to verify it — no more, no less. If a requirement is ambiguous, the architect will make a guess. If a requirement is untestable, the code-fixing stage has no pass criterion. Precision here pays off across every stage that follows.

## When to Apply

Write or refine `docs/spec.md` when:
- The `conversational-intake` session has closed (all five areas Accepted)
- You have `docs/concept.md` available as the source of truth
- The user asks to review, improve, or expand an existing spec

## Inputs

Read these before writing:
- `docs/concept.md` — the confirmed concept, constraints, and decisions from intake
- The intake session's Accepted log — the raw confirmed facts

Every requirement must trace back to something in the concept doc. If you find yourself writing a requirement that has no grounding in `concept.md`, either the requirement is out of scope or the concept doc is incomplete — stop and resolve which.

## EARS Notation

EARS (Easy Approach to Requirements Syntax) gives each functional requirement a consistent, parseable shape. Use one of these four forms:

| Pattern | When to use | Template |
|---|---|---|
| **Event-driven** | Something triggers a behaviour | `WHEN [trigger event] THE SYSTEM SHALL [response]` |
| **State-driven** | Behaviour active while in a state | `WHILE [system state] THE SYSTEM SHALL [behaviour]` |
| **Conditional** | Optional feature or configuration | `IF [condition] THE SYSTEM SHALL [behaviour]` |
| **Unwanted behaviour** | Error or boundary handling | `IF [unwanted event/condition] THE SYSTEM SHALL [recovery]` |

You can combine patterns: `WHEN [trigger] IF [condition] THE SYSTEM SHALL [response]`.

**What to avoid:**
- Vague verbs: "handle", "support", "manage", "allow" — always replace with a specific action
- Compound requirements: if a single FR contains "and", it usually needs to be split into two
- Passive voice hiding the subject: "errors shall be logged" → "WHEN an error occurs THE SYSTEM SHALL write a structured log entry to the run log"
- Aspirational language: "should", "may", "could" — use SHALL for requirements, or omit if it's not a requirement

## NFR Targets Must Be Measurable

Every NFR must have a number or an observable condition. Vague NFRs cannot be tested and will not hold up at the code-fixing stage gate.

| Bad | Good |
|---|---|
| "The system should be fast" | `NFR-01: Response latency SHALL be under 2 s at p95 for requests under 10 kB` |
| "The system must be secure" | `NFR-02: The CLI SHALL reject any config.yaml containing an API key literal on startup` |
| "The system should be reliable" | `NFR-03: WHILE a workflow is interrupted THE SYSTEM SHALL be resumable from the last completed stage gate without data loss` |

If the user did not give you a number during intake, use a sensible default appropriate to the domain and note it explicitly: `(default — confirm with user)`. Do not omit the NFR just because no number was given.

## Completeness Checks

Before finalising the spec, verify:

**Coverage** — every item in `concept.md → Accepted` has at least one FR or NFR that implements it. If an Accepted item has no requirement, write one or explicitly note it as implementation detail (out of spec scope).

**No orphans** — every FR traces to a Goal or an Accepted item. If it traces to neither, it is either out of scope or the concept doc needs updating.

**Conflict detection** — scan FR pairs for contradictions. Common sources: performance vs. correctness, security vs. usability, online vs. offline behaviour. Flag conflicts explicitly; do not silently drop one side.

**Testability audit** — for each FR, ask: "Could a developer write a test for this without asking me another question?" If the answer is no, the requirement is too vague.

**Non-Goals coverage** — each item in Non-Goals should explain *why* it is out of scope, not just that it is. "Out of scope: multi-tenancy" is weaker than "Out of scope: multi-tenancy — single-user CLI, tenant isolation would require auth infrastructure not in scope for v1."

## Spec File Format

Write `docs/spec.md` using this structure exactly:

```markdown
# Requirements Spec: [Project Name]

> Source: docs/concept.md — [Status: READY] — [Date]

## Problem Statement
<One paragraph. Who has the problem, what the problem is, and what a solution enables. Concrete and specific — name the user, name the pain.>

## Goals
- <Outcome this system achieves, user-facing>

## Non-Goals
- <What is explicitly excluded, with a one-line reason>

## Functional Requirements

### [Logical Group Name]
- **FR-01**: WHEN [trigger] THE SYSTEM SHALL [behaviour]
  - *Acceptance criterion*: <specific, observable, testable outcome — no "should">
- **FR-02**: IF [condition] THE SYSTEM SHALL [behaviour]
  - *Acceptance criterion*: <...>

### [Next Group]
- **FR-NN**: ...

## Non-Functional Requirements
- **NFR-01**: [Quality attribute] — [measurable target]
  - *Acceptance criterion*: <how to verify — test type, tool, threshold>

## Open Items
- **[Label]**: <anything deferred from intake that the architect must resolve before this spec is final>

*(none)* — if nothing is deferred
```

Group FRs by logical area (e.g., "CLI Commands", "Stage Execution", "Persistence", "Security") rather than listing them as a flat sequence. Groups make the spec navigable and make gaps obvious.

## Iteration Protocol

If `docs/spec.md` already exists and you are asked to review or extend it:
1. Read the existing spec and `docs/concept.md`
2. Run the completeness checks above and list any gaps found
3. Propose additions or corrections — do not silently overwrite existing requirements
4. On confirmation, update the file and note the changes in a comment block at the bottom of the file under `## Changelog`

## Boundaries
- Do not design solutions — requirements describe *what*, not *how*
- Do not invent requirements not grounded in `concept.md`
- Do not leave NFRs without measurable targets (use a reasoned default if the user gave none)
- Do not write compound FRs — one behaviour per FR
- Do not mark the spec complete if any Accepted item from intake is uncovered
