# Round 5 — cost & speed, measured fairly

The cost and speed numbers in [`../../../BENCHMARKS.md`](../../../BENCHMARKS.md) → *Round 5*.
Both use the **fair** baseline: a dynamic Workflow with sub-agents on the **top tier**
(the real "just use a workflow" default), not a strawman single cheap agent.

## Files

- `cost.workflow.js` — same 24 tasks, same 2-step pipeline (implement → verify gate),
  two arms differing **only in model tier**: all-Opus vs tier-routed (Sonnet impl + Opus
  gate). Per-role output tokens via `budget.spent()`. Grade the returned code with
  [`../round4/grader.py`](../round4/grader.py) for the bug-fix rates.
- `speed.workflow.js` — serial (1 agent writes 8 functions) vs parallel (8 agents, one
  each), 3 projects. Pass `args = {mode: "serial"}` or `{mode: "parallel"}`; read
  `duration_ms` from the workflow result.
- `results.json` — the measured numbers.

## Headline

| | result |
|---|---|
| **Cost** (tier-routed vs all-Opus, output $) | $1.18 vs $1.46 → **~19% cheaper**, bug-fix 58% vs 50% |
| **Speed** (parallel vs serial, wall-clock) | 21.6 s vs 12.3 s → **parallel ~1.8× SLOWER** on tiny tasks |

## Honesty notes (both matter)

- The cost saving was first mis-stated as **36%** using a stale Opus output price of
  **$75/M**. At the current **$25/M** it is **19%**. We caught our own number — see the
  correction in `BENCHMARKS.md`.
- **Parallel lost.** Fan-out has per-agent overhead; on trivial tickets a single agent is
  faster. Parallelism pays off only on large, genuinely-parallelizable work — which is
  the skill's own YAGNI rule (*don't bring a fleet to a one-liner*).
- Wall-clock is load-sensitive; treat the speed number as indicative, not a benchmark.
