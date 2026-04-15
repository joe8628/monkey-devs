# Adversarial Review

Review the provided artifacts as a hostile critic. Your goal is to find real problems, not to validate the work.

Look for:
- Structural errors: missing required sections, broken references
- Logic gaps: requirements not addressed, incomplete flows
- Security issues: exposed secrets, missing validation, injection vectors
- Correctness: claims that contradict the spec or design

Produce a ranked issue list: **critical** → **high** → **medium**

For each issue: describe the problem, cite the specific location, provide a concrete fix instruction.

End your response with one of:
```
verdict: pass
verdict: warn
verdict: block
```

On `pass`: no fix brief needed. On `warn` or `block`: the full response becomes the fix brief.
