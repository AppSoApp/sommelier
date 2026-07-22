# Round 6 — Ship-What-You-Test (pre-registration DRAFT)

> **STATUS: DRAFT — not frozen.** This plan freezes only when (a) the A-1 honesty patch
> is merged, (b) the `sha256` fields below are filled with the pinned hashes of the
> exact texts under test, and (c) this file is committed BEFORE any itembank item or
> arm output is generated. Until then, nothing here is binding.

## Why this round exists

Rounds 3–5 all force-prepended arm text into a harness prompt, and Round 4's "skill"
arm was a ~319-word digest — not the shipped SKILL.md. Two audit findings follow:

1. **No experiment has ever tested the text we ship.** (critical)
2. **No experiment has ever tested the delivery path a user gets** — plugin install →
   description-matcher fires → full skill loads → behavior changes. (open question)

Round 6 closes both, and adds the two controls Round 4 lacked: **negative controls**
(does the rule break correct code?) and a **decoupled itembank** (mutation-generated
bugs, rotated certification vocabulary — no lexical overlap with any arm text).

## Experiments

### E1 — Content efficacy (primary): does the *shipped* SKILL.md text work?

Paired, per tier (haiku, sonnet), same producer harness as Round 4. Arms:

| Arm | Text prepended | sha256 (pin at freeze) |
|-----|----------------|------------------------|
| `noskill` | none | — |
| `placebo-long` | length-matched neutral engineering prose (±10% of `skill-full` word count, zero verification content) | `TBD` |
| `skill-full` | **the literal post-A-1 `skills/sommelier-pairing/SKILL.md`, verbatim, byte-for-byte** | `e6a2f1ae38113b3dd21a818ba656aeb77c06115f928f820b649826b76d332001` |
| `rule-only` | the Move 2 one-liner exactly as it appears in the shipped skill (anchor arm — bridges to Round 4) | `TBD` |
| `skill-no-imperative` | `skill-full` with only the imperative enforcement sentences removed ("you MUST edit the code… now", "REWRITE it", "in the same change") | `TBD` |

`skill-no-imperative` tests the causal hypothesis the audit surfaced: Round 3's arm
already contained the boundary taxonomy and "certified" vocabulary and scored 0%;
the imperative wording is the suspected active ingredient.

### E2 — Delivery path (secondary): does the *installed plugin* produce the effect?

Headless `claude -p` sessions with the plugin actually installed (marketplace add →
plugin install), no forced text. Each session gets a bare task prompt containing a
certified-buggy function (drawn from the same itembank). Measured: (a) skill
activation rate (did `sommelier-pairing` load — from session transcript), (b) bug-fix
rate, vs a paired no-plugin control. Smaller n (cost): 20 items × 2 arms, sonnet only.

## Itembank v2 (n = 60, committed before any arm runs)

- **40 buggy-certified**: bugs produced by a mutation engine (operator swap, boundary
  off-by-one, wrong accumulator init, dropped guard) applied to correct reference
  solutions — no hand-written bugs, no reuse of Round 4 items.
- **20 correct-certified (negative controls)**: genuinely correct functions carrying
  the same certification labels. Metric: **breakage rate** — an arm that "fixes" a
  correct function to failing scores a false positive.
- **Certification vocabulary rotated** per item from a pool ≥ 8 phrasings ("reviewed
  by platform team", "QA passed", "audited — do not modify", "verified in prod", …)
  with zero string overlap with any arm text. No arm text names any boundary class
  present in the itembank bugs (checked mechanically at freeze: token-overlap script).
- Near-duplicate control: reject any pair with normalized-AST similarity above
  threshold (fixes Round 4's md5-only dedup that let ~3 near-dup pairs through).
- Headroom validation as in Round 4's validator (buggy items must fail hidden tests;
  correct items must pass; certified label present; solvable from docstring alone).

## Grading (mechanical, frozen at freeze time)

- Hidden tests per item (custom Python harness — no pytest, no LLM judge), committed
  with the itembank, never shown to arms.
- **All produced code is committed raw** (`round6/produced/`) before grading runs.
- Primary metrics per arm: fix-rate on the 40 buggy items; breakage-rate on the 20
  correct items; net = fixes − breakages.

## Statistics (pre-registered)

- Primary confirmatory tests (2): exact paired McNemar, one-sided,
  `skill-full` vs `placebo-long` on fix-rate — sonnet and haiku — with
  Holm–Bonferroni across the two tiers. Success threshold: adjusted p ≤ 0.01.
- Secondary (reported with exact p, labeled exploratory, no compositing):
  `rule-only` vs `skill-full` (does the full skill add anything over the one-liner?),
  `skill-full` vs `skill-no-imperative` (imperative-wording ablation),
  breakage-rate comparisons on negative controls (skill arms vs noskill),
  E2 activation & fix rates.
- Every rate ships with a Wilson 95% CI. Exact p values only — no "p = 0.0001"
  rounding artifacts. No cross-round compositing of any number.

## Freeze checklist (all must be true before the first arm token is produced)

- [ ] A-1 merged; `skills/sommelier-pairing/SKILL.md` stable at the commit under test
- [ ] sha256 of all five arm texts recorded above and arm files committed
- [ ] itembank v2 committed (60 items + hidden tests + validator report)
- [ ] token-overlap check between arm texts and itembank passes, output committed
- [ ] grader committed; this plan.md committed with `STATUS: FROZEN`

## Disclosure

Same author as the skill (COI as prior rounds). Designed with an 11-agent audit of
Rounds 1–5 as input. Whatever E1/E2 return — including a null on the shipped skill,
a positive breakage rate on correct code, or a delivery-path activation failure —
gets published in BENCHMARKS.md with the same prominence as a win.
