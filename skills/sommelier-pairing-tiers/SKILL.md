---
name: sommelier-pairing-tiers
description: Use when running a concrete Claude fleet — a long-lived Opus orchestrator dispatching Sonnet implementers across model-tier aliases inside a dynamic workflow, with worktree isolation and evidence+APPROVE gates. The tier-pinned companion to sommelier-pairing. Triggers include "team-start", "dispatch the fleet", "worktree isolation", "Team Manager", and running ~50 tickets across Claude tiers.
---

# Sommelier: Pairing — Tier-Pinned

Same three moves and guardrails as **`sommelier-pairing`** — read that skill first;
everything about DESIGN, DON'T SETTLE (falsify claims, fix on REFUTED), and the
"don't build on unverified code" rule applies here unchanged. This companion only
pins the **concrete Claude tiers** for a Team-Manager–style fleet.

## Tier aliases (dispatch mechanism)

Dispatch by **alias**, never a pinned version — the alias resolves to the session's
latest model of that tier, so you never chase version bumps.

| Ticket kind | Alias | Why |
|-------------|-------|-----|
| Spec-faithful implementation | `'sonnet'` | Mechanical, contract-faithful, fast. |
| High-risk gate — RBAC, payments, security, audit, invariants | `'opus'` + `superpowers:code-reviewer` | Protects invariants; APPROVE required pre-merge. |
| Cheap mechanical — rename, move, format, scaffold | `'haiku'` | No judgment needed. |
| Orchestration, sequencing, merge | `'opus'` (Manager) | Never delegated. |

In a workflow: `agent({model:'sonnet'})` / `{model:'opus'}` / `{model:'haiku'}`.
Cheapest tier that still passes the gate. Scale fan-out to budget, not agent depth.

## Dynamic workflow shape

```
PRD (frozen)
  └─ Foundation                              [opus]
     └─ ~50 parallel implementer tickets      [sonnet, file-owner-disjoint]  ── worktree isolation on overlap
        └─ gate: re-measure metric [verifier] + code-reviewer APPROVE       [opus]
           └─ completeness critic (loop-until-dry)                          [opus]
              └─ Manager merges evidence+APPROVE only; tsc/test; per-feature commit [opus]
```

## Team-Manager integration (optional)

- State lives in one append-only journal; no other state files.
- Worker completion is fire-and-forget; evidence-schema validation + audit run in background.
- Merge only work with both re-measured evidence and an APPROVE audit verdict.
- Decision tiers: LOW = autonomous, MEDIUM = hold/escalate, HIGH = stop.

*Honest evaluation of this skill — including where it lost — is in
[`BENCHMARKS.md`](../../BENCHMARKS.md).*
