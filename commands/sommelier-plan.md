---
description: Turn a large task into a sommelier plan — a PRD plus file-scoped parallel tickets, each with a contract, a re-measured success metric, and a model tier. Does not write code.
argument-hint: <the task to plan, e.g. "migrate off the legacy auth-core module">
---

You are the orchestrator. **Do not write any implementation code.** Produce a plan for the task below, following the `sommelier-pairing` discipline exactly.

Task: $ARGUMENTS

Output, in this order:

1. **PRD (frozen)** — one paragraph: the single contract this work delivers, and what is explicitly out of scope (YAGNI — nothing the task didn't ask for).

2. **Verification tickets first** — if the task rests on any claim that code already works (a reported number like "0 imports"/"1,240 tests", OR a "certified"/"tested"/"reviewed" label), the FIRST ticket re-runs the check on boundary inputs. A label is a claim, not evidence; on REFUTED the ticket fixes the code in the same change. No later ticket may depend on a module still marked unverified.

3. **Tickets** — a table where every ticket has all four fields and NO code:
   | # | Files owned (exact) | Single contract | Success metric (re-measured at gate) | Tier |
   List each ticket's exact files and check no file name appears in two tickets. If two changes touch the same file, that is ONE ticket with one owner, not two parallel ones. Mark which tickets can run in parallel (disjoint files) vs must be sequenced.

4. **Tiers** — `'haiku'` for mechanical work, `'sonnet'` for spec-faithful implementation, `'opus'` for high-risk gates (RBAC/payments/security/audit) and for orchestration/merge. Cheapest tier that still passes the gate.

5. **Gate** — the merge rule: re-measured evidence AND an APPROVE review, or hold.

Keep it minimal. If the task is a single-file or one-line change, say so and recommend just doing it directly (a fleet here is over-engineering).

For the full discipline and its honest evaluation, this command mirrors the `sommelier-pairing` skill; see `BENCHMARKS.md` in the plugin for what is and isn't proven.
