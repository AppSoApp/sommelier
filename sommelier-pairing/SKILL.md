---
name: sommelier-pairing
description: Use when a task is large enough to need more than one implementer — turning a vague "build/refactor/migrate X" into a PRD plus many file-scoped parallel tickets, dispatching them across model tiers, and gating merges on re-measured evidence rather than self-reported success. Triggers include "plan this", "break this down", "50 tickets", "parallel agents", "orchestrate", multi-file migrations, and audits where reports can't be trusted.
---

# Sommelier: Pairing (Parallel Development Orchestration)

## Overview

A meta-skill for the orchestrator (the long-lived planner) — **never write code yourself; decompose, dispatch, and gate.** Three moves, in order:

1. **DESIGN (Tekton)** — freeze one PRD, shatter it into ~N file-scoped tickets.
2. **DON'T SETTLE (Sim Francisco)** — trust no report; re-measure every claim; run a completeness critic before declaring done.
3. **DELEGATE (Custom Universe)** — put a model tier on every ticket; the cheapest model that can pass the gate.

Grounded in two constraints that override everything below:
- **YAGNI** — build only what THIS task asks. No speculative abstraction, no "future-proof" branches, no provider indirection for a single provider.
- **Karpathy minimalism** — simplest working baseline first, verify empirically (measure, don't guess), avoid early optimization. *The best code is the code you don't write.*

## When to Use

- A request needs 2+ independent implementers, or spans many files/modules.
- A migration, audit, or sweep too large to hold in one context.
- Any place where an agent's or a report's **numbers** decide the plan — and could be wrong.

**When NOT to use:** a single-file change, a one-line fix, or a conversational answer. Just do it.

## Move 1 — DESIGN (Tekton): PRD → file-scoped tickets

The deliverable of planning is **not a prose plan**. It is a PRD plus a set of tickets that a fleet can execute in parallel with zero coordination.

Every ticket is a **contract**, and must carry all four fields:

| Field | Rule |
|-------|------|
| **File ownership** | The exact files this ticket may write. No two tickets share a writable file → no merge conflicts, safe parallelism. |
| **Single contract** | One interface/behavior this ticket delivers, stated so another ticket can depend on it without reading the code. |
| **Success metric** | A number or check that will be **re-measured** at the gate (e.g. "PR handling time ↓ X%", "0 imports of legacy module", "tsc clean"). Not "looks done". |
| **Model tier** | Which tier implements it (see Move 3). |

Sequence: **PRD (single contract, frozen) → Foundation ticket(s) first → parallel implementer tickets (file-owner–disjoint) → gate → merge.** Freeze the PRD before dispatch; a moving contract breaks every worker downstream.

## Move 2 — DON'T SETTLE (Sim Francisco): re-measure, then critic

**Never believe a report.** When a ticket (or a prior investigation) claims "290KB, 7000 lines, 0 imports", an independent verifier re-runs the measurement and returns a verdict:

- **VERIFIED** — reproduced the number.
- **REFUTED** — the claim is false; reopen the ticket.
- **PARTIAL** — partially true; scope the gap into a follow-up ticket.

Then one **completeness critic** pass over the whole result set — adversarially hunt for *what was skipped*: a claim never verified, a file never read, an edge case dropped, a metric quietly relaxed. What it finds becomes the next round. Loop until a round finds nothing new (loop-until-dry), not until you're tired.

Merge only when **both** hold: evidence (the success metric, re-measured) AND an APPROVE verdict from the review gate. Missing either → hold, don't merge.

## Move 3 — DELEGATE (Custom Universe): a tier per ticket

The orchestrator chooses the model, not just the task. Match tier to the ticket's risk and mechanical-ness:

| Ticket kind | Tier | Why |
|-------------|------|-----|
| Spec-faithful implementation | **Mid tier** | Fast, mechanical, follows the contract. |
| High-risk gate (RBAC, payments, security, audit, invariants) | **Top tier** | Protects invariants; APPROVE required before merge. |
| Cheap mechanical work (rename, move, format, scaffold) | **Cheapest tier** | No judgment needed. |
| Orchestration / sequencing / merge decisions | **Top tier (you)** | Never delegated. |

Rule of thumb: **the cheapest tier that can still pass the gate.** Scale the fan-out to the budget — more budget buys more parallel finders/verifiers, not deeper single agents.

## Putting it together (dynamic workflow)

Drive the whole thing as **one dynamic workflow**, not a chain of one-off dispatches:

```
PRD (frozen contract)
  └─ Foundation ticket(s)                     [top tier]
     └─ parallel implementer tickets          [mid tier, file-owner-disjoint]  ── worktree isolation if writers overlap
        └─ per-ticket gate: re-measure metric [verifier]  +  review APPROVE     [top tier]
           └─ completeness critic (loop-until-dry)        [top tier]
              └─ orchestrator merges evidence+APPROVE only, commits per feature [you]
```

## Why this is an efficient way to drive Claude's dynamic Workflow

This skill is not just "a plan" — it is a **shape for Claude's dynamic Workflow tool**.
The four-field ticket exists precisely so the Workflow can fan work out safely:

- **Disjoint file ownership → real parallelism.** Because no two tickets write the
  same file, implementer agents run concurrently with zero coordination
  (`pipeline`/`parallel`) instead of one long serial pass. Wall-clock collapses to
  the slowest single ticket, not the sum of all tickets.
- **Tier-per-ticket → cheap tokens.** Mechanical tickets go to the cheapest tier,
  only gates ride the top tier. You buy breadth (more parallel finders/verifiers)
  instead of depth (one expensive agent thinking longer).
- **Evidence gate → no wasted re-work.** Fire-and-forget workers; validation runs
  in the background and only evidence+APPROVE merges. Bad work is caught at the
  gate, not after it has polluted downstream tickets.

### vs. a single Opus plan (opusplan) — by design, not by measured win

A one-shot "Opus plans, then executes" pass is **serial and un-gated** by
construction: one context holds the whole task and self-reports "done". The
sommelier shape differs *structurally* on these axes:

| Axis | Single Opus plan (opusplan) | Sommelier dynamic workflow |
|------|------------------------------|-----------------------------|
| **Concurrency** | Serial — one context, one thread | Parallel — N disjoint tickets at once |
| **Token cost** | Everything at top tier | Cheapest tier per ticket; top tier only for gates |
| **Trust model** | Self-reported "done" | Independent re-measure + APPROVE gate |
| **Context limit** | Whole task must fit one context | Sharded across contexts; scales past one window |
| **Failure blast radius** | A wrong step contaminates the rest | Caught at the per-ticket gate |

These are **architectural differences, not proven efficiency gains.** An honest
100-cycle A/B and a 3-arm study found the effect is *not* a clean win — the skill
did **not** beat a plain "just use a Workflow" instruction, and the modeled
cost/latency numbers turned out to be tautological (retracted). The **one**
ground-truth signal that held up: a single-pass plan caught far fewer *planted
false numbers* than any orchestrated, verifying arm (~56% vs 100%) — i.e. the
value is in the **verification gate**, not in fanning out per se. Read the full,
un-spun results — including the negative ones — in [`BENCHMARKS.md`](../BENCHMARKS.md).

## Additional patterns worth adding

- **File-ownership lock as the parallelism primitive.** Disjoint writable-file sets are what *make* 50 agents safe. Compute them before dispatch; if two tickets want the same file, split or serialize them.
- **Evidence-gated merge.** A merge needs a re-measured metric + APPROVE. Fire-and-forget the worker; validate its evidence in the background.
- **Budget-scaled fan-out.** `finders = floor(budget / cost_per_agent)`. Log what you dropped — silent truncation reads as "covered everything" when it wasn't.
- **Worktree isolation** only when parallel writers would actually collide — it costs setup + disk, so don't pay for it otherwise (YAGNI).
- **Numbers are claims, not facts.** Every KB / line-count / "0 usages" in a report is a hypothesis until an independent agent reproduces it.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Prose plan instead of file-scoped tickets | Emit contracts with all four fields, or the fleet can't run parallel. |
| Two tickets writing the same file | Recompute file ownership; make sets disjoint. |
| Trusting a worker's "done" | Re-measure the success metric independently before merge. |
| Stopping at first pass | Run the completeness critic; loop-until-dry. |
| Everything on the top tier | Push mechanical work down; reserve top tier for gates + orchestration. |
| Abstraction "for later" | YAGNI. Delete it. Simplest baseline that passes the gate. |
