# Technical Specification: Monkey Devs

**Version**: 1.2
**Date**: 2026-04-15
**Status**: Finalized — architecture complete
**Sources**: `docs/concepts/monkey-devs.md` v1.2 (concept document)
**Design**: `docs/design/design-monkey-devs.md` v1.2 (all open decisions resolved)

**Changelog**:
- v1.0 (2026-04-14): Initial draft, ready for architecture
- v1.1 (2026-04-14): Updated to reflect architectural decisions — IDE dependency removed, Python CLI model adopted, OpenCode references replaced with Python CLI + LangGraph model, FR-37–FR-39 added for multi-vendor model configuration, all open decisions (OD-01–OD-05) resolved, all constraints and assumptions updated
- v1.2 (2026-04-15): FR-40–FR-44 added for autonomous adversarial review loop and documentation agent; Stage 4 model corrected to `openai/o4-mini`; Stage 5 split into 5a (documentation) and 5b (delivery); WorkflowState, skills inventory, and CLI table updated

---

## 1. Problem Statement

A solo operator who needs to build software — internal tools, scripts, automation pipelines, web applications, and APIs — currently depends on a full-stack development team to deliver those projects. This creates a bottleneck: work is gated on team availability, coordination overhead, and specialization gaps that a single person cannot fill alone.

Agentic coding offers a path to independence, but existing tools are either monolithic (one agent does everything poorly) or require the user to manually orchestrate multiple AI tools, which recreates the coordination burden in a different form.

Monkey Devs solves this by providing a structured multi-agent development workflow where specialized AI agents handle each phase of the software development lifecycle under the user's direction. The user retains control at defined decision points without doing the manual coding work themselves. The system operates as a standalone Python CLI — no IDE, no cloud infrastructure, no server required.

---

## 2. Goals

- **G-01**: Enable a solo operator to initiate, guide, and receive working software without writing code manually.
- **G-02**: Provide a five-stage structured workflow with a human approval gate at each stage boundary.
- **G-03**: Support both internal tools/scripts and full applications (web apps, APIs, mobile) within the same workflow.
- **G-04**: Allow the system to resume a workflow after a session crash or restart without losing progress.
- **G-05**: Remain IDE-agnostic — the system operates as a standalone CLI with no IDE dependency.
- **G-06**: Minimize LLM token cost by preferring markdown skill files over agentic tools wherever quality is equivalent.
- **G-07**: Produce working, locally runnable code as the primary deliverable.

---

## 3. Non-Goals

- **Not in scope**: Automated deployment to any cloud provider, VPS, or hosting environment — delivery ends at a working local repository.
- **Not in scope**: Multi-user support, role-based access control, or team collaboration features.
- **Not in scope**: A fixed or opinionated technology stack — agents select the appropriate stack per project.
- **Not in scope**: Real-time agent monitoring or observability dashboards.
- **Not in scope**: Automated publishing, packaging, or distribution of produced software.
- **Not in scope**: IDE plugin or extension development.

---

## 4. Users and Stakeholders

| Role | Description | Primary Interaction |
|------|-------------|---------------------|
| Solo Operator | The single user of the system. Initiates workflows, approves or redirects at each stage gate, and receives the final code output. | CLI commands, stage gate approval, fix/redirect instructions |

No additional roles, permissions model, or multi-user support is in scope.

---

## 5. Functional Requirements

### 5.1 Orchestrator — Python CLI Control Loop

- **FR-01**: The system MUST provide a principal orchestrator implemented as a Python CLI (`monkey-devs`) using Typer, driving a LangGraph workflow graph.
- **FR-02**: The orchestrator MUST act as a deterministic resource manager: at each stage, it MUST read `.opencode/registry.yaml` and select skills (by filtering `stages` field) and tools for that stage. No LLM is invoked for orchestration.
- **FR-03**: The orchestrator MUST NOT invoke any LLM and MUST NOT read, write, or generate code at any point. All LLM calls and code-level operations MUST be delegated to stage nodes.
- **FR-04**: The orchestrator MUST maintain the LangGraph workflow state via the SQLite checkpointer, tracking the current stage, completion status, and human approval decisions.
- **FR-05**: The orchestrator MUST pause workflow execution at each stage boundary via LangGraph `interrupt()` and present a stage gate to the user before activating the next stage node.
- **FR-06**: The orchestrator MUST support workflow resumption: if the process terminates or crashes, `monkey-devs resume` MUST restore execution from the last SQLite checkpoint.
- **FR-07**: The orchestrator MUST communicate its resource allocation decisions to the user at each stage gate. Summary view is default; `monkey-devs details` expands the full allocation log.

### 5.2 Stage Nodes — LangGraph Async Functions

- **FR-08**: The system MUST provide the following async Python node functions in the LangGraph graph:
  - `concept_spec_node` — Concept & Spec (model: `google/gemini-2.5-pro`)
  - `architecture_node` — Architecture & Task Management (model: `google/gemini-2.5-pro`)
  - `implementation_node` — Implementation & Code Generation (model: `anthropic/claude-opus-4-6`; invoked once per task via `Send()`)
  - `code_fixing_node` — Code Fixing & Test Categorization (model: `openai/o4-mini`)
  - `documentation_node` — Documentation (Stage 5a; model: `google/gemini-2.5-pro`)
  - `delivery_node` — Delivery (Stage 5b; model: `anthropic/claude-sonnet-4-6`)
  - `review_node` — Adversarial Review (shared; model: `anthropic/claude-opus-4-6`; runs after every primary stage node)
  - `fix_node` — Artifact Fix (shared; model: `google/gemini-2.5-pro`; runs after `review_node` when verdict is not `pass`)
- **FR-09**: Stage nodes MUST be invoked automatically by the orchestrator at the appropriate stage via LangGraph graph edges.
- **FR-10**: Stage nodes MUST receive a structured handoff message as their system prompt. The handoff message MUST follow the four-block schema: `CONTEXT` (project name, stage, task_id, prior_output) / `SKILLS` (full injected skill file content, named and delimited) / `TOOLS` (tool name + scoped instruction) / `INSTRUCTIONS` (stage directive and rejection reason if correction branch).
- **FR-11**: Stage nodes MUST NOT self-configure — they MUST rely entirely on the handoff message composed by the Python CLI for their skill and tool context.
- **FR-12**: Each stage node MUST have tool access scoped to its stage via `get_stage_tools(stage)` and a Python bash allowlist validator. Sub-agents MUST NOT access tools not explicitly allocated.

### 5.3 Workflow Stages

- **FR-13**: Stage 1 — Concept & Spec: The node MUST conduct a conversational intake with the user using the `conversational-intake` skill (one focused question at a time). It MUST produce two artifacts: `docs/concept.md` and `docs/spec.md` with acceptance criteria.
- **FR-14**: Stage 1 — Concept & Spec: The node MUST propose 2–3 candidate technology stacks with rationale using the `stack-evaluation` skill, ranked by suitability. It MUST NOT make a final stack decision.
- **FR-15**: Stage 2 — Architecture: The node MUST make a final, binding technology stack decision using the `stack-decision` skill, based on Stage 1 artifacts.
- **FR-16**: Stage 2 — Architecture: The node MUST produce `docs/architecture.md` and `.opencode/tasks.yaml`. Tasks in `tasks.yaml` MUST follow the schema: `id`, `title`, `description`, `status` (pending/in-progress/done), `stage`, `depends_on`, `failure_classification`.
- **FR-17**: Stage 3 — Implementation: The node MUST write both production code and tests using the `tdd-implementation` and `code-generation` skills. Tests MUST be written as part of this stage, not deferred. The node is invoked once per task unit by the orchestrator's task-dispatch logic.
- **FR-18**: Stage 4 — Code Fixing: The node MUST run all tests and attempt to fix failing tests automatically. Any failures it cannot resolve MUST be explicitly classified as either `code-issue` or `test-issue` in `tasks.yaml` before the stage gate. It MUST NOT silently drop, skip, or weaken tests.
- **FR-19**: Stage 4 — Code Fixing: The classification of unresolved failures MUST be presented to the user at the stage gate with a rationale for each classification.
- **FR-20**: Stage 5a — Documentation: The `documentation_node` MUST produce `docs/api-reference.md` (endpoint/schema reference), `docs/developer-guide.md` (setup, test, and module structure guide), and inline docstrings written into source files. It MUST have `filesystem_read` access to the full project and `filesystem_write` access to `docs/` and all source files.
- **FR-20b**: Stage 5b — Delivery: The `delivery_node` MUST produce `README.md` and `docs/delivery.md`. It MUST surface a delivery summary listing what was built and where relevant files are located. It runs after `documentation_node` and shares the Stage 5 gate.

### 5.4 Human Approval Gates

- **FR-21**: The system MUST present a stage gate to the user after each stage completes. The gate MUST give the user three options: approve and continue, fix/update the output and continue, or reject and redirect (returns to the current stage with new instructions via a correction branch).
- **FR-22**: No stage MAY be skipped. All five stage gates require explicit user action before the next stage begins.
- **FR-23**: When the user fixes or updates a stage output, the workflow MUST continue from that stage with the updated output — it MUST NOT restart from Stage 1.

### 5.5 Resource Registry

- **FR-24**: The system MUST maintain a resource registry at `.opencode/registry.yaml` listing all available skills and tools with their metadata.
- **FR-25**: The resource registry MUST be readable and updatable independently of the workflow — new skills and tools MAY be added at any time without modifying Python source code.
- **FR-26**: The orchestrator MUST read the resource registry at workflow start to build its allocation model for the current workflow.

### 5.6 Skills System

- **FR-27**: Skills MUST be defined as markdown prompt files stored in `.opencode/skills/`.
- **FR-28**: Skills MUST have metadata in `registry.yaml`: `name`, `description`, `stages` (list of applicable stage numbers), and `path`.
- **FR-29**: Skills MUST be injected into stage nodes via the orchestrator's handoff message SKILLS block — full file content concatenated as named, delimited sections. Skills MUST NOT be hardcoded into stage node Python functions.
- **FR-30**: The system MUST prefer skills over tools in all cases where a skill can cover the need. Binary allocation rule: skill if the operation produces/transforms/structures text or decisions; tool only if the operation requires executing code, reading/writing files, or external system interaction.

### 5.7 Tools

- **FR-31**: Tools are Python-callable capabilities (file I/O, bash execution, optional MCP servers) registered in `registry.yaml`.
- **FR-32**: Tools MUST have metadata in `registry.yaml`: `name`, `description`, `type` (builtin/mcp), `stages`, and `connection`.
- **FR-33**: Tool access MUST be granted to stage nodes via `get_stage_tools(stage)`. A Python bash allowlist validator MUST block any shell command not on the permitted list before execution. Stage nodes MUST NOT access tools not explicitly allocated.

### 5.8 Technology Stack Selection

- **FR-34**: The Concept & Spec node MUST propose a ranked shortlist of 2–3 technology stack candidates with rationale at the end of Stage 1.
- **FR-35**: The Architecture node MUST make the final, binding stack decision at Stage 2. This decision MUST be recorded in `docs/architecture.md` and communicated to the user at the Stage 2 gate.
- **FR-36**: No fixed or default stack MAY be imposed by the system. Stack selection is always per-project.

### 5.9 Autonomous Adversarial Review Loop

- **FR-40**: After every primary stage node completes and before the stage gate is presented, the system MUST automatically run a `review_node` that critiques the stage artifact using the `adversarial-review` skill and produces a structured fix brief at `.opencode/review/stage-N-fix-brief.md`. The fix brief MUST include a verdict (`pass | warn | block`) and a ranked issue list (critical → high → medium), each issue with a concrete fix instruction.
- **FR-41**: When the review verdict is `pass`, the system MUST skip the `fix_node` entirely and proceed directly to the stage gate. No fix brief is written.
- **FR-42**: When the review verdict is `warn` or `block`, the system MUST run `fix_node` which rewrites the stage artifact in place using the fix brief as its sole instruction set. The gate MUST display the review verdict and a fix brief summary alongside the standard approval options.
- **FR-43**: The review→fix loop MUST be bypassable via `config.review.enabled: false`. When disabled, `review_node` and `fix_node` are skipped for all stages.

### 5.10 Documentation Agent

- **FR-44**: Stage 5 MUST execute a `documentation_node` (5a) before the `delivery_node` (5b). The documentation node MUST produce `docs/api-reference.md`, `docs/developer-guide.md`, and inline docstrings written into source files. Both sub-nodes are covered by the single Stage 5 gate. The review→fix pair evaluates the combined Stage 5 output before the gate.

### 5.11 Multi-Vendor Model Configuration

- **FR-37**: Each stage node MUST have an independently configurable LLM model. Models MAY be from different vendors. Configuration is stored in `.opencode/config.yaml` using LiteLLM model string format (`provider/model-id`).
- **FR-38**: Model configuration MUST be defined before a workflow starts and MAY only be updated before starting or after a workflow completes. `monkey-devs config set-model` MUST be blocked with a clear error message during an active workflow.
- **FR-39**: The CLI MUST provide commands to view (`monkey-devs config models`), update (`monkey-devs config set-model <stage> <model>`), and validate (`monkey-devs config validate`) model configuration. Validate MUST check for API key presence, model reachability, and accidental key literals in config files.

**Default model assignments:**

| Stage | Default Model | Rationale |
|-------|--------------|-----------|
| Concept & Spec | `google/gemini-2.5-pro` | Large context window for long intake conversations; strong reasoning for requirements |
| Architecture | `google/gemini-2.5-pro` | Handles full project context for system design |
| Implementation | `anthropic/claude-opus-4-6` | Highest code generation quality for production code + tests |
| Code Fixing | `openai/o4-mini` | Confirmed OpenAI model; strong code reasoning at lower cost than GPT-4o |
| Documentation (5a) | `google/gemini-2.5-pro` | Large context window for full-codebase reference doc generation; reuses fixer model |
| Delivery (5b) | `anthropic/claude-sonnet-4-6` | Fast and precise for README and delivery summary |
| Reviewer (all stages) | `anthropic/claude-opus-4-6` | Strong critical reasoning for adversarial artifact critique |
| Fixer (all stages) | `google/gemini-2.5-pro` | Large context window for full-artifact rewrites |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Resumability | The workflow MUST be resumable after a process crash or session end. LangGraph SQLite checkpointer at `.opencode/workflow-state.db` MUST persist state durably between sessions. |
| NFR-02 | Portability | The system MUST NOT be locked to any IDE or external service. The `monkey-devs` Python CLI and LangGraph SQLite state are the only runtime dependencies. Runs on macOS, Linux, and Windows. |
| NFR-03 | Cost Efficiency | The system MUST prefer markdown skill files over tools. Binary rule: skill for text/decision operations; tool only for execution operations. Enforced deterministically by Python CLI via `stages` filter on `registry.yaml`. |
| NFR-04 | Correctness | All test failures at Stage 4 MUST be classified (`code-issue` or `test-issue`) before Stage 5 begins. The stage gate MUST block advancement if any unclassified failures remain in `tasks.yaml`. |
| NFR-05 | Transparency | The stage gate MUST display sub-agent name, skills used, and tools used at every gate. Full allocation detail available via `monkey-devs details` (reads JSONL run log). |
| NFR-06 | Extensibility | New skills and tools MUST be addable by updating `registry.yaml` only — no Python source changes required. |

---

## 7. System Context

Monkey Devs is a standalone Python CLI application. It does not require an IDE, a running server, or any cloud infrastructure. The user installs it locally and interacts with it entirely through the terminal.

**Inside the system boundary:**
- `monkey-devs` Python CLI package (`monkey_devs/`)
- LangGraph workflow graph (five primary stage nodes + documentation sub-node + two shared quality nodes + five correction branches + interrupt points)
- Python CLI orchestrator (deterministic control loop — no LLM)
- Resource registry (`.opencode/registry.yaml`)
- Model and provider config (`.opencode/config.yaml`)
- Skill files (`.opencode/skills/*.md`) — 19 files
- LangGraph SQLite state (`.opencode/workflow-state.db`)
- Task file (`.opencode/tasks.yaml`)
- Review fix briefs (`.opencode/review/stage-N-fix-brief.md`) — gitignored
- Run logs (`.opencode/logs/run-<timestamp>.jsonl`)

**Outside the system boundary (dependencies):**
- **LangGraph** + `langgraph-checkpoint-sqlite`: workflow state machine and durable persistence
- **LiteLLM**: multi-vendor LLM abstraction layer
- **LLM providers**: Anthropic (`ANTHROPIC_API_KEY`), OpenAI (`OPENAI_API_KEY`), Google (`GEMINI_API_KEY`) — keys stored in environment only
- **User's local filesystem**: destination for all project output

---

## 8. Key Concepts and Data Model

### 8.1 Glossary

| Term | Definition |
|------|------------|
| Orchestrator | The Python CLI control loop. Deterministic — no LLM. Reads registry, filters skills/tools by stage, composes handoff messages, dispatches tasks, renders stage gates, drives LangGraph. |
| Stage Node | An async Python function in the LangGraph graph. Receives handoff message as system prompt. Invokes LiteLLM. Streams output to terminal. Writes artifacts to filesystem. |
| Skill | A markdown prompt file in `.opencode/skills/`. Injected into stage node system prompts at handoff. Zero execution cost. |
| Tool | A Python-callable capability (file I/O, bash) granted to a stage node via `get_stage_tools()`. Bash access is gated by an allowlist validator. |
| Resource Registry | `.opencode/registry.yaml` — YAML manifest of all skills and tools with metadata. Read by Python CLI at workflow start. |
| Stage Gate | A CLI pause point after each stage. LangGraph `interrupt()` halts execution. CLI renders summary + options. Resumes on `monkey-devs approve` or `monkey-devs reject`. |
| Handoff Message | A four-block markdown message (CONTEXT / SKILLS / TOOLS / INSTRUCTIONS) composed by the Python CLI and used as the LLM system prompt for a stage node invocation. |
| Workflow | The five-stage LangGraph pipeline instance for a specific project. Persisted in SQLite. Resumable after interruption. |
| Correction Branch | A paired LangGraph node for each stage. Activated on rejection — carries rejection reason and prior output, re-invokes the same stage node with updated context. Capped at `max_corrections_per_stage`. |
| Task | A unit of implementation work in `.opencode/tasks.yaml`. Created by Stage 2. Dispatched to individual Implementation nodes via LangGraph `Send()` after topological sort of `depends_on` relationships. |
| Review Node | A shared async LangGraph node that runs after every primary stage node. Critiques the stage artifact using the `adversarial-review` skill. Produces a fix brief with a `pass | warn | block` verdict. |
| Fix Node | A shared async LangGraph node that runs after `review_node` when verdict is not `pass`. Rewrites the stage artifact in place using the fix brief as its instruction set. Skipped when verdict is `pass`. |
| Fix Brief | A structured markdown document at `.opencode/review/stage-N-fix-brief.md`. Contains a verdict and a ranked issue list with concrete fix instructions per issue. |

### 8.2 Core Entities

**WorkflowState (LangGraph TypedDict)**

```python
class WorkflowState(TypedDict):
    project_name: str
    project_path: str
    current_stage: int                       # 1–5
    workflow_status: str                     # active | completed | interrupted
    stage_statuses: dict[int, str]           # pending | active | complete | approved | rejected
    stage_outputs: dict[int, str]            # absolute path to artifact per stage
    stage_models: dict[int, str]             # model used per stage; Stage 5 uses "5a" and "5b" sub-keys
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
    thread_id: str                           # LangGraph thread ID for interrupt/resume
    correction_counts: dict[int, int]        # correction cycles consumed per stage
    review_verdicts: dict[int, str]          # pass | warn | block per stage
    review_brief_paths: dict[int, str]       # absolute path to fix brief per stage
    review_skipped: dict[int, bool]          # True when review verdict was pass
```

**Task (tasks.yaml entry)**

```yaml
- id: T-01
  title: "Implement user authentication"
  description: "..."
  status: pending             # pending | in-progress | done
  stage: 3
  depends_on: []
  failure_classification: null  # code-issue | test-issue (Stage 4 only)
```

**Skill (registry.yaml entry)**

```yaml
- name: conversational-intake
  description: "Forge-style one-question-at-a-time intake pattern"
  stages: [1]
  path: .opencode/skills/conversational-intake.md
```

**Tool (registry.yaml entry)**

```yaml
- name: bash
  description: "Shell command execution (allowlisted commands only)"
  type: builtin
  stages: [3, 4]
  connection: builtin
```

---

## 9. Interface Contracts

### CLI Interface

| Command | Description |
|---------|-------------|
| `monkey-devs init` | Initialize new project, create `.opencode/` structure, add `.gitignore` entries, start Stage 1 |
| `monkey-devs run` | Run the current stage (streams LLM output to terminal) |
| `monkey-devs run --verbose` | Run with skill injection + state transition events shown |
| `monkey-devs run --debug` | Run with full real-time event log |
| `monkey-devs status` | Show workflow state, current stage, task list |
| `monkey-devs approve` | Approve current stage gate, advance to next stage |
| `monkey-devs reject --reason "..."` | Reject current stage, route to correction branch |
| `monkey-devs resume [--project-path PATH]` | Resume an interrupted workflow from last SQLite checkpoint. Prints a helpful error if no `.opencode/` directory is found and `--project-path` is not provided. |
| `monkey-devs details` | Show full allocation log for current stage (reads JSONL run log) |
| `monkey-devs tasks` | List tasks and status (Stage 3+) |
| `monkey-devs registry` | Show resource registry contents |
| `monkey-devs skills list` | List skills with stage assignments |
| `monkey-devs config models` | Show current model assignments |
| `monkey-devs config set-model <stage> <model>` | Update model for a stage (blocked during active workflow) |
| `monkey-devs config validate` | Check API keys, model reachability, no key literals in config |

### Handoff Message Schema

```
## HANDOFF: [Stage Name]

### CONTEXT
project: [project name]
stage: [1-5]
task_id: [T-XX | "all"]
prior_output: [artifact path | "none"]

### SKILLS
---
## Skill: [name]
[full skill file content]

### TOOLS
- [tool-name]: [scoped instruction for this stage]

### INSTRUCTIONS
[Stage directive. Rejection reason wrapped in <user-rejection-reason> tags if correction branch.]
```

---

## 10. Constraints and Assumptions

**Constraints:**

- **C-01**: All stage logic MUST be implemented as LangGraph async node functions in the Python `monkey_devs` package.
- **C-02**: The orchestrator (Python CLI control loop) MUST NOT invoke any LLM under any circumstances.
- **C-03**: Skills MUST be markdown files. They MUST NOT be compiled code, scripts, or executables.
- **C-04**: LangGraph with `langgraph-checkpoint-sqlite` is the required workflow state manager. No alternative state persistence is in scope.
- **C-05**: Deployment automation is out of scope. The system delivers a working local repository only.
- **C-06**: The system targets a single user. No multi-user, authentication, or authorization layer is in scope.
- **C-07**: All five stage gates are mandatory. No stage may be skipped regardless of project size or complexity.
- **C-08**: API keys MUST be stored in environment variables only. `config.yaml` MUST store env var names, never key values. `monkey-devs config validate` MUST block workflow start if key literals are detected.

**Assumptions — all resolved:**

- **A-01**: ~~OpenCode IDE compatibility~~ — **Eliminated**. System is a standalone Python CLI. No IDE compatibility required or assumed.
- **A-02**: LangGraph SQLite checkpointer durability across process crashes. **Validated** — SQLite file survives process termination; LangGraph `interrupt()` + resume is a first-class supported pattern.
- **A-03**: Four-block handoff message schema is sufficient for stage nodes to initialize correctly. **Resolved** — schema defined (CONTEXT / SKILLS / TOOLS / INSTRUCTIONS). To be validated empirically during prototype.

---

## 11. Open Decisions — ALL RESOLVED

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| OD-01 | Resource registry format | YAML at `.opencode/registry.yaml` | Human-readable, comment-friendly, structured for deterministic filtering. See ADR-001. |
| OD-02 | Stage gate disclosure level | Summary + drill-down via `monkey-devs details` | Routine approvals stay clean; full log available on demand. See ADR-002. |
| OD-03 | LangGraph rejection handling | Correction branch per stage | First-class LangGraph node; preserves rejection reason and prior output. See ADR-003. |
| OD-04 | Sub-agent permission model | Python-enforced via `get_stage_tools()` + bash allowlist validator | OpenCode eliminated; permissions are code, not IDE config. |
| OD-05 | Task tracking location | Local YAML at `.opencode/tasks.yaml` | No external dependencies; readable by Python CLI; structured for task dispatch. |

---

## 12. Out of Scope

- Automated deployment to any environment (cloud, VPS, container registry)
- Multi-user support, team workflows, or shared project state
- A fixed or default technology stack
- Real-time agent monitoring, logging dashboards, or observability tooling beyond JSONL run logs
- Automated publishing, packaging, or distribution of produced software
- IDE-specific plugin or extension development
- Any form of billing, usage metering, or cost tracking
- Web UI or graphical interface

---

## Ready for Implementation

**Spec file**: `docs/specs/spec-monkey-devs.md` v1.2 — Finalized
**Concept file**: `docs/concepts/monkey-devs.md` v1.2 — Architecture Complete
**Design file**: `docs/design/design-monkey-devs.md` v1.2 — Approved for generation

All open decisions resolved. All assumptions confirmed or eliminated. No blockers.
See `docs/design/design-monkey-devs.md` Part III for implementation units and generation order (IU-01 through IU-25).
