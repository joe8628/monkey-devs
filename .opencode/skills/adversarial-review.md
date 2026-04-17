# Adversarial Review

## Purpose
This skill governs how the orchestrator's review node critiques the artifacts produced by each stage before the stage gate is presented to the user. Its output — a ranked issue list and a verdict — feeds directly into `WorkflowState` and the stage gate renderer.

The review runs with the `reviewer` model defined in `.opencode/config.yaml` (a separate, typically more capable model than the stage node's model). It is invoked after the stage node completes and before `interrupt()` pauses for user approval.

**The reviewer's job is to find real problems, not to validate the work.** Assume the stage node took the path of least resistance. Look for what is conspicuously absent. Do not accept "this should work" — trace whether it actually does.

## When to Apply
After each stage node completes, before the stage gate is presented. `review.enabled` in `.opencode/config.yaml` can be set to `false` to bypass the review entirely — when bypassed, `review_skipped[stage]` is set to `True` and no verdict is recorded.

## Inputs

For every review:
- The artifact paths from `state["stage_outputs"][stage]` — read each file before forming any finding
- `docs/spec.md` — the FRs and NFRs are the ground truth for correctness checks
- `docs/concept.md` — the hard constraints and Non-Goals

For stages 2–5, additionally:
- `docs/architecture.md` — the Interface Contracts and component definitions

Do not review from memory. Read the actual artifacts. A finding not grounded in a specific line or section is not a finding.

## The Hostile Critic Stance

Review as if your job is to find the reason to reject, not to confirm the work is done.

**Look for what is absent, not what is present.** A spec section that exists but is never referenced in the architecture is a gap. A test file that exists but doesn't test the error path is a gap. A Known Limitations section that says "none" when tasks.yaml has `failure_classification` entries set is a gap.

**Trace claims rather than accepting them.** If the architecture says "FR-07 is implemented by the OrchestratorNode," find FR-07 in spec.md, find the OrchestratorNode in architecture.md, and verify the component description actually covers FR-07. Do not accept the mapping at face value.

**Never write a finding about style.** Off-by-one indentation, variable naming preference, and comment placement are not findings. Security vulnerabilities, missing requirements, broken references, and incorrect interfaces are findings.

## Issue Severity

Assign each finding one of three severities:

| Severity | Meaning | Example |
|---|---|---|
| **critical** | A blocker — the stage output cannot be approved as-is | API key literal in config file; FR with no owning component; circular dependency blocking Stage 3 dispatch |
| **high** | A significant gap — approval is risky without fixing | Interface contract differs from implementation; test asserts wrong exception type; required section missing from a deliverable document |
| **medium** | A real issue but not blocking — the user should know | Vague error message that won't help debugging; NFR not traced to a component; example in docs that won't compile |

Rank findings: all critical first, then high, then medium. Do not soften a critical finding to high to avoid triggering a block verdict.

## Stage-Specific Review Criteria

Apply the general criteria (structural, logic, security, correctness) plus these stage-specific checks:

### Stage 1 — Concept & Spec

**Spec completeness**
- Every FR uses EARS notation (WHEN/WHILE/IF) — reject vague "the system should" statements
- Every NFR has a measurable target (a number, a threshold, a binary observable)
- No FR is orphaned — every FR traces to at least one Goal from concept.md

**Stack candidates**
- Exactly 2–3 candidates evaluated — not fewer, not more
- Every candidate is scored against every criterion — no blank cells
- Trade-off narratives are project-specific, not generic

**Security**
- No API keys, connection strings, or credentials anywhere in concept.md or spec.md

### Stage 2 — Architecture

**FR coverage**
- Every FR from spec.md is owned by exactly one component — trace each one
- No component owns zero FRs (components without requirements are speculative additions)

**Interface contracts**
- Every arrow in the component diagram has a corresponding Interface Contract section
- Every Interface Contract names the function signature, preconditions, postconditions, and error types

**Task file**
- Every task in tasks.yaml has a non-empty `How to verify` line — tasks without verification criteria cannot be tested
- No cycles in `depends_on` — run topological sort mentally or trace each chain
- All `depends_on` IDs exist in the same file

**Stack decision**
- ADR-001 exists in architecture.md and names the complete stack (language, frameworks, persistence, testing, tooling)

### Stage 3 — Implementation

**Test coverage**
- Every task's `How to verify` criterion has at least one test function that exercises it
- No test file that consists only of `pass` or placeholder assertions

**Security**
- No subprocess calls with `shell=True` — command injection vector
- No path operations without boundary validation — path traversal vector
- No hardcoded credentials, API keys, or tokens in source or test files
- No `eval()` or `exec()` on user-supplied strings

**Correctness**
- Every public function's signature matches the Interface Contract from architecture.md — name, parameters, return type
- Every exception type in the Interface Contract is actually raised in the implementation, not caught and swallowed

**Completeness**
- All tasks in tasks.yaml have `status: done` — no `pending` or `in-progress` tasks

### Stage 4 — Code Fixing

**Classification completeness**
- Every task with a failing test has `failure_classification` set to `code-issue` or `test-issue` — `null` is not acceptable
- No task has `failure_classification: ambiguous` — ambiguous cases should have been resolved with user input before reaching the stage gate

**Fix correctness**
- For `code-issue` classifications: the production code was changed and the test now passes
- For `test-issue` classifications: the test was changed and passes without modifying production code

**Regression check**
- All previously passing tests still pass — no regressions introduced by fixes

### Stage 5 — Delivery

**Command accuracy**
- Every command in delivery.md and README.md works exactly as written from a clean project checkout
- Every referenced file path exists at the stated location

**Known Limitations honesty**
- If any task in tasks.yaml has `failure_classification` set and is not `done`, it appears in Known Limitations
- The section is not empty unless every FR is implemented and every test passes

**Document completeness**
- Every document listed in the README's Further Documentation section exists at its stated path

## Verdict Calibration

Choose the verdict after ranking all findings:

| Verdict | When to use |
|---|---|
| `pass` | No findings, or only findings you would not write a memo about |
| `warn` | One or more high or medium findings; no critical findings |
| `block` | One or more critical findings |

Do not use `warn` when `block` is correct. A critical finding that is softened to avoid blocking is a failure of the review.

## Output Format

```markdown
## Adversarial Review — Stage N: [Stage Name]

### Findings

**CRITICAL**

1. [Short title]
   Location: [file:line or section name]
   Problem: [what is wrong and why it matters]
   Fix: [concrete instruction — what to change and to what]

**HIGH**

2. [Short title]
   ...

**MEDIUM**

3. [Short title]
   ...

### Verdict

verdict: [pass | warn | block]
```

If there are no findings at a severity level, omit that section header. If there are no findings at all, omit the Findings section and write only the verdict.

## Fix Brief Storage

On `warn` or `block`:
1. Write the full review output to `.opencode/review-issue-log-stage-N.md`
2. Store the absolute path in `state["review_brief_paths"][stage]`
3. Set `state["review_verdicts"][stage]` to `"warn"` or `"block"`

On `pass`:
1. Set `state["review_skipped"][stage]` to `True`
2. Set `state["review_verdicts"][stage]` to `"pass"`
3. Do not write a fix brief file

The stage gate renderer reads `review_verdicts[stage]` and `review_brief_paths[stage]` to display the Review line. The fix_node reads the brief path to apply corrections before the next stage runs.

## Boundaries
- Do not form a finding without citing a specific location in the actual artifact
- Do not find style issues — find structural errors, logic gaps, security issues, and correctness failures
- Do not soften a `block` verdict to `warn` to avoid triggering the correction branch
- Do not skip the review when `review.enabled` is true in config — it is only skippable via config, not by judgment
- Do not review artifacts that were not produced by the stage being reviewed — confine findings to `stage_outputs[stage]`
