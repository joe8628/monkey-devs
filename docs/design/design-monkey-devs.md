# Design and Architecture Document: Monkey Devs

**Version**: 1.0
**Date**: 2026-04-14
**Status**: Finalized
**Spec Source**: spec-monkey-devs.md v1.0-draft
**Architect Session**: 2026-04-14

---

## Part I — Finalized Specification

> This section carries forward the technical specification with all open decisions resolved
> and all architectural annotations applied. Requirement IDs (FR-XX, NFR-XX) are preserved
> for traceability.

### 1. Problem Statement

A solo operator who needs to build software — internal tools, scripts, automation pipelines,
web applications, and APIs — currently depends on a full-stack development team to deliver
those projects. This creates a bottleneck: work is gated on team availability, coordination
overhead, and specialization gaps that a single person cannot fill alone.

Agentic coding offers a path to independence, but existing tools are either monolithic (one
agent does everything poorly) or require the user to manually orchestrate multiple AI tools,
which recreates the coordination burden in a different form.

Monkey Devs solves this by providing a structured multi-agent development workflow where
specialized AI agents handle each phase of the software development lifecycle under the
user's direction. The user retains control at defined decision points without doing the
manual coding work themselves.

---

### 2. Goals

- **G-01**: Enable a solo operator to initiate, guide, and receive working software without writing code manually.
- **G-02**: Provide a five-stage structured workflow with a human approval gate at each stage boundary.
- **G-03**: Support both internal tools/scripts and full applications (web apps, APIs, mobile) within the same workflow.
- **G-04**: Allow the system to resume a workflow after a session crash or restart without losing progress.
- **G-05**: Remain IDE-agnostic — the system operates as a standalone CLI, with no IDE dependency.
- **G-06**: Minimize LLM token cost by preferring markdown skill files over agentic tools wherever quality is equivalent.
- **G-07**: Produce working, locally runnable code as the primary deliverable.

---

### 3. Non-Goals

- Automated deployment to any cloud provider, VPS, or hosting environment.
- Multi-user support, role-based access control, or team collaboration features.
- A fixed or opinionated technology stack — agents select the appropriate stack per project.
- Real-time agent monitoring or observability dashboards.
- Automated publishing, packaging, or distribution of produced software.

---

### 4. Users and Stakeholders

| Role | Description | Primary Interaction |
|------|-------------|---------------------|
| Solo Operator | The single user of the system. Initiates workflows, approves or redirects at each stage gate, and receives the final code output. | CLI commands, stage gate approval, fix/redirect instructions |

---

### 5. Functional Requirements

| ID | Requirement | Fulfilled By |
|----|-------------|--------------|
| FR-01 | The system MUST provide a principal orchestrator as a Python CLI control loop, managing workflow state via LangGraph. | `monkey-devs` CLI + LangGraph graph |
| FR-02 | The orchestrator MUST act as a resource manager: at each stage, it MUST read the project context and registry to select and allocate the appropriate skills and tools for that stage. | Python CLI `compose_handoff()` function |
| FR-03 | The orchestrator MUST NOT read, write, or generate code at any point. All code-level operations MUST be delegated to stage nodes. | Python CLI control loop (no LLM, no code ops) |
| FR-04 | The orchestrator MUST maintain the LangGraph workflow state, tracking the current stage, completion status, and human approval decisions. | LangGraph `WorkflowState` + SQLite checkpointer |
| FR-05 | The orchestrator MUST pause workflow execution at each stage boundary and present a stage gate to the user before activating the next stage node. | LangGraph `interrupt()` + CLI gate renderer |
| FR-06 | The orchestrator MUST support workflow resumption after session interruption. | SQLite checkpointer + `monkey-devs resume` |
| FR-07 | The orchestrator MUST communicate its resource allocation decisions to the user at each stage gate. | CLI stage gate output + `monkey-devs details` |
| FR-08 | The system MUST provide five pre-defined stage nodes in the LangGraph graph: Concept & Spec, Architecture, Implementation, Code Fixing, Delivery. | LangGraph async node functions |
| FR-09 | Stage nodes MUST be invoked automatically by the orchestrator at the appropriate stage. | LangGraph graph edges + Python CLI |
| FR-10 | Stage nodes MUST receive a structured handoff message at invocation containing: injected skill content, granted tools, and relevant project context. | `compose_handoff()` → four-block markdown schema |
| FR-11 | Stage nodes MUST NOT self-configure — they MUST rely entirely on the handoff message for skill and tool allocation. | Handoff message is the sole system prompt |
| FR-12 | Each stage node MUST have tool access scoped to its stage via Python-enforced permissions. | `get_stage_tools(stage)` + bash allowlist validator |
| FR-13 | Stage 1 MUST conduct conversational intake and produce a concept summary and requirements spec with acceptance criteria. | Concept & Spec node + `conversational-intake`, `requirements-writing` skills |
| FR-14 | Stage 1 MUST propose 2–3 candidate technology stacks with rationale, ranked by suitability. It MUST NOT make a final stack decision. | `stack-evaluation` skill |
| FR-15 | Stage 2 MUST make a final, binding technology stack decision. | `stack-decision` skill |
| FR-16 | Stage 2 MUST produce a system design and a task breakdown in `.opencode/tasks.yaml`. | `system-design`, `task-decomposition` skills |
| FR-17 | Stage 3 MUST write both production code and tests. Tests MUST be written as part of this stage. | Implementation node + `tdd-implementation`, `code-generation` skills |
| FR-18 | Stage 4 MUST run all tests and attempt to fix failing tests. Unresolved failures MUST be classified as `code-issue` or `test-issue`. | Code Fixing node + `test-categorization`, `systematic-debugging` skills |
| FR-19 | Stage 4 classifications MUST be presented to the user at the stage gate with rationale. | CLI stage gate renderer |
| FR-20 | Stage 5 MUST produce a working, locally runnable repository and a delivery summary. | Delivery node + `delivery-summary`, `readme-writing` skills |
| FR-21 | The system MUST present a stage gate after each stage with three options: approve, fix/update and continue, reject and redirect. | `monkey-devs approve` / `monkey-devs reject` |
| FR-22 | No stage MAY be skipped. All five stage gates require explicit user action. | LangGraph graph — no bypass edges |
| FR-23 | When the user fixes or updates a stage output, the workflow MUST continue from that stage — not restart from Stage 1. | Correction branch per stage in LangGraph graph |
| FR-24 | The system MUST maintain a resource registry at `.opencode/registry.yaml`. | YAML manifest, read by Python CLI |
| FR-25 | The registry MUST be updatable independently of workflow execution. | Standalone YAML file, no runtime lock |
| FR-26 | The orchestrator MUST read the registry at workflow start to build its allocation model. | `load_registry()` called in CLI `run` command |
| FR-27 | Skills MUST be defined as markdown prompt files in `.opencode/skills/`. | `.opencode/skills/*.md` |
| FR-28 | Skills MUST have metadata accessible to the orchestrator: name, description, applicable stages. | `registry.yaml` `skills` section |
| FR-29 | Skills MUST be injected into stage nodes via the handoff message. | `compose_handoff()` loads and concatenates skill files |
| FR-30 | The system MUST prefer skills over tools when a skill can cover the need at equivalent quality. | Binary rule: skill if text/decision, tool if execution |
| FR-31 | Tools are executable capabilities registered in the registry. | `registry.yaml` `tools` section |
| FR-32 | Tools MUST have metadata: name, description, type, applicable stages. | `registry.yaml` `tools` section |
| FR-33 | Tool access MUST be granted to stage nodes via Python-enforced scoping. | `get_stage_tools(stage)` per node |
| FR-34 | Stage 1 MUST propose a ranked shortlist of 2–3 stack candidates with rationale. | `stack-evaluation` skill |
| FR-35 | Stage 2 MUST make the final, binding stack decision, recorded in the architecture artifact. | `stack-decision` skill + `docs/architecture.md` |
| FR-36 | No fixed or default stack MAY be imposed. Stack selection is always per-project. | No hardcoded stack in any skill or node |

**New requirement — Multi-vendor model configuration:**

| ID | Requirement | Fulfilled By |
|----|-------------|--------------|
| FR-37 | Each stage node MUST have an independently configurable LLM model. Models MAY be from different vendors. | `config.yaml` `models` section + LiteLLM |
| FR-38 | Model configuration MUST be defined before a workflow starts and MAY only be updated before starting or after a workflow completes. | `monkey-devs config set-model` blocked during active workflows |
| FR-39 | The CLI MUST provide commands to view, update, and validate model configuration. | `monkey-devs config models`, `set-model`, `validate` |

---

### 6. Non-Functional Requirements

| ID | Category | Requirement | Architectural Response |
|----|----------|-------------|------------------------|
| NFR-01 | Resumability | Workflow MUST be resumable after session crash or restart. | SQLite checkpointer at `.opencode/workflow-state.db`; `monkey-devs resume` restores from last checkpoint |
| NFR-02 | Portability | System MUST NOT be locked to a single IDE. | Standalone Python CLI; zero IDE dependencies |
| NFR-03 | Cost Efficiency | Prefer skills over tools when a skill can cover the need. | Binary rule enforced by Python CLI: skill if text/decision operation; tool only if execution required. Applied deterministically via `stages` filter on registry. |
| NFR-04 | Correctness | All test failures at Stage 4 MUST be classified before delivery. | Code Fixing node blocked from advancing until all failures carry a `code-issue` or `test-issue` classification in `tasks.yaml` |
| NFR-05 | Transparency | Orchestrator MUST surface resource allocation decisions at every stage gate. | CLI gate renderer shows sub-agent name + skill/tool list; `monkey-devs details` expands full allocation from run log |
| NFR-06 | Extensibility | New skills and tools MUST be addable without modifying stage node definitions. | `registry.yaml` is the only file that needs updating; node code reads registry dynamically |

---

### 7. System Context

Monkey Devs is a standalone Python CLI application. It does not require an IDE, a running server, or any cloud infrastructure.

**Inside the system boundary:**
- `monkey-devs` Python CLI package (`monkey_devs/`)
- LangGraph workflow graph with five stage nodes + correction branches
- Resource registry (`.opencode/registry.yaml`)
- Model and provider config (`.opencode/config.yaml`)
- Skill files (`.opencode/skills/*.md`)
- LangGraph SQLite state (`.opencode/workflow-state.db`)
- Run logs (`.opencode/logs/`)
- Task file (`.opencode/tasks.yaml`)

**Outside the system boundary (dependencies):**
- **LangGraph**: workflow state machine and durable state persistence
- **LiteLLM**: multi-vendor LLM abstraction layer
- **LLM providers**: Anthropic, OpenAI, Google (via API keys in environment)
- **User's local filesystem**: destination for all project output

---

### 8. Key Concepts and Data Model

#### Glossary

| Term | Definition |
|------|------------|
| Orchestrator | The Python CLI control loop. A pure resource manager — reads registry, composes handoff messages, manages LangGraph state, renders stage gates. Never invokes an LLM. |
| Stage Node | An async Python function in the LangGraph graph. Receives a handoff message as its system prompt, invokes an LLM via LiteLLM, streams output to terminal, writes artifacts to filesystem. |
| Skill | A markdown prompt file injected into a stage node's system prompt at invocation. Preferred over tools for all text/decision operations. |
| Tool | A Python-callable capability (file I/O, bash execution) granted to a stage node via `get_stage_tools()`. Only used when a skill cannot perform the operation. |
| Resource Registry | `.opencode/registry.yaml` — lists all skills and tools with metadata. Read by the orchestrator at workflow start. |
| Stage Gate | A CLI pause point after each stage. Presents stage summary, allocated resources, unresolved issues, and three action options. Implemented via LangGraph `interrupt()`. |
| Handoff Message | A four-block markdown message (CONTEXT / SKILLS / TOOLS / INSTRUCTIONS) composed by the Python CLI and used as the system prompt for the stage node's LLM call. |
| Workflow | The five-stage LangGraph pipeline instance for a specific project. Persisted in SQLite. Resumable after interruption. |
| Correction Branch | A paired LangGraph node for each stage. Activated on rejection — carries rejection reason and prior output as inputs, re-invokes the same stage node with updated context. |
| Task | A unit of implementation work in `.opencode/tasks.yaml`. Created by Stage 2, dispatched by the orchestrator to individual Implementation nodes in Stage 3. |

#### Core Entity Schemas

**WorkflowState (LangGraph TypedDict)**
```python
class WorkflowState(TypedDict):
    project_name: str
    project_path: str
    current_stage: int                       # 1–5
    workflow_status: str                     # active | completed | interrupted
    stage_statuses: dict[int, str]           # pending | active | complete | approved | rejected
    stage_outputs: dict[int, str]            # path to artifact per stage
    stage_models: dict[int, str]             # model used per stage (audit)
    correction_active: bool
    correction_stage: int | None
    correction_reason: str | None
    tasks: list[str]                         # task IDs from tasks.yaml
    tasks_dispatched: list[str]
    tasks_completed: list[str]
    gate_decisions: dict[int, str]           # approved | fix | rejected
    allocated_skills: dict[int, list[str]]
    allocated_tools: dict[int, list[str]]
```

**tasks.yaml schema**
```yaml
project: my-project
tasks:
  - id: T-01
    title: "Implement user authentication"
    description: "..."
    status: pending        # pending | in-progress | done
    stage: 3
    depends_on: []
    failure_classification: null   # code-issue | test-issue (Stage 4 only)
```

**registry.yaml schema**
```yaml
workflow:
  state_db: .opencode/workflow-state.db

skills:
  - name: conversational-intake
    description: "Forge-style one-question-at-a-time intake pattern"
    stages: [1]
    path: .opencode/skills/conversational-intake.md

tools:
  - name: filesystem
    description: "Read/write access to local filesystem"
    type: opencode-builtin
    stages: [1, 2, 3, 4, 5]
    connection: builtin
```

**config.yaml schema**
```yaml
models:
  concept-spec:    google/gemini-2.5-pro
  architecture:    google/gemini-2.5-pro
  implementation:  anthropic/claude-opus-4-6
  code-fixing:     openai/codex-mini
  delivery:        anthropic/claude-sonnet-4-6

providers:
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
  openai:
    api_key_env: OPENAI_API_KEY
  google:
    api_key_env: GEMINI_API_KEY
```

---

### 9. Interface Contracts

#### CLI Interface

| Command | Description |
|---------|-------------|
| `monkey-devs init` | Initialize new project, create `.opencode/` structure, start Stage 1 |
| `monkey-devs run` | Run the current stage (streams LLM output to terminal) |
| `monkey-devs run --verbose` | Run with skill injection + state transition events |
| `monkey-devs run --debug` | Run with full real-time event log |
| `monkey-devs status` | Show workflow state, current stage, task list |
| `monkey-devs approve` | Approve current stage gate, advance to next stage |
| `monkey-devs reject --reason "..."` | Reject current stage, enter correction branch |
| `monkey-devs resume` | Resume an interrupted workflow from last checkpoint |
| `monkey-devs tasks` | List tasks and their status (Stage 3+) |
| `monkey-devs registry` | Show resource registry contents |
| `monkey-devs skills list` | List skills with stage assignments |
| `monkey-devs config models` | Show current model assignments |
| `monkey-devs config set-model <stage> <model>` | Update model for a stage (blocked during active workflow) |
| `monkey-devs config validate` | Verify API keys are set, models are reachable, no key literals in config |
| `monkey-devs details` | Expand full allocation log for current stage gate |

#### Handoff Message Schema

```markdown
## HANDOFF: [Stage Name]

### CONTEXT
project: [project name]
stage: [1-5]
task_id: [T-XX or "all" for non-Implementation stages]
prior_output: [path to previous stage artifact, or "none"]

### SKILLS
---
## Skill: [skill-name]
[full content of skill markdown file]

---
## Skill: [skill-name]
[full content of skill markdown file]

### TOOLS
- [tool-name]: [one-line description of what to use it for in this stage]

### INSTRUCTIONS
[Stage-specific directive: what to produce, what artifacts to write,
what to present at completion. Includes rejection reason if correction branch.]
```

---

### 10. Constraints and Assumptions

**Constraints:**

- **C-01**: All stage logic MUST be implemented as LangGraph async node functions in the Python CLI package.
- **C-02**: The orchestrator (Python CLI control loop) MUST NOT invoke any LLM. All LLM calls happen inside stage nodes only.
- **C-03**: Skills MUST be markdown files. They MUST NOT be compiled code, scripts, or executables.
- **C-04**: LangGraph with SQLite checkpointer is the required workflow state manager.
- **C-05**: Deployment automation is out of scope. The system delivers a working local repository only.
- **C-06**: The system targets a single user. No multi-user, authentication, or authorization layer is in scope.
- **C-07**: All five stage gates are mandatory. No stage may be skipped regardless of project size.

**Assumptions — all resolved:**

- **A-01**: ~~OpenCode IDE compatibility~~ — **Eliminated**. System is a standalone Python CLI with no IDE dependency.
- **A-02**: LangGraph SQLite checkpointer is sufficient for cross-session durability. **Validated** — SQLite survives process crashes; `interrupt()` + resume pattern is a first-class LangGraph feature.
- **A-03**: Handoff message format is sufficient for stage nodes to initialize correctly. **Resolved** — four-block schema (CONTEXT / SKILLS / TOOLS / INSTRUCTIONS) defined. To be validated during prototype.

---

### 11. Open Decisions — RESOLVED

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| OD-01 | Resource registry format | YAML at `.opencode/registry.yaml` | Human-readable, comment-friendly, structured enough for deterministic filtering without a schema validator |
| OD-02 | Stage gate disclosure level | Summary + drill-down on request | Routine approvals stay clean; `monkey-devs details` provides full allocation log on demand |
| OD-03 | LangGraph rejection handling | Correction branch per stage | First-class LangGraph node; preserves rejection reason and prior output; clean state history |
| OD-04 | Sub-agent permission matrix | Python-enforced per stage node via `get_stage_tools()` + bash allowlist | OpenCode eliminated; permissions are code, not IDE config |
| OD-05 | Task tracking location | Local YAML at `.opencode/tasks.yaml` | No external dependencies; readable by Python CLI without tools; YAML supports structured dispatch |

---

## Part II — Architecture

### 1. Architectural Strategy

**Pattern**: LangGraph-native agentic pipeline with Python CLI orchestration
**Rationale**: LangGraph provides a first-class human-in-the-loop interrupt/resume model, durable SQLite state persistence, and a graph execution model that maps directly to the five-stage workflow. Python CLI orchestration replaces an LLM-based orchestrator, making resource allocation deterministic, free of LLM cost, and fully testable.

**Technology Stack**:
- Runtime: Python 3.11+
- Workflow engine: LangGraph + `langgraph-checkpoint-sqlite`
- LLM abstraction: LiteLLM
- CLI framework: Typer
- Package manager: uv

**Default model assignments:**
| Stage | Model | Rationale |
|-------|-------|-----------|
| Concept & Spec | `google/gemini-2.5-pro` | Largest context window for long intake conversations; strong reasoning for requirements |
| Architecture | `google/gemini-2.5-pro` | Handles full project context during system design |
| Implementation | `anthropic/claude-opus-4-6` | Highest code generation quality for production code + tests |
| Code Fixing | `openai/codex-mini` | Purpose-built for code understanding and repair |
| Delivery | `anthropic/claude-sonnet-4-6` | Fast and precise for documentation and delivery summary |

**Communication style**: Synchronous — CLI invokes LangGraph, LangGraph invokes LiteLLM, output streams to terminal
**Deployment model**: Local Python package, installed via pip/uv. No server, no daemon, no cloud.

---

### 2. System Layer

**Topology**: Single-process Python application. The user invokes the CLI, which drives a LangGraph state machine that calls LLM APIs via LiteLLM.

```
User (terminal)
    │
    ▼
monkey-devs CLI (Typer)
    │  reads/writes
    ├──────────────────► .opencode/registry.yaml
    ├──────────────────► .opencode/config.yaml
    ├──────────────────► .opencode/tasks.yaml
    ├──────────────────► .opencode/logs/run-<ts>.jsonl
    │
    │  drives
    ▼
LangGraph Graph
    │  persists via
    ├──────────────────► .opencode/workflow-state.db (SQLite)
    │
    │  invokes nodes
    ▼
Stage Nodes (async Python functions)
    │  calls via LiteLLM
    ├──────────────────► Anthropic API
    ├──────────────────► OpenAI API
    ├──────────────────► Google AI API
    │
    │  streams output to
    ▼
User (terminal)
    │
    │  writes artifacts to
    ▼
Project filesystem (user's working directory)
```

**Component inventory:**

| Component | Type | Responsibility |
|-----------|------|----------------|
| `monkey-devs` CLI | CLI entrypoint (Typer) | User interface, command dispatch, stage gate rendering |
| LangGraph Graph | Workflow state machine | Stage transitions, interrupt/resume, correction branch routing |
| Python CLI Control Loop | Orchestrator (no LLM) | Registry loading, skill selection, handoff composition, task dispatch |
| Stage Nodes (×5) | Async LLM functions | Execute stage work via LiteLLM; stream output; write artifacts |
| Correction Branches (×5) | LangGraph nodes | Re-invoke stage node with rejection reason + prior output |
| SQLite Checkpointer | Persistence layer | Durable state across sessions |
| Resource Registry | YAML manifest | Skills and tools catalog |
| Config Store | YAML file | Model assignments and provider API key references |
| Skill Files | Markdown prompts | Injected into stage node system prompts |
| Task File | YAML | Implementation unit tracking; Stage 3 dispatch source |
| Run Logs | JSONL | Per-event audit trail; source for `details` drill-down |

**FRs satisfied**: FR-01 through FR-07, NFR-01, NFR-02

---

### 3. Application Layer

#### Python CLI Control Loop (Orchestrator)

- **Responsibility**: The deterministic brain of the system. Reads registry, selects skills and tools for the current stage, composes handoff messages, dispatches tasks, renders stage gates, issues LangGraph commands.
- **Key functions**: `load_registry()`, `compose_handoff()`, `get_stage_tools()`, `render_stage_gate()`, `dispatch_tasks()`
- **State**: Stateless between CLI invocations — all state lives in LangGraph SQLite
- **LLM calls**: None. Zero LLM tokens consumed by orchestration.
- **FRs fulfilled**: FR-02, FR-03, FR-07, FR-24, FR-26, FR-29, FR-30, NFR-03, NFR-05

#### Stage Node: Concept & Spec

- **Responsibility**: Conversational intake with the user; produces concept document and requirements spec; proposes 2–3 ranked stack candidates.
- **Model**: `google/gemini-2.5-pro`
- **Skills**: `conversational-intake`, `requirements-writing`, `stack-evaluation`
- **Tools**: file-read (project docs), file-write (`docs/`)
- **Output artifact**: `docs/concept.md`, `docs/spec.md`
- **FRs fulfilled**: FR-13, FR-14, FR-34

#### Stage Node: Architecture

- **Responsibility**: Makes final binding stack decision; produces system design and task breakdown.
- **Model**: `google/gemini-2.5-pro`
- **Skills**: `system-design`, `task-decomposition`, `adr-writing`, `stack-decision`
- **Tools**: file-read (full project), file-write (`docs/`, `.opencode/tasks.yaml`)
- **Output artifact**: `docs/architecture.md`, `.opencode/tasks.yaml`
- **FRs fulfilled**: FR-15, FR-16, FR-35

#### Stage Node: Implementation

- **Responsibility**: Writes production code and tests for one assigned task unit. Invoked once per task by the orchestrator's task-dispatch logic.
- **Model**: `anthropic/claude-opus-4-6`
- **Skills**: `tdd-implementation`, `code-generation`
- **Tools**: file-read (full project), file-write (full project), bash (build/test commands — allowlisted)
- **Output artifact**: source files per task
- **FRs fulfilled**: FR-17

#### Stage Node: Code Fixing

- **Responsibility**: Runs all tests; attempts to fix failures; classifies all unresolved failures as `code-issue` or `test-issue`; presents classifications at stage gate.
- **Model**: `openai/codex-mini`
- **Skills**: `test-categorization`, `systematic-debugging`
- **Tools**: file-read (full project), file-write (full project), bash (test runner — allowlisted)
- **Output artifact**: updated source files; classifications written to `.opencode/tasks.yaml`
- **FRs fulfilled**: FR-18, FR-19, NFR-04

#### Stage Node: Delivery

- **Responsibility**: Produces delivery summary and README; confirms repository is locally runnable.
- **Model**: `anthropic/claude-sonnet-4-6`
- **Skills**: `delivery-summary`, `readme-writing`
- **Tools**: file-read (full project), file-write (`docs/`, README)
- **Output artifact**: `README.md`, `docs/delivery.md`
- **FRs fulfilled**: FR-20

---

### 4. Data Layer

#### Storage Technologies

| Store | Technology | Path | Owner | Purpose |
|-------|------------|------|-------|---------|
| Workflow state | SQLite (LangGraph checkpointer) | `.opencode/workflow-state.db` | LangGraph | Durable workflow state across sessions |
| Resource registry | YAML | `.opencode/registry.yaml` | Python CLI | Skills and tools catalog |
| Model config | YAML | `.opencode/config.yaml` | Python CLI | LLM model assignments and provider keys |
| Task file | YAML | `.opencode/tasks.yaml` | Architecture node + CLI | Implementation units and status |
| Run logs | JSONL | `.opencode/logs/run-<ts>.jsonl` | Python CLI | Per-event audit trail |
| Skill files | Markdown | `.opencode/skills/*.md` | Static files | Prompt content injected at handoff |
| Project artifacts | Markdown / source files | `docs/`, project root | Stage nodes | Stage outputs (spec, architecture, code) |

#### Key Schemas

**registry.yaml**
```yaml
workflow:
  state_db: .opencode/workflow-state.db

skills:
  - name: conversational-intake
    description: "Forge-style one-question-at-a-time intake pattern"
    stages: [1]
    path: .opencode/skills/conversational-intake.md
  - name: requirements-writing
    description: "Writing specs with acceptance criteria"
    stages: [1]
    path: .opencode/skills/requirements-writing.md
  - name: stack-evaluation
    description: "Evaluating and ranking 2-3 technology stack candidates"
    stages: [1]
    path: .opencode/skills/stack-evaluation.md
  - name: system-design
    description: "Producing architecture decisions and system design artifacts"
    stages: [2]
    path: .opencode/skills/system-design.md
  - name: task-decomposition
    description: "Breaking work into implementable units for tasks.yaml"
    stages: [2]
    path: .opencode/skills/task-decomposition.md
  - name: adr-writing
    description: "Writing architecture decision records"
    stages: [2]
    path: .opencode/skills/adr-writing.md
  - name: stack-decision
    description: "Making a final binding stack decision with rationale"
    stages: [2]
    path: .opencode/skills/stack-decision.md
  - name: tdd-implementation
    description: "Test-first development pattern"
    stages: [3]
    path: .opencode/skills/tdd-implementation.md
  - name: code-generation
    description: "Writing production code from task specs"
    stages: [3]
    path: .opencode/skills/code-generation.md
  - name: test-categorization
    description: "Classifying failures as code-issue or test-issue with rationale"
    stages: [4]
    path: .opencode/skills/test-categorization.md
  - name: systematic-debugging
    description: "Root-cause analysis before attempting fixes"
    stages: [4]
    path: .opencode/skills/systematic-debugging.md
  - name: delivery-summary
    description: "Producing the delivery report (what was built, where files are)"
    stages: [5]
    path: .opencode/skills/delivery-summary.md
  - name: readme-writing
    description: "Writing project README and setup documentation"
    stages: [5]
    path: .opencode/skills/readme-writing.md
  - name: resource-allocation
    description: "How to read the registry and select skills/tools per stage"
    stages: [0]
    path: .opencode/skills/resource-allocation.md
  - name: stage-gate
    description: "How to format and present stage gates"
    stages: [0]
    path: .opencode/skills/stage-gate.md
  - name: handoff-composer
    description: "How to compose structured handoff messages for stage nodes"
    stages: [0]
    path: .opencode/skills/handoff-composer.md
  - name: task-dispatch
    description: "How to read tasks.yaml and dispatch Implementation nodes"
    stages: [0]
    path: .opencode/skills/task-dispatch.md

tools:
  - name: filesystem
    description: "Read/write access to local filesystem"
    type: builtin
    stages: [1, 2, 3, 4, 5]
    connection: builtin
  - name: bash
    description: "Shell command execution (allowlisted commands only)"
    type: builtin
    stages: [3, 4]
    connection: builtin
  - name: web-search
    description: "Web search for research during intake and architecture"
    type: mcp
    stages: [1, 2]
    connection: optional
```

**tasks.yaml**
```yaml
project: my-project
tasks:
  - id: T-01
    title: "Implement user authentication"
    description: "JWT-based auth with login and token refresh endpoints"
    status: pending             # pending | in-progress | done
    stage: 3
    depends_on: []
    failure_classification: null  # code-issue | test-issue (set by Stage 4)
```

**Run log event types (JSONL)**
```json
{"ts": "ISO8601", "event": "workflow_started", "project": "..."}
{"ts": "ISO8601", "event": "stage_started", "stage": 2, "model": "google/gemini-2.5-pro"}
{"ts": "ISO8601", "event": "skill_injected", "stage": 2, "skill": "system-design"}
{"ts": "ISO8601", "event": "tool_granted", "stage": 2, "tool": "filesystem"}
{"ts": "ISO8601", "event": "llm_call_complete", "stage": 2, "tokens_used": 4821}
{"ts": "ISO8601", "event": "artifact_written", "stage": 2, "path": "docs/architecture.md"}
{"ts": "ISO8601", "event": "stage_gate_presented", "stage": 2}
{"ts": "ISO8601", "event": "stage_approved", "stage": 2}
{"ts": "ISO8601", "event": "stage_rejected", "stage": 2, "reason": "..."}
{"ts": "ISO8601", "event": "correction_started", "stage": 2}
{"ts": "ISO8601", "event": "task_dispatched", "task_id": "T-01"}
{"ts": "ISO8601", "event": "task_completed", "task_id": "T-01"}
```

#### File Layout

```
.opencode/
├── registry.yaml          # Skills and tools catalog
├── config.yaml            # Model assignments and provider config
├── tasks.yaml             # Task list (created at Stage 2)
├── workflow-state.db      # LangGraph SQLite state
├── skills/
│   ├── conversational-intake.md
│   ├── requirements-writing.md
│   ├── stack-evaluation.md
│   ├── system-design.md
│   ├── task-decomposition.md
│   ├── adr-writing.md
│   ├── stack-decision.md
│   ├── tdd-implementation.md
│   ├── code-generation.md
│   ├── test-categorization.md
│   ├── systematic-debugging.md
│   ├── delivery-summary.md
│   ├── readme-writing.md
│   ├── resource-allocation.md
│   ├── stage-gate.md
│   ├── handoff-composer.md
│   └── task-dispatch.md
└── logs/
    └── run-<timestamp>.jsonl

monkey_devs/               # Python package
├── __init__.py
├── cli.py                 # Typer CLI entrypoint
├── orchestrator.py        # compose_handoff(), load_registry(), render_stage_gate()
├── graph.py               # LangGraph graph definition
├── nodes/
│   ├── concept_spec.py
│   ├── architecture.py
│   ├── implementation.py
│   ├── code_fixing.py
│   └── delivery.py
├── tools.py               # get_stage_tools(), bash allowlist validator
├── config.py              # load_config(), validate_config()
├── tasks.py               # load_tasks(), dispatch_tasks(), update_task_status()
└── logger.py              # JSONL run log writer
```

---

### 5. API Layer

The system exposes no network API. The sole interface is the CLI defined in Section 9.

---

### 6. Infrastructure Layer

**Deployment target**: Local developer machine (macOS, Linux, Windows)
**Installation**: `pip install monkey-devs` or `uv add monkey-devs`
**Runtime requirements**: Python 3.11+, API keys for configured LLM providers

**No CI/CD pipeline** — this is a local tool, not a deployed service.

**Environment configuration:**
- API keys are stored in environment variables, never in files
- `.opencode/` is added to `.gitignore` by `monkey-devs init`
- `config.yaml` stores only env var names, never key values

**`.gitignore` entries added by `monkey-devs init`:**
```
.opencode/workflow-state.db
.opencode/logs/
.opencode/config.yaml
```

Note: `registry.yaml`, `tasks.yaml`, and `skills/` are intentionally NOT gitignored — they are project artifacts the user may want to version.

---

### 7. Security Layer

**Authentication model**: None — local single-user tool, no auth required.

**API key management:**
- `config.yaml` stores env var names only (e.g. `api_key_env: ANTHROPIC_API_KEY`)
- Python CLI reads keys via `os.environ` at runtime
- `monkey-devs config validate` scans `config.yaml` for accidental key literals before any workflow operation and blocks execution if found
- `.opencode/config.yaml` is gitignored by default

**Prompt injection mitigation:**
- All user-supplied text (project name, rejection reasons, task descriptions) is inserted into handoff messages as data fields, never concatenated into instruction text
- Correction reasons are wrapped in explicit delimiters: `<user-rejection-reason>...</user-rejection-reason>`
- Stage node system prompts include an explicit instruction to treat delimited user content as data, not instructions

**Bash scope enforcement:**
- Stage 3 and Stage 4 nodes receive an allowlist of permitted commands in their TOOLS block
- Python CLI wraps shell execution in a command validator — commands not on the allowlist are blocked and logged
- Default allowlist includes standard test runners only: `pytest`, `npm test`, `yarn test`, `cargo test`, `go test`, `make test`, `mvn test`
- No `sudo`, `rm`, `curl`, `wget`, or network commands on the allowlist

**Threat model:**

| Threat | Mitigation |
|--------|------------|
| API key leak via config file commit | Keys stored as env var references; `config.yaml` gitignored; `validate` command scans for literals |
| Prompt injection via user input | User content wrapped in delimiters; stage nodes instructed to treat as data |
| Bash scope creep by LLM | Python allowlist validator blocks non-permitted commands before execution |
| Accidental project file deletion | Stage permissions enforce write-path scoping per stage; no stage has unrestricted delete access |

---

### 8. Observability Layer

**Logging — Structured JSONL run log:**
- Path: `.opencode/logs/run-<timestamp>.jsonl`
- Format: one JSON object per line
- Events: workflow lifecycle, stage transitions, skill injections, tool grants, LLM call completions, artifact writes, gate decisions, task dispatches
- Retention: last 10 run logs kept; older logs deleted automatically by `monkey-devs init` and `monkey-devs run`

**CLI output levels:**
- Default (`monkey-devs run`): streams LLM output to terminal only
- Verbose (`monkey-devs run --verbose`): adds skill injection events, tool grants, state transitions
- Debug (`monkey-devs run --debug`): full real-time event log to terminal

**Stage gate drill-down:**
- `monkey-devs details` reads the current run log and prints the full allocation event sequence for the active stage
- This is the primary observability surface for the user during a workflow

**Health check:**
- `monkey-devs config validate` verifies all API keys are present and models are reachable before workflow start
- No ongoing health metrics or alerting — single-user local tool does not require it

---

### 9. Integration Layer

#### LangGraph

- **Role**: Workflow state machine and durable state persistence
- **Version**: LangGraph latest stable + `langgraph-checkpoint-sqlite`
- **Integration point**: `graph.py` — defines the StateGraph with five stage nodes, five correction branches, and human interrupt points
- **Failure mode**: If LangGraph fails mid-stage, SQLite checkpoint preserves state to the last completed node. `monkey-devs resume` restores from checkpoint.
- **Interrupt pattern**: `interrupt()` called after each stage node completes. CLI waits for `approve` or `reject` command before calling `graph.invoke()` to resume.

#### LiteLLM

- **Role**: Unified LLM API abstraction across Anthropic, OpenAI, and Google
- **Integration point**: `nodes/*.py` — each stage node calls `litellm.acompletion()` with `stream=True`
- **Model string format**: `provider/model-id` (e.g. `anthropic/claude-opus-4-6`)
- **Failure mode**: LiteLLM raises an exception on API error. Stage node catches, logs the error event, and surfaces a clear message to the user. Workflow state is not advanced.
- **Streaming**: `stream_to_terminal()` utility in `orchestrator.py` handles async streaming to stdout

#### Stage Node Integration Pattern

```python
async def concept_spec_node(state: WorkflowState) -> WorkflowState:
    # Orchestrator composes handoff (deterministic, no LLM)
    handoff = compose_handoff(state, stage=1)
    tools = get_stage_tools(stage=1)

    # LiteLLM call with streaming
    response = await litellm.acompletion(
        model=config.models["concept-spec"],
        messages=[{"role": "system", "content": handoff}],
        stream=True,
        tools=tools
    )

    # Stream to terminal and collect artifact
    artifact_path = await stream_to_terminal(response, stage=1)

    # Log completion
    log_event("llm_call_complete", stage=1, tokens_used=response.usage.total_tokens)
    log_event("artifact_written", stage=1, path=artifact_path)

    # Update and return state
    return {
        **state,
        "stage_outputs": {**state["stage_outputs"], 1: artifact_path},
        "stage_statuses": {**state["stage_statuses"], 1: "complete"},
        "stage_models": {**state["stage_models"], 1: config.models["concept-spec"]},
    }
```

---

## Part III — Implementation Guidance

### Implementation Units

| ID | Unit | Type | Inputs | Outputs | Depends On |
|----|------|------|--------|---------|------------|
| IU-01 | Python package scaffold | Package structure | DAD file layout spec | `monkey_devs/` directory, `pyproject.toml` | — |
| IU-02 | Config loader | Module | `config.yaml` schema | `load_config()`, `validate_config()` | IU-01 |
| IU-03 | Registry loader | Module | `registry.yaml` schema | `load_registry()`, `get_skills_for_stage()`, `get_tools_for_stage()` | IU-01 |
| IU-04 | LangGraph state schema | Module | `WorkflowState` TypedDict | `state.py` with full TypedDict | IU-01 |
| IU-05 | SQLite checkpointer setup | Module | LangGraph checkpoint API | Persistent graph with SQLite backend | IU-04 |
| IU-06 | Handoff composer | Module | Registry loader + state | `compose_handoff()`, `render_skills_block()` | IU-03, IU-04 |
| IU-07 | Stage tool scoping | Module | Tools registry + bash allowlist | `get_stage_tools()`, `validate_bash_command()` | IU-03 |
| IU-08 | JSONL run logger | Module | Event schema | `log_event()`, log rotation | IU-01 |
| IU-09 | Task manager | Module | `tasks.yaml` schema | `load_tasks()`, `dispatch_tasks()`, `update_task_status()` | IU-01 |
| IU-10 | LangGraph graph definition | Module | All stage nodes + state | `graph.py` with 5 stage nodes + 5 correction branches + interrupt points | IU-04, IU-05 |
| IU-11 | Concept & Spec node | Stage node | Handoff composer, LiteLLM | `nodes/concept_spec.py` | IU-06, IU-07, IU-08 |
| IU-12 | Architecture node | Stage node | Handoff composer, LiteLLM | `nodes/architecture.py` | IU-06, IU-07, IU-08, IU-09 |
| IU-13 | Implementation node | Stage node | Handoff composer, LiteLLM, task manager | `nodes/implementation.py` | IU-06, IU-07, IU-08, IU-09 |
| IU-14 | Code Fixing node | Stage node | Handoff composer, LiteLLM, task manager | `nodes/code_fixing.py` | IU-06, IU-07, IU-08, IU-09 |
| IU-15 | Delivery node | Stage node | Handoff composer, LiteLLM | `nodes/delivery.py` | IU-06, IU-07, IU-08 |
| IU-16 | CLI entrypoint | CLI (Typer) | All modules | `cli.py` with all commands | IU-10, IU-02, IU-09 |
| IU-17 | Skill files (×15) | Markdown | DAD skill inventory | `.opencode/skills/*.md` | — |
| IU-18 | Default registry + config | YAML | DAD schemas | `.opencode/registry.yaml`, `.opencode/config.yaml` | — |

### Generation Order

Implement in this sequence to minimize blocking:

1. **IU-01** — Package scaffold (no dependencies)
2. **IU-17, IU-18** — Skill files + default config/registry (no code dependencies)
3. **IU-02, IU-03** — Config and registry loaders (depend on IU-01 only)
4. **IU-04** — LangGraph state schema (depends on IU-01 only)
5. **IU-08** — Run logger (depends on IU-01 only)
6. **IU-05** — SQLite checkpointer setup (depends on IU-04)
7. **IU-09** — Task manager (depends on IU-01)
8. **IU-06** — Handoff composer (depends on IU-03, IU-04)
9. **IU-07** — Stage tool scoping + bash validator (depends on IU-03)
10. **IU-11 through IU-15** — Stage nodes in parallel (all depend on IU-06, IU-07, IU-08)
11. **IU-10** — LangGraph graph definition (depends on IU-04, IU-05, all stage nodes)
12. **IU-16** — CLI entrypoint (depends on IU-10, IU-02, IU-09)

### Per-Unit Generation Notes

**IU-06 (Handoff composer)**: Skill files are loaded and concatenated in `registry.yaml` order within the SKILLS block. Each skill is wrapped in `---\n## Skill: <name>\n<content>`. The `INSTRUCTIONS` block references skills by name and specifies their application order for the stage.

**IU-07 (Bash validator)**: The allowlist is defined as a list of command prefixes (not full commands) — e.g. `pytest` matches `pytest tests/` and `pytest -v tests/unit/`. The validator splits the command string and checks the first token against the allowlist. Blocks and logs any non-matching command.

**IU-10 (LangGraph graph)**: Each stage has two nodes: `stage_N_node` (primary) and `stage_N_correction` (correction branch). The gate after each stage uses `interrupt()`. On resume, the CLI passes the gate decision (`approve` or `reject`) into the graph input. If `approve`, edge goes to `stage_N+1_node`. If `reject`, edge goes to `stage_N_correction`.

**IU-13 (Implementation node)**: This node is invoked once per task by `dispatch_tasks()`. The `task_id` field in the handoff CONTEXT block specifies which task to implement. The node updates `tasks.yaml` status to `in-progress` on start and `done` on completion.

**IU-16 (CLI)**: `monkey-devs config set-model` must check `WorkflowState.workflow_status` before writing. If `active`, raise a clear error: `"Cannot change model configuration during an active workflow. Run 'monkey-devs status' to see current state."` The `monkey-devs init` command must add `.opencode/config.yaml`, `.opencode/workflow-state.db`, and `.opencode/logs/` to `.gitignore`.

---

## Appendix A — Architecture Decision Records

### ADR-001: YAML for Resource Registry

- **Status**: Accepted
- **Context**: The orchestrator needs to read skill and tool metadata at workflow start to build its allocation model. The registry must be human-editable and updatable without touching Python code.
- **Decision**: YAML manifest at `.opencode/registry.yaml`
- **Rationale**: Human-readable, comment-friendly, structured enough for deterministic stage-based filtering without a schema validator. JSON lacks comments. Markdown requires fragile prose parsing.
- **Alternatives considered**: JSON manifest, Markdown index
- **Consequences**: Requires a YAML parser (PyYAML or ruamel.yaml). Schema validation is recommended but not required for v1.

### ADR-002: Summary + Drill-Down Stage Gate

- **Status**: Accepted
- **Context**: NFR-05 requires transparency at every stage gate. OD-02 asked whether to show full allocation logs, a summary, or a minimal notice.
- **Decision**: CLI renders a compact summary at each gate; `monkey-devs details` expands the full run log for the current stage.
- **Rationale**: Full logs at every gate add noise for routine approvals. Minimal notice violates NFR-05. Summary + drill-down satisfies transparency on demand without cluttering the default flow.
- **Alternatives considered**: Full allocation log always shown, minimal one-line notice
- **Consequences**: `monkey-devs details` must read the JSONL run log and filter to the current stage's events.

### ADR-003: Correction Branch per Stage in LangGraph

- **Status**: Accepted
- **Context**: FR-23 requires rejected stages to re-run with updated instructions without restarting from Stage 1. OD-03 offered three LangGraph patterns: rewind, correction branch, or state patch.
- **Decision**: Each stage has a paired correction branch node in the LangGraph graph.
- **Rationale**: First-class LangGraph node. Carries rejection reason and prior output as inputs. Preserves full state history. Maps cleanly to LangGraph's interrupt + resume pattern.
- **Alternatives considered**: State rewind (loses rejection context), in-place state patch (messy history)
- **Consequences**: Graph has 10 primary nodes (5 stage + 5 correction) plus 5 gate interrupt points. Graph definition is more complex but behavior is explicit and auditable.

### ADR-004: Python CLI as Deterministic Orchestrator

- **Status**: Accepted
- **Context**: Original spec assumed an LLM-based orchestrator agent running in an IDE. Removing IDE dependency (user request) required rethinking who handles skill selection and task dispatch.
- **Decision**: Python CLI control loop replaces the LLM orchestrator. Skill and tool selection is deterministic Python code (filter registry by stage). No LLM tokens consumed for orchestration.
- **Rationale**: Skill selection is a deterministic lookup — no LLM reasoning required. Python code is cheaper, faster, testable, and more predictable than LLM-based orchestration. FR-03 (orchestrator must not generate code) is naturally enforced.
- **Alternatives considered**: LLM-based orchestrator agent, OpenCode IDE orchestrator
- **Consequences**: Orchestration is free (zero LLM cost). All intelligence is in stage nodes. Skill selection depends entirely on `stages` field accuracy in `registry.yaml`.

### ADR-005: SQLite Checkpointer for Workflow Persistence

- **Status**: Accepted
- **Context**: NFR-01 requires workflow resumability after session crash. LangGraph offers in-memory, SQLite, and PostgreSQL checkpointers.
- **Decision**: `langgraph-checkpoint-sqlite` at `.opencode/workflow-state.db`
- **Rationale**: SQLite survives process crashes, requires no infrastructure, ships with `langgraph-checkpoint-sqlite`. PostgreSQL requires a running server (violates local-first constraint). In-memory is lost on crash.
- **Alternatives considered**: In-memory (rejected — not durable), PostgreSQL (rejected — requires infrastructure)
- **Consequences**: SQLite file is a project artifact. Must be gitignored. Single-file database is inspectable but not suitable for concurrent access (acceptable for single-user tool).

### ADR-006: LiteLLM for Multi-Vendor LLM Abstraction

- **Status**: Accepted
- **Context**: FR-37 requires independently configurable models per stage from different vendors. Each stage node needs to call a different LLM provider.
- **Decision**: LiteLLM as the unified abstraction layer with `provider/model-id` string format.
- **Rationale**: LiteLLM supports Anthropic, OpenAI, and Google via a single `acompletion()` interface. Adding a new provider requires only a config change, no code changes. Streaming is supported uniformly.
- **Alternatives considered**: Direct provider SDKs with an adapter pattern (more code, same outcome)
- **Consequences**: LiteLLM is a required dependency. Model strings must follow LiteLLM's naming convention.

### ADR-007: Standalone Python CLI (No IDE Dependency)

- **Status**: Accepted
- **Context**: Original spec targeted OpenCode IDE as the runtime. User requested removing IDE dependency in favor of a pure CLI.
- **Decision**: Monkey Devs is a standalone Python CLI package with no IDE dependency.
- **Rationale**: Eliminates A-01 (OpenCode compatibility) as a risk. More portable — runs in any terminal on any OS. Simpler architecture — fewer moving parts.
- **Alternatives considered**: OpenCode IDE runtime (eliminated per user decision), Claude Code native agent (IDE-specific)
- **Consequences**: User interaction is terminal-only. No GUI. IDE integration is possible in future but not in scope for v1.

### ADR-008: Default Model Assignments

- **Status**: Accepted
- **Context**: FR-37 requires per-stage model configuration. User specified vendor assignments per stage.
- **Decision**: Gemini 2.5 Pro for Stages 1–2, Claude Opus 4.6 for Stage 3, Codex Mini for Stage 4, Claude Sonnet 4.6 for Stage 5.
- **Rationale**: Gemini 2.5 Pro's large context window suits intake and architecture. Opus 4.6 is the highest-quality model for complex code generation. Codex Mini is purpose-built for code understanding and repair. Sonnet 4.6 is fast and capable for documentation work.
- **Alternatives considered**: Single model for all stages (cheaper but lower quality for specialized work)
- **Consequences**: Three provider API keys required (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`). `monkey-devs config validate` must check all three before workflow start.

---

## Appendix B — Implementation Readiness Report

**Ready for generation (no blockers):**
- IU-01: Package scaffold — fully specified
- IU-02: Config loader — schema defined, env var pattern defined
- IU-03: Registry loader — YAML schema defined, filter logic is a simple list comprehension
- IU-04: LangGraph state schema — full TypedDict defined
- IU-05: SQLite checkpointer — standard LangGraph pattern
- IU-08: Run logger — event schema fully defined
- IU-17: Skill files — 15 skills enumerated; content to be written per skill's purpose
- IU-18: Default registry + config — schemas fully defined

**Needs content before generation:**
- IU-06 (Handoff composer): Injection format defined; needs `compose_handoff()` to know the exact INSTRUCTIONS block template per stage
- IU-11 through IU-15 (Stage nodes): Integration pattern defined; each node needs its stage-specific INSTRUCTIONS template written before the system prompt can be assembled

**Recommended first sprint:**
1. IU-01 — Package scaffold (unblocks everything)
2. IU-04, IU-08 — State schema + logger (fast, no external deps)
3. IU-02, IU-03 — Config + registry loaders (needed by all stage nodes)
4. IU-17, IU-18 — Skill files + default YAML configs (can be written in parallel)
5. IU-06, IU-07 — Handoff composer + tool scoping (complete the orchestration layer)

**Blocking items before generation can start:**
- None. All open decisions are resolved. The INSTRUCTIONS block templates for each stage node are the only content items not yet written, but they do not block scaffold and module generation — they can be written in parallel with IU-01 through IU-09.

---

## Ready for Implementation

**DAD file**: `docs/design/design-monkey-devs.md`
**Spec file**: `docs/specs/spec-monkey-devs.md` (finalized, v1.0)
**Status**: Approved for generation

**Implementation units**:
- IU-01: Python package scaffold — structure — ready
- IU-02: Config loader — module — ready
- IU-03: Registry loader — module — ready
- IU-04: LangGraph state schema — module — ready
- IU-05: SQLite checkpointer setup — module — ready
- IU-06: Handoff composer — module — ready (INSTRUCTIONS templates to write in parallel)
- IU-07: Stage tool scoping + bash validator — module — ready
- IU-08: JSONL run logger — module — ready
- IU-09: Task manager — module — ready
- IU-10: LangGraph graph definition — module — needs IU-11 through IU-15
- IU-11: Concept & Spec node — stage node — ready (INSTRUCTIONS template to write)
- IU-12: Architecture node — stage node — ready (INSTRUCTIONS template to write)
- IU-13: Implementation node — stage node — ready (INSTRUCTIONS template to write)
- IU-14: Code Fixing node — stage node — ready (INSTRUCTIONS template to write)
- IU-15: Delivery node — stage node — ready (INSTRUCTIONS template to write)
- IU-16: CLI entrypoint — CLI — needs IU-10
- IU-17: Skill files (×15) — markdown — ready to write
- IU-18: Default registry + config — YAML — ready to write

**Recommended generation order**: IU-01 → IU-04, IU-08 → IU-02, IU-03 → IU-17, IU-18 → IU-06, IU-07 → IU-09 → IU-11–IU-15 → IU-10 → IU-16

**Constraints for generators**:
- Language/runtime: Python 3.11+
- Framework: Typer (CLI), LangGraph (workflow), LiteLLM (LLM abstraction)
- Package manager: uv
- Naming conventions: snake_case for modules and functions, kebab-case for CLI commands
- Test coverage requirement: unit tests for all orchestration modules (IU-02 through IU-09); integration tests for stage nodes against LangGraph graph

**Blocking items before generation can start**:
- None
