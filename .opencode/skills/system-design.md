# System Design

## Purpose
This skill governs how to produce the system design sections of `docs/architecture.md` in Stage 2. It runs after `stack-decision` has locked the technology stack. Its outputs — component boundaries, interface contracts, and data models — are the direct input for `task-decomposition`, which breaks the design into implementable units.

A good system design makes task boundaries obvious. If a developer can read the design and immediately know which component they own, what its inputs and outputs are, and how to test it in isolation, the design is doing its job. Vague responsibilities and implicit interfaces produce task conflicts and integration failures.

## When to Apply
After the "## Technology Stack" section exists in `docs/architecture.md` (written by `stack-decision`). Do not begin designing until the stack is locked — design decisions cascade from technology choices.

## Inputs
Read before beginning:
- `docs/concept.md` — scope boundaries, non-goals, and confirmed constraints
- `docs/spec.md` — FRs and NFRs are the requirements every design decision must satisfy
- `docs/stack-candidates.md` — understand *why* the chosen stack was selected; its trade-offs constrain the design
- `docs/architecture.md` — read the existing Technology Stack section; all components must use the locked stack

## Process

### 1. Map Requirements to Components

Before drawing anything, read every FR in `docs/spec.md` and ask: "Which part of the system is responsible for this behaviour?" Group FRs by responsibility. Each stable group is a candidate component.

Rules for component boundaries:
- One component = one cohesive responsibility. If you cannot name a component in four words or fewer, it is probably two components.
- Components are not layers (not "the service layer"). They are named, ownable units (e.g., `RunLogger`, `RegistryLoader`, `OrchestratorNode`).
- Every FR must be owned by exactly one component. If two components share ownership of an FR, the boundary is wrong.
- Non-goals and Out-of-scope items from `concept.md` must not appear as components.

### 2. Draw the Component Diagram

Produce an ASCII diagram showing all components and their relationships. Use this notation:

```
[ComponentA] --calls--> [ComponentB]
[ComponentA] --reads--> [StorageX]
[ComponentA] --emits--> [EventY]
[ExternalSystem] ..provides.. [ComponentA]
```

Label every arrow. An unlabelled arrow hides an assumption. Include:
- All internal components
- All external dependencies (LLM providers, databases, filesystem)
- Direction of every dependency (who calls whom)
- Async boundaries (mark with `~async~` on the arrow)

The diagram is not decoration — it is the first thing a developer reads. If it is cluttered, split it into a high-level overview diagram and one detail diagram per subsystem.

### 3. Write Component Responsibilities

One section per component. Each section must state:
- **What it does**: one sentence — the single responsibility
- **What it owns**: data, state, or files it is the authoritative source for
- **What it does not do**: explicit non-responsibilities that a reader might assume (prevents scope creep)
- **FR coverage**: which FRs this component implements (reference by ID)

### 4. Define Interface Contracts

For every arrow in the diagram, define the contract at that boundary:

**Function/method call:**
```
ComponentA.method_name(param: Type) -> ReturnType
Precondition: <what must be true before calling>
Postcondition: <what is guaranteed after calling>
Error: <what exceptions/errors are raised and when>
```

**File/artifact:**
```
Path: <relative path>
Format: <YAML / JSONL / Markdown / SQLite>
Written by: <component>
Read by: <component(s)>
Schema: <key fields and types>
```

**CLI command:**
```
Command: monkey-devs <subcommand> [flags]
Input: <what it reads>
Output: <what it produces or displays>
Side effects: <state changes>
```

Interface contracts are where task boundaries live. The implementation subagent for ComponentA should never need to read ComponentB's code to know how to call it — the contract tells them everything.

### 5. Specify Data Models

Define the key entities the system stores, passes, or transforms. For each:
- **Name** and brief description
- **Fields**: name, type, required/optional, and purpose
- **Owner**: which component is the authoritative writer
- **Lifetime**: when is it created, when does it change, when is it deleted

Use typed pseudocode, not prose:
```
WorkflowState:
  project_name: str          # human-readable project identifier
  current_stage: int         # 1–5, set by orchestrator on transition
  workflow_status: str       # active | completed | interrupted
  stage_outputs: dict[int | str, list[str]]  # absolute artifact paths per stage
  ...
```

If a data model is already defined in `docs/spec.md` or the codebase, reference it — do not duplicate. Only write what is new or needs elaboration.

### 6. Write ADRs for Key Decisions

Any design decision that is non-obvious, involves trade-offs, or rules out a plausible alternative warrants an ADR. Use the `adr-writing` skill format. Decisions that typically need ADRs:

- Why the system is structured this way rather than the obvious alternative
- Why a component boundary is placed where it is
- Why a particular data format or protocol was chosen
- Any decision where "why not X?" is a natural follow-up question

Write ADRs as a `## Architecture Decision Records` section in `docs/architecture.md`. Number them ADR-001, ADR-002, etc.

A decision documented nowhere except someone's memory is not a decision — it is a time bomb.

## Completeness Checks

Before finalising:

**FR coverage**: every FR in `docs/spec.md` must be owned by a component. List uncovered FRs and assign them or explicitly defer to a later stage.

**NFR validation**: for each NFR, identify which component is responsible for satisfying it and how. "NFR-03 (startup under 200 ms) — owned by CLI entrypoint; satisfied by lazy-loading registry only when needed."

**Interface completeness**: every arrow in the diagram must have a corresponding contract. No unlabelled edges, no undocumented file formats.

**Task seams**: check that each component can be implemented independently given only its interface contracts. If implementing ComponentA requires knowing ComponentB's internal state, the boundary is wrong.

## Output Format

Append to `docs/architecture.md` after the Technology Stack section:

```markdown
## System Design

### Component Overview
[ASCII diagram]

### Components

#### [ComponentName]
**Responsibility**: <one sentence>
**Owns**: <data/files/state>
**Does not**: <explicit exclusions>
**Implements**: FR-XX, FR-YY, NFR-ZZ

### Interface Contracts
[One subsection per contract]

### Data Models
[One subsection per model]

## Architecture Decision Records

### ADR-001: [Title]
[adr-writing format]
```

## Boundaries
- Do not begin designing before the stack is locked in `docs/architecture.md`
- Do not introduce components without a corresponding FR or NFR justifying their existence
- Do not leave any FR unowned at the end of the design
- Do not write implementation code or algorithm details — design describes structure, not procedure
- Do not duplicate data models already defined elsewhere — reference them
