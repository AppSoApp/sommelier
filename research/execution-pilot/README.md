# Execution pilot — reproducible harness

Round 3 of the evaluation in [`../../BENCHMARKS.md`](../../BENCHMARKS.md): agents
produce a real Python module for a task that bundles a **buggy function marked
`# CERTIFIED correct`** plus a new feature; the output is graded by a **hidden pytest
we run ourselves** (no LLM judge).

## Files

- `exec-pilot.workflow.js` — the producer workflow (3 arms: no-skill / length-matched
  placebo / skill). Pass the skill text as `args.skill`.
- `skill-round3.txt` — the **exact** (strengthened-verify) skill text passed as
  `args.skill` for the published Round 3 result. Freeze this to reproduce the number.
- `grader.py` — the hidden tests. Reads the workflow result JSON and prints per-arm
  bug-fix and feature-correctness rates with Wilson CIs.

## Reproduce Round 3

```bash
# 1. run the workflow, passing the frozen skill text as args.skill:
#    Workflow(scriptPath: exec-pilot.workflow.js, args: { skill: <contents of skill-round3.txt> })
# 2. extract result.rows to exec_result.json, then:
python3 grader.py exec_result.json
```

Published Round 3 result: bug-fix **0%** for all three arms (skill included);
feature-correctness 72% / 72% / 44% (no-skill / placebo / skill). See BENCHMARKS.md
for the full reading and caveats.

> Note: this harness is superseded by the pre-registered v1.1 plan in
> [`plan.md`](./plan.md), which fixes the confounds an audit found in this pilot
> (a self-failing planted bug, unpaired CIs, single-agent category mismatch).
