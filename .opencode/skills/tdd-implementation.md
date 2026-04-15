# Test-Driven Development

Follow this sequence strictly for every unit of work:

1. **Write the test first** — the test must reference the interface you intend to build
2. **Run the test** — confirm it fails for the right reason (not an import error)
3. **Write minimum implementation** — only enough code to make the test pass
4. **Run the test again** — confirm it passes
5. **Commit** — test and implementation together in one commit

Never write implementation code before a failing test exists. Never skip step 2 (the failure confirmation).
