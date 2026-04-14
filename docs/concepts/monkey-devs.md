# Concept: Monkey Devs

**Status**: READY
**Complexity**: COMPLEX
**Created**: 2026-04-14
**Updated**: 2026-04-14

## Summary

A solo-operator agentic development system that replaces a full-stack development team. The user describes what they want to build, and a LangGraph-orchestrated pipeline of specialized AI agents — each equipped with domain-specific skills — handles decomposition, design, implementation, and delivery. The user participates at five defined checkpoints: reviewing and approving each stage before execution continues, or intervening to fix/redirect the plan. Target output is working software, covering both internal tools/scripts and full applications.

The five workflow stages are:
1. **Concept & Spec** — agents clarify and formalize requirements
2. **Architecture & Task Management** — agents design the system and break it into tracked tasks
3. **Implementation & Code Generation** — agents write code and tests
4. **Code Fixing & Test Categorization** — agents run tests, fix failures, and classify remaining failures as code-issues or test-issues for human review
5. **Delivery** — agents finalize and produce the output

---

## Accepted

- **Orchestrator role**: Dual responsibility — (1) LangGraph workflow state machine (stage progression, human gates, branching); (2) resource manager that identifies and allocates the correct sub-agent, skills, and tools for each stage based on project context
- **Skill injection**: Orchestrator injects skills into sub-agents at handoff (not hardcoded in sub-agent `.md` files); sub-agents are lean executors, orchestrator holds allocation intelligence
- **Orchestrator constraint**: Orchestrator NEVER reads or creates code — it is a pure resource allocator only; all code-level work happens inside sub-agents
- **Skills vs Tools separation**: Skills = markdown prompt files (instructional, cost-effective, cover as much of the workflow as possible); Tools = MCP tools (executable, expensive, used only when a skill cannot cover the need)
- **Resource registry**: Both skills and tools are exposed to the orchestrator; orchestrator selects and allocates the right combination per stage and project
- **Agent model**: Two-tier OpenCode standard — principal orchestrator (`mode: primary`, Tab-switchable like plan/build mode) + five pre-defined stage sub-agents (`mode: subagent`, auto-invoked or via `@mention`); all defined as `.md` files in `.opencode/agents/`
- **Sub-agent roster**: `concept-spec.md`, `architecture.md`, `implementation.md`, `code-fixing.md`, `delivery.md` — each with scoped tool permissions via OpenCode `permission` field
- **Scope**: Both internal tools/scripts (data pipelines, automation, dashboards) and full applications (web apps, APIs, mobile)
- **Human-in-the-loop**: Checkpoint-based approval — user reviews and approves each stage, can fix/update architecture or code before the workflow continues
- **Workflow stages**: Five stages — Concept & Spec → Architecture & Task Management → Implementation & Code Generation → Code Fixing & Test Categorization → Delivery
- **Test categorization**: Failed tests are explicitly classified as code-issues or test-issues before delivery; prevents silent test weakening
- **Stack selection**: Agents choose the right stack per project — Concept & Spec stage proposes candidates, Architecture stage makes the final binding decision

---

## Blocked

*(none)*

---

## Discarded

*(none)*

---

## Sub-concepts

### 1. Orchestration Layer (LangGraph)
**Status**: EXPLORING
- LangGraph manages the state machine: stage progression, human-in-the-loop pause/resume, branching on rejection
- Orchestrator is also the **resource manager**: reads project context, identifies available agents/skills/tools, allocates the right combination to each sub-agent at handoff
- Skills and tools are injected into sub-agents via the handoff message — sub-agents are lean executors, not self-configuring
- Open: what form does the orchestrator's resource registry take — how does it know what skills and tools are available to allocate?

### 2. Agent Architecture
**Status**: EXPLORING
- **Two-tier OpenCode model**: principal orchestrator (mode: `primary`) + five stage sub-agents (mode: `subagent`)
- **Principal orchestrator**: defined as a primary agent in `.opencode/agents/monkey-devs.md`; appears in the OpenCode Tab cycle alongside Build/Plan — switching to it is exactly like switching to plan mode
- **Stage sub-agents**: pre-defined `.md` files in `.opencode/agents/`; invoked automatically by the orchestrator or via `@mention`
  - `concept-spec.md` — Concept & Spec agent (read-heavy permissions)
  - `architecture.md` — Architecture & Task Management agent
  - `implementation.md` — Implementation & Code Generation agent (full bash/edit access)
  - `code-fixing.md` — Code Fixing & Test Categorization agent (bash for test running)
  - `delivery.md` — Delivery agent (read + summarize)
- Tool permissions scoped per sub-agent via OpenCode `permission` field
- Open: what "loading skills" means — how sub-agents get their domain-specific instructions/capabilities beyond the base system prompt

### 3. Skills & Tools System
**Status**: READY
- **Skills**: markdown prompt files — instructional, cost-effective; cover as much of the workflow as possible
- **Tools**: MCP tools — executable, expensive; used only when a skill cannot cover the need
- Both exposed to the orchestrator via a resource registry; orchestrator selects and allocates per stage and project
- Orchestrator never reads or creates code — allocation is its only job
- Sub-agents receive injected skills (prompt context) + granted tools (MCP access) at handoff

### 4. Task Intake
**Status**: READY
- Conversational intake modeled on the forge skill: focused questions, iterative concept document built through dialogue
- Entry point to the whole system — Concept & Spec agent drives this conversation
- Output: a structured concept document that seeds the Architecture stage

### 5. Stage Gates (Human Approval)
**Status**: EXPLORING
- Five stages confirmed: Concept & Spec → Architecture & Task Management → Implementation & Code Generation → Code Fixing & Test Categorization → Delivery
- What does the user see and interact with at each gate?
- What happens when the user rejects or modifies — does the workflow rewind, branch, or patch?

### 6. Output & Delivery
**Status**: READY
- Delivery = working code in a local repo, ready to run
- Deployment is out of scope — handled manually by the user
- Agents surface a summary of what was built and where files live at the final gate

---

## Open Questions

1. ~~**OQ1 — What kind of software?**~~ — **RESOLVED.** Both internal tools/scripts and full applications.
2. ~~**OQ2 — Human-in-the-loop model?**~~ — **RESOLVED.** Checkpoint-based: user approves each stage and can fix/update before continuing.
3. ~~**OQ3 — What are the workflow stages?**~~ — **RESOLVED.** Five stages: Concept & Spec → Architecture & Task Management → Implementation & Code Generation → Code Fixing & Test Categorization → Delivery.
4. ~~**OQ4 — What languages and stacks are in scope?**~~ — **RESOLVED.** No fixed stack — agents choose per project. Concept & Spec proposes candidates; Architecture makes the final binding decision.
5. ~~**OQ5 — How does the user describe what to build?**~~ — **RESOLVED.** Conversational intake modeled on the forge skill: agent asks focused questions, builds up a concept document iteratively through dialogue.
6. ~~**OQ6 — What does delivery look like?**~~ — **RESOLVED.** Working code in a local repo, ready to run. Deployment is out of scope for now — handled manually by the user.
7. ~~**OQ7 — How does the principal orchestrator surface in IDE environments?**~~ — **RESOLVED.** OpenCode primary agent (`mode: primary`) in `.opencode/agents/monkey-devs.md`; Tab-switchable like plan/build mode. Each IDE uses OpenCode's standard agent loading mechanism.
8. ~~**OQ8 — Are sub-agents pre-defined or dynamically instantiated?**~~ — **RESOLVED.** Pre-defined `.md` files in `.opencode/agents/`, one per stage. Five fixed sub-agents matching the five workflow stages.
9. ~~**OQ9 — What is the skill loading mechanism for sub-agents?**~~ — **RESOLVED.** Orchestrator injects skills at handoff. Orchestrator acts as resource manager — identifies available agents, skills, and tools, and allocates the right set to each sub-agent based on project context. Sub-agents are lean executors.
10. ~~**OQ10 — What is a skill structurally?**~~ — **RESOLVED.** Skills = markdown prompt files (instructional, cost-effective). Tools = MCP tools (executable, used sparingly). Both exposed to the orchestrator. Orchestrator never reads or creates code — pure resource allocator only.

---

## Ready for Architecture

**Concept summary**: Monkey Devs is a solo-operator agentic development system built on the OpenCode agent standard. A principal orchestrator agent (`mode: primary`, defined in `.opencode/agents/monkey-devs.md`) acts as both a LangGraph workflow state machine and a resource manager — it never reads or creates code, only allocates the right skills and tools to the right sub-agent at each stage. Five pre-defined stage sub-agents (`mode: subagent`) handle execution: Concept & Spec (conversational intake modeled on forge), Architecture & Task Management (finalizes stack, designs system, breaks into tasks), Implementation & Code Generation (writes code and tests), Code Fixing & Test Categorization (runs tests, fixes issues, classifies unresolved failures as code-issue or test-issue), and Delivery (produces working code in a local repo). Skills are markdown prompt files injected at handoff; MCP tools are granted sparingly only when skills cannot cover the need. The user has a human approval gate at every stage boundary — approve and continue, or fix and redirect before the next stage begins. No fixed tech stack; Concept proposes candidates, Architecture decides. Deployment is out of scope.

**Key constraints**:
- OpenCode agent standard: orchestrator is `mode: primary` (Tab-switchable); sub-agents are `mode: subagent` (auto-invoked or `@mention`); all defined as `.md` files in `.opencode/agents/`
- Orchestrator is a pure resource allocator — NEVER reads or creates code; all code-level work happens inside sub-agents
- Skills = markdown prompt files (instructional, cost-effective, maximize coverage); Tools = MCP tools (executable, expensive, use sparingly)
- Both skills and tools are exposed to the orchestrator via a resource registry; injected/granted at handoff per stage and project
- Five fixed stage gates — no stage may be skipped; each requires explicit human approval
- Stack selection: Concept proposes candidates, Architecture makes the final binding decision
- Delivery = working code in local repo only; no deployment automation

**Confirmed directions**:
- OpenCode two-tier agent model: one primary orchestrator + five pre-defined stage sub-agents
- Orchestrator as resource manager: reads project context, selects and allocates skills + tools per stage
- Skill injection at handoff — sub-agents are lean executors, not self-configuring
- Conversational intake modeled on the forge skill pattern (Concept & Spec agent)
- Checkpoint-based human-in-the-loop: approve, fix, or redirect at each stage gate
- Explicit test categorization before delivery: failures labeled code-issue or test-issue, never silently dropped

**Discarded alternatives**:
- Fixed tech stack — ruled out; agents choose per project
- Fully autonomous execution — ruled out; five human gates required
- Fine-grained approval at every agent action — ruled out; stage-level gates only
- MCP tools as skills — ruled out; skills are markdown only, MCP reserved for tools space
- Dynamically instantiated sub-agents — ruled out; pre-defined `.md` files per stage

**Blocked (deferred)**:
- Deployment automation — deferred; handled manually post-delivery

**Open questions for the architect**:
- What does the orchestrator's resource registry look like — a manifest file, a directory scan, or an index document the orchestrator reads at session start?
- How does the orchestrator surface its allocation decisions at each stage gate — what does the user see about which skills/tools were assigned?
- When the user rejects or modifies a stage output, does LangGraph rewind to the previous node, branch into a correction sub-graph, or patch and re-validate?
- What tool permissions does each sub-agent get via the OpenCode `permission` field? (e.g. Implementation gets full bash/edit; Concept gets read-only)
- How does the Architecture agent's task breakdown integrate with a task tracking system, if any?
