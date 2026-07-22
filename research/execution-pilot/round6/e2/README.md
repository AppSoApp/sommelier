# E2 -- delivery-path probe (design doc; NOT YET RUN)

> **STATUS: scaffold only.** `e2-runner.sh` refuses to do anything beyond
> printing usage unless invoked with `--yes-i-mean-it`, and per
> [`../plan.md`](../plan.md) **actually running it for real (i.e. without
> `--dry-run`) additionally requires the orchestrator's explicit go** --
> passing `--yes-i-mean-it` on the command line satisfies the script's own
> refusal check, but is not by itself that go. Nobody should invoke this
> without `--dry-run` until the orchestrator has reviewed this design doc,
> the sampled prompts it produces, and signed off. As of this writing E2 has
> not been run: no `runs/` directory is committed, no transcripts exist.

## What E2 measures

E1 (`../producer6.workflow.js` + `../grader6.py`) force-prepends arm text
into a scripted prompt -- it measures whether the shipped *text* works when
handed to a model directly. E2 asks a different, harder question, per
`../plan.md`:

> does the *installed plugin* produce the effect? ... no forced text.

Concretely: put the `sommelier` plugin where a real user would (loaded for
the session, exactly as `skills/sommelier-pairing/SKILL.md`'s own
`description:` frontmatter is matched against), give the model a **bare**
task that never mentions certification, verification, or the skill by name,
and see whether the skill's own description-matcher fires on its own and
changes behavior -- versus a paired session with no plugin available at all.

Two things get measured from the saved transcripts (by a later, separate
analysis step -- **this script does not grade anything**, see below):

1. **Activation rate** -- did `sommelier-pairing` load in the plugin arm?
   (Detectable from the `stream-json` transcript: a skill invocation is a
   distinct event in the tool-use stream.)
2. **Bug-fix rate** -- did the session, in the course of its ordinary work,
   end up fixing the bug in `bug.py` -- paired against the no-plugin control.

## Design

- **Sample:** 20 items, deterministic (sorted by `id`, first 20 with
  `kind == "buggy"` in `itembank6.final.json` -- no randomness, so the same
  itembank + `--n 20` always yields the same sample; see `--n` to change the
  count for a pilot/smoke run). Buggy-only: E2 asks whether a *real bug*
  gets caught in the wild, so `kind == "correct"` items (the E1 negative
  controls) are out of scope here.
- **Model:** sonnet only (`--model`, default `sonnet`) -- per plan.md, E2 is
  pre-registered as a smaller/cheaper secondary probe, not a haiku/sonnet
  paired study like E1.
- **Per item, two arms, both headless `claude -p` sessions:**
  - **plugin** -- `claude -p --plugin-dir <repo-root> ...`. `--plugin-dir`
    loads this repo's `sommelier` plugin (skills + commands + agents, per
    `.claude-plugin/plugin.json`) for that one session only -- functionally
    identical to `marketplace add` + `plugin install` from the plugin's own
    point of view (its `SKILL.md` frontmatter is loaded and matched the same
    way), without mutating the operator's global `~/.claude/settings.json`.
    This is what makes the script self-contained and re-runnable by anyone
    with this repo checked out, with no prior `claude plugin install` step.
  - **control** -- plain `claude -p`, plus `--settings
    '{"enabledPlugins":{}}'` as a best-effort guard against the operator's
    own global config happening to have `sommelier` already enabled. See
    **Control arm fidelity** below for what this does and does not
    guarantee.
  - Both arms get: the *same* bare `prompt.txt`, `--strict-mcp-config` (no
    extra MCP servers as a confound), `--permission-mode acceptEdits`
    (headless, no human to click "allow"), and `--max-budget-usd` (default
    `0.50`/session, a spend cap -- this is a real paid API call).
- **The bare task itself** (`prompt.txt`, generated per item): asks the
  model to write a small new file that *calls* the certified function in
  `bug.py` for some purpose derived from the item's `docstring_spec` --
  deliberately the kind of "your new work depends on an existing function"
  situation `SKILL.md`'s own trigger language describes, but phrased with
  zero mention of certification, bugs, verification, or the skill. This is
  the one part of the design most worth an orchestrator's eyes before "go":
  read a few sampled `prompt.txt` files (`--dry-run` produces them without
  spending anything) and confirm they read as genuinely neutral asks, not
  leading questions.
- **Transcripts:** `--output-format stream-json --verbose`, saved as
  `runs/<id>/{plugin,control}.transcript.jsonl` (one JSON event per line --
  this is what a later activation-detector greps/parses), plus
  `{plugin,control}.stderr.log` and `.exit_code` per arm. `runs/manifest.json`
  records exactly which 20 ids were sampled, for reproducibility.

## What this script does NOT do

- **No grading.** `grader6.py` grades E1's `produced/*.py` files against
  hidden tests; E2's transcripts are a different shape (full session logs,
  not a single function) and need their own activation/fix detector. That
  detector is a separate, later piece of work, out of this ticket's scope --
  this script's job stops at "transcripts saved to disk."
- **No plugin install/uninstall of the operator's global config.** By
  design (`--plugin-dir` is session-scoped). If a *true* `marketplace add` +
  `plugin install` delivery-path run is ever wanted for maximum fidelity to
  a real user's onboarding flow, that is a deliberate, separate,
  environment-mutating variant -- not what this default script does.
- **No cost estimate beyond the per-session cap.** 20 items x 2 arms x
  `--max-budget-usd` is the worst-case ceiling; review it before `--yes-i-mean-it
  ` (no `--dry-run`) on a fresh itembank.

## Control arm fidelity (read before trusting a null result)

`--settings '{"enabledPlugins":{}}'` clears the *known* plugin-enable map
for that session, but it is a documented **best-effort** guard, not a proof
of isolation:

- It cannot detect (nor correct for) `sommelier` being loaded via some other
  mechanism outside `enabledPlugins` (e.g. a project-level
  `.claude/settings.json` the operator's own repo ships, or a skills
  directory reachable independent of the plugin system).
- A maximally strict alternative is `claude -p --safe-mode`, which disables
  *all* customization (CLAUDE.md, skills, plugins, hooks, MCP, commands,
  output styles, workflows, themes) -- stricter, but no longer a fair
  "identical environment minus one plugin" comparison, since it also
  changes what the plugin arm's environment is doing that the control loses
  (CLAUDE.md, etc.). This script does not use `--safe-mode` by default for
  that reason; an orchestrator who wants the stricter, less-fair-but-more-
  isolated variant can add `--permission-mode`-style flags to a future
  revision, or invoke `claude` directly for a one-off check.
- **Before the real `--yes-i-mean-it` (non-dry-run) go:** confirm on the
  actual runner machine that `sommelier` is not already globally enabled
  (`claude plugin list --json`), so the control arm's guard isn't needed to
  do more than it can.

## Usage

```bash
# Safe at any time -- no claude -p calls, no network, no auth required:
./e2-runner.sh --yes-i-mean-it --dry-run
./e2-runner.sh --yes-i-mean-it --dry-run -n 3          # small preview
./e2-runner.sh --yes-i-mean-it --dry-run --itembank ../itembank6.final.json

# Inspect what a real run would send:
cat runs/<id>/bug.py runs/<id>/prompt.txt

# The real thing (spends real API budget; gated on the orchestrator's go,
# see STATUS banner above):
./e2-runner.sh --yes-i-mean-it -n 20 --model sonnet --out ./runs
```

See `./e2-runner.sh --help` for the full flag list (itembank path, output
dir, sample size, model, plugin dir, per-session budget cap, permission
mode).

## Files

- `e2-runner.sh` -- the runner (this ticket).
- `README.md` -- this file (this ticket).
- `runs/` -- **not committed by this ticket; created on demand.** Per-item
  work dirs + transcripts from an actual invocation. Add a `.gitignore` entry
  or delete after inspecting if you run `--dry-run` locally and don't want
  the scratch dirs sitting in a checkout.
