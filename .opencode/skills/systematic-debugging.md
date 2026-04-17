# Systematic Debugging

## Overview

Random fixes waste time and introduce new failures. Patching symptoms without understanding root causes always resurfaces the original problem in a different form.

**Core principle:** Find the root cause before touching any code. Every fix applied without a confirmed root cause is a guess.

**Violating the letter of this process is violating the spirit of it.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE CONFIRMATION FIRST
```

If you have not completed Phase 1, you cannot propose or apply a fix.

## Input from test-categorization

This skill runs after `test-categorization` has classified every failing test as `code-issue`, `test-issue`, or `ambiguous`. The classification determines which path to take:

| Classification | Fix target | Do NOT touch |
|---|---|---|
| `code-issue` | Production code (`monkey_devs/`) | The failing test |
| `test-issue` | The test file (`tests/`) | Production code |
| `ambiguous` | Nothing — surface to user first | Both |

Process all `ambiguous` failures before starting any fixes. An ambiguous classification means the Interface in `.opencode/tasks.yaml` was underspecified — applying any fix before clarifying risks locking in the wrong interpretation. Present the specific ambiguity and the two conflicting interpretations to the user, then wait.

After the user resolves an `ambiguous` case, update the task's classification to `code-issue` or `test-issue` and proceed with the appropriate path.

## The Four Phases

You MUST complete each phase before proceeding to the next. Do not skip phases because the issue seems simple — simple bugs have root causes too.

---

### Phase 1: Root Cause Investigation

**BEFORE writing any fix:**

**1. Read the full error output**

Copy the exact error message and complete stack trace. Do not paraphrase. Look for:
- The exception type and message
- The exact file and line where it originates
- The full call chain up to the test function

Run `uv run pytest <test_file>::<test_function> -xvs` to get the full verbose output for the specific failure you are investigating.

**2. Reproduce consistently**

Can you trigger the failure in isolation? Run the single failing test before drawing conclusions. A failure that only appears when the full suite runs is an ordering or state-pollution problem — a different root cause than the test suggests.

**3. Trace the call chain**

For `code-issue` failures: trace backward from where the exception appears to where the bad value originates. The error appears at the symptom; the root cause is at the source. Keep asking "what called this with this value?" until you reach the originating code.

For `test-issue` failures: trace what the test asserts against what the task's Interface actually specifies. The mismatch is the root cause.

**4. Confirm against the task description**

Read the task's description in `.opencode/tasks.yaml`. Match the failing assertion against the Interface and How to verify sections. This tells you definitively whether the production code or the test is wrong — do not skip this step even if the root cause seems obvious from the traceback.

**5. State the root cause in one sentence**

Before moving to Phase 2, write: "The root cause is: [X] because [Y]." If you cannot complete this sentence with specifics, you have not found the root cause. Gather more evidence.

---

### Phase 2: Pattern Analysis

**Find the working baseline before fixing:**

**1. Find working analogues**

Locate similar code in the project that works correctly. If you are fixing a `load_*` function, find another `load_*` that passes its tests. What is structurally different between the working and broken code?

**2. Compare against the Interface contract**

Re-read the Interface section of the task. List every point of divergence between what the Interface requires and what the current code does. Do not assume you have found all divergences — enumerate them.

**3. Identify the minimal change**

From the list of divergences, identify the smallest change that closes the gap between the implementation and the Interface contract. Any fix larger than this is scope creep; any fix smaller is incomplete.

---

### Phase 3: Hypothesis and Verification

**Scientific method — one hypothesis at a time:**

**1. Form a single, specific hypothesis**

"I think the root cause is X because Y, and fixing Z should resolve it."

Write this down. A hypothesis that does not name a specific variable, line, or function is not specific enough.

**2. Make the minimal change**

Apply only the change your hypothesis identifies. Do not fix anything else at the same time. Do not refactor unrelated code. Do not improve style while you are here.

**3. Run the failing test**

Does it pass? If yes, proceed to Phase 4. If no, do not add another change on top. Form a new hypothesis and return to Phase 3 from the beginning.

**4. When you have tried 3+ hypotheses without success**

Stop. Three failed hypotheses means the problem is likely architectural — a structural mismatch between the component design and the task's Interface that small fixes cannot bridge.

Do not attempt a fourth fix. Instead:
- Describe what each attempted fix was
- Describe why each failed
- Describe what structural mismatch you suspect
- Surface this to the user before continuing

---

### Phase 4: Confirm and Close

**Verify the fix is complete and contained:**

**1. Run the fixed test in isolation**

`uv run pytest <test_file>::<test_function> -xvs` — it must pass.

**2. Run the full test suite**

`uv run pytest` — no regressions. If existing tests break, the fix changed behaviour that other components depend on. Investigate before proceeding — do not comment out or delete breaking tests.

**3. Verify the fix addresses the root cause**

Re-read the root cause statement from Phase 1. Does the fix address that statement directly? A fix that makes the test pass but does not address the root cause is a symptom patch — it will resurface.

**4. Update tasks.yaml**

Set the `failure_classification` field of the affected task to the confirmed classification (`code-issue` or `test-issue`) if it is not already set.

**5. Commit**

Commit the fix with a message that names the root cause:

```
fix(<scope>): <what was wrong and what was changed>

Root cause: <one sentence from Phase 1>
Task: <T-NN>
```

---

## Red Flags — Stop and Return to Phase 1

If you catch yourself thinking any of these, stop:

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "I'll apply multiple changes and see which one fixes it"
- "It's probably X, let me fix that" — without tracing the call chain
- "I don't fully understand why this fails but this might work"
- "One more fix attempt" — when two have already failed
- "This test is testing the wrong thing" — without reading the task description to confirm

These thoughts mean you are guessing. Return to Phase 1 and gather more evidence.

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The issue is obvious, process is overkill" | Obvious issues have root causes too. Confirming is fast when you're right. |
| "I need to fix this quickly" | Systematic is faster than thrashing. Three guesses take longer than one confirmed fix. |
| "I'll fix it then write the test" | The test tells you when it's actually fixed. Write nothing without a failing test first. |
| "Multiple changes at once saves time" | You cannot isolate what worked. Each new bug adds another round of investigation. |
| "I see where it fails, that's the root cause" | Where it fails is the symptom. The root cause is why the bad value got there. |
| "Three fixes failed, let me try one more" | Three failures signal an architectural problem. One more guess does not fix architecture. |

## Quick Reference

| Phase | Goal | Success Criteria |
|---|---|---|
| **1. Root Cause** | Read errors, trace call chain, confirm against task description | One-sentence root cause statement |
| **2. Pattern** | Find working analogues, enumerate divergences | Minimal change identified |
| **3. Hypothesis** | One hypothesis, one change, re-run | Test passes — or new hypothesis |
| **4. Confirm** | Full suite, root cause verified, commit | No regressions, task updated |

## Boundaries
- Do not apply a fix to production code for a `test-issue` — fix the test only
- Do not modify the test for a `code-issue` — the test encodes the contract
- Do not proceed past three failed hypotheses without surfacing to the user
- Do not commit a fix without running the full test suite
- Do not close a task as fixed without updating `failure_classification` in tasks.yaml
