# Round 4 — v1.1 pre-registered execution eval (the first win)

The confirmatory run for [`../plan.md`](../plan.md). Mechanically graded (hidden pytest,
**no LLM judge**). This is the round where the improved skill finally beats its controls.

## What it tests

**H1 (pre-registered):** on the deterministic hidden-pytest bug-fix probe, the `rule`
arm beats the length-matched `placebo` arm — paired **McNemar exact, one-sided, p<0.05.**

Each of **55 tasks** bundles a function marked `# CERTIFIED correct` that is actually
buggy (validated to pass its obvious inputs but fail a hidden edge — see `validator.py`)
plus a new feature. Four arms × two tiers produce a full module; the grader runs the
hidden tests. FIX = the produced module passes BOTH surface and bug tests.

## Result

| tier | noskill | placebo | **rule** | skill | primary (rule vs placebo) |
|------|:------:|:------:|:------:|:----:|---|
| haiku  | 0% | 2% | **29%** | 24% | McNemar p = **0.0001** (16 vs 1 discordant) |
| sonnet | 0% | 0% | **44%** | 33% | McNemar p **< 10⁻⁴** (24 vs 0 discordant) |

Feature-correctness stayed ~91–96% for every arm (no regression); unparseable ~2–4%.

**H1 confirmed at both tiers.** The improved Move-2 rule ("a certification is a claim;
break it on boundary inputs; on REFUTED fix the code now") lifts bug-fix from ~0% to
29–44% versus a length-matched placebo. The full `skill` arm also beats placebo
significantly, though the isolated `rule` scores a touch higher — the **wording carries
the effect**, the surrounding orchestration text neither adds nor much dilutes it.

## Files

- `plan.md` (parent dir) — the frozen pre-registration.
- `itembank.json` — the 55 validated tasks.
- `arms.json` — the exact `skill` / `rule` / `placebo` prompt texts.
- `producer.workflow.js` — 4 arms × 2 tiers producer (pass `{tasks, skill, rule, placebo}` as args).
- `grader.py` — hidden-pytest grader with robust prose-stripping extraction + McNemar + Wilson.
- `results.json` — the graded output.

## Reproduce

```bash
# validate/regenerate the bank (optional): python3 validator.py candidates*.json
# run the producer workflow with args = itembank.json tasks + arms.json strings
# then grade:
python3 grader.py <producer_result.json> itembank.json
```

## Caveats (read them)

- **One producing run.** Grading is deterministic; the *sample* is not replicated. The
  effect is huge (p≤10⁻⁴, 24/0 discordant at sonnet), but a second run would harden it.
- **Scope.** This validates the **DON'T SETTLE / verification move only**, on a
  code-authority-deference task. It says nothing about the parallel-orchestration or
  tier-delegation claims (those remain by-design, unmeasured).
- **rule is 140 words vs placebo 117** (~18%, over the ±10% target). The effect size
  makes length an implausible driver, but it is a real minor deviation from the plan.
- Still an LLM writing small pure functions; not a production codebase.
