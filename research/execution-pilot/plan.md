# Pre-registered evaluation plan — sommelier (Round 4)

**Status:** frozen before the Round 4 run. Purpose: give the improved skill a fair,
mechanically-graded chance to show **one real, attributable win**, and to falsify it
cleanly if it doesn't. Written after three prior null rounds (see `../../BENCHMARKS.md`).

## Why a new plan

The audit found the prior harness could neither win nor lose fairly:
- **Category mismatch** — an orchestration skill was tested on single-agent codegen.
- **A self-failing planted bug** — the `gcd` bug failed its *own* surface test, so a
  copy-verbatim agent scored `bug=False` with no choice: "didn't notice" and "chose
  not to fix" were conflated.
- **Unpaired CIs** — the design was paired but reported independent Wilson intervals
  (the exact error that buried Round 2).
- **Verbosity confound** — the skill's effect couldn't be separated from "added text".

## Primary confirmatory hypothesis (ONE)

> **H1.** On the deterministic hidden-pytest execution probe, the **rule** arm's
> `bug_fix` rate exceeds the **length-matched placebo** arm's, tested by paired
> **McNemar exact, one-sided, p < 0.05.**

Rationale: the only probe that is deterministic, execution-anchored, and where the
skill currently scores 0% — so beating it is a genuine, non-cosmetic win. Everything
else below is **exploratory** (Holm–Bonferroni corrected, reported as such).

## Arms (length-matched to within ±10% prompt tokens; log actual counts)

1. `noskill` — bare task.
2. `placebo` — generic senior-eng advice, padded to match the skill's length.
3. `rule` — **only** the ~8-line improved Move-2 rewrite + no-reuse guardrail
   (isolates the wording from the orchestration machinery).
4. `skill` — the full `sommelier-pairing` SKILL.md prepended (does the effect survive
   100 lines of orchestration text?).

`rule` vs `placebo` is the confirmatory contrast. `skill` vs `rule` is exploratory
(does packaging help or dilute?).

## Mechanical probes (no LLM judge)

- **FIX-PROBE (primary):** the returned certified function (a) AST-differs from the
  planted buggy source **and** (b) passes hidden pytest → separates "edited & correct"
  from "copied verbatim". Requires planted bugs with **headroom** (invisible on the
  function's obvious inputs, wrong on a hidden edge).
- **PROPAGATION-PROBE (exploratory):** does the new feature avoid inheriting the
  dependency's bug (computed independently, or fixed-then-reused)?
- **UNPARSEABLE-RATE (exploratory):** per-arm rate of outputs the extractor can't
  parse — a finding if the skill causes more prose instead of code.

## Item bank

**≥ 48 distinct tasks** from a template generator, each mechanically validated before
use: the buggy function must **pass its obvious surface test but fail a hidden edge**,
and a reference fix must pass all hidden tests. Certification string is **uniform**
across tasks for the confirmatory probe (one authority signal under test). *Task* is
the unit of analysis, not rep.

## Tiers / setting

Run at **two tiers**: `haiku`/`effort:low` (hard floor) and `sonnet`/`effort:medium`
(the tier the skill assigns to implementation). Report `bug_fix` per (arm × tier).
Most-likely-real win: **rule beats placebo at the mid tier.**

**Variance sanity check:** if two independent arms produce byte-identical aggregate
vectors, mark the run INVALID and re-run with confirmed non-zero temperature / cache
disabled (this killed Round 2).

## n / power

Paired McNemar on the primary. Target **n ≥ 48 tasks/arm/tier** (floor); stretch to
120 if the effect is small. Achieved-precision goal: Wilson half-width ≤ 12 pt on the
primary at the floor, ≤ 10 pt at stretch.

## Statistics

- Wilson 95% CIs via a single unit-tested helper (or `statsmodels.proportion_confint`).
- Paired difference reported with a **McNemar exact** p and discordant-pair counts
  (b, c) — never overlapping independent Wilsons — for the primary.
- **Holm–Bonferroni** across all exploratory probes. The primary (rule vs placebo,
  FIX-PROBE, mid tier) is the sole confirmatory test.

## Pre-registered win / loss conditions

- **WIN (H1 holds):** replace the scorecard's red rows with ONE narrow green claim —
  *"On a hidden-pytest execution benchmark, the certified-marker trigger raises bug-fix
  from 0% (plain/placebo) to X% [CI, McNemar p]"* — keeping all prior nulls published.
- **PARTIAL:** `rule` wins but `skill` does not → the honest claim is "these rules help,
  deployed however" — a win for the middle move, **not** for the two-skill product.
- **LOSS (H1 fails):** publish the null as Round 4; the repo keeps its no-efficacy
  stance. A persistent 0/0 at `haiku` would indicate a capability floor no wording lifts.

## Reproducibility protocol

Freeze this file + the grader + the item bank **before** the producing run. Grader is
arm-blind until aggregation. Commit all artifacts. Do **not** edit the README headline
until the frozen harness has measured H1.
