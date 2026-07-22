# Round 6 — Ship-What-You-Test: **NULL RESULT (ceiling — instrument failure)**

> **Headline, stated plainly:** under this round's probe, the shipped skill showed
> **no effect over placebo** — because *every* arm, including no-skill baseline,
> fixed ~all the bugs. The probe collapsed at the ceiling, the mirror image of
> Round 3's floor. Pre-registered primary tests: sonnet p = 1, haiku p = 0.5.
> We publish it exactly as the frozen plan demands.

## What was run

Everything the frozen `plan.md` (commit `5cc6292`) pre-registered for E1:

- 5 arms × 2 tiers × 60 items = **600 producer calls**, all completed
  (43 `skill-no-imperative`×sonnet calls were interrupted by a session quota
  limit and re-dispatched ~30 min later via workflow resume with byte-identical
  prompts — logged as a protocol note, not a design change).
- All 600 produced files committed **raw, before grading** (`e16d9b6`).
- Graded mechanically by `grader6.py` (hidden tests, no LLM judge) → `results6.json`.

## Results

| tier | arm | fix-rate (40 buggy) | breakage (20 correct) |
|------|-----|--------------------:|----------------------:|
| haiku | noskill | **40/40 = 100%** | 0/20 = 0% |
| haiku | placebo-long | 39/40 = 97.5% | 0/20 = 0% |
| haiku | rule-only | 39/40 = 97.5% | 0/20 = 0% |
| haiku | skill-full | 40/40 = 100% | 0/20 = 0% |
| haiku | skill-no-imperative | 39/40 = 97.5% | 0/20 = 0% |
| sonnet | *all five arms* | 40/40 = 100% | 0/20 = 0% |

Pre-registered primary McNemar (`skill-full` vs `placebo-long`): sonnet b=0,c=0
→ p = 1; haiku b=1,c=0 → p = 0.5. **Null on both tiers.** All secondary
contrasts equally flat.

## Diagnosis — why the ceiling (and why Round 4 had headroom)

The two probes differ in one decisive way:

- **Round 4:** the certified-buggy function was **background dependency** — the
  task was to build a *new* feature that uses it, its spec was never given, and
  nothing asked the agent to touch it. Fixing it required actively distrusting
  a "CERTIFIED" label on code outside your task. Baseline: **0%**.
- **Round 6 E1 (this round's template):** the agent was handed the function
  **plus its full edge-case spec** and asked to "produce the final version of
  the function." Diffing code against a complete spec and rewriting is the
  task's natural completion — **the task itself performs the verification**,
  so the verification rule has nothing left to add. Baseline: **100%**.

The itembank rule "solvable from the docstring alone" (imported for grading
solvability) is exactly what deleted the headroom once that docstring was shown
to the producer. The Round 4 propagation design — hide the dependency's spec,
make distrust cost something — is the load-bearing part of the instrument, and
this round's E1 template failed to reproduce it. That is an instrument-design
error by the orchestrator, not evidence against (or for) the skill.

## What Round 6 does and does not establish

- ✅ **Honest null, published:** the shipped SKILL.md text produced no measurable
  effect under a spec-in-hand rewrite probe. Consistent with the skill's own
  YAGNI clause: when the task already forces verification, the discipline adds
  nothing.
- ✅ **No measured harm:** 0/200 correct-certified outputs broken across all
  skill/rule arms — no evidence (in this weak probe) that the rule makes agents
  break working code.
- ❌ **Not established:** whether the shipped skill text reproduces Round 4's
  win under a faithful propagation probe. That needs **E1b**: same frozen
  itembank and arms, but a Round-4-shaped template (certified function as an
  unspecced dependency of a new-feature task). Requires a pre-registration
  addendum before any E1b output is produced.
- ❌ **Still open:** E2 (delivery path — does the installed plugin fire at all?)
  was scaffolded but not run.

## Files

- `results6.json` — full per-item records + summaries + McNemar (committed raw)
- `produced/` — all 600 outputs, committed before grading
- everything else — frozen at `5cc6292`
