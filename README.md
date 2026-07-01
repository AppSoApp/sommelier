<div align="center">

# 🍷 sommelier

**She cooks nothing. She composes the pairing, tastes every pour, and sends back what's corked.**

*An orchestration skill for Claude that turns a vague "build / refactor / migrate X" into a PRD +
file-scoped parallel tickets — and refuses to trust a number it hasn't re-measured itself.*

[![license](https://img.shields.io/badge/license-MIT-black)](./LICENSE)
[![skill](https://img.shields.io/badge/type-Agent%20Skill-7b1e3a)](./sommelier-pairing/SKILL.md)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-7b1e3a)](https://claude.com/claude-code)
[![benchmarks](https://img.shields.io/badge/benchmarks-honest-c9a227)](./BENCHMARKS.md)
[![stars](https://img.shields.io/github/stars/AppSoApp/sommelier?style=social)](https://github.com/AppSoApp/sommelier)

</div>

---

> **Honesty first.** This skill's second rule is *"never believe a report — re-measure it."*
> So we held ourselves to it: every number below is measured, and the parts where the skill
> **lost** are published too, in [`BENCHMARKS.md`](./BENCHMARKS.md). No inflated stats.

## What actually held up in testing

| Claim | Evidence | Status |
|-------|----------|:------:|
| **Catches planted false numbers a single-pass plan misses** — 100% vs ~56% | 3-arm study, 18 planted-lie cycles | ✅ measured *(needs paired re-run)* |
| A plan is **file-scoped tickets, not prose** | definitional — the ticket contract | ✅ by design |
| Pairs each task to the **cheapest model tier that passes** | definitional — tier-per-ticket | ✅ by design |
| ~~Faster / cheaper than a single Opus plan~~ | modeled indices were tautological | ❌ **retracted** |
| Beats a plain *"just use a Workflow"* instruction | plain ≈ sommelier (86% vs 80%) | ⚠️ **not shown** |

The honest headline: **the value is the verification gate, not the branding.** Read the full,
un-spun results → [`BENCHMARKS.md`](./BENCHMARKS.md).

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

## Before / after

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

## Benchmark (the one that survived scrutiny)

```
Planted false-number detection — share of "the report says 0 imports" cycles the plan re-measures

opusplan  (single serial plan)  ███████████████████████████░░░░░░░░░░░░░░░░  56%
plain     (just use a Workflow) ███████████████████████████████████████████ 100%
sommelier (this skill)          ███████████████████████████████████████████ 100%
                                n = 18 planted cycles · Haiku responders · Sonnet judge · not yet paired/CI'd
```

This shows *orchestrate-and-verify* beats *plan-then-execute*. It does **not** show the skill beats
plain orchestration (they tie). Everything — including the A/B where the skill scored **worse** — is
in [`BENCHMARKS.md`](./BENCHMARKS.md). We publish the losses on purpose.

## The two skills

| Skill | Model tiers | Use it when |
|-------|-------------|-------------|
| [`sommelier-pairing`](./sommelier-pairing/SKILL.md) | **generalized** (mid / top / cheapest) | You want the pairing portable across any cellar. |
| [`sommelier-pairing-tiers`](./sommelier-pairing-tiers/SKILL.md) | **pinned** (Sonnet pours / Opus tastes / Haiku serves bread) | You run a fleet on concrete Claude tiers. |

Both dispatch by tier **alias** (`'sonnet'` / `'opus'` / `'haiku'`), so the pour always resolves to
the latest bottle in that tier — no chasing version bumps.

## When NOT to use it

A single-file change or a one-line fix. **YAGNI** — just do it. A fleet is for tasks too big to hold
in one context, or where a report's numbers decide the plan and could be wrong.

## Install

```bash
# Claude Code (personal skills)
git clone https://github.com/AppSoApp/sommelier.git
cp -r sommelier/sommelier-pairing ~/.claude/skills/
```

The agent loads a skill by its `description` when the task matches — see each `SKILL.md` for triggers.

## Credits

`sommelier` is a pairing, and says so. The bottles belong to the people who filled the cellar
(Karpathy, the YAGNI tradition, and everyone who's argued that a report is a claim until you've
re-poured the number yourself). Margaux just knows what goes with what.

## License

[MIT](./LICENSE)
