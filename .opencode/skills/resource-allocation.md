# Resource Allocation

When allocating resources for a stage:

1. Read `.opencode/registry.yaml`
2. Filter skills: return only entries where the current stage number is in the `stages` list
3. Filter tools: return only entries where the current stage number is in the `stages` list
4. Skills with `stages: [0]` are orchestrator-only — never inject them into stage handoffs
5. Return the filtered lists to the orchestrator for handoff composition

The orchestrator uses these lists to build the SKILLS and TOOLS blocks of the handoff message.
