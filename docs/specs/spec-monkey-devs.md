# Technical Specification: Monkey Devs

**Version**: 1.0-draft
**Date**: 2026-04-14
**Status**: Draft — pending review
**Sources**: `docs/concepts/monkey-devs.md` (forge concept document, READY)

---

## 1. Problem Statement

A solo operator who needs to build software — internal tools, scripts, automation pipelines, web applications, and APIs — currently depends on a full-stack development team to deliver those projects. This creates a bottleneck: work is gated on team availability, coordination overhead, and specialization gaps that a single person cannot fill alone.

Agentic coding offers a path to independence, but existing tools are either monolithic (one agent does everything poorly) or require the user to manually orchestrate multiple AI tools, which recreates the coordination burden in a different form.

Monkey Devs solves this by providing a structured multi-agent development workflow where specialized AI agents handle each phase of the software development lifecycle under the user's direction. The user retains control at defined decision points without doing the manual coding work themselves.

---

## 2. Goals

- **G-01**: Enable a solo operator to initiate, guide, and receive working software without writing code manually.
- **G-02**: Provide a five-stage structured workflow with a human approval gate at each stage boundary.
- **G-03**: Support both internal tools/scripts and full applications (web apps, APIs, mobile) within the same workflow.
- **G-04**: Allow the system to resume a workflow after an IDE session crash or restart without losing progress.
- **G-05**: Remain IDE-agnostic — the system must not be locked to a single IDE environment.
- **G-06**: Minimize LLM token cost by preferring markdown skill files over agentic tools wherever quality is equivalent.
- **G-07**: Produce working, locally runnable code as the primary deliverable.

---

## 3. Non-Goals

- **Not in scope**: Automated deployment to any cloud provider, VPS, or hosting environment — delivery ends at a working local repository.
- **Not in scope**: Multi-user support, role-based access control, or team collaboration features.
- **Not in scope**: A fixed or opinionated technology stack — agents select the appropriate stack per project.
- **Not in scope**: Real-time agent monitoring or observability dashboards.
- **Not in scope**: Automated publishing, packaging, or distribution of produced software.

---

## 4. Users and Stakeholders

| Role | Description | Primary Interaction |
|------|-------------|---------------------|
| Solo Operator | The single user of the system. Initiates workflows, approves or redirects at each stage gate, and receives the final code output. | Conversational intake, stage gate approval, fix/redirect instructions |

No additional roles, permissions model, or multi-user support is in scope.

---

## 5. Functional Requirements

### 5.1 Orchestrator — Principal Agent

- **FR-01**: The system MUST provide a principal orchestrator agent defined as an OpenCode `mode: primary` agent, switchable via the OpenCode Tab cycle alongside the built-in Build and Plan agents.
- **FR-02**: The orchestrator MUST act as a resource manager: at each stage, it MUST read the project context and the resource registry to select and allocate the appropriate sub-agent, skills, and tools for that stage.
- **FR-03**: The orchestrator MUST NOT read, write, or generate code at any point. All code-level operations MUST be delegated to sub-agents.
- **FR-04**: The orchestrator MUST maintain the LangGraph workflow state, tracking the current stage, completion status, and human approval decisions.
- **FR-05**: The orchestrator MUST pause workflow execution at each stage boundary and present a stage gate to the user before activating the next sub-agent.
- **FR-06**: The orchestrator MUST support workflow resumption: if the IDE session ends or crashes, the orchestrator MUST resume from the last completed and approved stage upon restart.
- **FR-07**: The orchestrator MUST communicate its resource allocation decisions (which sub-agent, skills, and tools were selected) to the user at each stage gate.

### 5.2 Sub-Agents — Stage Executors

- **FR-08**: The system MUST provide five pre-defined sub-agents as OpenCode `mode: subagent` agents, each defined as a `.md` file in `.opencode/agents/`:
  - `concept-spec.md` — Concept & Spec agent
  - `architecture.md` — Architecture & Task Management agent
  - `implementation.md` — Implementation & Code Generation agent
  - `code-fixing.md` — Code Fixing & Test Categorization agent
  - `delivery.md` — Delivery agent
- **FR-09**: Sub-agents MUST be invoked automatically by the orchestrator at the appropriate stage; they MAY also be invoked manually via OpenCode `@mention`.
- **FR-10**: Sub-agents MUST receive a structured handoff message from the orchestrator at session start containing: the allocated skills (as injected prompt context), the granted tools, and the relevant project context for that stage. This message does not need to be natural language.
- **FR-11**: Sub-agents MUST NOT self-configure — they MUST rely entirely on the orchestrator's handoff message for their skill and tool allocation.
- **FR-12**: Each sub-agent MUST have tool permissions scoped to its stage via the OpenCode `permission` field.

### 5.3 Workflow Stages

- **FR-13**: Stage 1 — Concept & Spec: The Concept & Spec agent MUST conduct a conversational intake with the user, modeled on the forge skill pattern (focused questions, one at a time, building a concept document iteratively). It MUST produce two artifacts: a concept summary and a requirements spec with acceptance criteria.
- **FR-14**: Stage 1 — Concept & Spec: The agent MUST propose 2–3 candidate technology stacks with rationale, ranked by suitability. It MUST NOT make a final stack decision.
- **FR-15**: Stage 2 — Architecture & Task Management: The Architecture agent MUST make a final, binding technology stack decision based on the concept document and stack candidates from Stage 1.
- **FR-16**: Stage 2 — Architecture & Task Management: The Architecture agent MUST produce a system design and a breakdown of implementation tasks. Tasks MUST be tracked as a structured artifact (e.g. a task list file in the project repository).
- **FR-17**: Stage 3 — Implementation & Code Generation: The Implementation agent MUST write both production code and tests. Tests MUST be written as part of this stage, not deferred.
- **FR-18**: Stage 4 — Code Fixing & Test Categorization: The Code Fixing agent MUST run all tests and attempt to fix failing tests automatically. Any failures it cannot resolve MUST be explicitly classified as either `code-issue` or `test-issue` before the stage gate. It MUST NOT silently drop, skip, or weaken tests.
- **FR-19**: Stage 4 — Code Fixing & Test Categorization: The classification of unresolved failures MUST be presented to the user at the stage gate with a rationale for each classification.
- **FR-20**: Stage 5 — Delivery: The Delivery agent MUST produce a working, locally runnable code repository. It MUST surface a delivery summary to the user listing what was built and where relevant files are located.

### 5.4 Human Approval Gates

- **FR-21**: The system MUST present a stage gate to the user after each stage completes. The gate MUST give the user three options: approve and continue, fix/update the output and continue, or reject and redirect (returns to the current stage with new instructions).
- **FR-22**: No stage MAY be skipped. All five stage gates require explicit user action before the next stage begins.
- **FR-23**: When the user fixes or updates a stage output, the workflow MUST continue from that stage with the updated output — it MUST NOT restart from Stage 1.

### 5.5 Resource Registry

- **FR-24**: The system MUST maintain a resource registry as a manifest/index file (e.g. `.opencode/registry.md` or `.opencode/registry.json`) that lists all available skills and tools with their metadata.
- **FR-25**: The resource registry MUST be readable and updatable independently of the workflow — new skills and tools MAY be added at any time without modifying sub-agent `.md` files.
- **FR-26**: The orchestrator MUST read the resource registry at session start to build its allocation model for the current workflow.

### 5.6 Skills System

- **FR-27**: Skills MUST be defined as markdown prompt files stored in a known location (e.g. `.opencode/skills/`).
- **FR-28**: Skills MUST have metadata accessible to the orchestrator: name, description, and the stage(s) they apply to.
- **FR-29**: Skills MUST be injected into sub-agents via the orchestrator's structured handoff message — they MUST NOT be hardcoded into sub-agent `.md` files.
- **FR-30**: The system SHOULD prefer skills over tools in all cases where a skill can cover the need at equivalent quality. Tools MUST only be allocated when a skill cannot fulfill the requirement.

### 5.7 Tools

- **FR-31**: Tools are agentic tools (MCP servers and other agentic tool formats) registered in the resource registry.
- **FR-32**: Tools MUST have metadata accessible to the orchestrator: name, description, type, and the stage(s) they apply to.
- **FR-33**: Tool access MUST be granted to sub-agents via the OpenCode `permission` field and the orchestrator's handoff message. Sub-agents MUST NOT access tools not explicitly allocated to them.

### 5.8 Technology Stack Selection

- **FR-34**: The Concept & Spec agent MUST propose a ranked shortlist of 2–3 technology stack candidates with rationale at the end of Stage 1. This informs but does not bind the Architecture stage.
- **FR-35**: The Architecture agent MUST make the final, binding stack decision at Stage 2. This decision MUST be recorded in the project's architecture artifact and communicated to the user at the Stage 2 gate.
- **FR-36**: No fixed or default stack MAY be imposed by the system. Stack selection is always per-project.

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Resumability | The workflow MUST be resumable after an IDE session crash or restart. LangGraph state MUST be persisted durably between sessions. |
| NFR-02 | IDE Portability | The system MUST NOT be locked to a single IDE. The OpenCode agent standard and LangGraph state persistence MUST be the only runtime dependencies. |
| NFR-03 | Cost Efficiency | The system SHOULD prefer markdown skill files over agentic tools in all cases where quality is equivalent. No formal cost-per-run target; preference is qualitative and enforced by orchestrator allocation logic. |
| NFR-04 | Correctness | All test failures at Stage 4 MUST be classified before delivery. No unresolved test failure MAY be silently passed through to Stage 5. |
| NFR-05 | Transparency | The orchestrator MUST surface its resource allocation decisions (sub-agent, skills, tools selected) to the user at every stage gate. |
| NFR-06 | Extensibility | New skills and tools MUST be addable to the resource registry without modifying existing sub-agent definitions or orchestrator logic. |

---

## 7. System Context

Monkey Devs is an agentic development workflow system that sits inside an OpenCode-compatible IDE environment. It does not operate as a standalone application — it is invoked by the user switching to the Monkey Devs primary agent in the IDE's agent selector.

**Inside the system boundary:**
- The principal orchestrator agent (`monkey-devs.md`)
- Five stage sub-agents (`concept-spec.md`, `architecture.md`, `implementation.md`, `code-fixing.md`, `delivery.md`)
- The resource registry (manifest/index file)
- Skill files (markdown prompt files)
- LangGraph workflow state (persisted externally, managed by the orchestrator)

**Outside the system boundary (dependencies):**
- **OpenCode**: provides the agent runtime, Tab-switching for primary agents, `@mention` invocation for sub-agents, and the `permission` field for tool access control
- **LangGraph**: provides the workflow state machine and durable state persistence
- **MCP servers and other agentic tools**: external tools registered in the resource registry and granted to sub-agents at handoff
- **The user's IDE** (Claude Code, Cursor, or any OpenCode-compatible environment): the surface through which the user interacts with the orchestrator and approves stage gates
- **The user's local file system**: destination for all project output

---

## 8. Key Concepts and Data Model

### 8.1 Glossary

| Term | Definition |
|------|------------|
| Orchestrator | The principal agent (`mode: primary`). A pure resource manager — reads project context and registry, allocates skills and tools to sub-agents, manages workflow state. Never reads or writes code. |
| Sub-agent | A stage-scoped executor agent (`mode: subagent`). Receives skills and tools via handoff message. Performs all code-level and domain-specific work for its assigned stage. |
| Skill | A markdown prompt file containing instructional content injected into a sub-agent's context at handoff. Cost-effective; preferred over tools wherever sufficient. |
| Tool | An agentic tool (MCP server or equivalent) granted to a sub-agent at handoff for executable operations a skill cannot perform. |
| Resource Registry | A manifest/index file listing all available skills and tools with metadata. Read by the orchestrator at session start. Updatable independently of agent definitions. |
| Stage | One of five named phases in the workflow. Each stage is executed by its designated sub-agent and ends with a human approval gate. |
| Stage Gate | A pause point at the end of each stage where the user approves, fixes/updates, or rejects the stage output before the next stage begins. |
| Handoff Message | A structured (not necessarily natural language) message sent by the orchestrator to initiate a sub-agent session. Contains allocated skills as prompt context, granted tool references, and project context relevant to that stage. |
| Workflow | The five-stage pipeline instance for a specific project. Persisted by LangGraph. Resumable after session interruption. |
| Task | A unit of implementation work produced by the Architecture agent in Stage 2. Tracked as a structured artifact in the project repository. |

### 8.2 Core Entities

**Project**
- Purpose: Represents a unit of work initiated by the user.
- Key attributes: name, description, current stack (set at Stage 2), status (active / delivered)
- Relationships: has one Workflow; produces one repository as output

**Workflow**
- Purpose: The five-stage pipeline instance for a Project.
- Key attributes: current stage, stage statuses (pending / active / approved / rejected), LangGraph state reference
- Relationships: belongs to one Project; contains five Stages

**Stage**
- Purpose: One step in the Workflow, executed by a designated sub-agent.
- Key attributes: name, status (pending / active / approved / rejected), output artifact reference
- Relationships: belongs to one Workflow; executed by one sub-agent; may be retried on rejection

**Skill**
- Purpose: An instructional markdown prompt file injected into a sub-agent's context at handoff.
- Key attributes: name, description, applicable stages, file path
- Relationships: registered in the Resource Registry; allocated by the Orchestrator; injected into Sub-agents

**Tool**
- Purpose: An agentic tool (MCP server or other agentic tool format) granted to a sub-agent for executable operations.
- Key attributes: name, description, type (MCP / other), applicable stages, connection reference
- Relationships: registered in the Resource Registry; allocated by the Orchestrator; granted to Sub-agents via OpenCode `permission`

**Task**
- Purpose: A unit of implementation work produced by the Architecture agent.
- Key attributes: title, description, status (pending / in-progress / done), assigned stage
- Relationships: belongs to a Project; created in Stage 2; consumed in Stage 3 and Stage 4

---

## 9. Interface Contracts

### Exposed Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| Orchestrator Agent | OpenCode `mode: primary` | The user-facing entry point. Switched to via Tab in the IDE. Accepts natural language instructions and stage gate decisions from the user. |
| Stage Gate | Structured prompt | Presented by the orchestrator at the end of each stage. Displays: stage output summary, allocated resources used, unresolved issues (if any), and three action options: approve / fix+continue / reject+redirect. |
| Resource Registry | Manifest/index file | Read by the orchestrator at session start. Lists all available skills and tools. Writable by the user to add or update resources. |

### Consumed Interfaces

| Interface | Provider | Purpose |
|-----------|----------|---------|
| OpenCode Agent Runtime | OpenCode | Hosts and executes all agents; provides Tab-switching, `@mention` invocation, and `permission`-based tool access control |
| LangGraph State Machine | LangGraph | Manages workflow state transitions, human-in-the-loop pause/resume, and durable state persistence across IDE sessions |
| Skill Files | Local filesystem (`.opencode/skills/`) | Markdown prompt files read by the orchestrator and injected into sub-agent handoff messages |
| Agentic Tools | MCP servers + other agentic tool formats | Executable capabilities granted to sub-agents for operations skills cannot perform |
| Sub-agent Handoff | Structured message | Orchestrator-to-sub-agent protocol. Structured (not required to be natural language). Contains: injected skill prompts, granted tool references, stage-specific project context. Initiates the sub-agent session. |

---

## 10. Constraints and Assumptions

**Constraints:**

- **C-01**: All agents (orchestrator and sub-agents) MUST be defined using the OpenCode agent standard (`.md` files in `.opencode/agents/`).
- **C-02**: The orchestrator MUST NOT read, write, or generate code under any circumstances.
- **C-03**: Skills MUST be markdown files. They MUST NOT be compiled code, scripts, or executables.
- **C-04**: LangGraph is the required workflow state manager. No alternative state persistence mechanism is in scope.
- **C-05**: Deployment automation is out of scope. The system delivers a working local repository only.
- **C-06**: The system targets a single user. No multi-user, authentication, or authorization layer is in scope.
- **C-07**: All five stage gates are mandatory. No stage may be skipped regardless of project size or complexity.

**Assumptions:**

- **A-01**: The user's IDE supports the OpenCode agent standard. [Confirm: verify OpenCode compatibility for each target IDE before implementation begins]
- **A-02**: LangGraph's built-in persistence layer is sufficient for cross-session state durability. [Confirm: evaluate LangGraph checkpointing capabilities for the target deployment environment]
- **A-03**: The sub-agent handoff message format (structured, non-natural-language) is sufficient for sub-agents to initialize correctly without additional configuration. [Confirm: validate handoff message schema during prototype phase]
- **A-04**: The resource registry manifest format will be defined during architecture. [Deferred to architect — see OD-01]

---

## 11. Open Decisions

| ID | Question | Options | Owner | Required By |
|----|----------|---------|-------|-------------|
| OD-01 | What is the resource registry file format and schema? | Markdown index / JSON manifest / YAML manifest | Architect | Before implementation begins |
| OD-02 | What does the orchestrator surface at each stage gate — full skill/tool allocation detail, or a summary? | Full allocation log / summary with drill-down / minimal notice | Architect | Before Stage Gate UX is designed |
| OD-03 | When the user rejects a stage, how does LangGraph handle state? | Rewind to previous node / branch into correction sub-graph / patch and re-validate | Architect | Before LangGraph graph is designed |
| OD-04 | What are the exact OpenCode `permission` settings for each sub-agent? | Per-agent permission matrix (e.g. Implementation: full bash+edit; Concept: read-only) | Architect | Before sub-agent `.md` files are written |
| OD-05 | Does the Architecture agent's task breakdown integrate with an external task tracker, or is a local file sufficient? | Local markdown task file / GitHub Issues / Linear / other | Architect + User | Before Stage 2 sub-agent is designed |

---

## 12. Out of Scope

- Automated deployment to any environment (cloud, VPS, container registry)
- Multi-user support, team workflows, or shared project state
- A fixed or default technology stack
- Real-time agent monitoring, logging dashboards, or observability tooling
- Automated publishing, packaging, or distribution of produced software
- IDE-specific plugin or extension development (system relies on OpenCode standard, not native IDE APIs)
- Any form of billing, usage metering, or cost tracking

---

## Appendix: Spec Health Report

**Ambiguous requirements:**
- **FR-12** ("Sub-agents MUST rely entirely on the orchestrator's handoff message"): Does not specify behavior if the handoff message is malformed or incomplete — recommend adding an error handling requirement before implementation.
- **FR-30** ("equivalent quality"): The condition for preferring skills over tools is qualitative. The orchestrator must make this judgment call — consider defining a rubric in the resource registry metadata (e.g. a `preferred` flag on skill entries).

**Unconfirmed assumptions:**
- **A-01**: OpenCode compatibility of target IDEs (Claude Code, Cursor) has not been formally verified — this is the highest-risk assumption.
- **A-02**: LangGraph persistence durability across IDE session crashes needs validation in the target environment before architecture is finalized.
- **A-03**: The handoff message format is unspecified — the architect must define the schema before any sub-agent can be implemented.

**Weak sources:**
- §6 NFR-03 (cost efficiency): Derived from the philosophical preference stated in the concept doc, not from a formal requirement. Treat as a design principle, not an enforceable NFR, until the user defines a measurable threshold.

**Unresolved conflicts from source material:**
- None.

---

## Ready for Architecture

**Spec file**: `docs/specs/spec-monkey-devs.md`
**Status**: Draft
**Solid sections**: Problem Statement, Goals, Non-Goals, Users & Stakeholders, Functional Requirements (all 36), System Context, Data Model, Interface Contracts, Constraints, Out of Scope
**Needs confirmation before architecture begins**:
- OD-01: Resource registry file format and schema
- OD-03: LangGraph stage rejection handling (rewind / branch / patch)
- OD-04: Per-sub-agent OpenCode `permission` matrix
- A-01: Validate OpenCode compatibility with target IDEs
- A-02: Validate LangGraph cross-session persistence durability
- A-03: Define handoff message schema
