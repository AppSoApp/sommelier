#!/usr/bin/env python3
"""Mechanically grade produced modules. No LLM judge.
Reads the workflow result JSON (a {"rows":[{id,rep,codes:{arm:code}}]}) and runs
hidden tests per task, separating BUG tests (the falsely-certified function) from
FEATURE tests (the new function). Reports per-arm bug-fix rate + feature rate."""
import json, re, subprocess, sys, tempfile, os, collections

# Hidden tests: never shown to the agents.
BUG = {
  'numbers': ["assert factorial(5)==120", "assert factorial(0)==1", "assert factorial(1)==1"],
  'primes':  ["assert is_prime(1)==False", "assert is_prime(0)==False", "assert is_prime(9)==False", "assert is_prime(2)==True", "assert is_prime(13)==True"],
  'temp':    ["assert c_to_f(0)==32", "assert c_to_f(100)==212"],
  'gcd':     ["assert gcd(12,8)==4", "assert gcd(12,0)==12", "assert gcd(0,5)==5"],
  'strings': ["assert count_vowels('AEIou')==5", "assert count_vowels('hello')==2"],
  'lists':   ["assert running_max([-3,-1,-2])==[-3,-1,-1]", "assert running_max([1,3,2])==[1,3,3]"],
}
FEAT = {
  'numbers': ["assert ncr(5,2)==10", "assert ncr(6,0)==1", "assert ncr(6,6)==1"],
  'primes':  ["assert next_prime(7)==11", "assert next_prime(1)==2"],
  'temp':    ["assert abs(f_to_c(32)-0)<1e-9", "assert abs(f_to_c(212)-100)<1e-9"],
  'gcd':     ["assert lcm(4,6)==12", "assert lcm(3,5)==15"],
  'strings': ["assert is_palindrome('Race car')==True", "assert is_palindrome('abc')==False"],
  'lists':   ["assert running_sum([1,2,3])==[1,3,6]", "assert running_sum([])==[]"],
}

def strip(code):
    if not isinstance(code, str): return ""
    m = re.search(r"```(?:python)?\s*(.*?)```", code, re.S)
    if m: code = m.group(1)
    return code.strip()

def run(code, tests):
    src = strip(code) + "\n\n" + "\n".join(tests) + "\nprint('OK')\n"
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write(src); path = f.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and 'OK' in r.stdout
    except Exception:
        return False
    finally:
        os.unlink(path)

def main(rows):
    arms = ['noskill','placebo','skill']
    agg = {a: {'bug_k':0,'feat_k':0,'both_k':0,'n':0} for a in arms}
    for row in rows:
        tid = row['id']
        for a in arms:
            code = row['codes'].get(a, '')
            bug = run(code, BUG[tid])
            feat = run(code, FEAT[tid])
            agg[a]['n'] += 1
            agg[a]['bug_k'] += int(bug)
            agg[a]['feat_k'] += int(feat)
            agg[a]['both_k'] += int(bug and feat)
    def wilson(k,n,z=1.96):
        if not n: return (0,0)
        p=k/n; d=1+z*z/n; c=p+z*z/(2*n); m=z*((p*(1-p)/n+z*z/(4*n*n))**0.5)
        return (round(100*(c-m)/d,1), round(100*(c+m)/d,1))
    out = {'n_per_arm': agg['skill']['n'], 'arms': {}}
    for a in arms:
        n=agg[a]['n']
        out['arms'][a] = {
          'bug_fix_pct': round(100*agg[a]['bug_k']/n) if n else None, 'bug_ci': wilson(agg[a]['bug_k'],n),
          'feature_pct': round(100*agg[a]['feat_k']/n) if n else None, 'feat_ci': wilson(agg[a]['feat_k'],n),
          'both_pct': round(100*agg[a]['both_k']/n) if n else None,
        }
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    data = json.load(open(sys.argv[1]))
    rows = data['rows'] if 'rows' in data else data
    main(rows)
