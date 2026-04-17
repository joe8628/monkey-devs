# Test Failure Categorization

## Purpose
This skill governs how Stage 4 classifies each failing test before any fix is applied. Its output — a classification and rationale for every failure — tells `systematic-debugging` what to fix and whether to fix the production code or the test itself.

Categorization is the hardest judgment call in Stage 4. The same error message can appear for opposite reasons. This skill gives you the signals to distinguish them reliably.

## When to Apply
At the start of Stage 4, before `systematic-debugging` begins. Do not fix anything until every failing test has been classified.

## Two Classifications

| Classification | Meaning |
|---|---|
| `code-issue` | The test correctly describes the required behaviour; the production code does not satisfy it |
| `test-issue` | The production code is correct or not at fault; the test definition, assertions, or setup are wrong |

A third outcome is possible: `ambiguous` — the task's Interface was underspecified, causing the implementation and the test to diverge without either being clearly wrong. Treat this as a special case (see below).

## The Primary Anchor: The Task Description

The most reliable way to categorize a failure is to compare the test and the production code against the task description that generated both — specifically its **Interface** and **How to verify** sections in `.opencode/tasks.yaml`.

Before reading the test or the traceback in detail, read the task description:
- What function signature does Interface specify?
- What behaviour does How to verify require?
- What exception types does Interface specify for error cases?

Now the question becomes concrete: "Is the failing assertion one that the Interface/How to verify section actually requires?" If yes, the test is correct and the production code is wrong (`code-issue`). If no, the test is asserting something the spec never required (`test-issue`).

## Step-by-Step Process

### 1. Run the Full Suite

Run the complete test suite and collect all failures. List them — do not start categorizing individual failures until you have the full list. Patterns across failures often clarify individual ones.

### 2. For Each Failure: Read All Three Artifacts

Read in this order:
1. **The error message and traceback** — where the failure occurs
2. **The failing test** — what it asserts and how it's set up
3. **The task description** (from `.opencode/tasks.yaml`) — what was actually required

Reading only the traceback and test without the task description is guessing. The task description is the ground truth.

### 3. Apply the Decision Signals

Use the signals below to determine the classification. No single signal is definitive — weigh them together.

---

#### Signals for `code-issue` (test is correct, production code is wrong)

**Strong signals:**
- The failing assertion directly corresponds to a statement in the task's **How to verify** or **Interface** section — the test is testing exactly what was specified
- The error is `AssertionError` — the function runs but returns a wrong value
- The error is an unhandled exception in production code (`TypeError`, `KeyError`, `AttributeError` on the production object, not the test's mock) — the function exists but behaves incorrectly
- Multiple tests fail with the same root cause in production code — one bug surfaces multiple failures
- The test passed at an earlier point and recently regressed — a recent change broke it

**Moderate signals:**
- The test was written by the Stage 3 `tdd-implementation` cycle (visible from git history) — it was written against a failing implementation, so it encodes the spec correctly
- The test's setup (fixtures, input data) is straightforward and correct; the failure is in the assertion
- Other tests for the same module pass — the failure is localised to one function

---

#### Signals for `test-issue` (production code is correct, test is wrong)

**Strong signals:**
- The failing assertion contradicts the task's Interface or How to verify — the test asserts something the spec never required
- The test imports from a path that differs from the Interface's specified path — a path mismatch introduced in the test
- The error is `AttributeError` or `TypeError` raised inside the test's own setup or mock configuration — the test's plumbing is broken, not the production code
- The test asserts an implementation detail rather than observable behaviour: internal variable names, private method names, exact internal data structures not named in the Interface
- The test is brittle — it depends on ordering, timing, or environmental state not controlled by the test setup (flaky)
- The test's assertion is more restrictive than the spec: e.g., Interface says "returns a list", test asserts a specific length that no requirement establishes

**Moderate signals:**
- The production code satisfies all other tests for the same module — only this test fails, and the others test equivalent behaviour
- The task's How to verify is vague, and the test author added specificity that went beyond the spec
- The test setup creates conditions that cannot occur in production (impossible input combination)

---

#### When to classify as `ambiguous`

Use `ambiguous` when:
- The task's Interface did not specify a behaviour precisely enough for the implementation and the test to agree, and both are internally reasonable interpretations of the ambiguous spec
- Example: Interface says "raises an error on invalid input" without naming the exception type; implementation raises `ValueError`, test asserts `TypeError`; neither is clearly wrong

**Do not use `ambiguous` as a default** when you are uncertain. Investigate further. `ambiguous` means "the spec itself is the problem" — not "I cannot tell."

When you classify something as `ambiguous`, surface it immediately with the specific Interface line that is underspecified. Do not pass it to `systematic-debugging` — it requires a spec clarification first.

### 4. Produce the Classification Table

For every failure, output:

```
Test: <test_id or test file::function name>
Task: <T-NN>
Classification: code-issue | test-issue | ambiguous
Error: <one-line summary of the actual failure>
Rationale: <two sentences: why this classification, which signal(s) drove the decision>
```

List all classifications before any fixes begin.

### 5. Update tasks.yaml

For each classified failure, update the `failure_classification` field of the corresponding task in `.opencode/tasks.yaml`. Use the exact values: `code-issue`, `test-issue`, or `ambiguous`.

Tasks with no failing tests keep `failure_classification: null`.

## Common Misclassification Patterns

These failure patterns are frequently misread — check before classifying:

| What you see | Looks like | Often actually |
|---|---|---|
| `ModuleNotFoundError` | test-issue (test imports wrong path) | code-issue (production module was never created) |
| `AssertionError: None != X` | code-issue (returns None) | test-issue (test calls function without required arguments, gets None because error was swallowed) |
| `AttributeError: X has no attribute Y` | code-issue (attribute missing) | test-issue (test accesses a private attribute the Interface never exposes) |
| All tests in a file fail | code-issue in production | test-issue in conftest or shared fixture — one broken fixture fails every test that uses it |
| Test passes locally, fails in suite | code-issue | test-issue — test has ordering dependency or global state mutation |

For each of these, read the task's Interface before finalising the classification.

## Boundaries
- Do not fix any code or test until all failures are classified
- Do not classify `ambiguous` without identifying the specific Interface line that is underspecified
- Do not treat a passing test suite as evidence there are no issues — if a test was deleted or commented out to make the suite pass, that is a `test-issue` to surface
- Do not use git blame or authorship as a classification signal — who wrote the test is irrelevant; what the spec required is the only ground truth
