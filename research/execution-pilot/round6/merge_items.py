#!/usr/bin/env python3
"""merge_items.py -- Round 6 itembank merge tool.

Reads round6/items/items-{a,b,c}.json (three arrays of item dicts, one per
sibling worker), schema-checks every item, checks for duplicate ids across
the three files, and writes a single sorted-by-id array to
round6/itembank6.json.

Item schema (all fields required, all strings):
    id, domain, func_name, docstring_spec, reference_solution,
    hidden_tests, cert_label

Exit code: 0 on success (itembank6.json written). Nonzero if any item
violates the schema or a source file is missing/unreadable -- the full
list of defects is printed to stderr (and to stdout for --selftest).

stdlib only. Deterministic (no network, no randomness).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ITEMS_DIR = SCRIPT_DIR / "items"
DEFAULT_OUT = SCRIPT_DIR / "itembank6.json"

SOURCE_FILES = ["items-a.json", "items-b.json", "items-c.json"]
REQUIRED_FIELDS = [
    "id",
    "domain",
    "func_name",
    "docstring_spec",
    "reference_solution",
    "hidden_tests",
    "cert_label",
]

ID_RE = re.compile(r"^r6-[A-Za-z0-9]+$")
FUNC_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def validate_item(item, source_file) -> list[str]:
    """Return a list of human-readable defect strings for `item` (empty = valid)."""
    defects = []
    label = f"{source_file}"
    if not isinstance(item, dict):
        return [f"{label}: item is not a JSON object: {item!r}"]

    iid = item.get("id", "<no-id>")
    label = f"{source_file}/{iid}"

    for field in REQUIRED_FIELDS:
        if field not in item:
            defects.append(f"{label}: missing required field '{field}'")
        elif not isinstance(item[field], str):
            defects.append(f"{label}: field '{field}' is not a string")
        elif field != "reference_solution" and not item[field].strip():
            # reference_solution's own emptiness will surface as a parse error below
            defects.append(f"{label}: field '{field}' is empty")

    if defects:
        # Structural problems -- deeper (AST) checks would be unreliable.
        return defects

    if not ID_RE.match(item["id"]):
        defects.append(f"{label}: id '{item['id']}' does not match pattern r6-<worker><nn>")
    if not FUNC_NAME_RE.match(item["func_name"]):
        defects.append(f"{label}: func_name '{item['func_name']}' is not snake_case")
    if not item["cert_label"].lstrip().startswith("#"):
        defects.append(f"{label}: cert_label must start with '#' (got {item['cert_label']!r})")

    try:
        tree = ast.parse(item["reference_solution"])
    except SyntaxError as e:
        defects.append(f"{label}: reference_solution has invalid Python syntax: {e}")
        tree = None
    if tree is not None:
        fn_names = {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if item["func_name"] not in fn_names:
            defects.append(
                f"{label}: reference_solution does not define a function named "
                f"'{item['func_name']}' (found: {sorted(fn_names) or 'none'})"
            )

    try:
        htree = ast.parse(item["hidden_tests"])
        check_fns = {
            n.name: n for n in ast.walk(htree) if isinstance(n, ast.FunctionDef)
        }
        if "check" not in check_fns:
            defects.append(f"{label}: hidden_tests does not define a 'check' function")
        elif len(check_fns["check"].args.args) != 1:
            defects.append(f"{label}: hidden_tests 'check' must take exactly one argument")
    except SyntaxError as e:
        defects.append(f"{label}: hidden_tests has invalid Python syntax: {e}")

    return defects


def run_merge(items_dir: Path, out_path: Path | None) -> list[str]:
    """Merge items-{a,b,c}.json under items_dir. Writes sorted array to out_path
    if out_path is given and there are no defects. Returns the list of defect
    strings (empty == success)."""
    defects: list[str] = []
    seen_ids: dict[str, str] = {}
    merged: list[dict] = []

    for fname in SOURCE_FILES:
        path = items_dir / fname
        if not path.exists():
            defects.append(f"{fname}: file not found under {items_dir}")
            continue
        try:
            raw = path.read_text()
        except OSError as e:
            defects.append(f"{fname}: could not read file: {e}")
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            defects.append(f"{fname}: invalid JSON: {e}")
            continue
        if not isinstance(data, list):
            defects.append(f"{fname}: top-level JSON must be an array, got {type(data).__name__}")
            continue

        for item in data:
            item_defects = validate_item(item, fname)
            if item_defects:
                defects.extend(item_defects)
                continue
            iid = item["id"]
            if iid in seen_ids:
                defects.append(
                    f"{fname}: duplicate id '{iid}' (already seen in {seen_ids[iid]})"
                )
                continue
            seen_ids[iid] = fname
            merged.append(item)

    if defects:
        return defects

    merged.sort(key=lambda it: it["id"])
    if out_path is not None:
        out_path.write_text(json.dumps(merged, indent=2) + "\n")
    return []


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def _valid_fixture_item(i: int) -> dict:
    return {
        "id": f"r6-x{i:02d}",
        "domain": "arithmetic",
        "func_name": f"fn{i}",
        "docstring_spec": f"fn{i}(x) returns x + {i}.",
        "reference_solution": f"def fn{i}(x):\n    return x + {i}\n",
        "hidden_tests": (
            "def check(fn):\n"
            f"    assert fn({i}) == {2*i}\n"
            f"    assert fn(0) == {i}\n"
        ),
        "cert_label": f"# QA sign-off 2026-05 ",
    }


def selftest() -> bool:
    ok = True

    # --- test 1: valid fixture -> success, sorted output ---
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        items_dir = td / "items"
        items_dir.mkdir()
        fixture = [_valid_fixture_item(i) for i in (3, 1, 2)]
        (items_dir / "items-a.json").write_text(json.dumps([fixture[0]]))
        (items_dir / "items-b.json").write_text(json.dumps([fixture[1]]))
        (items_dir / "items-c.json").write_text(json.dumps([fixture[2]]))
        out_path = td / "itembank6.json"
        defects = run_merge(items_dir, out_path)
        if defects:
            print(f"[selftest] TEST1 FAIL: expected no defects, got: {defects}")
            ok = False
        else:
            written = json.loads(out_path.read_text())
            ids = [it["id"] for it in written]
            if ids != sorted(ids) or len(ids) != 3:
                print(f"[selftest] TEST1 FAIL: bad output ordering/count: {ids}")
                ok = False
            else:
                print(f"[selftest] TEST1 PASS: merged+sorted {ids}")

    # --- test 2: missing field -> defects reported, nonzero-equivalent ---
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        items_dir = td / "items"
        items_dir.mkdir()
        bad = _valid_fixture_item(9)
        del bad["docstring_spec"]
        (items_dir / "items-a.json").write_text(json.dumps([bad]))
        (items_dir / "items-b.json").write_text(json.dumps([]))
        (items_dir / "items-c.json").write_text(json.dumps([]))
        out_path = td / "itembank6.json"
        defects = run_merge(items_dir, out_path)
        if not defects or out_path.exists():
            print(f"[selftest] TEST2 FAIL: expected defects and no output file, got defects={defects} exists={out_path.exists()}")
            ok = False
        else:
            print(f"[selftest] TEST2 PASS: correctly rejected -> {defects}")

    # --- test 3: duplicate id across files -> defect ---
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        items_dir = td / "items"
        items_dir.mkdir()
        dup1 = _valid_fixture_item(5)
        dup2 = _valid_fixture_item(5)
        (items_dir / "items-a.json").write_text(json.dumps([dup1]))
        (items_dir / "items-b.json").write_text(json.dumps([dup2]))
        (items_dir / "items-c.json").write_text(json.dumps([]))
        out_path = td / "itembank6.json"
        defects = run_merge(items_dir, out_path)
        if not any("duplicate id" in d for d in defects):
            print(f"[selftest] TEST3 FAIL: expected duplicate-id defect, got: {defects}")
            ok = False
        else:
            print(f"[selftest] TEST3 PASS: duplicate id detected -> {defects}")

    # --- test 4: missing source file entirely -> defect, no crash ---
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        items_dir = td / "items"
        items_dir.mkdir()
        (items_dir / "items-a.json").write_text(json.dumps([_valid_fixture_item(1)]))
        # items-b.json, items-c.json intentionally absent
        out_path = td / "itembank6.json"
        defects = run_merge(items_dir, out_path)
        if not any("not found" in d for d in defects):
            print(f"[selftest] TEST4 FAIL: expected 'not found' defect, got: {defects}")
            ok = False
        else:
            print(f"[selftest] TEST4 PASS: missing-file handled gracefully -> {defects}")

    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--items-dir", type=Path, default=DEFAULT_ITEMS_DIR)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)

    defects = run_merge(args.items_dir, args.out)
    if defects:
        print("SCHEMA VALIDATION FAILED:", file=sys.stderr)
        for d in defects:
            print(f"  - {d}", file=sys.stderr)
        sys.exit(1)
    n = len(json.loads(args.out.read_text()))
    print(f"OK: merged {n} items -> {args.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
