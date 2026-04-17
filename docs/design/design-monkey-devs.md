# Design and Architecture Document: Monkey Devs

**Version**: 1.4
**Date**: 2026-04-15
**Status**: Finalized (v1.4 — required runtime defect remediation)
**Spec Source**: spec-monkey-devs.md v1.2
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
- Active thread pointer (`.opencode/active-thread-id`)
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
    stage_outputs: dict[int | str, list[str]]  # absolute artifact paths per stage/sub-stage
    stage_models: dict[int | str, str]       # model used per stage/sub-stage (audit)
    correction_active: bool
    correction_stage: int | None
    correction_reason: str | None
    tasks: list[str]                         # task IDs from tasks.yaml
    tasks_dispatched: list[str]
    tasks_completed: list[str]
    current_task_index: int                  # index into tasks[] for Stage 3 Send() fan-out
    gate_decisions: dict[int, str]           # approved | fix | rejected
    allocated_skills: dict[int, list[str]]
    allocated_tools: dict[int, list[str]]
    thread_id: str                           # LangGraph thread ID used for interrupt/resume
    correction_counts: dict[int, int]        # number of correction cycles per stage
    review_verdicts: dict[int, str]          # pass | warn | block per stage (keyed by stage number)
    review_brief_paths: dict[int, str]       # absolute path to fix brief per stage
    review_skipped: dict[int, bool]          # True when review verdict was pass and fix_node was bypassed
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
  code-fixing:     openai/o4-mini
  delivery:        anthropic/claude-sonnet-4-6
  reviewer:        anthropic/claude-opus-4-6   # adversarial critique — global, applies to all stages
  fixer:           google/gemini-2.5-pro        # artifact rewrite — used by fix_node and documentation_node

providers:
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
  openai:
    api_key_env: OPENAI_API_KEY
  google:
    api_key_env: GEMINI_API_KEY

timeouts:
  concept-spec:    120      # seconds per LLM call attempt
  architecture:    120
  implementation:  180
  code-fixing:     120
  delivery:        60
  reviewer:        90
  fixer:           120

workflow:
  max_corrections_per_stage: 3
  max_handoff_chars: 400000   # semantic truncation applied if exceeded
  max_intake_turns: 20
  max_tool_iterations: 30     # hard stop for repeated tool-call loops inside a single stage run
  auto_correction_on_validation_failure: true

review:
  enabled: true              # set false to bypass review_node and fix_node entirely
```

---

### 9. Interface Contracts

#### CLI Interface

| Command | Description |
|---------|-------------|
| `monkey-devs init` | Initialize new project, create `.opencode/` structure, write `.opencode/active-thread-id`, start Stage 1 |
| `monkey-devs run` | Run the current stage (streams LLM output to terminal) |
| `monkey-devs run --verbose` | Run with skill injection + state transition events |
| `monkey-devs run --debug` | Run with full real-time event log |
| `monkey-devs status` | Show workflow state, current stage, task list. Pure read operation; does not rotate logs or mutate workflow files. |
| `monkey-devs approve` | Approve current stage gate, resolve the active `thread_id` from `.opencode/active-thread-id`, and advance to the next stage |
| `monkey-devs reject --reason "..."` | Reject current stage, resolve the active `thread_id` from `.opencode/active-thread-id`, and enter the correction branch |
| `monkey-devs resume [--project-path PATH]` | Resume an interrupted workflow from last checkpoint. If run outside a project directory and `--project-path` is omitted, prints: "No .opencode/ directory found. Run from your project directory or pass --project-path." Before resuming Stage 3+ workflows it also re-validates `.opencode/tasks.yaml` and blocks on invalid task state. |
| `monkey-devs tasks` | List tasks and their status (Stage 3+) |
| `monkey-devs registry` | Show resource registry contents |
| `monkey-devs skills list` | List skills with stage assignments |
| `monkey-devs config models` | Show current model assignments |
| `monkey-devs config set-model <stage> <model>` | Update model for a stage (blocked during active workflow) |
| `monkey-devs config validate` | Verify API keys are set, models are reachable, registry schema is valid, no key literals exist in config, and warn when an estimated stage handoff exceeds 80% of a model's known context window |
| `monkey-devs details` | Expand full allocation log for current stage gate |

#### Handoff Message Schema

```markdown
## HANDOFF: [Stage Name]

### CONTEXT
project: [project name]
stage: [1-5 or "5a"/"5b" when relevant]
task_id: [T-XX or "all" for non-Implementation stages]
prior_outputs: [list of prior stage artifact paths, or []]

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
| OD-01 | Resource registry format | YAML at `.opencode/registry.yaml` | Human-readable, comment-friendly, structured enough for deterministic filtering, with schema validation enforced by `monkey-devs config validate` |
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
| Code Fixing | `openai/o4-mini` | Strong code understanding and repair; confirmed available in OpenAI API |
| Delivery | `anthropic/claude-sonnet-4-6` | Fast and precise for documentation and delivery summary |
| Reviewer (all stages) | `anthropic/claude-opus-4-6` | Strong critical reasoning for adversarial artifact critique |
| Fixer (all stages) | `google/gemini-2.5-pro` | Large context window for full-artifact rewrites and documentation generation |

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
| Documentation Node (Stage 5a) | Async LLM function | Generate API reference, developer guide, and inline docstrings |
| Review Node (shared) | Async LLM function | Critique each stage artifact; produce structured fix brief |
| Fix Node (shared) | Async LLM function | Rewrite stage artifact based on fix brief; skipped on `pass` verdict |
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

- **Responsibility**: The deterministic brain of the system. Reads registry, selects skills and tools for the current stage, composes handoff messages, dispatches tasks, renders stage gates, issues LangGraph commands, and maintains the active thread pointer.
- **Key functions**: `load_registry()`, `compose_handoff()`, `get_stage_tools()`, `render_stage_gate()`, `dispatch_tasks()`, `run_agentic_loop()`, `check_api_key_for_stage()`, `validate_artifacts()`, `resolve_active_thread_id()`
- **State**: Stateless between CLI invocations — all state lives in LangGraph SQLite
- **LLM calls**: None. Zero LLM tokens consumed by orchestration.
- **FRs fulfilled**: FR-02, FR-03, FR-07, FR-24, FR-26, FR-29, FR-30, NFR-03, NFR-05

#### Agentic Loop (shared by all stage nodes)

Every stage node executes a tool-execution agentic loop. This loop is implemented in `orchestrator.py` as `run_agentic_loop()` and called by all stage node functions:

1. Build initial `messages` list with the handoff as the system message.
2. Call `litellm.acompletion()` with `stream=True` and the stage's tool schemas.
3. Consume the async stream inside `asyncio.timeout(timeout_seconds)` so the stage timeout covers the full streaming block, not just connection setup. Accumulate `content` to terminal and accumulate `tool_calls`.
4. Append the assistant turn (content + tool_calls) to `messages`.
5. If the turn contains no tool calls → final response. Write artifact and exit loop.
6. For each tool call: call `execute_tool(tool_call, stage)`, append a `{"role": "tool", ...}` message to `messages`.
7. Go to step 2.

Retry policy (implemented in `run_agentic_loop()`): exponential backoff with 3 attempts for HTTP 429, 503, and network errors; delays of 1 s, 2 s, 4 s. Timeout per attempt is read from `config.timeouts[stage_key]` and applies to the entire streamed response, not only the initial `acompletion()` await. After 3 failures the exception is re-raised and the stage node logs a `stage_error` event; the workflow pauses with a clear user message.

**FRs fulfilled**: FR-09, FR-12

#### Stage Node: Concept & Spec

- **Responsibility**: Multi-turn conversational intake with the user; produces concept document and requirements spec; proposes 2–3 ranked stack candidates.
- **Model**: `google/gemini-2.5-pro`
- **Skills**: `conversational-intake`, `requirements-writing`, `stack-evaluation`
- **Tools**: `filesystem_read` (project docs), `filesystem_write` (`docs/`)
- **Output artifacts**: `docs/concept.md`, `docs/spec.md`
- **Multi-turn loop**: Stage 1 is a terminal input loop. After each LLM response is printed, the node awaits terminal input via `await asyncio.get_event_loop().run_in_executor(None, input, "\nYou: ")` and appends the user turn to `messages`. The loop continues until the LLM produces a response containing the sentinel `<intake-complete/>` or the turn count reaches `config.workflow.max_intake_turns` (default 20). On turn-limit exit, the node forces an artifact write from the best available draft, logs `intake_turn_limit_reached`, and surfaces that the intake ended due to the configured cap rather than agent completion.
- **FRs fulfilled**: FR-13, FR-14, FR-34

#### Stage Node: Architecture

- **Responsibility**: Makes final binding stack decision; produces system design and task breakdown.
- **Model**: `google/gemini-2.5-pro`
- **Skills**: `system-design`, `task-decomposition`, `adr-writing`, `stack-decision`
- **Tools**: file-read (full project), file-write (`docs/`, `.opencode/tasks.yaml`)
- **Output artifacts**: `docs/architecture.md`, `.opencode/tasks.yaml`
- **FRs fulfilled**: FR-15, FR-16, FR-35

#### Stage Node: Implementation

- **Responsibility**: Writes production code and tests for one assigned task unit. Invoked once per task via LangGraph `Send()` fan-out.
- **Model**: `anthropic/claude-opus-4-6`
- **Skills**: `tdd-implementation`, `code-generation`
- **Tools**: `filesystem_read` (full project), `filesystem_write` (full project), `bash_execute` (build/test commands — allowlisted)
- **Output artifacts**: source files per task branch; merged into `stage_outputs[3]` as a list of touched paths
- **Task dispatch topology**: After Stage 2 is approved, a `dispatch_stage3` router node reads `tasks` from `WorkflowState`, runs `topological_sort(tasks)` to resolve `depends_on` order, and emits one `Send("implementation_node", {"task_id": tid})` per task. LangGraph fans out to one `implementation_node` invocation per task. Each invocation receives its `task_id` in the handoff CONTEXT block and operates independently. When all `Send()` branches complete, LangGraph merges results and advances to the Stage 3 gate.
- **FRs fulfilled**: FR-17

#### Stage Node: Code Fixing

- **Responsibility**: Runs all tests; attempts to fix failures; classifies all unresolved failures as `code-issue` or `test-issue`; presents classifications at stage gate.
- **Model**: `openai/o4-mini`
- **Skills**: `test-categorization`, `systematic-debugging`
- **Tools**: file-read (full project), file-write (full project), bash (test runner — allowlisted)
- **Output artifacts**: updated source files plus `.opencode/tasks.yaml`
- **FRs fulfilled**: FR-18, FR-19, NFR-04

#### Stage Node: Documentation (Stage 5a)

- **Responsibility**: Generates technical reference documentation for the completed, fixed codebase. Runs as the first sub-phase of Stage 5, before the Delivery node. Uses the `fixer` model — same large-context rewrite capability used by the Fix node.
- **Model**: `fixer` (`google/gemini-2.5-pro`)
- **Skills**: `api-documentation`, `developer-guide-writing`, `docstring-writing`
- **Tools**: `filesystem_read` (full project), `filesystem_write` (`docs/` and source files)
- **Output artifacts**: `docs/api-reference.md`, `docs/developer-guide.md`, updated source files (inline docstrings/comments)
- **`stage_models` key**: `"5a"` — recorded separately from the Delivery node for audit
- **`stage_outputs` key**: `"5a"` — list of all documentation paths produced or modified in this sub-stage

#### Stage Node: Delivery (Stage 5b)

- **Responsibility**: Produces delivery summary and README; confirms repository is locally runnable. Runs after the Documentation node as the second sub-phase of Stage 5.
- **Model**: `anthropic/claude-sonnet-4-6`
- **Skills**: `delivery-summary`, `readme-writing`
- **Tools**: `filesystem_read` (full project), `filesystem_write` (`docs/`, README)
- **Output artifacts**: `README.md`, `docs/delivery.md`
- **`stage_models` key**: `"5b"`
- **`stage_outputs` key**: `"5b"` — combined Stage 5 artifact list. The delivery node copies forward every path from `stage_outputs["5a"]`, appends `README.md` and `docs/delivery.md`, and returns that aggregated list so the Stage 5 review runs against the full five-file output rather than a single path.
- **FRs fulfilled**: FR-20

#### Review Node (shared — all stages)

- **Responsibility**: Examines the primary stage artifact using the `adversarial-review` skill. Produces a structured fix brief at `.opencode/review/stage-N-fix-brief.md` with a verdict (`pass | warn | block`) and a ranked issue list (critical → high → medium), each with a concrete fix instruction. If the verdict is `pass`, updates `review_skipped[stage] = True` and exits without writing a brief — the fix node is bypassed. Runs after every primary stage node (and after Stage 5b for the combined documentation+delivery output) before `interrupt()`.
- **Model**: `reviewer` (`anthropic/claude-opus-4-6`)
- **Skills**: `adversarial-review`
- **Tools**: `filesystem_read` (every path in the current stage output list; Stage 5 uses the combined list at `stage_outputs["5b"]`)
- **Bypass condition**: `config.review.enabled = false` → conditional edge skips both `review_node` and `fix_node`

#### Fix Node (shared — all stages)

- **Responsibility**: Consumes the fix brief produced by the Review node and rewrites the current stage artifact set to address all listed issues. Receives the original artifact path list and the fix brief path via the handoff INSTRUCTIONS block. Writes updated artifacts in place. Skipped entirely when `review_skipped[stage] = True`.
- **Model**: `fixer` (`google/gemini-2.5-pro`)
- **Skills**: none — the fix brief is the complete instruction set
- **Tools**: `filesystem_read` (stage artifact list + fix brief), `filesystem_write` (stage artifact list)

---

### 4. Data Layer

#### Storage Technologies

| Store | Technology | Path | Owner | Purpose |
|-------|------------|------|-------|---------|
| Workflow state | SQLite (LangGraph checkpointer) | `.opencode/workflow-state.db` | LangGraph | Durable workflow state across sessions |
| Active thread pointer | Plain text | `.opencode/active-thread-id` | Python CLI | Stable lookup of the LangGraph `thread_id` for approve/reject/resume commands |
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
  - name: adversarial-review
    description: "Adversarial critique of stage artifacts: find issues, produce ranked fix brief"
    stages: [0]
    path: .opencode/skills/adversarial-review.md
  - name: api-documentation
    description: "Generate endpoint/schema API reference from source code"
    stages: [5]
    path: .opencode/skills/api-documentation.md
  - name: developer-guide-writing
    description: "Write setup, test, and module structure developer documentation"
    stages: [5]
    path: .opencode/skills/developer-guide-writing.md
  - name: docstring-writing
    description: "Write inline docstrings and comments for public interfaces"
    stages: [5]
    path: .opencode/skills/docstring-writing.md

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

`stages: [0]` is reserved for orchestrator-only reference skills. These entries are valid registry records, but `get_skills_for_stage()` never injects them into a normal stage handoff. They are consumed only by the CLI control loop or by explicit named loading paths such as `load_skill_by_name("adversarial-review")`.

#### Tool Schemas

`get_stage_tools(stage)` returns fully-formed OpenAI-format function schemas. Filesystem tool execution is guarded by `validate_path(path, project_root)` in `tools.py`, which resolves the requested path with `os.path.realpath()` and raises `FilesystemBoundaryError` when the resolved path is outside `project_root`. `execute_tool()` calls this validator before every filesystem read, write, or list operation. The four defined schemas are:

```python
FILESYSTEM_READ = {
    "type": "function",
    "function": {
        "name": "filesystem_read",
        "description": "Read the contents of a file from the local filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or project-relative path to the file."}
            },
            "required": ["path"]
        }
    }
}

FILESYSTEM_WRITE = {
    "type": "function",
    "function": {
        "name": "filesystem_write",
        "description": "Write content to a file on the local filesystem. Creates parent directories as needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or project-relative path to the file."},
                "content": {"type": "string", "description": "Full content to write to the file."}
            },
            "required": ["path", "content"]
        }
    }
}

FILESYSTEM_LIST = {
    "type": "function",
    "function": {
        "name": "filesystem_list",
        "description": "List files and directories at a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list."}
            },
            "required": ["path"]
        }
    }
}

BASH_EXECUTE = {
    "type": "function",
    "function": {
        "name": "bash_execute",
        "description": "Execute an allowlisted shell command. Only commands on the stage's allowlist are permitted.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."}
            },
            "required": ["command"]
        }
    }
}
```

`get_stage_tools(stage)` returns these schemas (not registry metadata) filtered by stage: Stages 1–5 receive `[FILESYSTEM_READ, FILESYSTEM_WRITE, FILESYSTEM_LIST]`; Stages 3 and 4 additionally receive `[BASH_EXECUTE]`.

**Run log event types (JSONL)**
```json
{"ts": "ISO8601", "event": "workflow_started", "project": "..."}
{"ts": "ISO8601", "event": "stage_started", "stage": 2, "model": "google/gemini-2.5-pro"}
{"ts": "ISO8601", "event": "skill_injected", "stage": 2, "skill": "system-design"}
{"ts": "ISO8601", "event": "tool_granted", "stage": 2, "tool": "filesystem"}
{"ts": "ISO8601", "event": "llm_call_complete", "stage": 2}
{"ts": "ISO8601", "event": "artifact_written", "stage": 2, "path": "docs/architecture.md"}
{"ts": "ISO8601", "event": "stage_gate_presented", "stage": 2}
{"ts": "ISO8601", "event": "stage_approved", "stage": 2}
{"ts": "ISO8601", "event": "stage_rejected", "stage": 2, "reason": "..."}
{"ts": "ISO8601", "event": "correction_started", "stage": 2}
{"ts": "ISO8601", "event": "task_dispatched", "task_id": "T-01"}
{"ts": "ISO8601", "event": "task_completed", "task_id": "T-01"}
{"ts": "ISO8601", "event": "intake_turn_limit_reached", "stage": 1, "turns": 20}
{"ts": "ISO8601", "event": "handoff_truncation_blocked", "stage": 3, "reason": "architecture_and_tasks_required"}
{"ts": "ISO8601", "event": "tasks_validation_post_fix_failed", "stage": 2, "error": "..."}
```

#### File Layout

```
.opencode/
├── registry.yaml          # Skills and tools catalog
├── config.yaml            # Model assignments and provider config
├── tasks.yaml             # Task list (created at Stage 2)
├── workflow-state.db      # LangGraph SQLite state
├── active-thread-id       # Plain-text pointer to the active LangGraph thread_id
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
│   ├── task-dispatch.md
│   ├── adversarial-review.md
│   ├── api-documentation.md
│   ├── developer-guide-writing.md
│   └── docstring-writing.md
├── review/                        # fix briefs (gitignored — intermediate artifacts)
│   └── stage-<N>-fix-brief.md
└── logs/
    └── run-<timestamp>.jsonl

monkey_devs/               # Python package
├── __init__.py
├── cli.py                 # Typer CLI entrypoint
├── orchestrator.py        # compose_handoff(), load_registry(), render_stage_gate(), run_agentic_loop(), check_api_key_for_stage(), validate_artifacts(), resolve_active_thread_id()
├── graph.py               # LangGraph graph definition (5 stage nodes + 5 correction branches + dispatch_stage3 + correction_limit_reached)
├── nodes/
│   ├── concept_spec.py
│   ├── architecture.py
│   ├── implementation.py
│   ├── code_fixing.py
│   ├── documentation.py
│   ├── delivery.py
│   └── review.py              # review_node() and fix_node() — shared across all stages
├── tools.py               # get_stage_tools(), validate_path(), execute_tool(), bash allowlist validator
├── config.py              # load_config(), validate_config(), model_context_limits
├── tasks.py               # load_tasks(), dispatch_tasks(), update_task_status(), topological_sort(), validate_tasks_yaml(), per-file asyncio lock
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
.opencode/active-thread-id
.opencode/logs/
.opencode/config.yaml
.opencode/review/
```

Note: `registry.yaml`, `tasks.yaml`, and `skills/` are intentionally NOT gitignored — they are project artifacts the user may want to version.

---

### 7. Security Layer

**Authentication model**: None — local single-user tool, no auth required.

**Filesystem boundary enforcement:**
- `tools.py` defines `validate_path(path, project_root) -> str`, which resolves the candidate path with `os.path.realpath()` and returns the canonical resolved path only when it remains under `project_root`
- If the resolved path escapes the project root, `validate_path()` raises `FilesystemBoundaryError`
- `execute_tool()` calls `validate_path()` before every `filesystem_read`, `filesystem_write`, and `filesystem_list` operation, so symlink traversal and `../` traversal are blocked before any filesystem access occurs

**API key management:**
- `config.yaml` stores env var names only (e.g. `api_key_env: ANTHROPIC_API_KEY`)
- Python CLI reads keys via `os.environ` at runtime
- `monkey-devs config validate` scans `config.yaml` for accidental key literals before any workflow operation and blocks execution if found
- Key literal scanner regex patterns checked by `validate_config()`:
  - OpenAI: `sk-[a-zA-Z0-9\-_]{20,}`
  - Google: `AIza[0-9A-Za-z\-_]{35}`
  - Anthropic: `sk-ant-[a-zA-Z0-9\-_]{90,}`
- `check_api_key_for_stage(stage)` is called at the start of each stage node (before the LLM call) via `os.environ.get()`. If the required key is absent, the stage raises a clear error: `"<KEY_NAME> is not set. Set it and run 'monkey-devs resume'."` No network call is made.
- `.opencode/config.yaml` is gitignored by default

**Prompt injection mitigation:**
- All user-supplied text (project name, rejection reasons, task descriptions) is inserted into handoff messages as data fields, never concatenated into instruction text
- Correction reasons are wrapped in explicit delimiters: `<user-rejection-reason>...</user-rejection-reason>`
- Prior stage artifact content is wrapped in delimiters: `<prior-stage-output stage="N">...</prior-stage-output>`. The stage node system prompt includes an explicit instruction to treat all delimited content as read-only reference material, not as instructions.
- Stage node system prompts include an explicit instruction to treat all delimited content as data, not instructions

**Bash scope enforcement:**
- Stage 3 and Stage 4 nodes receive an allowlist of permitted commands in their TOOLS block
- Python CLI `validate_bash_command(command)` enforces four checks in order:
  1. Parse the full command string with `shlex.split()`. If parsing raises `ValueError` (unmatched quotes), reject.
  2. Reject if any token or the raw string contains shell metacharacters: `;`, `&&`, `||`, `$()`, backticks, `|`, `>`, `<`, `&`.
  3. Check the first token (the executable) against the allowlist.
  Any check failure blocks the command and logs a `bash_blocked` event.
- Default allowlist executables: `pytest`, `npm`, `yarn`, `cargo`, `go`, `make`, `mvn`, `python`, `python3`, `pip`, `pip3`
- `pip` and `pip3` are permitted only as constrained exceptions for Stages 3 and 4. A secondary argument validator requires the second token to be `install`, allowing `pip install ...` and `pip install -r ...` forms only.
- No `sudo`, `rm`, `curl`, `wget`, or network commands on the allowlist
- Design limitation / accepted risk: this validator prevents direct shell injection in the command string, but it does not sandbox the behavior of allowlisted executables. An LLM can still ask `python`, `pytest`, `make`, `pip`, or similar allowlisted tools to execute LLM-authored code with arbitrary behavior inside project permissions.
- Future hardening pass: add an opt-in restricted execution mode for selected bash commands using `subprocess.run(timeout=...)` plus resource limits such as `RLIMIT_FSIZE` to reduce damage from LLM-authored code execution. This is explicitly deferred and not part of the v1 security boundary.

**Correction cycle limit:**
- `config.workflow.max_corrections_per_stage` (default: 3) caps the number of correction cycles per stage
- `WorkflowState.correction_counts` tracks cycles consumed per stage
- When `correction_counts[stage] >= max_corrections_per_stage`, the graph routes to `correction_limit_reached` node instead of the correction branch. This node surfaces a blocking message to the user and calls `interrupt()` to pause the workflow for user intervention (user must run `monkey-devs reject` with a new strategy or manually edit artifacts before re-approving)

**Threat model:**

| Threat | Mitigation |
|--------|------------|
| API key leak via config file commit | Keys stored as env var references; `config.yaml` gitignored; `validate_config()` scans for key literals using known-format regexes |
| Prompt injection via user input | User content wrapped in delimiters; stage nodes instructed to treat as data |
| Prompt injection via prior stage artifacts | Prior artifact content wrapped in `<prior-stage-output stage="N">` delimiters; stage nodes instructed to treat as read-only reference |
| Filesystem path traversal / symlink escape | `validate_path()` canonicalizes with `os.path.realpath()` and `execute_tool()` rejects any resolved path outside `project_root` with `FilesystemBoundaryError` |
| Bash scope creep by LLM | `validate_bash_command()`: `shlex.split()`, metacharacter rejection, first-token allowlist, plus `pip`/`pip3` second-token validation before execution |
| Arbitrary behavior inside allowlisted executables | Accepted residual risk in v1: allowlist validation constrains invocation syntax but does not sandbox LLM-authored Python, test, build, or package-install code executed by allowlisted tools |
| Accidental project file deletion | Stage permissions enforce write-path scoping per stage; no stage has unrestricted delete access |
| Correction infinite loop | `correction_counts` tracked in state; `correction_limit_reached` node blocks further correction after `max_corrections_per_stage` |

---

### 8. Observability Layer

**Logging — Structured JSONL run log:**
- Path: `.opencode/logs/run-<timestamp>.jsonl`
- Format: one JSON object per line
- Events: workflow lifecycle, stage transitions, skill injections, tool grants, LLM call completions, artifact writes, gate decisions, task dispatches
- Retention: last 10 run logs kept; older logs deleted automatically by `monkey-devs init` and `monkey-devs run`. `monkey-devs status` is intentionally read-only and never rotates logs.

**CLI output levels:**
- Default (`monkey-devs run`): streams LLM output to terminal only
- Verbose (`monkey-devs run --verbose`): adds skill injection events, tool grants, state transitions
- Debug (`monkey-devs run --debug`): full real-time event log to terminal

**Stage gate drill-down:**
- `monkey-devs details` reads the current run log and prints the full allocation event sequence for the active stage
- This is the primary observability surface for the user during a workflow

**Health check:**
- `monkey-devs config validate` verifies all API keys are present, models are reachable, registry schema is valid, and warns when estimated stage handoffs exceed 80% of a configured model context window before workflow start
- No ongoing health metrics or alerting — single-user local tool does not require it

---

### 9. Integration Layer

#### LangGraph

- **Role**: Workflow state machine and durable state persistence
- **Version**: LangGraph latest stable + `langgraph-checkpoint-sqlite`
- **Integration point**: `graph.py` — defines the StateGraph with five primary stage nodes, one documentation sub-node (5a), five correction branches, two shared quality nodes (review, fix), and five gate interrupt points
- **Failure mode**: If LangGraph fails mid-stage, SQLite checkpoint preserves state to the last completed node. `monkey-devs resume` restores from checkpoint.
- **Interrupt pattern**: `interrupt()` called after the `fix_node` (or after the primary stage node when `review.enabled = false`). At workflow start the CLI writes the active LangGraph `thread_id` to `.opencode/active-thread-id` and refreshes that file on every run/resume. `monkey-devs approve` and `monkey-devs reject` resolve `thread_id` from that file first, falling back to a checkpoint lookup filtered by `project_path` metadata only if the pointer file is missing. The CLI then calls `graph.invoke(Command(resume=value), config={"configurable": {"thread_id": thread_id}})` where `value` is `{"decision": "approve"}` for approvals or `{"decision": "reject", "reason": "<user text>"}` for rejection. The first node after resume copies `value["decision"]` into `gate_decisions[current_stage]` and, for rejection, copies `value["reason"]` into `state["correction_reason"]` before correction routing executes.
- **Graph shape**: `stage_N_node → review_node → fix_node → interrupt()` for Stages 1–4. Stage 5: `documentation_node → delivery_node → review_node → fix_node → interrupt()`. The `review_node` and `fix_node` are shared functions parameterized by `state["current_stage"]`.

#### LiteLLM

- **Role**: Unified LLM API abstraction across Anthropic, OpenAI, and Google
- **Integration point**: `nodes/*.py` — each stage node calls `litellm.acompletion()` with `stream=True`
- **Model string format**: `provider/model-id` (e.g. `anthropic/claude-opus-4-6`)
- **Failure mode**: LiteLLM raises an exception on API error. Stage node catches, logs the error event, and surfaces a clear message to the user. Workflow state is not advanced.
- **Streaming**: `stream_to_terminal()` utility in `orchestrator.py` handles async streaming to stdout. The full stream-consumption block is covered by the stage timeout via `asyncio.timeout()` so a stalled stream cannot hang indefinitely after the initial `acompletion()` call succeeds.

#### Stage Node Integration Pattern

The agentic loop lives in `orchestrator.run_agentic_loop()` and is called by every stage node. The concept-spec node also wraps it in a multi-turn user input loop. The pattern below is the canonical reference for all stage nodes.

```python
# orchestrator.py
import asyncio, shlex
import litellm
from litellm.exceptions import RateLimitError, ServiceUnavailableError

async def run_agentic_loop(
    messages: list[dict],
    model: str,
    tools: list[dict],
    stage: int,
    timeout_seconds: int,
    max_tool_iterations: int,
) -> str:
    """
    Execute the tool-calling agentic loop for a stage node.
    Returns the final text response from the model.
    Raises after 3 failed retry attempts.
    """
    MAX_RETRIES = 3
    tool_iteration_count = 0

    while True:
        if tool_iteration_count >= max_tool_iterations:
            raise AgentLoopLimitError(
                f"Stage {stage} exceeded {max_tool_iterations} tool iterations on {model}. "
                "Review the prompt or select a different model before retrying."
            )

        # --- retry with exponential backoff ---
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                stream = await asyncio.wait_for(
                    litellm.acompletion(
                        model=model,
                        messages=messages,
                        stream=True,
                        tools=tools or None,
                    ),
                    timeout=timeout_seconds,
                )
                last_exc = None
                break
            except (RateLimitError, ServiceUnavailableError, OSError) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
        if last_exc:
            raise last_exc

        # --- consume stream ---
        response_content = ""
        tool_call_chunks: dict[int, dict[str, str | None]] = {}

        async def consume_stream() -> None:
            nonlocal response_content, tool_call_chunks
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end="", flush=True)
                    response_content += delta.content
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        entry = tool_call_chunks.setdefault(
                            tc_delta.index,
                            {"id": None, "name": None, "arguments": ""},
                        )
                        if tc_delta.id and entry["id"] is None:
                            entry["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name and entry["name"] is None:
                                entry["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                entry["arguments"] += tc_delta.function.arguments

        normalized_tool_calls: list[dict] = []

        async with asyncio.timeout(timeout_seconds):
            await consume_stream()
            normalized_tool_calls = [
                {
                    "id": entry["id"],
                    "type": "function",
                    "function": {
                        "name": entry["name"],
                        "arguments": entry["arguments"],
                    },
                }
                for _, entry in sorted(tool_call_chunks.items())
            ]

        # --- append assistant turn ---
        messages.append({
            "role": "assistant",
            "content": response_content,
            "tool_calls": normalized_tool_calls if normalized_tool_calls else None,
        })

        # --- final response: no tool calls ---
        if not normalized_tool_calls:
            return response_content

        # --- execute tools and inject results ---
        tool_iteration_count += 1
        for tc in normalized_tool_calls:
            result = await execute_tool(tc, stage=stage)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": str(result),
            })
        # loop continues


# nodes/concept_spec.py
async def concept_spec_node(state: WorkflowState) -> WorkflowState:
    check_api_key_for_stage(stage=1)

    handoff = compose_handoff(state, stage=1)
    tools = get_stage_tools(stage=1)
    model = config.models["concept-spec"]
    timeout = config.timeouts["concept-spec"]

    # Stage 1 multi-turn conversational loop
    messages = [{"role": "system", "content": handoff}]
    final_response = ""
    turn_count = 0
    while True:
        response = await run_agentic_loop(
            messages,
            model,
            tools,
            stage=1,
            timeout_seconds=timeout,
            max_tool_iterations=config.workflow.max_tool_iterations,
        )
        turn_count += 1
        if "<intake-complete/>" in response:
            final_response = response
            break
        if turn_count >= config.workflow.max_intake_turns:
            final_response = response
            log_event("intake_turn_limit_reached", stage=1, turns=turn_count)
            break
        # Print response was handled inside run_agentic_loop; prompt user for next input
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\nYou: ")
        messages.append({"role": "user", "content": user_input})
        # run_agentic_loop already appended the assistant turn; add user turn and loop

    artifact_paths = write_stage_artifacts(final_response, stage=1, state=state)

    log_event("llm_call_complete", stage=1)
    for path in artifact_paths:
        log_event("artifact_written", stage=1, path=path)

    return {
        **state,
        "stage_outputs": {**state["stage_outputs"], 1: [str(path) for path in artifact_paths]},
        "stage_statuses": {**state["stage_statuses"], 1: "complete"},
        "stage_models": {**state["stage_models"], 1: model},
    }
```

`write_stage_artifacts(response_text: str, stage: int | str, state: WorkflowState) -> list[pathlib.Path]` is the artifact-writer used for stage outputs emitted as structured assistant text rather than via `filesystem_write` tool calls. For Stage 1 it parses stage-specific `<artifact path="...">...</artifact>` blocks from `response_text`, writes exactly `docs/concept.md` and `docs/spec.md`, and returns those absolute paths. For Stage 2 and Stage 5b the same helper may be reused only for their canonical text artifacts (`docs/architecture.md`, `.opencode/tasks.yaml`, `README.md`, `docs/delivery.md`) when the stage instructions require response-embedded artifacts. Nodes that persist files through successful `filesystem_write` tool calls do not re-write those files through this helper; they record the tool-confirmed paths directly into `state["stage_outputs"]`.

All other stage nodes (architecture, code_fixing, delivery) call `run_agentic_loop()` directly without the multi-turn user input wrapper. The implementation node additionally reads its `task_id` from the `Send()` input rather than from `state["current_task_index"]`.

---

## Part III — Implementation Guidance

### Implementation Units

| ID | Unit | Type | Inputs | Outputs | Depends On |
|----|------|------|--------|---------|------------|
| IU-01 | Python package scaffold | Package structure | DAD file layout spec | `monkey_devs/` directory, `pyproject.toml` | — |
| IU-02 | Config loader | Module | `config.yaml` schema | `load_config()`, `validate_config()` | IU-01 |
| IU-03 | Registry loader | Module | `registry.yaml` schema | `load_registry()`, `get_skills_for_stage()`, `get_tools_for_stage()`, registry schema model | IU-01 |
| IU-04 | LangGraph state schema | Module | `WorkflowState` TypedDict | `state.py` with full TypedDict | IU-01 |
| IU-05 | SQLite checkpointer setup | Module | LangGraph checkpoint API | Persistent graph with SQLite backend | IU-04 |
| IU-06 | Handoff composer | Module | Registry loader + state | `compose_handoff()`, `render_skills_block()` | IU-03, IU-04 |
| IU-07 | Stage tool scoping | Module | Tools registry + bash allowlist | `get_stage_tools()`, `validate_path()`, `execute_tool()`, `validate_bash_command()` | IU-03 |
| IU-08 | JSONL run logger | Module | Event schema | `log_event()`, log rotation | IU-01 |
| IU-09 | Task manager | Module | `tasks.yaml` schema | `load_tasks()`, `dispatch_tasks()`, `update_task_status()`, `validate_tasks_yaml()` | IU-01 |
| IU-10 | LangGraph graph definition | Module | All stage nodes + state | `graph.py` with 5 stage nodes + 5 correction branches + interrupt points | IU-04, IU-05 |
| IU-11 | Concept & Spec node | Stage node | Handoff composer, LiteLLM | `nodes/concept_spec.py` | IU-06, IU-07, IU-08 |
| IU-12 | Architecture node | Stage node | Handoff composer, LiteLLM | `nodes/architecture.py` | IU-06, IU-07, IU-08, IU-09 |
| IU-13 | Implementation node | Stage node | Handoff composer, LiteLLM, task manager | `nodes/implementation.py` | IU-06, IU-07, IU-08, IU-09 |
| IU-14 | Code Fixing node | Stage node | Handoff composer, LiteLLM, task manager | `nodes/code_fixing.py` | IU-06, IU-07, IU-08, IU-09 |
| IU-15 | Delivery node | Stage node | Handoff composer, LiteLLM | `nodes/delivery.py` | IU-06, IU-07, IU-08 |
| IU-16 | CLI entrypoint | CLI (Typer) | All modules | `cli.py` with all commands | IU-10, IU-02, IU-09 |
| IU-17 | Skill files (×15) | Markdown | DAD skill inventory | `.opencode/skills/*.md` | — |
| IU-18 | Default registry + config | YAML | DAD schemas | `.opencode/registry.yaml`, `.opencode/config.yaml` | — |
| IU-19 | Review node | Shared LangGraph node | Stage artifact + `adversarial-review` skill | Fix brief at `.opencode/review/stage-N-fix-brief.md`; `review_verdicts`, `review_brief_paths`, `review_skipped` in state | IU-06, IU-08, IU-10 |
| IU-20 | Fix node | Shared LangGraph node | Fix brief + stage artifact path list | Updated artifacts written in place; skipped when `review_skipped[stage] = True` | IU-19 |
| IU-21 | Documentation node | Stage node (5a) | Full codebase + `api-documentation`, `developer-guide-writing`, `docstring-writing` skills | `docs/api-reference.md`, `docs/developer-guide.md`, updated source files | IU-06, IU-07, IU-08 |
| IU-22 | Adversarial-review skill | Skill file | — | `.opencode/skills/adversarial-review.md` | — |
| IU-23 | API documentation skill | Skill file | — | `.opencode/skills/api-documentation.md` | — |
| IU-24 | Developer guide skill | Skill file | — | `.opencode/skills/developer-guide-writing.md` | — |
| IU-25 | Docstring skill | Skill file | — | `.opencode/skills/docstring-writing.md` | — |

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
11. **IU-22 through IU-25** — New skill files (no code dependencies, parallel with other skills)
12. **IU-21** — Documentation node (depends on IU-06, IU-07, IU-08)
13. **IU-19** — Review node (depends on IU-06, IU-08, IU-10)
14. **IU-20** — Fix node (depends on IU-19)
15. **IU-10** — LangGraph graph definition (depends on IU-04, IU-05, all stage nodes including IU-19–IU-21)
16. **IU-16** — CLI entrypoint (depends on IU-10, IU-02, IU-09)

### Per-Unit Generation Notes

**IU-02 (Config loader)**: `config.py` owns a `model_context_limits` map keyed by model string (for the default supported models). `validate_config()` uses this map together with per-stage handoff-size estimates from `compose_handoff()` to warn, but not block, when a configured stage is expected to exceed 80% of the assigned model's context window.

**IU-03 (Registry loader)**: Registry records are validated during `monkey-devs config validate` using pydantic or jsonschema before any workflow run begins. Typos or malformed `stages:` fields are fatal validation errors; the CLI must not silently degrade resource selection.

**IU-06 (Handoff composer)**: Skill files are loaded and concatenated in `registry.yaml` order within the SKILLS block. Each skill is wrapped in `---\n## Skill: <name>\n<content>`. The `INSTRUCTIONS` block references skills by name and specifies their application order for the stage. Prior stage artifact content is injected into the CONTEXT block wrapped in `<prior-stage-output stage="N">...</prior-stage-output>` delimiters. Before returning the handoff string, `compose_handoff()` measures its character length and compares against `config.workflow.max_handoff_chars`. If the handoff exceeds the limit, truncation is semantic rather than first-N/last-N: drop lower-priority prior artifact bodies first (`docs/delivery.md`, then `docs/concept.md`) before touching higher-value artifacts. For Stage 3 specifically, `docs/architecture.md` and `.opencode/tasks.yaml` are mandatory and must never be truncated; if they cannot fit within `max_handoff_chars`, `compose_handoff()` raises `HandoffTruncationBlockedError`, logs `handoff_truncation_blocked`, and the stage gate tells the user to choose a higher-context model. `compose_handoff()` estimates per-stage handoff size during `config validate` so the CLI can warn when the configured model is likely to exceed 80% of its known context window.

**IU-07 (Stage tool scoping + bash validator)**: `get_stage_tools(stage)` returns fully-formed OpenAI-format schemas (see Data Layer "Tool Schemas") filtered by stage — not registry metadata strings. `tools.py` also defines `validate_path(path: str, project_root: str) -> str`, which canonicalizes paths with `os.path.realpath()` and raises `FilesystemBoundaryError` when the resolved path escapes `project_root`; `execute_tool()` must call it before every filesystem tool operation. `validate_bash_command(command: str) -> None` enforces four sequential checks: (1) parse with `shlex.split(command)` — raise `BashValidationError` if `ValueError` (unmatched quotes); (2) reject if the raw command string or any token contains shell metacharacters `;`, `&&`, `||`, `$()`, backtick, `|`, `>`, `<`, `&`; (3) check `shlex.split(command)[0]` (the executable) against the allowlist set; (4) if the executable is `pip` or `pip3`, require the second token to be exactly `install`. Any check failure raises `BashValidationError`, logs a `bash_blocked` event, and returns the error message to the LLM as the `bash_execute` tool result so the model can recover. This protects the invocation string, but it does not sandbox the behavior of LLM-authored code executed by allowlisted programs.

**IU-10 (LangGraph graph)**: The graph contains: five primary stage nodes, one documentation sub-node (5a), five correction branch nodes, one `dispatch_stage3` router node, one shared post-interrupt routing node, one `correction_limit_reached` node, two shared quality nodes (`review_node`, `fix_node`), and five gate interrupt points.

Stage dispatch topology: after Stage 2 is approved, `dispatch_stage3` calls `topological_sort(state["tasks"])` and emits `Send("implementation_node", {"task_id": tid})` for each task in sorted order. LangGraph fans out; results merge automatically when all branches complete.

Gate interrupt/resume: `interrupt()` is called after each primary stage node completes. The CLI writes the active `thread_id` to `.opencode/active-thread-id` at workflow start and refreshes it on every run/resume. On `monkey-devs approve`, the CLI resumes with `Command(resume={"decision": "approve"})`. On `monkey-devs reject --reason "..."`, the CLI resumes with `Command(resume={"decision": "reject", "reason": "<user text>"})`. If the pointer file is missing, the CLI may fall back to `checkpointer.list()` filtered by `project_path` metadata to recover the thread. The shared post-interrupt routing node copies the resumed `decision` into `gate_decisions[current_stage]`, copies `reason` into `correction_reason` when present, clears `correction_reason` on approval, and only then evaluates the conditional edge for approve vs. correction routing.

Correction routing: when a gate decision is `"reject"`, a conditional edge checks `state["correction_counts"][stage] >= config.workflow.max_corrections_per_stage`. If true, route to `correction_limit_reached` (which calls `interrupt()` with a blocking message). If false, increment `correction_counts[stage]` and route to `stage_N_correction`.

The graph has no bypass edges — all five stage gates are mandatory.

**IU-13 (Implementation node)**: This node is invoked once per task via LangGraph `Send()` fan-out from `dispatch_stage3`. The `task_id` is passed in the `Send()` payload, not read from `state["current_task_index"]`. The node constructs its handoff using `compose_handoff(state, stage=3, task_id=task_id)`, calls `run_agentic_loop()`, updates `tasks.yaml` status to `in-progress` on start and `done` on completion. `tasks.py` must expose `topological_sort(tasks: list[dict]) -> list[dict]` — called by `dispatch_stage3` before emitting `Send()` calls. If `topological_sort` detects a cycle in `depends_on` references, it raises `TaskCycleError` which surfaces as a blocking error at Stage 3 start before any implementation node runs.

**IU-19 (Review node)**: `review_node(state)` in `nodes/review.py`. Reads `state["current_stage"]` to locate the stage artifact paths from `state["stage_outputs"]`; for Stage 5 it explicitly reviews the combined artifact list in `state["stage_outputs"]["5b"]`. The review node does not call `get_skills_for_stage()`: it loads `adversarial-review` through a dedicated `load_skill_by_name("adversarial-review")` path because stage-0 skills are orchestrator-only reference skills, not normal stage injections. It injects the skill and artifact contents into the handoff INSTRUCTIONS block. Calls `run_agentic_loop()` with `config.models["reviewer"]` and `config.timeouts["reviewer"]`. Parses the verdict line (`verdict: pass|warn|block`) from the response. On `pass`: sets `review_skipped[stage] = True`, sets `review_verdicts[stage] = "pass"`, returns — does not write a fix brief. On `warn` or `block`: writes the full response as `stage-N-fix-brief.md`, sets `review_brief_paths[stage]` and `review_verdicts[stage]`. When `config.review.enabled = false`, a conditional edge in `graph.py` routes directly from the primary stage node to `interrupt()`, bypassing both `review_node` and `fix_node`. `check_api_key_for_stage` checks the reviewer's provider key before the LLM call.

**IU-20 (Fix node)**: `fix_node(state)` in `nodes/review.py` (same file as review node). First checks `state["review_skipped"].get(stage, False)` — if `True`, returns state unchanged immediately (no LLM call). Otherwise: loads the fix brief from `state["review_brief_paths"][stage]` and the original artifact path list from `state["stage_outputs"][stage]` (or `state["stage_outputs"]["5b"]` for Stage 5). Composes a handoff with the fix brief as the INSTRUCTIONS block and the artifact content in CONTEXT. Calls `run_agentic_loop()` with `config.models["fixer"]` and `config.timeouts["fixer"]`. Writes updated artifacts in place. For Stage 2, the INSTRUCTIONS block includes: "If architectural changes affect components, interfaces, or data models, regenerate `.opencode/tasks.yaml`." After the Stage 2 fix completes, the orchestrator re-runs `validate_tasks_yaml()` before `interrupt()`. If validation still fails, it logs `tasks_validation_post_fix_failed` and surfaces a blocking gate message so the user can correct the task file manually before approval. Logs `fix_applied` event on completion.

**IU-21 (Documentation node)**: `documentation_node(state)` in `nodes/documentation.py`. Runs as Stage 5a, before `delivery_node`. Uses `config.models["fixer"]` (shared with Fix node — no new model key). Injects `api-documentation`, `developer-guide-writing`, and `docstring-writing` skills via `compose_handoff(state, stage=5, sub_stage="documentation")`. Has `filesystem_read` access to the full project and `filesystem_write` access to `docs/` and all source files. Must write `docs/api-reference.md` and `docs/developer-guide.md` as named artifacts. Inline docstring updates are written directly into source files via `filesystem_write` tool calls during the agentic loop. Records `stage_models["5a"] = config.models["fixer"]` and `stage_outputs["5a"] = [...]` in returned state. The downstream `delivery_node` records `stage_models["5b"] = config.models["delivery"]` and builds `stage_outputs["5b"]` as the combined artifact list for Stage 5 review.

**IU-09 (Task manager)**: `tasks.py` exposes: `load_tasks()`, `update_task_status()`, `topological_sort(tasks)` (Kahn's algorithm; raises `TaskCycleError` on cycle), and `validate_tasks_yaml(path)`. The module owns a per-file `asyncio.Lock()` for `.opencode/tasks.yaml`; every read-modify-write path acquires the lock before loading the file. `update_task_status()` writes atomically by serializing to `.opencode/tasks.yaml.tmp` and then replacing the target with `os.replace(tmp, tasks.yaml)`. `validate_tasks_yaml()` is called by the orchestrator after Stage 2 completes and before the Stage 2 gate is presented. It checks: valid YAML syntax, all required fields present (`id`, `title`, `status`, `depends_on`, `failure_classification`), `status` values are in `{pending, in-progress, done}`, `depends_on` entries reference valid task IDs. If validation fails and `config.workflow.auto_correction_on_validation_failure` is `true`, the orchestrator increments `correction_counts[2]`, automatically triggers the Architecture correction branch (not a user rejection), and logs `tasks_validation_failed`. If the flag is `false`, the invalid task file is surfaced directly at the stage gate for manual correction. `monkey-devs resume` also runs `validate_tasks_yaml()` before proceeding with any workflow state that depends on tasks.

**IU-16 (CLI)**: `monkey-devs approve` and `monkey-devs reject` load `thread_id` from `.opencode/active-thread-id` and call `graph.invoke(Command(resume=value), config={"configurable": {"thread_id": thread_id}})`. If that file is missing, they may recover by calling `checkpointer.list()` filtered by `project_path` metadata to find the active thread. The resume payload is `{"decision": "approve"}` for `monkey-devs approve` and `{"decision": "reject", "reason": "<user text>"}` for `monkey-devs reject --reason "..."`; the graph's post-interrupt routing node is responsible for persisting `correction_reason` into `WorkflowState` before correction routing runs. `monkey-devs config set-model` must check `WorkflowState.workflow_status` before writing — if `active`, raise: `"Cannot change model configuration during an active workflow. Run 'monkey-devs status' to see current state."` `monkey-devs init` adds `.opencode/config.yaml`, `.opencode/workflow-state.db`, `.opencode/active-thread-id`, and `.opencode/logs/` to `.gitignore`, creates `.opencode/active-thread-id`, and initializes it with the new workflow thread. `monkey-devs resume` checks for `.opencode/` in the current directory; if absent and `--project-path` was not provided, prints: `"No .opencode/ directory found. Run from your project directory or pass --project-path."` `monkey-devs resume` calls `validate_artifacts(state)` before proceeding and re-runs `validate_tasks_yaml()` whenever the resumed workflow depends on `.opencode/tasks.yaml`; if any `stage_outputs` path is missing, it surfaces: `"Stage N artifact missing at <path>. Re-run that stage before resuming."` `monkey-devs config validate` validates `registry.yaml` with pydantic or jsonschema, fails loudly on malformed `stages:` data, and uses `config.py`'s `model_context_limits` map to warn when a stage's estimated handoff would exceed 80% of the assigned model's known context window.

---

## Appendix A — Architecture Decision Records

### ADR-001: YAML for Resource Registry

- **Status**: Accepted
- **Context**: The orchestrator needs to read skill and tool metadata at workflow start to build its allocation model. The registry must be human-editable and updatable without touching Python code.
- **Decision**: YAML manifest at `.opencode/registry.yaml`
- **Rationale**: Human-readable, comment-friendly, and structured enough for deterministic stage-based filtering while remaining easy to validate with pydantic or jsonschema. JSON lacks comments. Markdown requires fragile prose parsing.
- **Alternatives considered**: JSON manifest, Markdown index
- **Consequences**: Requires a YAML parser (PyYAML or ruamel.yaml). `monkey-devs config validate` must run registry schema validation and fail loudly on malformed `stages:` or tool definitions.

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
- **Consequences**: Graph has 10 primary nodes (5 stage + 5 correction), one shared post-interrupt routing node, plus 5 gate interrupt points. Graph definition is more complex but behavior is explicit and auditable.

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
- **Decision**: Gemini 2.5 Pro for Stages 1–2, Claude Opus 4.6 for Stage 3, `openai/o4-mini` for Stage 4, Claude Sonnet 4.6 for Stage 5.
- **Rationale**: Gemini 2.5 Pro's large context window suits intake and architecture. Opus 4.6 is the highest-quality model for complex code generation. `o4-mini` is a confirmed OpenAI model with strong code reasoning at lower cost than GPT-4o. Sonnet 4.6 is fast and capable for documentation work. (`openai/codex-mini` was removed — this model name does not appear in the OpenAI API model list.)
- **Alternatives considered**: Single model for all stages (cheaper but lower quality for specialized work)
- **Consequences**: Three provider API keys required (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`). `monkey-devs config validate` must check all three before workflow start.

### ADR-009: Autonomous Review→Fix Loop Before Every Stage Gate

- **Status**: Accepted
- **Context**: Stage outputs are produced by LLM agents and may contain structural errors, missing sections, or logic gaps that the user should not have to manually identify. The existing correction branch handles user-driven fixes but does not prevent avoidable defects from reaching the gate.
- **Decision**: A shared `review_node` + `fix_node` pair runs automatically after every primary stage node, before `interrupt()`. The review agent produces a structured fix brief; the fix agent rewrites the artifact. The user always sees the post-fix artifact at the gate.
- **Rationale**: Separating review from production (different model, different node) maximizes adversarial value — the model that produced the artifact does not also judge it. A single pass keeps latency bounded. The human gate immediately after is the final check. The `pass` bypass ensures the fix node adds zero cost when the artifact is already clean.
- **Alternatives considered**: Review inside the stage node (same model, lower adversarial value); user-invoked `monkey-devs review` command (optional, defeats the purpose); review loop with iteration ceiling (higher cost, marginal quality gain given the human gate).
- **Consequences**: Two new shared nodes in the graph. Two new model config keys (`reviewer`, `fixer`). `.opencode/review/` directory added and gitignored. `WorkflowState` gains three new fields.

### ADR-010: Documentation Node as Stage 5a, Reusing Fixer Model

- **Status**: Accepted
- **Context**: The Delivery node (Stage 5) produces user-facing documentation (README, delivery summary) but does not produce technical reference documentation (API reference, developer guide, inline docstrings). A documentation agent was requested to fill this gap.
- **Decision**: A `documentation_node` runs as Stage 5a, before the existing Delivery node (now Stage 5b). It uses the `fixer` model (`google/gemini-2.5-pro`) — already configured for large-context rewrites — rather than adding a new model config key. Both sub-nodes are covered by the single Stage 5 gate. The review→fix pair (ADR-009) applies to the combined Stage 5 output.
- **Rationale**: Embedding documentation in Stage 5 avoids adding a mandatory Stage 6, preserving the five-gate workflow contract (FR-22). The `fixer` model's large context window is well-suited for reading a full codebase and generating comprehensive reference docs. No new model key keeps the config minimal.
- **Alternatives considered**: Stage 6 with its own gate (breaks FR-22); parallel per-task documentation during Stage 3 (documentation quality degrades against incomplete codebase); separate `monkey-devs document` command (not integrated into the workflow guarantee).
- **Consequences**: `stage_models` gains `"5a"` and `"5b"` sub-keys, and `stage_outputs` stores Stage 5 artifacts as combined path lists rather than a single path. Three new skill files required. `nodes/documentation.py` added. Stage 5 gate summary must present both documentation and delivery artifacts.

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
- None. The 2026-04-15 remediation brief has been incorporated into this design (v1.4), including streaming tool-call reconstruction, non-blocking Stage 1 input handling, correction-reason resume payload handling, an explicit tool-iteration ceiling, and a defined `write_stage_artifacts()` contract. Deferred recommended and optional follow-ups are tracked in `docs/review-issue-log.md`.

---

## Ready for Implementation

**DAD file**: `docs/design/design-monkey-devs.md`
**Spec file**: `docs/specs/spec-monkey-devs.md` (finalized, v1.2)
**Status**: Approved for generation (v1.4 — required runtime defect remediation applied)

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
- IU-19: Review node — shared LangGraph node — ready
- IU-20: Fix node — shared LangGraph node — ready (needs IU-19)
- IU-21: Documentation node — stage node (5a) — ready
- IU-22: Adversarial-review skill — markdown — ready to write
- IU-23: API documentation skill — markdown — ready to write
- IU-24: Developer guide skill — markdown — ready to write
- IU-25: Docstring skill — markdown — ready to write

**Recommended generation order**: IU-01 → IU-04, IU-08 → IU-02, IU-03 → IU-17, IU-18 → IU-06, IU-07 → IU-09 → IU-11–IU-15 → IU-10 → IU-16

**Constraints for generators**:
- Language/runtime: Python 3.11+
- Framework: Typer (CLI), LangGraph (workflow), LiteLLM (LLM abstraction)
- Package manager: uv
- Naming conventions: snake_case for modules and functions, kebab-case for CLI commands
- Test coverage requirement: unit tests for all orchestration modules (IU-02 through IU-09); integration tests for stage nodes against LangGraph graph

**Blocking items before generation can start**:
- None
