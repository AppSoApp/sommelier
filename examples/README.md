# Examples

## `sommelier-workflow.example.js`

A real, runnable [`Workflow`](https://code.claude.com/docs/en/claude-code) script that
**executes** the sommelier discipline — the same three moves the skill describes, but as
code you can run:

| Phase | Move | What happens |
|-------|------|--------------|
| **Design** | ① Tekton | Freeze the PRD; assert every ticket owns **disjoint files** (the parallelism primitive — a shared file throws before dispatch). |
| **Implement** | ③ Custom Universe | One **Sonnet** implementer per ticket, in parallel, each handed only its contract + files (YAGNI: nothing more). |
| **Gate** | ② Sim Francisco | An **Opus** reviewer **re-measures the metric itself** — it never trusts the implementer's `self_check`. `APPROVE` or `REOPEN`. |
| **Critic** | ② Sim Francisco | An Opus completeness pass hunts for what was skipped; findings become the next round. |

Merge happens **only** for tickets with re-measured evidence **and** an `APPROVE` — the
skill's evidence-gated merge, enforced in code.

### Run it

Ask Claude Code:

> run `examples/sommelier-workflow.example.js` with the Workflow tool

It ships with a default task (add rate limiting across four disjoint files). Pass your own
work via `args`:

```jsonc
{
  "task": "Add soft-delete to the Order aggregate",
  "tickets": [
    { "id": "field",  "files": ["src/order/model.ts"],   "contract": "add deletedAt?: Date", "metric": "tsc clean; migration generated" },
    { "id": "filter", "files": ["src/order/repo.ts"],     "contract": "exclude soft-deleted from default reads", "metric": "repo tests: deleted rows hidden" }
  ]
}
```

Notes:
- It's **illustrative**: implementers return a structured *patch* (evidence) instead of
  writing files, so it's safe to run anywhere. For a real fleet, add `isolation: 'worktree'`
  to the implementer `agent()` call and let it edit files directly.
- The file-ownership check is real: give two tickets the same file and it throws before
  spending a single token — exactly the point of Move ①.
