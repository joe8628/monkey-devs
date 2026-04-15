# Concept: Monkey Devs

**Status**: ARCHITECTURE COMPLETE
**Complexity**: COMPLEX
**Created**: 2026-04-14
**Updated**: 2026-04-14
**Version**: 1.1
**Changelog**:
- v1.0 (2026-04-14): Initial concept, ready for architecture
- v1.1 (2026-04-14): Updated to reflect architectural decisions — IDE dependency removed, Python CLI model adopted, OpenCode references replaced, all open questions resolved

---

## Summary

A solo-operator agentic development system that replaces a full-stack development team. The user describes what they want to build via a command-line interface, and a LangGraph-orchestrated pipeline of specialized AI agents — each equipped with domain-specific skills — handles decomposition, design, implementation, and delivery. The user participates at five defined checkpoints: reviewing and approving each stage before execution continues, or intervening to fix/redirect the plan. Target output is working software, covering both internal tools/scripts and full applications.

The system runs as a standalone Python CLI (`monkey-devs`) with no IDE dependency. A deterministic Python control loop handles orchestration (resource allocation, skill injection, task dispatch) — no LLM tokens are consumed for orchestration. LLM calls happen only inside the five stage nodes, each powered by a purpose-selected model via LiteLLM.

The five workflow stages are:
1. **Concept & Spec** — Gemini 2.5 Pro conducts conversational intake and produces concept + requirements spec
2. **Architecture & Task Management** — Gemini 2.5 Pro designs the system and produces a task breakdown in `.opencode/tasks.yaml`
3. **Implementation & Code Generation** — Claude Opus 4.6 writes production code and tests, one task unit at a time
4. **Code Fixing & Test Categorization** — Codex Mini runs tests, fixes failures, classifies unresolved failures as `code-issue` or `test-issue`
5. **Delivery** — Claude Sonnet 4.6 finalizes the repository and produces a delivery summary

---

## Accepted

- **Orchestrator model**: Python CLI control loop — deterministic, no LLM. Reads `.opencode/registry.yaml`, selects skills and tools per stage by filtering on the `stages` field, composes handoff messages, dispatches tasks, renders stage gates. Zero LLM tokens consumed for orchestration.
- **No IDE dependency**: System is a standalone Python CLI. No OpenCode, no Cursor, no Claude Code IDE integration required. Runs in any terminal.
- **Skill injection**: Python CLI composes handoff messages that inject full skill file content into the stage node's system prompt. Sub-agents are lean LLM calls — the orchestrator holds all allocation intelligence.
- **Orchestrator constraint**: Orchestrator NEVER invokes an LLM and NEVER reads or creates code. All LLM calls and code-level work happen inside stage nodes only.
- **Skills vs Tools**: Skills = markdown prompt files (injected into system prompts, zero cost); Tools = Python-callable capabilities (file I/O, bash execution), granted per stage via `get_stage_tools()`. Binary allocation rule: skill if the operation produces/transforms/structures text or decisions; tool only if the operation requires executing code, reading/writing files, or external system interaction.
- **Resource registry**: `.opencode/registry.yaml` — YAML manifest listing all skills and tools with `name`, `description`, `stages`, and type-specific fields. Read by the Python CLI at workflow start.
- **Stage nodes**: Five async Python functions in the LangGraph graph, each powered by a specific LLM model via LiteLLM. Receive handoff messages as system prompts. Stream output to terminal. Write artifacts to filesystem.
- **Multi-vendor models**: Each stage node uses a purpose-selected model. Configurable in `.opencode/config.yaml`. Locked during active workflows; updatable before start or after completion.
- **Task dispatch**: After Stage 2 approval, Python CLI reads `.opencode/tasks.yaml` and spawns one Implementation node per task unit. Enables parallel or sequential task-level execution.
- **Correction branches**: Each stage has a paired LangGraph correction branch node. Rejection writes reason + prior output to state, routes to the correction branch, re-invokes the stage node with updated context.
- **Human-in-the-loop**: LangGraph `interrupt()` pauses execution at each stage gate. CLI renders a compact summary (sub-agent name, skills/tools used, unresolved issues, three options). `monkey-devs details` expands full allocation log from JSONL run log.
- **Workflow persistence**: LangGraph SQLite checkpointer at `.opencode/workflow-state.db`. Survives process crashes. `monkey-devs resume` restores from last checkpoint.
- **Scope**: Both internal tools/scripts and full applications (web apps, APIs, mobile).
- **Test categorization**: All unresolved test failures classified as `code-issue` or `test-issue` before Stage 5. No silent test weakening.
- **Stack selection**: No fixed stack. Stage 1 proposes 2–3 ranked candidates; Stage 2 makes the final binding decision.
- **Delivery**: Working code in a local repo. Deployment is out of scope.

---

## Blocked

*(none)*

---

## Discarded

- **OpenCode IDE runtime**: Eliminated. System is a standalone Python CLI — no IDE dependency of any kind.
- **LLM-based orchestrator agent**: Replaced by a deterministic Python control loop. Skill selection is a registry lookup, not LLM reasoning.
- **OpenCode `permission` field**: Replaced by Python-enforced tool scoping via `get_stage_tools()` per stage node.
- **MCP servers as default tools**: Replaced by Python-native capabilities (file I/O, bash). MCP remains an optional extension via registry.
- **Fixed tech stack**: Ruled out — agents choose per project.
- **Fully autonomous execution**: Ruled out — five human gates required.
- **Fine-grained approval at every agent action**: Ruled out — stage-level gates only.
- **Dynamically instantiated sub-agents**: Replaced by fixed LangGraph stage node functions.

---

## Sub-concepts

### 1. Orchestration Layer
**Status**: RESOLVED

- **Python CLI control loop** drives the LangGraph graph — deterministic, no LLM, zero orchestration cost
- LangGraph manages state transitions, human `interrupt()` pause points, and correction branch routing
- SQLite checkpointer persists state at `.opencode/workflow-state.db` — survives crashes, resumable via `monkey-devs resume`
- Skill selection: Python filters `registry.yaml` by `stages: [N]` for current stage N — no reasoning required
- Task dispatch: Python reads `.opencode/tasks.yaml`, filters `status: pending`, spawns one Implementation node per task

### 2. Agent Architecture
**Status**: RESOLVED

- **Python CLI as orchestrator**: no LLM, reads registry, composes handoffs, dispatches tasks, renders gates
- **Five LangGraph stage nodes** (async Python functions): each invokes LiteLLM with a handoff message as system prompt
  - `concept_spec_node` — `google/gemini-2.5-pro`
  - `architecture_node` — `google/gemini-2.5-pro`
  - `implementation_node` — `anthropic/claude-opus-4-6` (one per task unit)
  - `code_fixing_node` — `openai/codex-mini`
  - `delivery_node` — `anthropic/claude-sonnet-4-6`
- **Five correction branch nodes** — paired with each stage node; activated on user rejection
- Tool permissions enforced by Python code (`get_stage_tools()` + bash allowlist validator), not IDE config

### 3. Skills & Tools System
**Status**: RESOLVED

- **15 skill files** in `.opencode/skills/` — markdown prompt files injected into stage node system prompts
- **Orchestrator skills** (stage 0): `resource-allocation`, `stage-gate`, `handoff-composer`, `task-dispatch`
- **Stage 1 skills**: `conversational-intake`, `requirements-writing`, `stack-evaluation`
- **Stage 2 skills**: `system-design`, `task-decomposition`, `adr-writing`, `stack-decision`
- **Stage 3 skills**: `tdd-implementation`, `code-generation`
- **Stage 4 skills**: `test-categorization`, `systematic-debugging`
- **Stage 5 skills**: `delivery-summary`, `readme-writing`
- **Tools**: Python-native file I/O and bash (allowlisted). Optional `web-search` MCP for Stages 1–2.
- **Allocation rule**: Skill if text/decision operation; tool only if execution required (binary, enforced by Python code)

### 4. Task Intake
**Status**: RESOLVED

- Conversational intake via `conversational-intake` skill — forge-style, one question at a time
- Entry point: `monkey-devs init` starts the CLI, Stage 1 node drives the conversation
- Output: `docs/concept.md` and `docs/spec.md`

### 5. Stage Gates
**Status**: RESOLVED

- LangGraph `interrupt()` pauses after each stage node completes
- CLI renders: stage name, model used, skills/tools summary, unresolved issues, three options (approve / fix+continue / reject+redirect)
- `monkey-devs approve` → advances to next stage node
- `monkey-devs reject --reason "..."` → routes to correction branch, re-invokes current stage with rejection context
- `monkey-devs details` → full allocation log from JSONL run log (drill-down on request)
- `monkey-devs fix` path: workflow continues from current stage with updated output — no restart from Stage 1

### 6. Output & Delivery
**Status**: RESOLVED

- Delivery = working code in a local repo, ready to run
- `delivery-summary` skill produces `docs/delivery.md` listing what was built and where files live
- `readme-writing` skill produces `README.md` with setup and run instructions
- Deployment is out of scope — handled manually by the user

---

## Open Questions

All open questions resolved. See Architecture Decision Records in `docs/design/design-monkey-devs.md`.

1. ~~**OQ1 — What kind of software?**~~ — **RESOLVED.** Both internal tools/scripts and full applications.
2. ~~**OQ2 — Human-in-the-loop model?**~~ — **RESOLVED.** Checkpoint-based: approve, fix, or redirect at each of five stage gates.
3. ~~**OQ3 — What are the workflow stages?**~~ — **RESOLVED.** Five stages: Concept & Spec → Architecture → Implementation → Code Fixing → Delivery.
4. ~~**OQ4 — What languages and stacks are in scope?**~~ — **RESOLVED.** No fixed stack — agents choose per project.
5. ~~**OQ5 — How does the user describe what to build?**~~ — **RESOLVED.** Conversational intake via `monkey-devs init`, driven by `conversational-intake` skill.
6. ~~**OQ6 — What does delivery look like?**~~ — **RESOLVED.** Working code in local repo. Deployment out of scope.
7. ~~**OQ7 — How does the orchestrator surface in the environment?**~~ — **RESOLVED.** `monkey-devs` CLI — no IDE required.
8. ~~**OQ8 — Are stage executors pre-defined or dynamically instantiated?**~~ — **RESOLVED.** Fixed LangGraph async node functions, one per stage.
9. ~~**OQ9 — What is the skill loading mechanism?**~~ — **RESOLVED.** Python CLI loads skill files from `.opencode/skills/` and injects full content into handoff messages.
10. ~~**OQ10 — What is a skill structurally?**~~ — **RESOLVED.** Markdown prompt files. Tools are Python-native capabilities or optional MCP servers.
11. ~~**OQ11 — What is the resource registry format?**~~ — **RESOLVED.** YAML at `.opencode/registry.yaml` (ADR-001).
12. ~~**OQ12 — How are stage rejections handled?**~~ — **RESOLVED.** Correction branch per stage in LangGraph graph (ADR-003).
13. ~~**OQ13 — Does orchestration require an LLM?**~~ — **RESOLVED.** No — Python CLI control loop is fully deterministic (ADR-004).
14. ~~**OQ14 — How is workflow state persisted?**~~ — **RESOLVED.** SQLite checkpointer via `langgraph-checkpoint-sqlite` (ADR-005).
15. ~~**OQ15 — How are multiple LLM vendors supported?**~~ — **RESOLVED.** LiteLLM abstraction layer with per-stage model config in `.opencode/config.yaml` (ADR-006).

---

## Architecture Complete

**Concept file**: `docs/concepts/monkey-devs.md` v1.1
**Spec file**: `docs/specs/spec-monkey-devs.md` v1.1
**Design file**: `docs/design/design-monkey-devs.md` v1.0

**System in one sentence**: `monkey-devs` is a standalone Python CLI that drives a LangGraph pipeline of five LiteLLM-powered stage nodes — Gemini for intake and architecture, Opus for implementation, Codex for fixing, Sonnet for delivery — with deterministic Python orchestration, SQLite persistence, and human approval gates at every stage boundary.

**Confirmed decisions**:
- Standalone Python CLI — no IDE dependency (ADR-007)
- Deterministic Python orchestrator — no LLM for orchestration (ADR-004)
- LangGraph + SQLite for durable workflow state (ADR-005)
- LiteLLM for multi-vendor model abstraction (ADR-006)
- Correction branches per stage for rejection handling (ADR-003)
- YAML resource registry (ADR-001)
- Summary + drill-down stage gates (ADR-002)
- Per-stage model assignments: Gemini 2.5 Pro / Gemini 2.5 Pro / Claude Opus 4.6 / Codex Mini / Claude Sonnet 4.6 (ADR-008)
- 15 skill files in `.opencode/skills/`
- Task dispatch per task unit in Stage 3

**Discarded alternatives**:
- OpenCode IDE runtime — eliminated; no IDE lock-in
- LLM-based orchestrator — replaced by deterministic Python code
- MCP servers as primary tools — replaced by Python-native capabilities
- Fixed tech stack — ruled out
- Fully autonomous execution — ruled out; five human gates required
