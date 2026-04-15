# Stage Gate Presentation

Present a stage gate summary with:

1. **Stage**: name and number
2. **Model**: LLM model used for this stage
3. **Skills Injected**: names only (not full content)
4. **Artifacts Produced**: list of file paths written
5. **Unresolved Issues**: any test failures or classification gaps
6. **Actions Available**:
   - `monkey-devs approve` — advance to next stage
   - `monkey-devs reject --reason "..."` — trigger correction branch
   - `monkey-devs details` — expand full allocation log

Keep the summary compact. The user reads it to decide whether to approve or reject.
