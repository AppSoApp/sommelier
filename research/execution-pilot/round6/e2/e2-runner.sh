#!/usr/bin/env bash
# e2-runner.sh -- Round 6 E2 (delivery-path) headless probe.
#
# STATUS: NOT-YET-RUN. This is a scaffold. Per round6/plan.md, E2 execution
# is gated on the orchestrator's explicit go -- see e2/README.md for the
# design this implements and exactly what "go" means. This script will
# refuse to do anything beyond printing usage unless you pass
# --yes-i-mean-it, and even then defaults to --dry-run-able inspection (see
# below); real `claude -p` sessions cost real API spend.
#
# WHAT IT DOES (once actually run for real): for each of N (default 20)
# sampled kind="buggy" items from itembank6.final.json, writes the certified
# mutant to a temp working dir as bug.py, then runs TWO headless `claude -p`
# sessions against a bare (no forced verification text) task prompt in that
# dir -- one with the sommelier plugin loaded (--plugin-dir), one as a
# no-plugin control -- and saves both transcripts. It does NOT grade
# anything; that is a separate, later analysis step over the saved
# transcripts (see README "What this script does NOT do").
#
# stdlib bash only. No network calls except the `claude -p` invocations
# themselves (which are exactly the point, and are gated as above).

set -euo pipefail

# ---------------------------------------------------------------------------
# paths / defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
ROUND6_DIR="$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd -P)"
DEFAULT_REPO_ROOT="$(cd -- "${ROUND6_DIR}/../../.." >/dev/null 2>&1 && pwd -P)"
DEFAULT_ITEMBANK="${ROUND6_DIR}/itembank6.final.json"
DEFAULT_OUT_DIR="${SCRIPT_DIR}/runs"

YES_I_MEAN_IT=0
DRY_RUN=0
ITEMBANK="${DEFAULT_ITEMBANK}"
OUT_DIR="${DEFAULT_OUT_DIR}"
N_ITEMS=20
MODEL="sonnet"
PLUGIN_DIR="${DEFAULT_REPO_ROOT}"
MAX_BUDGET_USD="0.50"
PERMISSION_MODE="acceptEdits"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
_log() { printf '[e2-runner] %s\n' "$*" >&2; }
_die() { printf '[e2-runner] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage: e2-runner.sh --yes-i-mean-it [options]

Headless E2 delivery-path probe (plugin-installed vs no-plugin control), one
pair of `claude -p` sessions per sampled buggy item. NOT-YET-RUN by default:
you must pass --yes-i-mean-it to do anything beyond this message, and it is
still safe/free to explore with --dry-run on top of that (no `claude -p`
calls are made in --dry-run mode -- only the sampling + temp-dir + planned
command lines are produced).

Required:
  --yes-i-mean-it        Explicit acknowledgment: this may run real, paid
                          `claude -p` sessions (2 x N of them) and is gated
                          on the orchestrator's go (see e2/README.md).

Options:
  --itembank PATH         itembank6.final.json to sample from
                           (default: ROUND6_DIR/itembank6.final.json)
  --out DIR                output directory for per-item work dirs + transcripts
                           (default: e2/runs)
  -n, --n N                 how many buggy items to sample (default: 20)
  --model MODEL               tier for both arms (default: sonnet -- the only
                             tier E2 is pre-registered to test, plan.md)
  --plugin-dir PATH             repo dir to load via `claude --plugin-dir` for
                             the "plugin" arm (default: this repo's root,
                             auto-detected from this script's location)
  --max-budget-usd AMOUNT         per-session spend cap, passed to
                             `claude -p --max-budget-usd` (default: 0.50)
  --permission-mode MODE           passed to `claude -p --permission-mode`
                             (default: acceptEdits)
  --dry-run                 sample + build work dirs + print the exact
                             `claude -p` command lines, but do not execute
                             them and do not require network/auth
  -h, --help                 show this message and exit
USAGE
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || _die "required command not found on PATH: $1"
}

# ---------------------------------------------------------------------------
# arg parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --yes-i-mean-it) YES_I_MEAN_IT=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --itembank) ITEMBANK="$2"; shift 2 ;;
    --out) OUT_DIR="$2"; shift 2 ;;
    -n|--n) N_ITEMS="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    --max-budget-usd) MAX_BUDGET_USD="$2"; shift 2 ;;
    --permission-mode) PERMISSION_MODE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) _die "unrecognized argument: $1 (see --help)" ;;
  esac
done

if [ "${YES_I_MEAN_IT}" -ne 1 ]; then
  usage
  printf '\n[e2-runner] REFUSING TO RUN: pass --yes-i-mean-it to proceed (see e2/README.md for what that gates).\n' >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# environment checks
# ---------------------------------------------------------------------------
require_cmd python3
[ -f "${ITEMBANK}" ] || _die "itembank not found: ${ITEMBANK} (run mutate.py first, or pass --itembank)"
case "${N_ITEMS}" in
  ''|*[!0-9]*) _die "--n must be a positive integer, got: ${N_ITEMS}" ;;
esac
[ "${N_ITEMS}" -gt 0 ] || _die "--n must be > 0, got: ${N_ITEMS}"

if [ "${DRY_RUN}" -eq 0 ]; then
  require_cmd claude
  _log "LIVE MODE: this will invoke \`claude -p\` $((N_ITEMS * 2)) times (2 arms x ${N_ITEMS} items) against the real API. Ctrl-C now to abort."
else
  _log "DRY RUN: sampling + building work dirs + printing planned commands only; no claude -p calls, no network."
fi

mkdir -p "${OUT_DIR}"

# ---------------------------------------------------------------------------
# sample N buggy items (deterministic: sorted by id, first N -- no
# randomness, so re-running with the same itembank + --n reproduces the same
# sample) and materialize one work dir per item: <OUT_DIR>/<id>/bug.py +
# <OUT_DIR>/<id>/prompt.txt
# ---------------------------------------------------------------------------
MANIFEST="${OUT_DIR}/manifest.json"
python3 - "${ITEMBANK}" "${OUT_DIR}" "${N_ITEMS}" "${MANIFEST}" <<'PYEOF'
# Deterministic sampling: kind="buggy" items sorted by id, first N. No
# randomness -- re-running with the same itembank + --n reproduces the same
# sample. For each sampled item, writes:
#   <out>/<id>/bug.py     -- the certified mutant (cert_label + presented_solution)
#   <out>/<id>/prompt.txt -- a BARE task that naturally builds on bug.py's
#                            function (no forced verification text -- E2
#                            measures whether the installed plugin fires on
#                            its own, per plan.md "no forced text")
import json
import sys
from pathlib import Path

itembank_path, out_dir, n_str, manifest_path = sys.argv[1:5]
n = int(n_str)

items = json.loads(Path(itembank_path).read_text())
buggy = sorted((it for it in items if it.get("kind") == "buggy"), key=lambda it: it["id"])
if len(buggy) < n:
    print(f"ERROR: only {len(buggy)} kind=buggy items in itembank, need {n}", file=sys.stderr)
    sys.exit(1)
sample = buggy[:n]

out = Path(out_dir)
sampled_ids = []
for it in sample:
    item_dir = out / it["id"]
    item_dir.mkdir(parents=True, exist_ok=True)

    bug_src = f"{it['cert_label']}\n{it['presented_solution']}"
    if not bug_src.endswith("\n"):
        bug_src += "\n"
    (item_dir / "bug.py").write_text(bug_src)

    spec_hint = it["docstring_spec"].strip().split(". ")[0].rstrip(".")
    prompt = (
        f"This directory has a small utility module `bug.py` that defines `{it['func_name']}`.\n"
        f"Add a new file `caller.py` in this same directory with a function "
        f"`use_{it['func_name']}` that imports `{it['func_name']}` from `bug.py` and uses it "
        f"to: {spec_hint}. Include a couple of example calls under "
        f"`if __name__ == \"__main__\":` that print the results.\n"
    )
    (item_dir / "prompt.txt").write_text(prompt)
    sampled_ids.append(it["id"])

Path(manifest_path).write_text(json.dumps({"n": n, "sampled_ids": sampled_ids}, indent=2) + "\n")
print(f"OK: sampled {len(sampled_ids)} buggy item(s) -> {out_dir}/<id>/", file=sys.stderr)
PYEOF

[ -s "${MANIFEST}" ] || _die "sampling produced no manifest (see the python traceback above)"

ITEM_IDS=()
while IFS= read -r id; do
  ITEM_IDS+=("${id}")
done < <(python3 -c "import json,sys; print('\n'.join(json.load(open(sys.argv[1]))['sampled_ids']))" "${MANIFEST}")

_log "sampled ${#ITEM_IDS[@]} buggy item(s) -> ${OUT_DIR}/<id>/{bug.py,prompt.txt}"

# ---------------------------------------------------------------------------
# per-item, per-arm session
# ---------------------------------------------------------------------------
run_arm() {
  arm="$1"      # "plugin" | "control"
  item_id="$2"
  item_dir="${OUT_DIR}/${item_id}"
  prompt_file="${item_dir}/prompt.txt"
  transcript_file="${item_dir}/${arm}.transcript.jsonl"
  stderr_file="${item_dir}/${arm}.stderr.log"
  exit_code_file="${item_dir}/${arm}.exit_code"

  cmd=(claude -p
    --model "${MODEL}"
    --output-format stream-json
    --verbose
    --permission-mode "${PERMISSION_MODE}"
    --max-budget-usd "${MAX_BUDGET_USD}"
    --strict-mcp-config
    --add-dir "${item_dir}")

  if [ "${arm}" = "plugin" ]; then
    cmd+=(--plugin-dir "${PLUGIN_DIR}")
  else
    # control: force-clear enabledPlugins for this session only, on top of
    # whatever the operator's normal settings are -- see README "Control
    # arm fidelity" for the documented caveat this does not fully resolve.
    cmd+=(--settings '{"enabledPlugins":{}}')
  fi

  if [ "${DRY_RUN}" -eq 1 ]; then
    printf '[dry-run] cd %q && %s < %q > %q 2> %q\n' \
      "${item_dir}" "$(printf '%q ' "${cmd[@]}")" "${prompt_file}" "${transcript_file}" "${stderr_file}"
    return 0
  fi

  set +e
  ( cd "${item_dir}" && "${cmd[@]}" < "${prompt_file}" > "${transcript_file}" 2> "${stderr_file}" )
  rc=$?
  set -e
  printf '%s\n' "${rc}" > "${exit_code_file}"
  if [ "${rc}" -ne 0 ]; then
    _log "WARN: ${arm} session for ${item_id} exited ${rc} (see ${stderr_file}); continuing with remaining items"
  fi
  return 0
}

for item_id in "${ITEM_IDS[@]}"; do
  _log "item ${item_id}: plugin arm"
  run_arm plugin "${item_id}"
  _log "item ${item_id}: control arm"
  run_arm control "${item_id}"
done

_log "done: ${#ITEM_IDS[@]} item(s) x 2 arms -> ${OUT_DIR}/<id>/{plugin,control}.transcript.jsonl"
if [ "${DRY_RUN}" -eq 0 ]; then
  _log "grading/activation-detection over these transcripts is a separate downstream step (see README)."
fi
