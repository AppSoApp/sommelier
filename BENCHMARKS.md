# Benchmarks — the honest version

> This skill's second rule is **"never believe a report — re-measure it."** It would
> be hypocritical to ship inflated numbers. So here is everything we measured,
> including the parts where the skill **lost** or the metric **didn't hold up**.
>
> **TL;DR (after three studies, including a paired n=48 test with a length-matched
> placebo):** We **could not show** that the `sommelier` skill beats a length-matched
> placebo — or even just telling Claude *"you are an orchestrator."* On the fairest
> test, every probe's confidence interval overlaps the control; on two probes the skill
> is nominally *worse*. The one finding that survives is **not skill-specific**:
> framing work as *orchestrate-and-verify* (rather than single-pass plan-then-execute)
> catches more planted false numbers — but plain generic advice reproduces it. **This
> repo makes no efficacy claim.** It ships as an opinionated discipline, not a proven
> speedup.

---

## What we ran

Two blind, LLM-judged simulations. Responders on Haiku, judges on Sonnet, an Opus
adversarial critic on each aggregate.

| Study | Design | Cycles | Arms |
|-------|--------|--------|------|
| **A/B** | same task, with-skill vs no-skill, single-shot planning | 100 | 2 |
| **3-arm** | opusplan (single serial) vs plain Workflow vs sommelier skill | 32 | 3 |

Half of every scenario set carried a **planted false number** (e.g. *"a report says
this module has 0 imports"*) as a ground-truth probe for verification behavior.

---

## The one signal that held up: planted-error detection

This is the only metric anchored to ground truth (we planted the lie, so detection
is objective, not rubric-subjective).

```
Planted false-number detection rate
(share of planted-lie cycles where the plan re-measures instead of trusting the report)

opusplan  (single serial plan) │███████████████████████████░░░░░░░░░░░░░░░░░░░░░│  56%
plain     (just use a Workflow)│███████████████████████████████████████████████│ 100%
sommelier (this skill)         │███████████████████████████████████████████████│ 100%
                                0%                                            100%
                                                   n = 18 planted cycles (3-arm study)
```

**Read it carefully:** this says *orchestrate-and-verify* beats *plan-then-execute*.
It does **not** say the sommelier skill beats plain orchestration — they tie at
100%. This was the *early, easier* 3-arm study; **Round 2 below re-ran it paired,
harder (with authority pressure), and with CIs** — and the tie held while the
absolute rates dropped. Treat this chart as the first look, superseded by Round 2.

<svg xmlns="http://www.w3.org/2000/svg" width="640" height="230" viewBox="0 0 640 230" role="img" aria-label="Planted false-number detection rate by arm">
  <style>
    text { font-family: -apple-system, Segoe UI, Roboto, sans-serif; }
    .t { font-size: 15px; font-weight: 600; fill: #2b2b2b; }
    .l { font-size: 13px; fill: #555; }
    .v { font-size: 13px; font-weight: 700; fill: #2b2b2b; }
    .cap { font-size: 11px; fill: #888; }
  </style>
  <text x="20" y="28" class="t">Planted false-number detection rate</text>
  <text x="20" y="46" class="cap">higher = more often re-measures a suspicious reported number (n = 18)</text>
  <!-- axis -->
  <line x1="200" y1="70" x2="200" y2="190" stroke="#ddd" stroke-width="1"/>
  <line x1="600" y1="70" x2="600" y2="190" stroke="#f2f2f2" stroke-width="1"/>
  <!-- opusplan 56% -->
  <text x="190" y="92" text-anchor="end" class="l">opusplan</text>
  <rect x="200" y="78" width="224" height="26" rx="4" fill="#c9a227"/>
  <text x="432" y="97" class="v">56%</text>
  <!-- plain 100% -->
  <text x="190" y="132" text-anchor="end" class="l">plain Workflow</text>
  <rect x="200" y="118" width="400" height="26" rx="4" fill="#7b1e3a"/>
  <text x="558" y="137" class="v" fill="#fff">100%</text>
  <!-- sommelier 100% -->
  <text x="190" y="172" text-anchor="end" class="l">sommelier (skill)</text>
  <rect x="200" y="158" width="400" height="26" rx="4" fill="#7b1e3a"/>
  <text x="558" y="177" class="v" fill="#fff">100%</text>
  <text x="200" y="212" class="cap">3-arm study · Haiku responders · Sonnet judge · not yet paired/CI'd</text>
</svg>

---

## Where the skill lost or tied (published on purpose)

### A/B, 100 cycles — the skill *reduced* rubric compliance

Injecting the full skill into a single planning prompt scored **worse** than no
skill on almost every axis:

| Criterion | no skill | with skill | Δ |
|-----------|:-------:|:----------:|:--:|
| overall compliance | **76%** | **61%** | **−15** |
| file-scoped tickets | 45% | 51% | +6 *(within noise)* |
| disjoint file ownership | 65% | 60% | −5 *(within noise)* |
| re-measures / evidence gate | 85% | 65% | −20 |
| delegates to model tiers | 96% | 74% | −22 |
| YAGNI / minimalism | 77% | 55% | −22 |
| doesn't self-code | 87% | 58% | −29 |
| **planted-lie detection** | **94%** | **76%** | **−18** |

Two things are happening, and we can't fully separate them:
- **Real skill defect:** the skill's detail nudged plans toward *over-structuring*
  and *pre-writing code inline* (violating its own YAGNI / "don't self-code" rules).
- **Measurement artifact:** a long injected prompt reads as "over-engineering" to a
  minimalism rubric; the baseline was already near-ceiling (delegate 96%), leaving
  only downside; single judge, imperfect blinding, no length-matched placebo.

### 3-arm — the skill did **not** beat "just use a Workflow"

| Arm | rubric quality* | avg parallel units | planted-lie detection |
|-----|:--------------:|:------------------:|:---------------------:|
| opusplan | 35% | 2.44 | 56% |
| plain Workflow | **86%** | 3.97 | 100% |
| sommelier skill | 80% | 4.63 | 100% |

\* *Quality here is graded against the orchestrator's own doctrine (delegate,
tiers, no-self-code), which structurally penalizes the plan-then-execute arm for
behaving as designed. Treat the quality column as **descriptive, not probative.***

**Plain ≈ sommelier.** Telling Claude to use a dynamic Workflow does most of the
work; the skill adds no measured advantage over that on these metrics (and slightly
trails on the doctrine rubric).

---

## Retracted: the "faster / cheaper" claim

An earlier draft of this repo claimed the sommelier shape is *more efficient* than
opusplan, with modeled cost/latency indices. **We retract those numbers.** The Opus
critic showed they were tautological:

- `modeled_wallclock_index` was exactly `1 / parallel_units` — i.e. it *assumed*
  perfect linear speedup with zero coordination/gate overhead (Amdahl ignored).
- `modeled_cost_index` was a fixed linear function of tier-diversity with opusplan
  pinned at `1.0` — the cost ranking was baked in by definition.

**No tokens and no wall-clock were ever measured.** Any wider fan-out "wins" those
indices by construction. Until we measure real per-tier token counts at real prices
and real critical-path time, this repo makes **no efficiency claim.**

---

## Round 2 — tightened skill, paired vs a length-matched placebo (n=48, the decisive test)

After Round 1, the skill was tightened with explicit guardrails (no inline code, no
speculative infra, re-measure reported numbers, list-files-don't-claim). Round 2 gave
it the fairest possible test: **paired** (same task to all arms), a **length-matched
placebo** arm (generic senior-engineering advice of similar length — so we measure the
skill's *content*, not just the fact that it adds text), **ground-truth probes only**,
and **Wilson 95% CIs**.

| Probe (success = good behavior) | no-skill | placebo | tightened skill | n | skill vs placebo |
|---|:--:|:--:|:--:|:--:|:--|
| planted-lie re-measured | 52% | 52% | 57% `[36–76]` | 21 | overlaps — nominally *worse* is within noise |
| file-conflict avoided | 67% | 67% | 42% `[19–68]` | 12 | overlaps — skill **nominally worse** |
| YAGNI-bait refused | 7% | 7% | 20% `[7–45]` | 15 | overlaps — rides on k=3/15 |
| no inline code in plan | 98% | 98% | 100% `[93–100]` | 48 | ceiling — no headroom |

**Verdict (Opus critic, adopted): zero probes reach significance over the
length-matched placebo. Every Wilson CI overlaps.** On planted-lie detection and
file-conflict avoidance the skill is *nominally worse* than the controls; the one
nominal gain (YAGNI, 7%→20%) rests on 3 of 15 and could be a coin-flip. The most
defensible reading: **the skill's measurable effect is indistinguishable from adding
generic length-matched text.**

Two honest asides:
- **The file-conflict result is instructive, not just null.** The skill *pushes for
  parallelism*, which can *introduce* a shared-file conflict that a plain sequential
  plan never creates — the guardrail we added didn't fully counter it. A pro-parallel
  skill has to work harder to stay conflict-safe than a plan that just goes serial.
- **Measurement caveat:** the no-skill and placebo arms scored *byte-identical* on all
  four probes — implausible for truly independent runs, and a sign the probes (LLM-
  judged, on plan *text*) may not be resolving real variance. Treat all of the above
  as "no demonstrated effect," not "proven no effect."

### What this means

Across **three** studies the conclusion is consistent: **we cannot show this skill
beats a length-matched placebo — or even just framing the task as "you are an
orchestrator."** The single real signal (orchestrate-and-verify catches planted errors
that a single-pass plan misses) is **not specific to this skill** — plain generic
advice reproduces it. These probes also grade *what a plan says*, not *what an agent
does at execution time*, where a real efficiency effect (if any) would live — and we
have **not** measured that.

**So this repo makes no efficacy claim.** It ships as an *opinionated discipline* —
a checklist that encodes verification-gated, file-scoped, tier-paired orchestration —
whose value is argued, not proven. If that honesty isn't worth it to you, don't
install it. That, too, is YAGNI.

## Methodology & threats to validity

- **Responders:** Claude Haiku. **Judges:** Claude Sonnet (structured rubric).
  **Critics:** Claude Opus, prompted to refute.
- **Blinding:** A/B swapped presentation order per cycle; but a single judge and
  no inter-rater/human check means residual arm-identification bias is possible.
- **Category mismatch:** this skill targets *large multi-agent* orchestration; we
  probed it via *single-shot prose planning* on a small model. That likely
  under-measures its real setting and over-measures verbosity penalties.
- **No CIs / significance tests.** At n=100 binary, SE ≈ ±5pts; the only Δ that
  clearly exceeds noise are the A/B negatives and the planted-error gap.
- **Conflict of interest:** the skill was authored and the study run by the same
  party. Read accordingly.

## What would make a real claim (roadmap)

1. Measure real tokens/latency from logs; price per tier; critical-path time.
2. Amdahl-aware cost/time model, calibrated against measured values.
3. Outcome-anchored grading (task correctness + planted-error detection), not
   doctrine adherence.
4. Paired, blinded, powered design: same task/planted set to all arms, ≥2 judges +
   human audit, pre-registered rubric, Wilson CIs, McNemar / mixed-effects.

Until then, the honest headline stands: **verification gates catch errors that a
single-pass plan misses; everything else is unproven.**

*Raw run artifacts: A/B `wf_fb321d80-660`, 3-arm `wf_0a82d1ee-30a` (301 + 193
agents, ~9.2M subagent tokens).*
