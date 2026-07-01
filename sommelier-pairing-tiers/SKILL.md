---
name: sommelier-pairing-tiers
description: Use when a long-lived orchestrator (Team Manager) must turn a large "build/refactor/migrate X" into a PRD plus ~50 file-scoped parallel tickets, dispatch them across concrete Claude model tiers (Sonnet implement / Opus gate / Haiku mechanical), and gate merges on re-measured evidence plus an APPROVE verdict. This is the tier-pinned variant of sommelier-pairing. Triggers: "plan this", "break down", "50 tickets", "dispatch", "team-start", multi-file migrations, report-can't-be-trusted audits.
---

# Sommelier: Pairing — Tier-Pinned

## Overview

The tier-pinned sibling of `sommelier-pairing`. Same three moves — **DESIGN (Tekton) → DON'T SETTLE (Sim Francisco) → DELEGATE (Custom Universe)** — but with concrete Claude model tiers wired in, for a Team-Manager–style autonomous fleet.

The orchestrator is **Opus, long-lived. It never writes code.** It decomposes, dispatches Sonnet implementers inside a dynamic workflow, and gates merges. Bound by **YAGNI** (build only what's asked) and **Karpathy minimalism** (simplest working baseline, measure don't guess — *the best code is the code you don't write*).

## Guardrails — read these first (this is where it goes wrong)

- **The plan contains NO implementation code.** A ticket is a contract (files +
  behavior + metric + tier), never the code that satisfies it. Writing it yourself
  defeats the point — that's the Sonnet worker's job.
- **Add nothing the task didn't ask for (YAGNI).** No feature flags, DI containers,
  canary rollouts, dual-backend providers, or migration docs unless the task named
  them. Speculative infrastructure is the #1 way this backfires.
- **A reported number is a hypothesis, not a fact.** If a decision rests on a reported
  number, the FIRST ticket re-measures it before anyone plans on top of it.

## When to Use

- A request needs a fleet of implementers or spans many files/modules.
- A migration/audit/sweep too large for one context.
- Any plan whose decisions rest on numbers a report supplied — which must be re-measured.

**When NOT to use:** single-file or one-line changes, or conversational answers. Do those directly.

## Move 1 — DESIGN (Tekton): PRD → ~50 file-scoped tickets

Planning outputs a **PRD + tickets**, not prose. Each ticket is a contract with four fields:

| Field | Rule |
|-------|------|
| **File ownership** | Exact writable files. Disjoint across tickets → no conflicts, safe parallel dispatch. |
| **Single contract** | One behavior/interface, stated so dependents needn't read the code. |
| **Success metric** | A number/check re-measured at the gate (e.g. "PR handling time ↓ X%", "0 legacy imports", "tsc/test clean"). |
| **Model tier** | Concrete tier below. |

**List each ticket's exact files and check no file appears twice — do not just claim "ownership separated" in a header** (that is how conflicts slip through). Two changes that both live in `user.ts` = one ticket, not two parallel ones.

Sequence: **PRD frozen → Foundation (Opus-designed) → parallel Sonnet implementers (file-owner-disjoint) → Opus+reviewer gate → Opus merge + tsc/test + per-feature commit.**

## Move 2 — DON'T SETTLE (Sim Francisco): re-measure, then critic

Trust no report. An independent verifier reproduces every claimed number and returns **VERIFIED / REFUTED / PARTIAL**. REFUTED reopens the ticket; PARTIAL spawns a scoped follow-up. Then one **completeness critic** pass hunts for what was skipped — unverified claim, unread file, dropped edge case, quietly relaxed metric — and loops until a round finds nothing new (loop-until-dry).

**Merge only with evidence (re-measured metric) AND an APPROVE verdict. Missing either → hold.**

## Move 3 — DELEGATE (Custom Universe): concrete Claude tiers

**Dispatch with the alias, not a pinned version.** In a workflow use
`agent({model:'sonnet'})` / `{model:'opus'}` / `{model:'haiku'}` — the alias
resolves to the session's latest model of that tier at runtime, so you never
chase version bumps. The concrete IDs below are a **snapshot (as of 2026-07)** for
reference only; they are not the dispatch mechanism and will go stale.

| Ticket kind | Tier alias | Snapshot ID (2026-07) | Why |
|-------------|-----------|-----------------------|-----|
| Spec-faithful implementation | `'sonnet'` | `claude-sonnet-4-6` | Mechanical, contract-faithful, fast. |
| High-risk gate — RBAC, payments, security, audit, invariants | `'opus'` + `superpowers:code-reviewer` | `claude-opus-4-8` | Protects invariants; APPROVE required pre-merge. |
| Cheap mechanical — rename, move, format, scaffold | `'haiku'` | `claude-haiku-4-5` | No judgment needed. |
| Orchestration, sequencing, merge | `'opus'` (Manager) | `claude-opus-4-8` | Never delegated. |

Cheapest tier that still passes the gate. Scale fan-out to budget, not agent depth.

## Dynamic workflow shape

```
PRD (frozen)
  └─ Foundation                              [Opus]
     └─ ~50 parallel implementer tickets      [Sonnet 4.6, file-owner-disjoint]  ── worktree isolation on overlap
        └─ gate: re-measure metric [verifier] + code-reviewer APPROVE           [Opus]
           └─ completeness critic (loop-until-dry)                              [Opus]
              └─ Manager merges evidence+APPROVE only; tsc/test; per-feature commit [Opus]
```

## Team-Manager integration (optional)

- State lives in one append-only journal; no other state files.
- Worker completion is fire-and-forget; evidence-schema validation + audit run in background.
- Merge only work with both evidence and an APPROVE audit verdict.
- Decision tiers: LOW = autonomous, MEDIUM = hold/escalate, HIGH = stop.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Prose plan, not file-scoped tickets | Emit four-field contracts. |
| Two tickets writing one file | Recompute disjoint file ownership. |
| Believing a worker's "done" | Re-measure the metric independently. |
| Stopping at first pass | Completeness critic, loop-until-dry. |
| Everything on Opus | Sonnet implements, Haiku does mechanical, Opus gates. |
| Abstraction "for later" | YAGNI — delete it. |
