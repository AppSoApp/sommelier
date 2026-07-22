---
description: Turn a large task into a sommelier plan — a PRD plus file-scoped parallel tickets, each with a contract, a re-measured success metric, and a model tier. Does not write code.
argument-hint: <the task to plan, e.g. "migrate off the legacy auth-core module">
---

You are the orchestrator. **Do not write any implementation code.** Produce a plan for the task below, following the `sommelier-pairing` discipline exactly.

Task: $ARGUMENTS

## Step 0 — escape hatch (check first, before any output section)

Keep it minimal.

- If $ARGUMENTS is empty, ask for the task and stop.
- If the task is a single-file or one-line change, output ONLY `No plan needed: <one-line recommendation>` and stop — a fleet here is over-engineering. If the change involves trusting a "certified"/"tested" claim, the one-line recommendation is to run the sommelier verify move on it.

Otherwise, output, in this order:

1. **PRD (frozen)** — one paragraph: the single contract this work delivers, and what is explicitly out of scope (YAGNI — nothing the task didn't ask for).

2. **Tickets** — a table where every ticket has all four fields and NO code, plus a "Depends on" column:
   | # | Files owned (exact) | Single contract | Success metric (re-measured at gate) | Tier | Depends on |
   List each ticket's exact files and check no file name appears in two tickets. If two changes touch the same file, that is ONE ticket with one owner, not two parallel ones. "Depends on" holds the ticket #(s) it must finish after, or "–" if it's parallel-ready — that column is the parallel/sequenced notation; nothing else marks it.

   Verification tickets come first: if the task rests on any claim that code already works (a reported number like "0 imports"/"1,240 tests", OR a "certified"/"tested"/"reviewed" label), the first row(s) of this table re-run the check on boundary inputs, contract prefixed `VERIFY:`. A label is a claim, not evidence; on REFUTED the ticket fixes the code in the same change. No later ticket may depend on a module still marked unverified.

3. **Tiers** — `'haiku'` for mechanical work, `'sonnet'` for spec-faithful implementation, `'opus'` for high-risk gates (RBAC/payments/security/audit) and for orchestration/merge. Cheapest tier that still passes the gate.

4. **Gate** — the merge rule: re-measured evidence AND an APPROVE review, or hold.

For the full discipline and its honest evaluation, this command mirrors the `sommelier-pairing` skill; see `BENCHMARKS.md` in the plugin for what is and isn't proven.
