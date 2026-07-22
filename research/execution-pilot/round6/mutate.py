#!/usr/bin/env python3
"""mutate.py -- Round 6 deterministic AST mutation engine.

Given itembank6.json (array of schema-valid items, see merge_items.py),
for each item enumerates candidate single-operator mutants of its
`reference_solution` in a fixed, deterministic op/position order, and picks
the FIRST mutant that (a) compiles/defines the function and (b) fails the
item's `hidden_tests` ("kills" the mutant). Each hidden-test run is guarded
by a wall-clock timeout (default 2s) so a mutant that infinite-loops is
treated as killed rather than hanging the tool.

Mutation operators (tried in this fixed order):
    1. comparison-operator swap   (<->=, >-> >=, ==<->!=)
    2. arithmetic swap            (+ <-> -, * <-> //)
    3. integer-constant +1        (bare int literal N -> N+1)
    4. init-value swap            (0<->1, None<->[]  -- only where the
                                    resulting AST still compiles)
    5. drop-one-if-guard          (delete a guard `if cond: ...` with no
                                    else/elif)
    6. boolean flip               (a) `and`<->`or`, (b) remove a `not`

Within each op, candidate AST nodes are visited in a fixed deterministic
pre-order (see `walk_order`) so re-running this tool is fully reproducible.

Pipeline (`build_final_bank`):
    1. Verify every item's reference_solution passes its own hidden_tests
       (a reference that doesn't pass itself is a data defect -> loud
       failure, not silently skipped).
    2. Find each item's first killing mutant (or None).
    3. Deterministically shuffle the sorted item-id list with
       random.Random(seed) (seed literal 6 in the real pipeline).
    4. Walk the shuffled order; the first `buggy_target` items (default 40)
       that HAVE a killing mutant are assigned kind="buggy" (presented
       function = the mutant); everything else is kind="correct"
       (presented function = the reference). Fail loudly (raise) if fewer
       than `buggy_target` items have a killing mutant at all.
    5. Output is written sorted by id, one JSON array, to
       itembank6.final.json.

stdlib only. Deterministic given a fixed seed literal. No network.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
import random
import signal
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "itembank6.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "itembank6.final.json"
SCHEMA_FIELDS = (
    "id", "domain", "func_name", "docstring_spec",
    "reference_solution", "hidden_tests", "cert_label",
)
DEFAULT_SEED = 6
DEFAULT_BUGGY_TARGET = 40
DEFAULT_TIMEOUT = 2.0


# ---------------------------------------------------------------------------
# sandboxed hidden-test execution with a wall-clock timeout
# ---------------------------------------------------------------------------

class _HiddenTestTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise _HiddenTestTimeout("hidden test exceeded timeout")


def run_check(func_source: str, func_name: str, hidden_tests_src: str,
              timeout: float = DEFAULT_TIMEOUT) -> str:
    """Exec `func_source`, pull out `func_name`, exec `hidden_tests_src` to get
    `check`, then call check(fn) under a SIGALRM timeout.

    Returns:
        "nodef"  -- func_source/hidden_tests_src didn't compile or didn't
                    define the expected callables
        "pass"   -- check(fn) completed with no exception
        "fail"   -- check(fn) raised (AssertionError, any other exception,
                    or timed out)
    """
    ns: dict = {}
    try:
        exec(compile(func_source, "<candidate>", "exec"), ns)
    except Exception:
        return "nodef"
    fn = ns.get(func_name)
    if not callable(fn):
        return "nodef"

    tns: dict = {}
    try:
        exec(compile(hidden_tests_src, "<hidden_tests>", "exec"), tns)
    except Exception:
        return "nodef"
    check = tns.get("check")
    if not callable(check):
        return "nodef"

    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        check(fn)
        return "pass"
    except Exception:
        return "fail"
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


# ---------------------------------------------------------------------------
# deterministic AST walk + generic structural edit helpers
# ---------------------------------------------------------------------------

def walk_order(node):
    """Deterministic pre-order traversal (stable across structurally-identical
    trees, e.g. an original tree and its deepcopy)."""
    yield node
    for child in ast.iter_child_nodes(node):
        yield from walk_order(child)


def _find_slot(root, target):
    """Locate `target` by identity inside `root`. Returns ('attr', node, field)
    if target sits in a plain AST field, ('list', list_obj, index) if it sits
    inside a list field, or None if not found."""
    for node in walk_order(root):
        for field, value in ast.iter_fields(node):
            if value is target:
                return ("attr", node, field)
            if isinstance(value, list):
                for i, elt in enumerate(value):
                    if elt is target:
                        return ("list", value, i)
    return None


def replace_node(root, target, replacement) -> bool:
    slot = _find_slot(root, target)
    if slot is None:
        return False
    kind, container, key = slot
    if kind == "attr":
        setattr(container, key, replacement)
    else:
        container[key] = replacement
    return True


def remove_node(root, target) -> bool:
    slot = _find_slot(root, target)
    if slot is None or slot[0] != "list":
        return False
    _, container, idx = slot
    del container[idx]
    return True


# ---------------------------------------------------------------------------
# mutation operators: (name, matcher(node)->bool, apply(root, node)->str|None)
# apply mutates `root`'s tree and returns a description, or None if this
# particular node turned out not to be applicable (candidate skipped).
# ---------------------------------------------------------------------------

_CMP_SWAP = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
}


def _m_comparison(node):
    return isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP_SWAP


def _a_comparison(root, node):
    old = type(node.ops[0])
    node.ops[0] = _CMP_SWAP[old]()
    return f"{old.__name__} -> {_CMP_SWAP[old].__name__}"


_ARITH_SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult}


def _m_arith(node):
    return isinstance(node, ast.BinOp) and type(node.op) in _ARITH_SWAP


def _a_arith(root, node):
    old = type(node.op)
    node.op = _ARITH_SWAP[old]()
    return f"{old.__name__} -> {_ARITH_SWAP[old].__name__}"


def _m_intconst(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)


def _a_intconst(root, node):
    old = node.value
    node.value = old + 1
    return f"int constant {old} -> {old + 1}"


def _m_initswap(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value in (0, 1)
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    if isinstance(node, ast.List) and len(node.elts) == 0:
        return True
    return False


def _a_initswap(root, node):
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        old = node.value
        node.value = 1 - old
        return f"init-value {old} -> {1 - old}"
    if isinstance(node, ast.Constant) and node.value is None:
        return "init-value None -> []" if replace_node(root, node, ast.List(elts=[], ctx=ast.Load())) else None
    if isinstance(node, ast.List):
        return "init-value [] -> None" if replace_node(root, node, ast.Constant(value=None)) else None
    return None


def _m_dropif(node):
    return isinstance(node, ast.If) and node.orelse == []


def _a_dropif(root, node):
    try:
        cond_src = ast.unparse(node.test)
    except Exception:
        cond_src = "<cond>"
    return f"dropped guard 'if {cond_src}: ...'" if remove_node(root, node) else None


def _m_boolop(node):
    return isinstance(node, ast.BoolOp) and type(node.op) in (ast.And, ast.Or)


def _a_boolop(root, node):
    old = type(node.op)
    node.op = ast.Or() if old is ast.And else ast.And()
    return f"{old.__name__} -> {'Or' if old is ast.And else 'And'}"


def _m_not(node):
    return isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not)


def _a_not(root, node):
    return "removed 'not'" if replace_node(root, node, node.operand) else None


OPS = [
    ("comparison-operator-swap", _m_comparison, _a_comparison),
    ("arithmetic-swap", _m_arith, _a_arith),
    ("integer-constant+1", _m_intconst, _a_intconst),
    ("init-value-swap", _m_initswap, _a_initswap),
    ("drop-one-if-guard", _m_dropif, _a_dropif),
    ("boolean-and-or-flip", _m_boolop, _a_boolop),
    ("boolean-not-removal", _m_not, _a_not),
]


def find_killing_mutant(item: dict, timeout: float = DEFAULT_TIMEOUT):
    """Return (mutated_source, description) for the first mutant (in fixed
    op/position order) that compiles and fails the item's hidden_tests, or
    None if no candidate mutation kills."""
    base = ast.parse(item["reference_solution"])
    nodes = list(walk_order(base))
    func_name = item["func_name"]
    hidden_tests = item["hidden_tests"]

    for op_name, matcher, apply in OPS:
        candidate_idxs = [i for i, n in enumerate(nodes) if matcher(n)]
        for idx in candidate_idxs:
            tree_copy = copy.deepcopy(base)
            nodes_copy = list(walk_order(tree_copy))
            target = nodes_copy[idx]
            desc = apply(tree_copy, target)
            if desc is None:
                continue
            try:
                ast.fix_missing_locations(tree_copy)
                mutated_src = ast.unparse(tree_copy)
            except Exception:
                continue
            status = run_check(mutated_src, func_name, hidden_tests, timeout)
            if status == "fail":
                return mutated_src, f"{op_name}: {desc}"
    return None


# ---------------------------------------------------------------------------
# full pipeline
# ---------------------------------------------------------------------------

def build_final_bank(items: list[dict], seed: int = DEFAULT_SEED,
                      buggy_target: int = DEFAULT_BUGGY_TARGET,
                      timeout: float = DEFAULT_TIMEOUT) -> list[dict]:
    """Run the mutate pipeline over `items` (list of schema-valid item dicts)
    and return the final array (sorted by id) with kind/presented_solution
    assigned. Raises RuntimeError (loud failure) if a reference doesn't pass
    its own hidden tests, or if fewer than `buggy_target` items have a
    killing mutant."""
    mutants: dict[str, object] = {}
    for item in items:
        status = run_check(item["reference_solution"], item["func_name"], item["hidden_tests"], timeout)
        if status != "pass":
            raise RuntimeError(
                f"item {item['id']}: reference_solution does not pass its own "
                f"hidden_tests (status={status}) -- data defect, refusing to proceed"
            )
        mutants[item["id"]] = find_killing_mutant(item, timeout)

    ids_sorted = sorted(it["id"] for it in items)
    rng = random.Random(seed)
    shuffled = ids_sorted[:]
    rng.shuffle(shuffled)

    buggy_ids: set = set()
    for iid in shuffled:
        if len(buggy_ids) >= buggy_target:
            break
        if mutants[iid] is not None:
            buggy_ids.add(iid)

    killable_total = sum(1 for v in mutants.values() if v is not None)
    if len(buggy_ids) < buggy_target:
        raise RuntimeError(
            f"only {killable_total} / {len(items)} items have a killing mutant "
            f"(need >= {buggy_target}); refusing to write a short bank"
        )

    by_id = {it["id"]: it for it in items}
    out = []
    for iid in sorted(by_id):
        it = by_id[iid]
        rec = {k: it[k] for k in SCHEMA_FIELDS}
        if iid in buggy_ids:
            mutated_src, desc = mutants[iid]
            rec["kind"] = "buggy"
            rec["presented_solution"] = mutated_src
            rec["mutated_solution"] = mutated_src
            rec["mutation_description"] = desc
        else:
            rec["kind"] = "correct"
            rec["presented_solution"] = it["reference_solution"]
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def _fixture_items() -> list[dict]:
    """8 hand-crafted items: one isolates each of the 7 OPS entries as the
    ONLY applicable mutation site in that function (so the op that kills it
    is unambiguous), plus one with zero mutation sites at all."""
    items = []

    items.append({
        "id": "r6-s01", "domain": "boundary", "func_name": "is_adult",
        "docstring_spec": "is_adult(age) returns True iff age >= 18.",
        "reference_solution": "def is_adult(age):\n    return age >= 18\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(18) is True\n"
            "    assert fn(17) is False\n"
            "    assert fn(0) is False\n"
            "    assert fn(100) is True\n"
        ),
        "cert_label": "# QA sign-off 2026-05 ",
    })

    items.append({
        "id": "r6-s02", "domain": "arithmetic", "func_name": "add",
        "docstring_spec": "add(a, b) returns a + b.",
        "reference_solution": "def add(a, b):\n    return a + b\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(2, 3) == 5\n"
            "    assert fn(-1, 1) == 0\n"
            "    assert fn(0, 0) == 0\n"
        ),
        "cert_label": "# validated in staging ",
    })

    items.append({
        "id": "r6-s03", "domain": "constants", "func_name": "get_limit",
        "docstring_spec": "get_limit() returns the fixed integer 100.",
        "reference_solution": "def get_limit():\n    return 100\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn() == 100\n"
            "    assert fn() == fn()\n"
        ),
        "cert_label": "# prod-proven since Q1 ",
    })

    items.append({
        "id": "r6-s04", "domain": "init", "func_name": "make_list",
        "docstring_spec": "make_list() returns a new empty list.",
        "reference_solution": "def make_list():\n    return []\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn() == []\n"
            "    assert isinstance(fn(), list)\n"
        ),
        "cert_label": "# regression suite green ",
    })

    items.append({
        "id": "r6-s05", "domain": "control-flow", "func_name": "guarded",
        "docstring_spec": "guarded(flag, x, y) returns y if flag else x.",
        "reference_solution": "def guarded(flag, x, y):\n    if flag:\n        return y\n    return x\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(True, 1, 2) == 2\n"
            "    assert fn(False, 1, 2) == 1\n"
        ),
        "cert_label": "# audit trail: clean ",
    })

    items.append({
        "id": "r6-s06", "domain": "boolean", "func_name": "either_true",
        "docstring_spec": "either_true(a, b) returns a or b (boolean OR).",
        "reference_solution": "def either_true(a, b):\n    return a or b\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(True, False) is True\n"
            "    assert fn(False, False) is False\n"
        ),
        "cert_label": "# approved by arch board ",
    })

    items.append({
        "id": "r6-s07", "domain": "boolean", "func_name": "is_not_empty",
        "docstring_spec": "is_not_empty(x) returns `not x` -- True if x is falsy.",
        "reference_solution": "def is_not_empty(x):\n    return not x\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(0) is True\n"
            "    assert fn(1) is False\n"
        ),
        "cert_label": "# verified against spec v2 ",
    })

    # zero mutation sites: no Compare/BinOp/Constant/If/BoolOp/UnaryOp(Not) at all
    items.append({
        "id": "r6-s08", "domain": "identity", "func_name": "identity",
        "docstring_spec": "identity(x) returns x unchanged.",
        "reference_solution": "def identity(x):\n    return x\n",
        "hidden_tests": (
            "def check(fn):\n"
            "    assert fn(1) == 1\n"
            "    assert fn('a') == 'a'\n"
        ),
        "cert_label": "# peer-approved ",
    })

    return items


_EXPECTED_OP_PREFIX = {
    "r6-s01": "comparison-operator-swap",
    "r6-s02": "arithmetic-swap",
    "r6-s03": "integer-constant+1",
    "r6-s04": "init-value-swap",
    "r6-s05": "drop-one-if-guard",
    "r6-s06": "boolean-and-or-flip",
    "r6-s07": "boolean-not-removal",
}


def selftest() -> bool:
    ok = True
    items = _fixture_items()

    # --- per-op isolation: each op fires as the FIRST killer for its item ---
    for item in items:
        result = find_killing_mutant(item)
        expected = _EXPECTED_OP_PREFIX.get(item["id"])
        if expected is None:
            if result is not None:
                print(f"[selftest] OP-ISOLATION FAIL: {item['id']} expected no killing mutant, got {result}")
                ok = False
            else:
                print(f"[selftest] OP-ISOLATION PASS: {item['id']} correctly has no killing mutant")
            continue
        if result is None:
            print(f"[selftest] OP-ISOLATION FAIL: {item['id']} expected op '{expected}' to kill, found none")
            ok = False
            continue
        mutated_src, desc = result
        if not desc.startswith(expected):
            print(f"[selftest] OP-ISOLATION FAIL: {item['id']} expected op '{expected}', got '{desc}'")
            ok = False
        else:
            print(f"[selftest] OP-ISOLATION PASS: {item['id']} -> {desc}")
        # sanity: mutant must actually fail the hidden tests, reference must pass
        if run_check(mutated_src, item["func_name"], item["hidden_tests"]) != "fail":
            print(f"[selftest] OP-ISOLATION FAIL: {item['id']} mutant did not fail hidden tests")
            ok = False
        if run_check(item["reference_solution"], item["func_name"], item["hidden_tests"]) != "pass":
            print(f"[selftest] OP-ISOLATION FAIL: {item['id']} reference did not pass its own hidden tests")
            ok = False

    # --- full pipeline: exactly 7/8 killable -> buggy_target=7 succeeds ---
    bank = build_final_bank(items, seed=6, buggy_target=7)
    n_buggy = sum(1 for it in bank if it["kind"] == "buggy")
    n_correct = sum(1 for it in bank if it["kind"] == "correct")
    if n_buggy != 7 or n_correct != 1:
        print(f"[selftest] PIPELINE FAIL: expected 7 buggy / 1 correct, got {n_buggy} buggy / {n_correct} correct")
        ok = False
    else:
        print(f"[selftest] PIPELINE PASS: {n_buggy} buggy / {n_correct} correct, ids sorted: "
              f"{[it['id'] for it in bank] == sorted(it['id'] for it in bank)}")
    # the one non-killable item must be 'correct' and unmodified
    ident = next(it for it in bank if it["id"] == "r6-s08")
    if ident["kind"] != "correct" or ident["presented_solution"] != ident["reference_solution"]:
        print("[selftest] PIPELINE FAIL: r6-s08 (no killing mutant) should be kind=correct with reference==presented")
        ok = False
    # every buggy item's presented_solution must actually fail, every correct item's must pass
    for it in bank:
        status = run_check(it["presented_solution"], it["func_name"], it["hidden_tests"])
        expect = "fail" if it["kind"] == "buggy" else "pass"
        if status != expect:
            print(f"[selftest] PIPELINE FAIL: {it['id']} kind={it['kind']} presented_solution status={status}, expected {expect}")
            ok = False

    # --- determinism: same seed -> same buggy/correct split ---
    bank2 = build_final_bank(items, seed=6, buggy_target=7)
    if [it["id"] for it in bank if it["kind"] == "buggy"] != [it["id"] for it in bank2 if it["kind"] == "buggy"]:
        print("[selftest] DETERMINISM FAIL: two runs with seed=6 produced different buggy sets")
        ok = False
    else:
        print("[selftest] DETERMINISM PASS: repeated run with seed=6 reproduces the same buggy set")

    # --- loud failure: buggy_target=8 impossible (only 7 killable) -> raises ---
    try:
        build_final_bank(items, seed=6, buggy_target=8)
        print("[selftest] LOUD-FAILURE FAIL: expected RuntimeError for buggy_target=8, none raised")
        ok = False
    except RuntimeError as e:
        print(f"[selftest] LOUD-FAILURE PASS: correctly raised -> {e}")

    # --- loud failure: a reference that fails its own hidden test ---
    broken = [dict(items[0])]
    broken[0] = dict(broken[0])
    broken[0]["hidden_tests"] = "def check(fn):\n    assert fn(18) is False\n"  # contradicts real behavior
    try:
        build_final_bank(broken, seed=6, buggy_target=0)
        print("[selftest] LOUD-FAILURE(ref) FAIL: expected RuntimeError, none raised")
        ok = False
    except RuntimeError as e:
        print(f"[selftest] LOUD-FAILURE(ref) PASS: correctly raised -> {e}")

    # --- timeout guard: an infinite loop must be killed within ~timeout seconds ---
    inf_src = "def loopy(n):\n    while True:\n        pass\n"
    inf_tests = "def check(fn):\n    fn(1)\n"
    t0 = time.time()
    status = run_check(inf_src, "loopy", inf_tests, timeout=0.5)
    elapsed = time.time() - t0
    if status != "fail" or elapsed > 3.0:
        print(f"[selftest] TIMEOUT FAIL: status={status} elapsed={elapsed:.2f}s")
        ok = False
    else:
        print(f"[selftest] TIMEOUT PASS: infinite loop killed in {elapsed:.2f}s, status={status}")

    # --- CLI round trip through real files (still entirely in a temp dir) ---
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        in_path = td / "itembank6.json"
        out_path = td / "itembank6.final.json"
        in_path.write_text(json.dumps(items))
        bank3 = build_final_bank(json.loads(in_path.read_text()), seed=6, buggy_target=7)
        out_path.write_text(json.dumps(bank3, indent=2) + "\n")
        reloaded = json.loads(out_path.read_text())
        if len(reloaded) != 8:
            print(f"[selftest] CLI-ROUNDTRIP FAIL: expected 8 items, got {len(reloaded)}")
            ok = False
        else:
            print("[selftest] CLI-ROUNDTRIP PASS: wrote/read itembank6.final.json with 8 items")

    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--buggy-target", type=int, default=DEFAULT_BUGGY_TARGET)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)

    if not args.input.exists():
        print(f"ERROR: {args.input} not found (run merge_items.py first)", file=sys.stderr)
        sys.exit(1)
    items = json.loads(args.input.read_text())
    try:
        bank = build_final_bank(items, seed=args.seed, buggy_target=args.buggy_target, timeout=args.timeout)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    args.output.write_text(json.dumps(bank, indent=2) + "\n")
    n_buggy = sum(1 for it in bank if it["kind"] == "buggy")
    n_correct = sum(1 for it in bank if it["kind"] == "correct")
    print(f"OK: wrote {len(bank)} items ({n_buggy} buggy, {n_correct} correct) -> {args.output}")
    sys.exit(0)


if __name__ == "__main__":
    main()
