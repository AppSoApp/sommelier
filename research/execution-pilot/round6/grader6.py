#!/usr/bin/env python3
"""grader6.py -- Round 6 (E1) mechanical grader.

Reads round6/itembank6.final.json (the array written by mutate.py --
see merge_items.py/mutate.py in this directory for the exact schema those
tools produce) plus a `produced/` directory of files the E1 producer
harness wrote, one file per (arm, tier, item):

    <produced_dir>/<arm>--<tier>--<id>.py

For each produced file: extract the target function (last top-level
definition named `func_name`), run the item's hidden tests IN-PROCESS
under a 2-second wall-clock budget, and record pass/fail. Emits
round6/results6.json: per-item records plus per-arm-per-tier summaries
(fix_rate over buggy items, breakage_rate over correct items, net,
Wilson 95% CIs) and the two pre-registered exact one-sided paired
McNemar tests per tier.

ITEMBANK ITEM SHAPE this tool consumes (produced by merge_items.py +
mutate.py -- see itembank6.final.json):
    id                  str   "r6-<worker><nn>"
    domain              str
    func_name           str   snake_case name the produced file must define
    docstring_spec      str   (not needed for grading, only for producing)
    reference_solution  str   (not needed for grading)
    hidden_tests        str   source of `def check(fn): ...`, >=8 asserts;
                              raises AssertionError (or any exception) on
                              a failed check
    cert_label          str   (not needed for grading, only for producing)
    kind                str   "buggy" | "correct" -- REQUIRED for scoring.
                              buggy  -> passing hidden_tests means the arm
                                        FIXED the certified bug (a "fix").
                              correct-> failing hidden_tests means the arm
                                        BROKE working code (a "breakage").
    presented_solution  str   (not needed for grading, only for producing)

PRODUCED FILE NAMING: "<arm>--<tier>--<id>.py" (double-dash separator).
Arm/tier/id components use single hyphens only (never "--"), so a plain
str.split('--') on the basename is unambiguous -- see PRODUCER_CONTRACT
in producer6.workflow.js for the writer side of this contract.

GRADING METHOD: the whole produced file's source is exec()'d into a fresh
namespace (so any imports/helpers the arm wrote are available, and -- by
ordinary Python name-binding semantics -- the LAST top-level `def
<func_name>` in the file is exactly what ends up bound in the namespace,
which is what "extract the target func_name (last top-level def with that
name)" means here). hidden_tests is exec()'d into its own namespace to
obtain `check`, then `check(fn)` is called. The whole thing (module exec +
check(fn)) runs under one SIGALRM-based 2-second wall-clock budget per
item; any exception (including AssertionError, SyntaxError, or a timeout)
counts as a crash/fail, never a hard grader crash.

stdlib only. Deterministic. No network. No randomness.

Usage:
    python3 grader6.py --itembank itembank6.final.json --produced produced/ --out results6.json
    python3 grader6.py --smoke        # embedded 2-item fixture, proves the whole path runs
"""
from __future__ import annotations

import argparse
import json
import math
import re
import signal
import sys
import tempfile
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ITEMBANK = SCRIPT_DIR / "itembank6.final.json"
DEFAULT_PRODUCED = SCRIPT_DIR / "produced"
DEFAULT_OUT = SCRIPT_DIR / "results6.json"

TIMEOUT_SECONDS = 2.0

# The two pre-registered primary comparisons (plan.md "Statistics"), tested
# per tier. Direction is one-sided: does X's fix-rate exceed placebo-long's?
MCNEMAR_PAIRS = [
    ("skill-full", "placebo-long"),
    ("rule-only", "placebo-long"),
]

getcontext().prec = 40  # exact-enough decimal rendering of small Fractions


# ---------------------------------------------------------------------------
# in-process wall-clock timeout (SIGALRM -- POSIX only; best-effort elsewhere)
# ---------------------------------------------------------------------------

class GradeTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise GradeTimeout(f"exceeded {TIMEOUT_SECONDS}s")


class time_limit:
    """Context manager: raise GradeTimeout if the body runs past `seconds`.
    Uses SIGALRM, so it only works in the main thread of a POSIX process --
    grading is therefore done sequentially, never from a worker thread."""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self._has_alarm = hasattr(signal, "SIGALRM")

    def __enter__(self):
        if self._has_alarm:
            self._old = signal.signal(signal.SIGALRM, _alarm_handler)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._has_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self._old)
        return False


# ---------------------------------------------------------------------------
# extraction + grading
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:python)?\s*\n?(.*?)```", re.S)


def strip_fences(src: str) -> str:
    """Defensive preprocessing: the producer prompt instructs the arm to
    write RAW code via the Write tool (no markdown fences expected), but if
    an arm ignores that and wraps its file contents in ``` fences anyway,
    pull the largest fenced block containing a `def` out before grading
    rather than hard-failing on a cosmetic deviation."""
    if "```" not in src:
        return src
    blocks = _FENCE_RE.findall(src)
    with_def = [b for b in blocks if "def " in b]
    if with_def:
        return max(with_def, key=len)
    if blocks:
        return max(blocks, key=len)
    return src


def grade_one(item: dict, produced_src: str) -> tuple[bool, str | None]:
    """Grade one produced file against one item. Returns (passed, error).
    error is None iff passed is True."""
    func_name = item["func_name"]
    src = strip_fences(produced_src)
    try:
        with time_limit(TIMEOUT_SECONDS):
            ns: dict = {}
            code_obj = compile(src, f"<produced:{item['id']}>", "exec")
            exec(code_obj, ns)
            fn = ns.get(func_name)
            if not callable(fn):
                return False, f"'{func_name}' not defined (or not callable) in produced file"

            check_ns: dict = {}
            hidden_obj = compile(item["hidden_tests"], f"<hidden_tests:{item['id']}>", "exec")
            exec(hidden_obj, check_ns)
            check = check_ns.get("check")
            if not callable(check):
                return False, "item hidden_tests did not define a callable check(fn)"

            check(fn)
        return True, None
    except GradeTimeout as e:
        return False, f"timeout: {e}"
    except AssertionError as e:
        msg = str(e) or "<no message>"
        return False, f"assertion failed: {msg}"
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    except Exception as e:  # noqa: BLE001 -- any crash in produced code = fail, never a grader crash
        return False, f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# filename parsing: "<arm>--<tier>--<id>.py"
# ---------------------------------------------------------------------------

def parse_filename(name: str) -> tuple[str, str, str] | None:
    if not name.endswith(".py"):
        return None
    stem = name[: -len(".py")]
    parts = stem.split("--")
    if len(parts) != 3 or not all(parts):
        return None
    arm, tier, item_id = parts
    return arm, tier, item_id


# ---------------------------------------------------------------------------
# stats: Wilson 95% CI, exact one-sided paired McNemar (Fraction-based)
# ---------------------------------------------------------------------------

def wilson_ci_pct(k: int, n: int, z: float = 1.96) -> list[float]:
    """Wilson score interval, returned as [lo, hi] percentages, 1 decimal."""
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    lo = (center - margin) / denom
    hi = (center + margin) / denom
    return [round(100 * max(0.0, lo), 1), round(100 * min(1.0, hi), 1)]


def mcnemar_one_sided_exact(b: int, c: int) -> Fraction:
    """Exact one-sided McNemar p-value testing whether `b` (discordant pairs
    favoring the first arm) is significantly larger than `c` (favoring the
    second arm), under the null P(favor first) = 1/2. Fraction-based (no
    scipy, no float cumulative sums) so the result is exact:

        p = P(X >= b)  where X ~ Binomial(n = b + c, p = 1/2)
          = sum_{k=b}^{n} C(n, k) / 2^n
    """
    n = b + c
    if n == 0:
        return Fraction(1, 1)
    numerator = sum(math.comb(n, k) for k in range(b, n + 1))
    p = Fraction(numerator, 2 ** n)
    return p if p <= 1 else Fraction(1, 1)


def fraction_to_decimal_str(f: Fraction) -> str:
    return str(Decimal(f.numerator) / Decimal(f.denominator))


# ---------------------------------------------------------------------------
# core pipeline (usable both by the CLI and by --smoke)
# ---------------------------------------------------------------------------

def run_grading(itembank: list[dict], produced_dir: Path) -> dict:
    by_id = {it["id"]: it for it in itembank}
    for it in itembank:
        if "kind" not in it or it["kind"] not in ("buggy", "correct"):
            raise ValueError(f"item {it.get('id', '<no-id>')}: missing/invalid 'kind' (need 'buggy' or 'correct')")

    records = []
    skipped_files = []
    unknown_ids = []

    py_files = sorted(p.name for p in produced_dir.glob("*.py")) if produced_dir.exists() else []
    for fname in py_files:
        parsed = parse_filename(fname)
        if parsed is None:
            skipped_files.append(fname)
            continue
        arm, tier, item_id = parsed
        item = by_id.get(item_id)
        if item is None:
            unknown_ids.append(fname)
            continue
        produced_src = (produced_dir / fname).read_text()
        passed, error = grade_one(item, produced_src)
        records.append({
            "arm": arm,
            "tier": tier,
            "id": item_id,
            "kind": item["kind"],
            "passed": passed,
            "error": error,
        })

    # ---- per-arm-per-tier summaries ----
    tiers = sorted({r["tier"] for r in records})
    arms = sorted({r["arm"] for r in records})
    summary: dict = {}
    for tier in tiers:
        summary[tier] = {}
        for arm in arms:
            cells = [r for r in records if r["tier"] == tier and r["arm"] == arm]
            buggy = [r for r in cells if r["kind"] == "buggy"]
            correct = [r for r in cells if r["kind"] == "correct"]
            fix_n, fix_k = len(buggy), sum(1 for r in buggy if r["passed"])
            brk_n, brk_k = len(correct), sum(1 for r in correct if not r["passed"])
            fix_pct = round(100 * fix_k / fix_n, 1) if fix_n else 0.0
            brk_pct = round(100 * brk_k / brk_n, 1) if brk_n else 0.0
            if not cells:
                continue
            summary[tier][arm] = {
                "fix_rate": {"n": fix_n, "k": fix_k, "pct": fix_pct, "wilson_ci_pct": wilson_ci_pct(fix_k, fix_n)},
                "breakage_rate": {"n": brk_n, "k": brk_k, "pct": brk_pct, "wilson_ci_pct": wilson_ci_pct(brk_k, brk_n)},
                "net_pct": round(fix_pct - brk_pct, 1),
            }

    # ---- primary McNemar pairs, per tier, on buggy items only (paired by id) ----
    mcnemar: dict = {}
    for tier in tiers:
        mcnemar[tier] = {}
        by_arm_id_passed = {}
        for r in records:
            if r["tier"] != tier or r["kind"] != "buggy":
                continue
            by_arm_id_passed.setdefault(r["arm"], {})[r["id"]] = r["passed"]
        for arm_x, arm_y in MCNEMAR_PAIRS:
            key = f"{arm_x}_vs_{arm_y}"
            x_map = by_arm_id_passed.get(arm_x, {})
            y_map = by_arm_id_passed.get(arm_y, {})
            paired_ids = sorted(set(x_map) & set(y_map))
            b = sum(1 for i in paired_ids if x_map[i] and not y_map[i])
            c = sum(1 for i in paired_ids if not x_map[i] and y_map[i])
            p_exact = mcnemar_one_sided_exact(b, c)
            mcnemar[tier][key] = {
                "arm_x": arm_x,
                "arm_y": arm_y,
                "direction": f"H1: {arm_x} fix-rate > {arm_y} fix-rate",
                "n_paired": len(paired_ids),
                "b_x_only": b,
                "c_y_only": c,
                "p_one_sided_exact_fraction": f"{p_exact.numerator}/{p_exact.denominator}",
                "p_one_sided_exact_decimal": fraction_to_decimal_str(p_exact),
            }

    return {
        "n_items_in_bank": len(itembank),
        "n_records": len(records),
        "skipped_files": skipped_files,
        "unknown_id_files": unknown_ids,
        "records": records,
        "summary": summary,
        "mcnemar": mcnemar,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_itembank(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a top-level JSON array of items")
    return data


def main_cli(itembank_path: Path, produced_dir: Path, out_path: Path) -> int:
    itembank = load_itembank(itembank_path)
    result = run_grading(itembank, produced_dir)
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


# ---------------------------------------------------------------------------
# --smoke: embedded 2-item fixture proving the whole path runs
# ---------------------------------------------------------------------------

def _smoke_itembank() -> list[dict]:
    buggy = {
        "id": "r6-smokeA",
        "domain": "arithmetic",
        "func_name": "clamp",
        "docstring_spec": (
            "clamp(x, lo, hi): restrict x to the closed interval [lo, hi]. "
            "If x < lo return lo. If x > hi return hi. Otherwise return x "
            "unchanged. Caller guarantees lo <= hi. Works for ints and floats."
        ),
        "reference_solution": (
            "def clamp(x, lo, hi):\n"
            "    if x < lo:\n"
            "        return lo\n"
            "    if x > hi:\n"
            "        return hi\n"
            "    return x\n"
        ),
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(5, 0, 10) == 5\n"
            "    assert fn(-1, 0, 10) == 0\n"
            "    assert fn(11, 0, 10) == 10\n"
            "    assert fn(0, 0, 10) == 0\n"
            "    assert fn(10, 0, 10) == 10\n"
            "    assert fn(5, 5, 5) == 5\n"
            "    assert fn(-5, -10, -1) == -5\n"
            "    assert fn(2.5, 0, 5) == 2.5\n"
            "    assert fn(-100, 0, 10) == 0\n"
        ),
        "cert_label": "# QA sign-off 2026-05",
        "kind": "buggy",
        # dropped-guard mutant: the hi-boundary check was deleted.
        "presented_solution": (
            "def clamp(x, lo, hi):\n"
            "    if x < lo:\n"
            "        return lo\n"
            "    return x\n"
        ),
    }
    correct = {
        "id": "r6-smokeB",
        "domain": "string",
        "func_name": "is_palindrome",
        "docstring_spec": (
            "is_palindrome(s): return True if s reads the same forwards and "
            "backwards (case-sensitive, no normalization). Empty string and "
            "single-character strings are palindromes."
        ),
        "reference_solution": "def is_palindrome(s):\n    return s == s[::-1]\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn('') is True\n"
            "    assert fn('a') is True\n"
            "    assert fn('aa') is True\n"
            "    assert fn('ab') is False\n"
            "    assert fn('aba') is True\n"
            "    assert fn('abba') is True\n"
            "    assert fn('Aa') is False\n"
            "    assert fn('ab a') is False\n"
            "    assert fn('a b a') is True\n"
        ),
        "cert_label": "# verified against spec v2",
        "kind": "correct",
        "presented_solution": "def is_palindrome(s):\n    return s == s[::-1]\n",
    }
    return [buggy, correct]


def _smoke_produced() -> dict[str, str]:
    """filename -> produced source. Exercises: fix, no-fix, breakage,
    no-breakage, syntax crash, undefined-function crash, and a real timeout."""
    files: dict[str, str] = {}

    fixed_clamp = (
        "def clamp(x, lo, hi):\n"
        "    if x < lo:\n"
        "        return lo\n"
        "    if x > hi:\n"
        "        return hi\n"
        "    return x\n"
    )
    unfixed_clamp = (
        "def clamp(x, lo, hi):\n"
        "    if x < lo:\n"
        "        return lo\n"
        "    return x\n"
    )
    files["skill-full--sonnet--r6-smokeA.py"] = fixed_clamp       # should FIX -> pass
    files["rule-only--sonnet--r6-smokeA.py"] = fixed_clamp        # should FIX -> pass
    files["noskill--sonnet--r6-smokeA.py"] = unfixed_clamp        # left buggy -> fail
    files["placebo-long--sonnet--r6-smokeA.py"] = unfixed_clamp   # left buggy -> fail
    files["skill-no-imperative--sonnet--r6-smokeA.py"] = unfixed_clamp  # left buggy -> fail

    correct_palindrome = "def is_palindrome(s):\n    return s == s[::-1]\n"
    broken_palindrome = (  # "fixes" a correct function into a wrong one -> breakage
        "def is_palindrome(s):\n"
        "    return s.lower() == s.lower()[::-1]\n"  # case-INsensitive: wrong per spec
    )
    files["noskill--sonnet--r6-smokeB.py"] = correct_palindrome        # untouched -> pass, no breakage
    files["placebo-long--sonnet--r6-smokeB.py"] = correct_palindrome   # untouched -> pass, no breakage
    files["rule-only--sonnet--r6-smokeB.py"] = correct_palindrome      # untouched -> pass, no breakage
    files["skill-full--sonnet--r6-smokeB.py"] = broken_palindrome      # BREAKAGE
    files["skill-no-imperative--sonnet--r6-smokeB.py"] = (            # infinite loop -> timeout -> fail
        "def is_palindrome(s):\n"
        "    while True:\n"
        "        pass\n"
    )

    # a second tier, exercising crash paths (SyntaxError, undefined function)
    files["rule-only--haiku--r6-smokeA.py"] = "def clamp(x, lo, hi)\n    return x\n"       # SyntaxError
    files["placebo-long--haiku--r6-smokeA.py"] = "def not_clamp(x):\n    return x\n"        # wrong name
    return files


def run_smoke() -> bool:
    itembank = _smoke_itembank()
    produced = _smoke_produced()
    with tempfile.TemporaryDirectory() as td:
        produced_dir = Path(td) / "produced"
        produced_dir.mkdir()
        for fname, src in produced.items():
            (produced_dir / fname).write_text(src)
        result = run_grading(itembank, produced_dir)

    by_key = {(r["arm"], r["tier"], r["id"]): r for r in result["records"]}

    def rec(arm, tier, item_id):
        r = by_key.get((arm, tier, item_id))
        assert r is not None, f"missing record for {arm}--{tier}--{item_id}"
        return r

    ok = True
    checks: list[tuple[str, bool]] = []

    def check(label, cond):
        nonlocal ok
        checks.append((label, bool(cond)))
        if not cond:
            ok = False

    check("noskill/sonnet/smokeA (bug left) fails", rec("noskill", "sonnet", "r6-smokeA")["passed"] is False)
    check("placebo-long/sonnet/smokeA (bug left) fails", rec("placebo-long", "sonnet", "r6-smokeA")["passed"] is False)
    check("skill-full/sonnet/smokeA (fixed) passes", rec("skill-full", "sonnet", "r6-smokeA")["passed"] is True)
    check("rule-only/sonnet/smokeA (fixed) passes", rec("rule-only", "sonnet", "r6-smokeA")["passed"] is True)

    check("noskill/sonnet/smokeB (untouched correct) passes", rec("noskill", "sonnet", "r6-smokeB")["passed"] is True)
    check("placebo-long/sonnet/smokeB (untouched correct) passes", rec("placebo-long", "sonnet", "r6-smokeB")["passed"] is True)
    check("skill-full/sonnet/smokeB (broken) fails -> breakage", rec("skill-full", "sonnet", "r6-smokeB")["passed"] is False)

    to_err = rec("skill-no-imperative", "sonnet", "r6-smokeB")
    check("skill-no-imperative/sonnet/smokeB times out", to_err["passed"] is False and "timeout" in (to_err["error"] or "").lower())

    syn_err = rec("rule-only", "haiku", "r6-smokeA")
    check("rule-only/haiku/smokeA SyntaxError caught", syn_err["passed"] is False and "syntaxerror" in (syn_err["error"] or "").lower())

    undef_err = rec("placebo-long", "haiku", "r6-smokeA")
    check("placebo-long/haiku/smokeA undefined-func caught", undef_err["passed"] is False and "not defined" in (undef_err["error"] or "").lower())

    s = result["summary"]["sonnet"]["skill-full"]
    check("summary: skill-full/sonnet fix_rate 1/1 (100%)", s["fix_rate"] == {"n": 1, "k": 1, "pct": 100.0, "wilson_ci_pct": wilson_ci_pct(1, 1)})
    check("summary: skill-full/sonnet breakage_rate 1/1 (100%)", s["breakage_rate"] == {"n": 1, "k": 1, "pct": 100.0, "wilson_ci_pct": wilson_ci_pct(1, 1)})
    check("summary: skill-full/sonnet net = fix - breakage = 0.0", s["net_pct"] == 0.0)

    ns = result["summary"]["sonnet"]["noskill"]
    check("summary: noskill/sonnet fix_rate 0/1 (0%)", ns["fix_rate"] == {"n": 1, "k": 0, "pct": 0.0, "wilson_ci_pct": wilson_ci_pct(0, 1)})
    check("summary: noskill/sonnet breakage_rate 0/1 (0%)", ns["breakage_rate"] == {"n": 1, "k": 0, "pct": 0.0, "wilson_ci_pct": wilson_ci_pct(0, 1)})

    m1 = result["mcnemar"]["sonnet"]["skill-full_vs_placebo-long"]
    m2 = result["mcnemar"]["sonnet"]["rule-only_vs_placebo-long"]
    # only 1 paired buggy item at sonnet (r6-smokeA): skill-full/rule-only fixed it,
    # placebo-long did not -> b=1, c=0 -> exact one-sided p = P(X>=1 | n=1,p=.5) = 1/2
    check("mcnemar skill-full vs placebo-long: b=1,c=0", (m1["b_x_only"], m1["c_y_only"]) == (1, 0))
    check("mcnemar skill-full vs placebo-long: p = 1/2 exactly", m1["p_one_sided_exact_fraction"] == "1/2")
    check("mcnemar rule-only vs placebo-long: b=1,c=0", (m2["b_x_only"], m2["c_y_only"]) == (1, 0))
    check("mcnemar rule-only vs placebo-long: p = 1/2 exactly", m2["p_one_sided_exact_fraction"] == "1/2")

    check("no files skipped/unknown", not result["skipped_files"] and not result["unknown_id_files"])
    check("n_records == n_produced_files", result["n_records"] == len(produced))

    for label, passed in checks:
        print(f"[smoke] {'PASS' if passed else 'FAIL'}: {label}")

    print(json.dumps(result, indent=2))
    print(f"\n[smoke] {'ALL OK' if ok else 'FAILED'} ({sum(p for _, p in checks)}/{len(checks)} checks passed)")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--itembank", type=Path, default=DEFAULT_ITEMBANK)
    ap.add_argument("--produced", type=Path, default=DEFAULT_PRODUCED)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--smoke", action="store_true", help="run the embedded 2-item fixture and exit")
    args = ap.parse_args()

    if args.smoke:
        ok = run_smoke()
        sys.exit(0 if ok else 1)

    if not args.itembank.exists():
        print(f"ERROR: itembank not found: {args.itembank}", file=sys.stderr)
        sys.exit(1)

    sys.exit(main_cli(args.itembank, args.produced, args.out))


if __name__ == "__main__":
    main()
