# Task Decomposition

Break the implementation into independently deliverable tasks for `tasks.yaml`.

Rules:
- Each task must be implementable without depending on incomplete work from other tasks
- Tasks must list their `depends_on` IDs explicitly
- Each task maps to a single, testable unit of work
- Use IDs in the format T-01, T-02, etc.

Output a valid YAML block:
```yaml
tasks:
  - id: T-01
    title: "Short imperative title"
    description: "What to build and how to verify it"
    status: pending
    stage: 3
    depends_on: []
    failure_classification: null
```

Order tasks so foundational work comes before dependent work.
