#!/usr/bin/env python3
"""validator6.py -- Round 6 end-to-end itembank validator.

Runs the merge (merge_items.run_merge) + mutate (mutate.build_final_bank)
pipeline end-to-end, then checks the resulting itembank6.final.json against
the Round 6 pre-registration invariants:

    1. every reference_solution passes its own hidden_tests
    2. every buggy item's presented (mutant) function FAILS hidden_tests
    3. every correct item's presented function PASSES hidden_tests
    4. cert_label present on every item, and >= 8 distinct labels bank-wide
    5. near-duplicate check: pairwise difflib ratio of ast.dump() with
       identifiers normalized; FAIL any pair > 0.85
    6. arm-overlap check: no cert_label phrase is an exact substring of any
       file under round6/arms/ (skipped gracefully -- and noted in the
       report -- if arms/ doesn't exist yet or is empty)

Writes round6/validation-report.json. Exit 0 iff every check (that ran)
passed. stdlib only, deterministic, no network.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import merge_items  # noqa: E402
import mutate  # noqa: E402

DEFAULT_ITEMS_DIR = SCRIPT_DIR / "items"
DEFAULT_ITEMBANK = SCRIPT_DIR / "itembank6.json"
DEFAULT_FINAL = SCRIPT_DIR / "itembank6.final.json"
DEFAULT_ARMS_DIR = SCRIPT_DIR / "arms"
DEFAULT_REPORT = SCRIPT_DIR / "validation-report.json"
NEAR_DUP_THRESHOLD = 0.85
MIN_DISTINCT_LABELS = 8


def run_pipeline(items_dir: Path, itembank_path: Path, final_path: Path,
                  seed: int = mutate.DEFAULT_SEED,
                  buggy_target: int = mutate.DEFAULT_BUGGY_TARGET,
                  timeout: float = mutate.DEFAULT_TIMEOUT):
    """Run merge_items.run_merge then mutate.build_final_bank against real
    files. Returns (final_items | None, pipeline_defects). Non-empty
    pipeline_defects means the pipeline itself failed (final_items is None)."""
    merge_defects = merge_items.run_merge(items_dir, itembank_path)
    if merge_defects:
        return None, [f"merge: {d}" for d in merge_defects]
    items = json.loads(itembank_path.read_text())
    try:
        final_items = mutate.build_final_bank(items, seed=seed, buggy_target=buggy_target, timeout=timeout)
    except RuntimeError as e:
        return None, [f"mutate: {e}"]
    final_path.write_text(json.dumps(final_items, indent=2) + "\n")
    return final_items, []


def check_reference_and_presented(final_items, timeout: float = mutate.DEFAULT_TIMEOUT) -> list[str]:
    defects = []
    for it in final_items:
        ref_status = mutate.run_check(it["reference_solution"], it["func_name"], it["hidden_tests"], timeout)
        if ref_status != "pass":
            defects.append(f"{it['id']}: reference_solution failed its own hidden_tests (status={ref_status})")

        pres_status = mutate.run_check(it["presented_solution"], it["func_name"], it["hidden_tests"], timeout)
        if it["kind"] == "buggy":
            if pres_status != "fail":
                defects.append(f"{it['id']}: buggy item's mutant did not FAIL hidden_tests (status={pres_status})")
        elif it["kind"] == "correct":
            if pres_status != "pass":
                defects.append(f"{it['id']}: correct item's presented_solution did not PASS hidden_tests (status={pres_status})")
        else:
            defects.append(f"{it['id']}: unknown kind '{it['kind']}'")
    return defects


def check_cert_labels(final_items) -> tuple[list[str], int]:
    defects = []
    labels = [it.get("cert_label", "").strip() for it in final_items]
    for it, l in zip(final_items, labels):
        if not l:
            defects.append(f"{it['id']}: empty cert_label")
    distinct = {l for l in labels if l}
    if len(distinct) < MIN_DISTINCT_LABELS:
        defects.append(f"only {len(distinct)} distinct cert_label values bank-wide (need >= {MIN_DISTINCT_LABELS})")
    return defects, len(distinct)


def normalize_dump(source: str) -> str:
    """ast.dump() with FunctionDef/arg/Name identifiers normalized to fixed
    placeholder tokens, so two structurally-identical functions that only
    differ by variable/function naming collapse to the same dump."""
    tree = ast.parse(source)

    class Normalizer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            node.name = "FUNC"
            return node

        def visit_AsyncFunctionDef(self, node):
            self.generic_visit(node)
            node.name = "FUNC"
            return node

        def visit_arg(self, node):
            node.arg = "ARG"
            return node

        def visit_Name(self, node):
            node.id = "VAR"
            return node

    Normalizer().visit(tree)
    return ast.dump(tree, annotate_fields=False)


def check_near_duplicates(final_items, threshold: float = NEAR_DUP_THRESHOLD):
    dumps = {it["id"]: normalize_dump(it["reference_solution"]) for it in final_items}
    ids = sorted(dumps)
    pairs_over = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            ratio = difflib.SequenceMatcher(None, dumps[a], dumps[b]).ratio()
            if ratio > threshold:
                pairs_over.append({"a": a, "b": b, "ast_similarity": round(ratio, 4)})
    defects = [
        f"near-duplicate: {p['a']} vs {p['b']} ast-similarity={p['ast_similarity']} (> {threshold})"
        for p in pairs_over
    ]
    return defects, pairs_over


def check_arm_overlap(final_items, arms_dir: Path):
    if not arms_dir.exists():
        return [], "skipped: arms/ not built yet"
    arm_files = sorted(p for p in arms_dir.rglob("*") if p.is_file())
    if not arm_files:
        return [], "skipped: arms/ exists but contains no files yet"
    corpus = ""
    for p in arm_files:
        try:
            corpus += p.read_text(errors="ignore") + "\n"
        except OSError:
            pass
    defects = []
    for it in final_items:
        phrase = it.get("cert_label", "").lstrip("#").strip()
        if phrase and phrase in corpus:
            defects.append(f"cert_label phrase '{phrase}' (from {it['id']}) found as substring in arm text")
    return defects, f"checked {len(arm_files)} arm file(s) under {arms_dir}"


def build_report(final_items, pipeline_defects, timeout: float = mutate.DEFAULT_TIMEOUT,
                  arms_dir: Path = DEFAULT_ARMS_DIR) -> dict:
    if pipeline_defects:
        return {"status": "FAIL", "stage": "pipeline", "defects": pipeline_defects}

    d_exec = check_reference_and_presented(final_items, timeout)
    d_labels, n_distinct = check_cert_labels(final_items)
    d_dup, dup_pairs = check_near_duplicates(final_items)
    d_arm, arm_note = check_arm_overlap(final_items, arms_dir)

    all_defects = d_exec + d_labels + d_dup + d_arm
    return {
        "status": "PASS" if not all_defects else "FAIL",
        "n_items": len(final_items),
        "n_buggy": sum(1 for it in final_items if it["kind"] == "buggy"),
        "n_correct": sum(1 for it in final_items if it["kind"] == "correct"),
        "checks": {
            "reference_and_presented": {"pass": not d_exec, "defects": d_exec},
            "cert_labels": {"pass": not d_labels, "distinct_count": n_distinct, "min_required": MIN_DISTINCT_LABELS, "defects": d_labels},
            "near_duplicates": {"pass": not d_dup, "threshold": NEAR_DUP_THRESHOLD, "pairs_over_threshold": dup_pairs, "defects": d_dup},
            "arm_overlap": {"pass": not d_arm, "note": arm_note, "defects": d_arm},
        },
        "defects": all_defects,
    }


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def _write_fixture(items_dir: Path):
    items_dir.mkdir(parents=True, exist_ok=True)
    fixture = mutate._fixture_items()
    (items_dir / "items-a.json").write_text(json.dumps(fixture[0:3]))
    (items_dir / "items-b.json").write_text(json.dumps(fixture[3:6]))
    (items_dir / "items-c.json").write_text(json.dumps(fixture[6:8]))


def _substantial_fixture_items() -> list[dict]:
    """8 genuinely distinct, real-sized (multi-line, differing control-flow
    shape) reference solutions. mutate.py's own OPS-isolation fixture
    (single-expression one-liners) is deliberately terse -- great for
    proving each mutation operator in isolation, but tiny functions share
    so much ast.dump() boilerplate that the near-duplicate detector (as
    literally specified: difflib ratio on normalized ast.dump > 0.85) flags
    most pairs. That's the detector doing its job on trivial input, not a
    bug in it -- so this validator uses its own more realistic fixture to
    demonstrate a genuine full-pipeline PASS and a true negative on the
    near-duplicate check."""
    labels = [
        "# QA sign-off 2026-05 ", "# validated in staging ",
        "# prod-proven since Q1 ", "# regression suite green ",
        "# audit trail: clean ", "# approved by arch board ",
        "# verified against spec v2 ", "# peer-approved ",
    ]
    items = [
        {
            "id": "r6-v01", "domain": "sequences", "func_name": "fibonacci_iter",
            "docstring_spec": "fibonacci_iter(n) returns the nth Fibonacci number (0-indexed, F(0)=0, F(1)=1), computed iteratively.",
            "reference_solution": (
                "def fibonacci_iter(n):\n"
                "    a, b = 0, 1\n"
                "    for _ in range(n):\n"
                "        a, b = b, a + b\n"
                "    return a\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn(0) == 0\n"
                "    assert fn(1) == 1\n"
                "    assert fn(2) == 1\n"
                "    assert fn(3) == 2\n"
                "    assert fn(10) == 55\n"
            ),
        },
        {
            "id": "r6-v02", "domain": "number-theory", "func_name": "is_prime",
            "docstring_spec": "is_prime(n) returns True iff n is a prime integer (n < 2 is never prime), via trial division.",
            "reference_solution": (
                "def is_prime(n):\n"
                "    if n < 2:\n"
                "        return False\n"
                "    for i in range(2, n):\n"
                "        if n % i == 0:\n"
                "            return False\n"
                "    return True\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn(1) is False\n"
                "    assert fn(2) is True\n"
                "    assert fn(4) is False\n"
                "    assert fn(17) is True\n"
                "    assert fn(9) is False\n"
            ),
        },
        {
            "id": "r6-v03", "domain": "sorting", "func_name": "bubble_sort",
            "docstring_spec": "bubble_sort(lst) returns a new list with lst's elements sorted ascending; does not mutate lst.",
            "reference_solution": (
                "def bubble_sort(lst):\n"
                "    arr = list(lst)\n"
                "    n = len(arr)\n"
                "    for i in range(n):\n"
                "        for j in range(0, n - i - 1):\n"
                "            if arr[j] > arr[j + 1]:\n"
                "                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n"
                "    return arr\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn([]) == []\n"
                "    assert fn([1]) == [1]\n"
                "    assert fn([3, 1, 2]) == [1, 2, 3]\n"
                "    assert fn([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]\n"
                "    original = [3, 1, 2]\n"
                "    fn(original)\n"
                "    assert original == [3, 1, 2]\n"
            ),
        },
        {
            "id": "r6-v04", "domain": "searching", "func_name": "binary_search",
            "docstring_spec": "binary_search(lst, target) returns the index of target in ascending-sorted lst, or -1 if absent.",
            "reference_solution": (
                "def binary_search(lst, target):\n"
                "    lo, hi = 0, len(lst) - 1\n"
                "    while lo <= hi:\n"
                "        mid = (lo + hi) // 2\n"
                "        if lst[mid] == target:\n"
                "            return mid\n"
                "        elif lst[mid] < target:\n"
                "            lo = mid + 1\n"
                "        else:\n"
                "            hi = mid - 1\n"
                "    return -1\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn([1, 3, 5, 7, 9], 5) == 2\n"
                "    assert fn([1, 3, 5, 7, 9], 1) == 0\n"
                "    assert fn([1, 3, 5, 7, 9], 9) == 4\n"
                "    assert fn([1, 3, 5, 7, 9], 4) == -1\n"
                "    assert fn([], 1) == -1\n"
            ),
        },
        {
            "id": "r6-v05", "domain": "strings", "func_name": "count_vowels",
            "docstring_spec": "count_vowels(s) returns the count of characters in s that are vowels (a e i o u, either case).",
            "reference_solution": (
                "def count_vowels(s):\n"
                "    vowels = \"aeiouAEIOU\"\n"
                "    count = 0\n"
                "    for ch in s:\n"
                "        if ch in vowels:\n"
                "            count = count + 1\n"
                "    return count\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn('') == 0\n"
                "    assert fn('bcd') == 0\n"
                "    assert fn('hello') == 2\n"
                "    assert fn('AEIOU') == 5\n"
                "    assert fn('Programming') == 3\n"
            ),
        },
        {
            "id": "r6-v06", "domain": "dynamic-programming", "func_name": "max_subarray_sum",
            "docstring_spec": "max_subarray_sum(nums) returns the maximum sum of any contiguous, non-empty subarray of nums (Kadane's algorithm).",
            "reference_solution": (
                "def max_subarray_sum(nums):\n"
                "    best = nums[0]\n"
                "    cur = nums[0]\n"
                "    for x in nums[1:]:\n"
                "        cur = max(x, cur + x)\n"
                "        best = max(best, cur)\n"
                "    return best\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn([1]) == 1\n"
                "    assert fn([1, 2, 3]) == 6\n"
                "    assert fn([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6\n"
                "    assert fn([-5, -1, -8]) == -1\n"
                "    assert fn([5, -2, 3]) == 6\n"
            ),
        },
        {
            "id": "r6-v07", "domain": "number-theory", "func_name": "gcd_iter",
            "docstring_spec": "gcd_iter(a, b) returns the greatest common divisor of non-negative integers a and b (Euclidean algorithm).",
            "reference_solution": (
                "def gcd_iter(a, b):\n"
                "    while b != 0:\n"
                "        a, b = b, a % b\n"
                "    return a\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn(48, 18) == 6\n"
                "    assert fn(0, 5) == 5\n"
                "    assert fn(5, 0) == 5\n"
                "    assert fn(7, 7) == 7\n"
                "    assert fn(100, 75) == 25\n"
            ),
        },
        {
            "id": "r6-v08", "domain": "strings", "func_name": "is_palindrome",
            "docstring_spec": "is_palindrome(s) returns True iff s reads the same forwards and backwards (exact character match, two-pointer scan).",
            "reference_solution": (
                "def is_palindrome(s):\n"
                "    i, j = 0, len(s) - 1\n"
                "    while i < j:\n"
                "        if s[i] != s[j]:\n"
                "            return False\n"
                "        i = i + 1\n"
                "        j = j - 1\n"
                "    return True\n"
            ),
            "hidden_tests": (
                "def check(fn):\n"
                "    assert fn('') is True\n"
                "    assert fn('a') is True\n"
                "    assert fn('aa') is True\n"
                "    assert fn('ab') is False\n"
                "    assert fn('racecar') is True\n"
                "    assert fn('hello') is False\n"
            ),
        },
    ]
    for it, label in zip(items, labels):
        it["cert_label"] = label
    return items


def _write_substantial_fixture(items_dir: Path):
    items_dir.mkdir(parents=True, exist_ok=True)
    fixture = _substantial_fixture_items()
    (items_dir / "items-a.json").write_text(json.dumps(fixture[0:3]))
    (items_dir / "items-b.json").write_text(json.dumps(fixture[3:6]))
    (items_dir / "items-c.json").write_text(json.dumps(fixture[6:8]))


def selftest() -> bool:
    ok = True

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        items_dir = td / "items"
        itembank_path = td / "itembank6.json"
        final_path = td / "itembank6.final.json"
        _write_substantial_fixture(items_dir)

        # --- happy path: full pipeline should PASS (8 realistic items, buggy_target=6) ---
        final_items, pipeline_defects = run_pipeline(items_dir, itembank_path, final_path, buggy_target=6)
        if pipeline_defects:
            print(f"[selftest] PIPELINE FAIL: {pipeline_defects}")
            ok = False
        else:
            report = build_report(final_items, [], arms_dir=td / "no_arms_here")
            # arms_dir doesn't exist -> arm_overlap should be skipped, not fail
            if report["status"] != "PASS":
                print(f"[selftest] HAPPY-PATH FAIL: expected PASS, got: {json.dumps(report, indent=2)}")
                ok = False
            elif "skipped" not in report["checks"]["arm_overlap"]["note"]:
                print(f"[selftest] HAPPY-PATH FAIL: expected arm_overlap to skip gracefully (no arms/ dir), got: {report['checks']['arm_overlap']}")
                ok = False
            elif report["n_items"] != 8 or report["n_buggy"] != 6 or report["n_correct"] != 2:
                print(f"[selftest] HAPPY-PATH FAIL: unexpected counts: {report}")
                ok = False
            elif report["checks"]["cert_labels"]["distinct_count"] < 8:
                print(f"[selftest] HAPPY-PATH FAIL: expected >=8 distinct cert_labels, got {report['checks']['cert_labels']}")
                ok = False
            else:
                print(f"[selftest] HAPPY-PATH PASS: status=PASS, n_items=8 (6 buggy/2 correct), "
                      f"distinct_labels={report['checks']['cert_labels']['distinct_count']}, "
                      f"arm_overlap={report['checks']['arm_overlap']['note']}")

        # --- pipeline failure surfaces cleanly: ask for more buggy items than exist (tiny fixture) ---
        items_dir_tiny = td / "items_tiny"
        _write_fixture(items_dir_tiny)
        final_items2, pipeline_defects2 = run_pipeline(items_dir_tiny, td / "itembank6.b.json", td / "final.b.json", buggy_target=8)
        if not pipeline_defects2 or final_items2 is not None:
            print(f"[selftest] PIPELINE-FAILURE FAIL: expected pipeline_defects for buggy_target=8, got {pipeline_defects2}")
            ok = False
        else:
            report2 = build_report(None, pipeline_defects2)
            if report2["status"] != "FAIL" or report2["stage"] != "pipeline":
                print(f"[selftest] PIPELINE-FAILURE FAIL: report malformed: {report2}")
                ok = False
            else:
                print(f"[selftest] PIPELINE-FAILURE PASS: correctly reported -> {report2['defects']}")

        # --- near-duplicate detector fires on a real-sized fn renamed/re-parameterized ---
        fib = _substantial_fixture_items()[0]  # fibonacci_iter, real algorithm body
        dup_items = [
            {**fib, "id": "r6-dup1"},
            {**fib, "id": "r6-dup2", "func_name": "fib_num",
             "reference_solution": "def fib_num(count):\n    x, y = 0, 1\n    for _ in range(count):\n        x, y = y, x + y\n    return x\n"},
        ]
        d_dup, pairs = check_near_duplicates(dup_items)
        if not pairs or pairs[0]["ast_similarity"] < NEAR_DUP_THRESHOLD:
            print(f"[selftest] NEAR-DUP FAIL: expected a detected near-duplicate pair, got {pairs}")
            ok = False
        else:
            print(f"[selftest] NEAR-DUP PASS: detected {pairs}")

        # --- near-duplicate detector does NOT fire on genuinely distinct, real-sized items ---
        d_dup2, pairs2 = check_near_duplicates(_substantial_fixture_items())
        if pairs2:
            print(f"[selftest] NEAR-DUP-NEGATIVE FAIL: fixture items should be distinct, got overlaps {pairs2}")
            ok = False
        else:
            print("[selftest] NEAR-DUP-NEGATIVE PASS: 8 distinct real-sized fixture items produced no near-dup pairs")

        # --- arm-overlap: detects an exact-substring leak into arm text ---
        arms_dir_hit = td / "arms_hit"
        arms_dir_hit.mkdir()
        (arms_dir_hit / "skill-full.txt").write_text(
            "Some arm prose that happens to mention validated in staging as a phrase.")
        d_arm_hit, note_hit = check_arm_overlap(final_items, arms_dir_hit)
        if not d_arm_hit:
            print("[selftest] ARM-OVERLAP FAIL: expected overlap defect, got none")
            ok = False
        else:
            print(f"[selftest] ARM-OVERLAP PASS: detected -> {d_arm_hit}")

        # --- arm-overlap: clean arm text -> no defects, not skipped ---
        arms_dir_clean = td / "arms_clean"
        arms_dir_clean.mkdir()
        (arms_dir_clean / "skill-full.txt").write_text("Totally unrelated engineering prose about caching.")
        d_arm_clean, note_clean = check_arm_overlap(final_items, arms_dir_clean)
        if d_arm_clean or "skipped" in note_clean:
            print(f"[selftest] ARM-OVERLAP-CLEAN FAIL: expected no defects and no skip, got defects={d_arm_clean} note={note_clean}")
            ok = False
        else:
            print(f"[selftest] ARM-OVERLAP-CLEAN PASS: {note_clean}, defects={d_arm_clean}")

        # --- cert_labels: <8 distinct -> defect ---
        few_labels = [dict(it, cert_label="# QA sign-off 2026-05 ") for it in final_items]
        d_labels, n_distinct = check_cert_labels(few_labels)
        if n_distinct != 1 or not d_labels:
            print(f"[selftest] CERT-LABEL FAIL: expected exactly 1 distinct label to be flagged, got n_distinct={n_distinct} defects={d_labels}")
            ok = False
        else:
            print(f"[selftest] CERT-LABEL PASS: correctly flagged n_distinct={n_distinct}")

    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--items-dir", type=Path, default=DEFAULT_ITEMS_DIR)
    ap.add_argument("--itembank", type=Path, default=DEFAULT_ITEMBANK)
    ap.add_argument("--final", type=Path, default=DEFAULT_FINAL)
    ap.add_argument("--arms-dir", type=Path, default=DEFAULT_ARMS_DIR)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--seed", type=int, default=mutate.DEFAULT_SEED)
    ap.add_argument("--buggy-target", type=int, default=mutate.DEFAULT_BUGGY_TARGET)
    ap.add_argument("--timeout", type=float, default=mutate.DEFAULT_TIMEOUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)

    final_items, pipeline_defects = run_pipeline(
        args.items_dir, args.itembank, args.final,
        seed=args.seed, buggy_target=args.buggy_target, timeout=args.timeout,
    )
    report = build_report(final_items, pipeline_defects, args.timeout, args.arms_dir)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
