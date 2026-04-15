# Systematic Debugging

Follow this process for every failing test or error:

1. **Read the error output** — copy the exact error message and stack trace
2. **State a hypothesis** — one sentence explaining what you think is wrong
3. **Find the root cause** — read the relevant source files; do not guess
4. **Apply a minimal fix** — change only what is needed to address the root cause
5. **Re-run the test** — confirm it passes
6. If still failing: form a new hypothesis and repeat from step 2

Never apply a fix without first confirming the root cause in the code. Document the root cause found before writing any fix.
