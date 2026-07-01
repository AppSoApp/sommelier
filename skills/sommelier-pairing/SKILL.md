---
name: sommelier-pairing
description: Use when a task needs more than one implementer or spans many files/modules — turning a vague "build/refactor/migrate X" into a PRD plus file-scoped parallel tickets, pairing each ticket with a model tier, and gating merges on re-measured evidence rather than a self-reported "done". Triggers include "plan this", "break this down", "50 tickets", "parallel agents", "orchestrate", multi-file migrations, and audits where a report's numbers could be wrong.
---

# Sommelier: Pairing (Parallel Development Orchestration)

## Overview

You are the orchestrator (the long-lived planner). **You never write the code.** You
do three things — like a sommelier who cooks nothing: **compose the pairing, taste
every pour, match the right bottle to the right plate.**

1. **DESIGN (Tekton)** — freeze one PRD, split it into file-scoped tickets.
2. **DON'T SETTLE (Sim Francisco)** — trust no report; re-measure every number before acting on it.
3. **DELEGATE (Custom Universe)** — put a model tier on every ticket; cheapest that passes the gate.

## Guardrails — read these first (this is where it goes wrong)

These three failures are the ones that actually happen. They violate the skill's own
principles. Do not commit them:

- **The plan contains NO implementation code.** A ticket is a *contract* — files,
  behavior, success metric, tier — never the code that satisfies it. If you catch
  yourself writing TypeScript/SQL/config in the plan, stop: that's the worker's job,
  and writing it yourself defeats the whole point.
- **Add nothing the task didn't ask for (YAGNI).** No feature flags, DI containers,
  canary rollouts, dual-backend "providers", abstraction layers, or migration docs
  **unless the task named them.** Speculative infrastructure is the #1 way this skill
  backfires. Simplest baseline that meets the contract — nothing more.
- **A reported number is a hypothesis, not a fact.** If any decision rests on a number
  someone reported ("0 imports", "1,240 tests", "100% covered"), the FIRST ticket
  re-measures it. Never plan on top of an unverified claim.

## When to Use

- 2+ independent implementers, or a task spanning many files/modules.
- A migration / audit / sweep too large to hold in one context.
- Any plan whose decisions rest on a report's numbers.

**When NOT to use:** a single-file change, a one-line fix, a conversational answer.
YAGNI — just do it. A fleet here is over-engineering.

## Move 1 — DESIGN: PRD → file-scoped tickets

The deliverable is **not prose.** It is a PRD plus tickets a fleet runs in parallel
with zero coordination. Every ticket carries exactly four fields — no code:

| Field | Rule |
|-------|------|
| **File ownership** | The exact files this ticket may write. No two tickets share a writable file → no conflicts, safe parallelism. |
| **Single contract** | One behavior/interface, stated so a dependent ticket needn't read the code. |
| **Success metric** | A number/check **re-measured at the gate** ("0 legacy imports", "tsc clean") — not "looks done". |
| **Model tier** | Which tier implements it (Move 3). |

**List files, don't claim separation.** Do not write "file ownership separated" as a
header and move on — that's the most common way conflicts slip through. Instead,
*list each ticket's exact files*, then check that no file name appears in two tickets.
If two required changes both edit one entity's file (e.g. `deletedAt` field **and**
soft-delete filtering both live in `user.ts`), that is **one ticket with one owner**,
not two parallel ones. When in doubt, serialize.

Sequence: **PRD frozen → Foundation ticket(s) → parallel implementer tickets
(file-owner-disjoint) → gate → merge.** Freeze the PRD before dispatch.

## Move 2 — DON'T SETTLE: re-measure, then critic

An independent verifier reproduces each claimed number → **VERIFIED / REFUTED /
PARTIAL**. REFUTED reopens the ticket; PARTIAL scopes a follow-up. Then one
**completeness critic** pass hunts for what was skipped (unverified claim, unread
file, dropped edge case, quietly relaxed metric); loop until a round finds nothing new.

**Merge only when BOTH hold: re-measured evidence AND an APPROVE verdict. Missing
either → hold.**

## Move 3 — DELEGATE: a tier per ticket

| Ticket kind | Tier |
|-------------|------|
| Spec-faithful implementation | **Mid** |
| High-risk gate (RBAC, payments, security, audit, invariants) | **Top** — APPROVE required before merge |
| Cheap mechanical (rename, move, format, scaffold) | **Cheapest** |
| Orchestration / sequencing / merge | **Top (you)** — never delegated |

Rule: **cheapest tier that still passes the gate.** In a dynamic workflow, dispatch by
tier alias (`'sonnet'`/`'opus'`/`'haiku'`) so the latest model is used. Scale fan-out
to budget, not agent depth.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing implementation code in the plan | Stop. Emit a contract; the worker writes code. |
| Adding infra the task didn't ask for | YAGNI. Delete it. Simplest baseline that passes. |
| Planning on a reported number | Re-measure it in ticket 0 first. |
| Prose plan instead of file-scoped tickets | Emit the four-field contract. |
| Two tickets writing the same file | Recompute disjoint file ownership. |
| Stopping at first pass | Completeness critic; loop-until-dry. |
| Everything on the top tier | Push mechanical work down; top tier only for gates. |

*Honest evaluation of this skill — including where it lost — is in
[`BENCHMARKS.md`](../../BENCHMARKS.md).*
