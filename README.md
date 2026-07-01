<div align="center">

<img src="./assets/logo.svg" alt="sommelier" width="360">

# 🍷 sommelier

**She cooks nothing. She composes the pairing, tastes every pour, and sends back what's corked.**

*An orchestration skill for Claude that turns a vague "build / refactor / migrate X" into a PRD +
file-scoped parallel tickets — and refuses to trust a number it hasn't re-measured itself.*

[![license](https://img.shields.io/badge/license-MIT-black)](./LICENSE)
[![skill](https://img.shields.io/badge/type-Agent%20Skill-7b1e3a)](./skills/sommelier-pairing/SKILL.md)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-7b1e3a)](https://claude.com/claude-code)
[![benchmarks](https://img.shields.io/badge/benchmarks-honest-c9a227)](./BENCHMARKS.md)
[![stars](https://img.shields.io/github/stars/AppSoApp/sommelier?style=social)](https://github.com/AppSoApp/sommelier)

</div>

---

> **Honesty first.** This skill's second rule is *"never believe a report — re-measure it."*
> So we held ourselves to it: every number below is measured, and the parts where the skill
> **lost** are published too, in [`BENCHMARKS.md`](./BENCHMARKS.md). No inflated stats.

## What actually held up in testing

We ran four studies — three plan-text nulls and a **pre-registered, hidden-pytest
execution test** that found one real win. Every round (wins and losses) is published.
Here is the honest scorecard:

| Claim | Verdict |
|-------|:-------:|
| A plan is **file-scoped tickets, not prose** — a checkable contract per unit | ✅ by design |
| Pairs each task to the **cheapest model tier that passes** | ✅ by design |
| **Orchestrate-and-verify catches planted errors a single-pass plan misses** | ✅ plan-level only — **not specific to this skill**, and **0% in execution** (Round 3) |
| Catches a bug hidden behind an authority label (`# CERTIFIED`) | ✅ **v1.1 win** — the rewritten verify rule lifts bug-fix 0%→**29%** (haiku)/**44%** (sonnet) vs a length-matched placebo, McNemar **p ≤ 10⁻⁴**, pre-registered, hidden-pytest (Round 4) |
| Beats a plain *"just use a Workflow"* / *"you are an orchestrator"* on *planning* | ❌ **not shown** (every CI overlaps the control) |
| Beats a **length-matched placebo** on *plan-text* probes | ❌ **not shown** (the win above is on executed code, not plan text) |
| ~~Faster / cheaper than a single Opus plan~~ | ❌ **retracted** (modeled indices were tautological) |

**One proven win, the rest argued.** `sommelier` ships as an *opinionated discipline* —
a checklist encoding verification-gated, file-scoped, tier-paired orchestration. After
four rounds of self-testing, exactly **one** claim beat a length-matched placebo under a
pre-registered, mechanically-graded test: the **verification rule** (catching a bug behind
a `# CERTIFIED` label, 0%→29–44%, p ≤ 10⁻⁴). The orchestration, tier, and speed claims
remain **argued, not proven** — and we publish every round, including the three where the
skill lost → [`BENCHMARKS.md`](./BENCHMARKS.md).

---

## Meet the host

[**Margaux** 🍷](./CHARACTER.md) is a sommelier. She never touches a pan. Her whole craft is three
moves: **compose the pairing, taste every pour, match the right bottle to the right plate.** The
kitchen cooks; Margaux decides what belongs together and whether it's good enough to leave the cellar.

That *is* the orchestrator's job: it never writes code — it **pairs** (which model runs which
ticket), **tastes** (re-measures every claim), and **composes the flight** (the PRD and its tickets).

## The three pours

| Move | Codename | On the card |
|------|----------|-------------|
| ① **Design** | **Tekton** | Compose the flight first. The plan is a PRD + file-scoped tickets, not prose. Each ticket = file ownership + single contract + success metric + model tier. Disjoint files = no two pours fight over one glass. |
| ② **Don't settle** | **Sim Francisco** | The label means nothing — taste every pour. Re-measure every number → `VERIFIED / REFUTED / PARTIAL`. Then a completeness pass down the table, until nothing goes out unchecked. |
| ③ **Delegate** | **Custom Universe** | Pairing is the whole art. Put a model tier on every ticket — the humblest bottle that still passes the taste. |

Grounded in two borrowed bottles: **YAGNI** (build only what *this* task asks) and **Karpathy
minimalism** (simplest working baseline, measure don't guess — *the best code is the code you
don't write*).

## What the discipline looks like

*Illustrative, not a measured win (see the scorecard above) — this is the shape the skill asks for:*

```
Task: "Migrate off the legacy auth-core module. A report says it's 290KB, 7000 lines, 0 imports."

  ✗  opusplan (single serial plan)
     "I'll trust the report: 0 imports, so I'll delete it and rewire the 3 call sites…"
     → serial, self-reported done, and it believed a number nobody re-checked.

  ✓  sommelier
     Ticket 0  [verify]  re-run the import count yourself → VERIFIED / REFUTED / PARTIAL
     Ticket 1  [own: src/auth/*.ts]      swap adapter    metric: 0 legacy imports (re-measured)
     Ticket 2  [own: src/session/*.ts]   migrate store   metric: tsc clean
     …disjoint files → run in parallel · cheapest tier per ticket · merge only on evidence+APPROVE
```

## Benchmark (the honest one)

The fairest test we ran — a **paired n=48 study with a length-matched placebo**, planted-lie
detection probe, Wilson 95% CIs. Every interval overlaps:

```
Planted false-number detection (paired, n=21 on this probe, Wilson 95% CI)

length-matched placebo   52%   [31–73]  ─┐  CIs fully overlap
sommelier (this skill)   57%   [36–76]  ─┘  → +5pt is NOT significant
```

The skill beat the placebo on **zero** ground-truth probes, and in a later
**mechanically-graded execution test** (hidden pytest, no LLM judge) **no arm — skill included —
fixed a bug hidden behind a `# CERTIFIED correct` comment (0%)**. We publish the losses on
purpose. Full numbers across all three rounds, with the study where the skill scored *worse*, are
in [`BENCHMARKS.md`](./BENCHMARKS.md). *(No arm is relabeled or composited across studies.)*

## The two skills

| Skill | Model tiers | Use it when |
|-------|-------------|-------------|
| [`sommelier-pairing`](./skills/sommelier-pairing/SKILL.md) | **generalized** (mid / top / cheapest) | You want the pairing portable across any cellar. |
| [`sommelier-pairing-tiers`](./skills/sommelier-pairing-tiers/SKILL.md) | **pinned** (Sonnet pours / Opus tastes / Haiku serves bread) | You run a fleet on concrete Claude tiers. |

Both dispatch by tier **alias** (`'sonnet'` / `'opus'` / `'haiku'`), so the pour always resolves to
the latest bottle in that tier — no chasing version bumps.

## Command

The plugin also ships a slash command for a one-shot plan (no code, just the tickets):

```
/sommelier-plan migrate off the legacy auth-core module
```

It returns a frozen PRD + file-scoped tickets (contract · re-measured metric · tier) following the
`sommelier-pairing` discipline.

## When NOT to use it

A single-file change or a one-line fix. **YAGNI** — just do it. A fleet is for tasks too big to hold
in one context, or where a report's numbers decide the plan and could be wrong.

## Install

**As a Claude Code plugin (recommended).** This repo is both a plugin and a marketplace:

```
/plugin marketplace add AppSoApp/sommelier
/plugin install sommelier@appsoapp
```

Both skills and the `/sommelier-plan` command come bundled and are auto-discovered —
the skills are namespaced `sommelier:sommelier-pairing` and `sommelier:sommelier-pairing-tiers`.

**Or drop the skills in manually:**

```bash
git clone https://github.com/AppSoApp/sommelier.git
cp -r sommelier/skills/sommelier-pairing        ~/.claude/skills/
cp -r sommelier/skills/sommelier-pairing-tiers  ~/.claude/skills/
```

The agent loads a skill by its `description` when the task matches — see each `SKILL.md` for triggers.

## Credits

`sommelier` is a pairing, and says so. The bottles belong to the people who filled the cellar
(Karpathy, the YAGNI tradition, and everyone who's argued that a report is a claim until you've
re-poured the number yourself). Margaux just knows what goes with what.

## License

[MIT](./LICENSE)
