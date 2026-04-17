# Test-Driven Development

## Purpose
This skill governs the implementation loop for every task in Stage 3. It defines the order of operations — write the test, confirm it fails correctly, implement the minimum code to pass it, confirm no regressions — and the exit protocol (artifact emission, commit).

This skill governs *process*. The `code-generation` skill governs *quality*: naming conventions, error handling scope, and code style. Both apply to every task.

## When to Apply
For every task dispatched in Stage 3. The handoff message will contain a task drawn from `.opencode/tasks.yaml`. Apply this skill to each task before writing any production code.

## Inputs
Each task's `description` field encodes three sections. Parse them before writing anything:

```
What to build: <the component, function, or file to create>
Interface:     <function signatures, file paths, CLI commands, or data shapes it must satisfy>
How to verify: <the concrete observable outcome — test file to pass, command to run, assertion to make>
```

The **Interface** section defines what the test must target — import paths, function names, parameter types, return types. The **How to verify** section defines what the test must assert. Do not invent interfaces not specified in the task.

## The TDD Cycle

### Step 1: Parse the Task

Read the task description. Identify:
- The module or file path to create (from What to build)
- Every function/class signature the test must exercise (from Interface)
- Every assertion the test must make (from How to verify)

If the Interface specifies multiple independent behaviours (e.g., "load valid YAML" and "reject empty file"), write one test function per behaviour before implementing any of them.

### Step 2: Write the Test File

Write to the test file specified in How to verify, or create `tests/test_<module>.py` if not specified. The test must:
- Import the target module/function at the path the Interface specifies
- Call the function with the inputs the Interface describes
- Assert the outcome How to verify requires

Do not create helper stubs or placeholder implementations to make the import work. The test must reference the real target path — even if the module does not yet exist.

### Step 3: Run the Test — Confirm the Right Failure

Run the test suite. The failure you see now is the most important signal in the cycle:

**Acceptable failures (the module or function truly doesn't exist yet):**
- `ModuleNotFoundError` — the target file hasn't been created
- `AttributeError: module has no attribute '...'` — the file exists but the function is missing
- `AssertionError` — the function exists but returns the wrong value

**Unacceptable failures (the test itself is broken):**
- `SyntaxError` in the test file — fix the test before proceeding
- `ImportError` caused by a typo in the import path — fix the import path
- `FixtureError` from a missing conftest fixture — add the fixture or use a simpler setup
- `TypeError` from calling the function with wrong argument count — fix the test to match the Interface

If you see an unacceptable failure, fix the test and re-run until you see an acceptable failure. Do not proceed to implementation until Step 3 produces an acceptable failure.

### Step 4: Write the Minimum Implementation

Write the production code. Follow the `code-generation` skill for quality: match existing naming conventions, handle errors only at system boundaries, write no TODO placeholders, add no features beyond what the task specifies.

"Minimum" means the simplest code that will make the test pass — not the simplest possible code overall, but the simplest correct implementation. Do not add untested code paths.

### Step 5: Run the Test — Confirm It Passes

Run only the test file you wrote. It must pass completely — all test functions green, zero errors, zero warnings from your new code. If it fails:
- Read the failure message before changing anything
- Fix the implementation, not the test (unless Step 3 established the test was wrong)
- Re-run until fully green

### Step 6: Run the Full Test Suite — Confirm No Regressions

Run the entire test suite (`uv run pytest` for Python projects). If existing tests break:
- The implementation changed behaviour another component depended on — investigate before fixing
- Do not comment out or delete existing tests to make the suite pass
- If an existing test was genuinely wrong about an interface that changed, surface this before proceeding

### Step 7: Emit Artifacts

For every file you created or modified, emit an artifact block in your response:

```
<artifact path="relative/path/from/project/root">
[full file content]
</artifact>
```

Include both the test file and the implementation file.

### Step 8: Commit

Commit the test file and implementation file together in a single commit. Commit message format:

```
<type>(<scope>): <what was built>

Implements: <task ID from tasks.yaml>
How to verify: <one-line summary of the test coverage>
```

Use `feat` for new functionality, `fix` for corrections to existing code, `test` for test-only additions. The scope is the module or component name.

## Handling Partial Task Completion

If a task contains multiple verification scenarios and you implement them one at a time:
- Write **all** test functions for the task before writing **any** implementation
- Run the full set — all must fail for acceptable reasons
- Implement until all pass
- Do not commit partial implementations (some tests passing, some failing)

## Interaction with `code-generation`

`tdd-implementation` governs **when** code is written (after a failing test). `code-generation` governs **how** the code is written (style, error handling scope, self-documenting naming). Both apply simultaneously to Step 4. If there is tension — e.g., the minimum implementation that passes the test has a style issue — fix the style issue before committing; do not defer it.

## Boundaries
- Do not write implementation code before Step 3 has produced an acceptable failure
- Do not modify a test to make it pass — the test encodes the contract; the implementation must satisfy the contract
- Do not commit if Step 6 shows regressions
- Do not emit artifacts only for the implementation file — the test file is part of the deliverable
- Do not skip the full test suite run in Step 6 because "this change is isolated" — isolation is an assumption, not a fact
