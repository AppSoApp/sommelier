#!/usr/bin/env python3
"""Merge candidate files (argv), dedup by buggy_module content, assign unique ids,
keep only tasks where:
  (1) buggy fn PASSES surface_tests  (headroom: bug invisible on obvious inputs)
  (2) buggy fn FAILS bug_tests       (hidden edge exposes it)
  (3) correct fn + feature PASSES surface + bug + feature tests (reference sound)
Writes itembank.json."""
import json, subprocess, sys, tempfile, os, hashlib

def run(src):
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write(src + "\nprint('OK')\n"); path=f.name
    try:
        r=subprocess.run([sys.executable,path],capture_output=True,text=True,timeout=10)
        return r.returncode==0 and 'OK' in r.stdout
    except Exception:
        return False
    finally:
        os.unlink(path)

def valid(t):
    try:
        bm=t['buggy_module']; cf=t['correct_function']; ff=t['correct_feature']
        st="\n".join(t['surface_tests']); bt="\n".join(t['bug_tests']); ft="\n".join(t['feature_tests'])
        if not (st and bt and ft): return False
        if not run(bm+"\n"+st): return False
        if run(bm+"\n"+bt): return False
        if not run(cf+"\n"+ff+"\n"+st+"\n"+bt+"\n"+ft): return False
        return True
    except Exception:
        return False

def main(paths):
    cands=[]
    for p in paths:
        d=json.load(open(p)); cands += d['candidates'] if 'candidates' in d else d
    seen=set(); bank=[]; i=0
    for t in cands:
        try: h=hashlib.md5(t['buggy_module'].encode()).hexdigest()
        except Exception: continue
        if h in seen: continue
        if valid(t):
            seen.add(h)
            bank.append({'id': f't{i}', 'buggy_module': t['buggy_module'], 'feature_desc': t['feature_desc'],
                         'surface_tests': t['surface_tests'], 'bug_tests': t['bug_tests'], 'feature_tests': t['feature_tests']})
            i+=1
    json.dump({'tasks': bank}, open('itembank.json','w'), indent=1)
    print(f"merged_candidates={len(cands)}  unique_valid={len(bank)}")

if __name__=='__main__':
    main(sys.argv[1:])
