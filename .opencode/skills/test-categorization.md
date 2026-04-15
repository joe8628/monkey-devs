# Test Failure Categorization

For every failing test, classify it as one of:

- **code-issue**: the production code is wrong; the test correctly describes expected behaviour
- **test-issue**: the test is wrong, brittle, or tests the wrong thing; production code is correct

For each failure provide:
1. Test name
2. Classification: `code-issue` or `test-issue`
3. Rationale: one sentence explaining the root cause
4. Update `failure_classification` field in `.opencode/tasks.yaml` for the affected task

Do not fix any code or tests until every failure is classified.
