# Handoff Message Composition

Compose a four-block handoff message to use as the stage node's system prompt:

```
## HANDOFF: [Stage Name]

### CONTEXT
project: [project name]
stage: [stage number or sub-stage key]
task_id: [T-XX or "all"]
[prior stage outputs wrapped in <prior-stage-output stage="N">...</prior-stage-output>]

### SKILLS
[For each skill: --- then ## Skill: [name] then full skill file content]

### TOOLS
- [tool-name]: [one-line description of its use in this stage]

### INSTRUCTIONS
[Stage-specific directive: what to produce, what artifacts to write, completion signal]
```

Wrap all prior artifact content in delimiters. Never concatenate user text into the INSTRUCTIONS block directly.
