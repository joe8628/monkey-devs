# Stack Evaluation

## Purpose
This skill governs how to produce `docs/stack-candidates.md` at the end of Stage 1. It is a deliberate, criteria-driven comparison — not a gut-feel ranking. The document it produces is the primary input the Stage 2 architect uses when making the final binding stack decision via the `stack-decision` skill.

The goal is not to advocate for a stack. It is to give the architect enough signal to make a confident, defensible choice.

## When to Apply
After `docs/spec.md` exists and is confirmed. The NFRs and constraints in the spec are the raw material for evaluation criteria — do not begin evaluating stacks until those are in place.

## Inputs
Read before beginning:
- `docs/concept.md` — constraints, non-goals, ruled-out directions from intake
- `docs/spec.md` — NFRs drive scoring weights; Constraints section drives candidate filtering

## Step 1: Derive Evaluation Criteria

Do not use a generic scoring rubric. Extract the evaluation criteria directly from the spec.

For each NFR and each item in the concept's Constraints and Non-Goals, identify what it demands from the stack. Examples:

| Spec item | Criterion it implies |
|---|---|
| NFR: "CLI must start in under 200 ms" | Runtime startup performance |
| Constraint: "must run on Linux/macOS without Docker" | Portability, no containerisation requirement |
| Constraint: "team knows Python" | Language familiarity |
| Non-Goal: "no web UI" | Eliminates frontend framework weight |
| NFR: "resumable from crash" | Persistence / checkpointing support |

List 4–6 criteria. Assign each a **weight** (High / Medium / Low) based on how consequential it is to the project's success. A performance NFR with a hard number is High; a "nice to have" ergonomic preference is Low.

Write the criteria table into the output document before scoring anything.

## Step 2: Select Candidates

Propose exactly 2–3 candidates. Each must be meaningfully different — not three variations of the same ecosystem. The candidates should represent genuinely distinct points in the solution space (e.g., a mature opinionated framework vs. a minimal composable toolkit vs. a newer high-performance alternative).

**Candidate filtering rules:**
- Eliminate any candidate that violates a hard constraint from `concept.md` before scoring
- If a constraint eliminates an obvious candidate, note it explicitly under "Filtered Out" in the output — do not silently omit it
- Do not include a candidate you cannot score against all criteria

## Step 3: Score Each Candidate

For each candidate, score against every criterion on a 1–5 scale:

| Score | Meaning |
|---|---|
| 5 | Excellent fit — purpose-built or well-proven for this need |
| 4 | Good fit — meets the need with minor gaps |
| 3 | Adequate — meets the need with notable caveats |
| 2 | Weak fit — partial support, workarounds required |
| 1 | Poor fit — significant gap or known incompatibility |

Apply the weight: multiply score × weight factor (High = 3, Medium = 2, Low = 1). Sum the weighted scores to produce a **total**. Rank candidates by total, highest first.

The total is an input to the decision, not the decision itself. A candidate that scores lowest overall but uniquely satisfies a critical single criterion deserves a note calling that out.

## Step 4: Write Trade-off Narratives

For each candidate, write one focused paragraph on its trade-offs — what it gives you that the others do not, and what it costs or makes harder. Be specific:

- Good: "FastAPI's async-native design matches the concurrent LLM call pattern in FR-07, but its ecosystem for CLI packaging is shallow compared to Typer — you'd need to add Click or Typer on top."
- Bad: "FastAPI is modern and popular but has some trade-offs."

The trade-off narrative is what makes this document useful. A score without a narrative just tells the architect how the candidates ranked — it does not tell them *why*.

## Output Format

Write `docs/stack-candidates.md` using this structure:

```markdown
# Stack Candidates: [Project Name]

> Source: docs/spec.md — evaluated [Date]
> Status: CANDIDATES — awaiting final decision in Stage 2

## Evaluation Criteria

| Criterion | Weight | Source |
|---|---|---|
| [Criterion name] | High / Medium / Low | FR-XX or NFR-XX or Constraint |

## Filtered Out

- **[Candidate name]**: [reason it was eliminated before scoring]

*(none)* — if nothing was filtered

## Candidate Comparison

| Criterion | Weight | [Candidate A] | [Candidate B] | [Candidate C] |
|---|---|---|---|---|
| [Criterion] | H/M/L | score (weighted) | score (weighted) | score (weighted) |
| **Total** | | **NN** | **NN** | **NN** |
| **Rank** | | #1 | #2 | #3 |

## Candidate Profiles

### [Rank #1] [Candidate A]
**Score**: NN/NN max
**Summary**: <one sentence — what this stack is and why it ranked first>

**Trade-offs**:
<One paragraph. What this stack gives you that others don't. What it costs or makes harder. Specific to this project's requirements — not generic.>

**Key risks**:
- <Risk specific to this project>

---

### [Rank #2] [Candidate B]
...

---

### [Rank #3] [Candidate C]
...

---

## Recommendation Note

<One paragraph. Not a decision — a note for the architect. Highlight any single criterion where the ranking diverges from what a purely weighted score suggests, any candidate that uniquely satisfies a critical requirement, or any trade-off that should weigh heavily in the final call. Then stop — the decision is made in Stage 2.>
```

## Boundaries
- Do not select a stack — present candidates and evidence only
- Do not fabricate scores — if you cannot meaningfully evaluate a criterion for a candidate, say so explicitly
- Do not include more than 3 candidates; fewer is fine if the constraint filtering removes options
- Do not begin scoring before the criteria table is written
- Do not write generic trade-offs — every trade-off must reference a specific requirement or constraint from the spec
