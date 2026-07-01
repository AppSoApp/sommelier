#!/usr/bin/env python3
"""v1.1 grader v4 — robust prose-stripping extractor (behavioral fix rate).
Extracts code even when the agent wraps it in prose (REFUTED/VERIFIED narration),
so we measure bug-FIXING behavior, not output formatting. Unparseable rate kept as
a secondary usability finding. Primary: paired McNemar (1-sided) rule vs placebo on FIX."""
import json, re, subprocess, sys, tempfile, os, math
from concurrent.futures import ThreadPoolExecutor

def extract(code):
    if not isinstance(code, str): return ""
    blocks = re.findall(r"```(?:python)?\s*(.*?)```", code, re.S)
    cands = [b for b in blocks if 'def ' in b]
    if cands: code = max(cands, key=len)
    elif blocks: code = max(blocks, key=len)
    lines = code.splitlines()
    starts = [i for i, l in enumerate(lines) if re.match(r"\s*(def |class |import |from |@|#)", l)]
    if not starts: return code.strip()
    cand = lines[starts[0]:]
    for end in range(len(cand), 0, -1):
        src = "\n".join(cand[:end])
        try:
            compile(src, "<s>", "exec")
            if "def " in src: return src
        except Exception:
            pass
    return "\n".join(cand)

CELL = """{code}
import json as _j
def _t(tests):
    try:
        exec(tests, globals()); return True
    except Exception: return False
print("RESULT:"+_j.dumps({{'surface':_t({s!r}),'bug':_t({b!r}),'feat':_t({f!r})}}))
"""

def grade_cell(code, t):
    src = extract(code)
    prog = CELL.format(code=src, s="\n".join(t['surface_tests']), b="\n".join(t['bug_tests']), f="\n".join(t['feature_tests']))
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as fh:
        fh.write(prog); path = fh.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=8)
        m = re.search(r"RESULT:(\{.*\})", r.stdout)
        if not m: return {'fix': 0, 'feat': 0, 'unpars': 1}
        d = json.loads(m.group(1))
        return {'fix': 1 if (d['surface'] and d['bug']) else 0, 'feat': 1 if d['feat'] else 0, 'unpars': 0}
    except Exception:
        return {'fix': 0, 'feat': 0, 'unpars': 1}
    finally:
        os.unlink(path)

def wilson(k, n, z=1.96):
    if not n: return [0.0, 0.0]
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return [round(100*(c-m)/d, 1), round(100*(c+m)/d, 1)]

def mcnemar(b, c):
    n = b+c
    if n == 0: return 1.0
    return round(min(1.0, sum(math.comb(n, k) for k in range(b, n+1))*(0.5**n)), 4)

def main(rows_path, bank_path):
    rows = json.load(open(rows_path)); rows = rows.get('rows', rows)
    bank = {t['id']: t for t in json.load(open(bank_path))['tasks']}
    arms = ['noskill', 'placebo', 'rule', 'skill']
    jobs = []
    for r in rows:
        t = bank.get(r['id'])
        if not t: continue
        for a in arms: jobs.append((r['tier'], r['id'], a, r['codes'].get(a, ''), t))
    res = {}
    with ThreadPoolExecutor(max_workers=16) as ex:
        for tier, tid, a, g in ex.map(lambda j: (j[0], j[1], j[2], grade_cell(j[3], j[4])), jobs):
            res.setdefault((tier, tid), {})[a] = g
    tiers = sorted({tr for (tr, _) in res})
    out = {'tiers': {}}
    for tier in tiers:
        cells = [c for (tr, _), c in res.items() if tr == tier]
        n = len(cells); arm_stat = {}
        for a in arms:
            fk = sum(c[a]['fix'] for c in cells); ftk = sum(c[a]['feat'] for c in cells); uk = sum(c[a]['unpars'] for c in cells)
            arm_stat[a] = {'fix_pct': round(100*fk/n), 'fix_ci': wilson(fk, n), 'fix_k': fk,
                           'feat_pct': round(100*ftk/n), 'feat_ci': wilson(ftk, n),
                           'unparseable_pct': round(100*uk/n), 'n': n}
        def disc(x, y):
            b = sum(1 for c in cells if c[x]['fix'] == 1 and c[y]['fix'] == 0)
            cc = sum(1 for c in cells if c[x]['fix'] == 0 and c[y]['fix'] == 1)
            return b, cc, mcnemar(b, cc)
        b1, c1, p1 = disc('rule', 'placebo'); b2, c2, p2 = disc('skill', 'placebo')
        out['tiers'][tier] = {'n': n, 'arms': arm_stat,
            'PRIMARY_rule_vs_placebo_FIX': {'rule_only': b1, 'placebo_only': c1, 'mcnemar_p_1sided': p1, 'sig_.05': p1 < 0.05},
            'skill_vs_placebo_FIX': {'skill_only': b2, 'placebo_only': c2, 'mcnemar_p_1sided': p2, 'sig_.05': p2 < 0.05}}
    open('grade_result.json', 'w').write(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
