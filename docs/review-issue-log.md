# Monkey Devs Review Issue Log

**Source**: `docs/design/design-monkey-devs.md`
**Logged**: 2026-04-15
**Purpose**: Track non-blocking findings deferred from the 2026-04-15 adversarial review after the required defects were incorporated into the DAD.

## Recommended

### R-01
- **Priority**: High
- **Title**: Add Stage 3 concurrency cap
- **Finding**: Stage 3 fan-out has no concurrency cap, so large task sets can exhaust provider rate limits.
- **Deferred action**: Add `max_parallel_implementations` (default `4`) and enforce it with `asyncio.Semaphore` in `dispatch_stage3`.

### R-02
- **Priority**: Medium
- **Title**: Define `model_context_limits` map explicitly
- **Finding**: The design references `model_context_limits` but does not define the concrete default map or the fallback behavior for unknown user-configured models.
- **Deferred action**: Define the map in `config.py` for every default model and document "warn and skip" fallback behavior for unknown models.

### R-03
- **Priority**: Medium
- **Title**: Clarify `monkey-devs run` lifecycle semantics
- **Finding**: The design does not specify the exact workflow-state preconditions under which `run` is valid or how it differs from `approve`.
- **Deferred action**: Document valid preconditions, blocked states, and whether `run` can advance a resumed workflow or only execute the current runnable node.

### R-04
- **Priority**: Medium
- **Title**: Add structured handling for non-retryable API errors
- **Finding**: Non-retryable API failures currently propagate as raw exceptions with no user guidance.
- **Deferred action**: Catch context overflow, model-not-found, and authentication failures in `run_agentic_loop()` and surface stage/model/remediation guidance.

### R-05
- **Priority**: Medium
- **Title**: Document Stage 5 single-gate tradeoff
- **Finding**: A single Stage 5 gate forces full regeneration when either 5a or 5b is rejected.
- **Deferred action**: Record the tradeoff explicitly in ADR-010 and evaluate an optional sub-gate between 5a and 5b.

## Optional

### O-01
- **Priority**: Low
- **Title**: Add minimum Stage 1 intake turn count
- **Finding**: The model can emit `<intake-complete/>` on the first turn without capturing user input.
- **Deferred action**: Define and enforce a minimum user-turn requirement before accepting intake completion.

### O-02
- **Priority**: Low
- **Title**: Reconcile correction-branch topology wording
- **Finding**: ADR-003 and IU-10 describe the correction topology inconsistently.
- **Deferred action**: Add one sentence that aligns the node/function terminology across both sections.

### O-03
- **Priority**: Low
- **Title**: Document `max_handoff_chars` token assumption
- **Finding**: `max_handoff_chars: 400000` is a character proxy for a token budget, but the assumed chars-per-token ratio is undocumented.
- **Deferred action**: Record the conservative chars/token assumption and the default models it is designed to protect.

### O-04
- **Priority**: Low
- **Title**: Document `asyncio.Lock()` event-loop assumption
- **Finding**: The `tasks.yaml` lock is only correct if all fan-out nodes share one event loop.
- **Deferred action**: Add that LangGraph/event-loop assumption directly to the `tasks.py` implementation note.

### O-05
- **Priority**: Low
- **Title**: Reorder overlapping API key regex checks
- **Finding**: The Anthropic `sk-ant-` literal pattern is fully subsumed by the broader `sk-` pattern, so the Anthropic-specific branch is currently dead code.
- **Deferred action**: Reorder the regex checks or document that Anthropic literals are intentionally caught by the generic `sk-` detector.

### O-06
- **Priority**: Low
- **Title**: Remove logger test coupling via module-global counter
- **Finding**: A module-level logger filename counter would couple otherwise unrelated `RunLogger` instances across tests and process lifetime.
- **Deferred action**: Keep the pid/UUID-based filename strategy and avoid reintroducing a shared module-global counter.

### O-07
- **Priority**: Low
- **Title**: Tighten workflow state string types with `Literal`
- **Finding**: `WorkflowState` string fields such as `workflow_status`, `gate_decisions`, and related review values currently accept arbitrary strings.
- **Deferred action**: Replace the free-form `str` annotations with `Literal[...]` constraints before Phase 2 graph-routing logic depends on them.

### O-08
- **Priority**: Low
- **Title**: Add explicit dev dependency group
- **Finding**: `pyproject.toml` does not declare dev-only dependencies such as `pytest`, which will make CI/bootstrap setup less explicit once automation is introduced.
- **Deferred action**: Add a `dev` dependency group using `[dependency-groups]` or `[project.optional-dependencies]` before CI is configured.

### O-09
- **Priority**: Low
- **Title**: CLI stub completeness
- **Source**: 2026-04-16 adversarial review (Phase 2, IU-02–IU-09)
- **Finding**: CLI entry points are stubs; not a defect in the current phase but will require completion before the tool is usable end-to-end.
- **Deferred action**: Track in milestone backlog; implement before any end-to-end integration testing milestone.
