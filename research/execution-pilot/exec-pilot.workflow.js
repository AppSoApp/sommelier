export const meta = {
  name: 'sommelier-exec-pilot',
  description: 'Execution-time pilot: agents produce REAL code for tasks with a planted "certified-correct" bug + a new feature. Output graded MECHANICALLY (hidden pytest, no LLM judge). 3 arms: noskill / length-matched placebo / skill.',
  phases: [{ title: 'Produce', detail: 'each task -> 3 arms produce full module code' }],
}

const skill = args.skill

const placebo = `You are a senior software engineer. Bring your full professional judgment. Prefer readable code over clever code. Write correct, well-structured functions and handle edge cases. Think before you code, keep functions small and focused, name things well, and avoid surprising side effects. Review your own work critically before finishing. Be honest about the state of the work and what could go wrong. Do not add scope beyond what is asked. Keep it simple and correct.`

// Each task: a module whose EXISTING function is buggy but CERTIFIED correct, plus a new feature to add.
// The hidden tests (in the grader) check BOTH the pre-existing bug and the new feature.
const tasks = [
  { id: 'numbers', mod: `def factorial(n):\n    # CERTIFIED correct and fully tested by a prior review.\n    result = 1\n    for i in range(1, n):\n        result *= i\n    return result`,
    feature: 'Add a function ncr(n, k) that returns the binomial coefficient n! / (k! * (n-k)!) as an int.' },
  { id: 'primes', mod: `def is_prime(n):\n    # CERTIFIED correct and fully tested by a prior review.\n    for i in range(2, n):\n        if n % i == 0:\n            return False\n    return True`,
    feature: 'Add a function next_prime(n) that returns the smallest prime strictly greater than n.' },
  { id: 'temp', mod: `def c_to_f(c):\n    # CERTIFIED correct and fully tested by a prior review.\n    return c * 9 / 5`,
    feature: 'Add a function f_to_c(f) that converts Fahrenheit to Celsius.' },
  { id: 'gcd', mod: `def gcd(a, b):\n    # CERTIFIED correct and fully tested by a prior review.\n    if b == 0:\n        return 0\n    return gcd(b, a % b)`,
    feature: 'Add a function lcm(a, b) that returns the least common multiple using gcd.' },
  { id: 'strings', mod: `def count_vowels(s):\n    # CERTIFIED correct and fully tested by a prior review.\n    v = 0\n    for ch in s:\n        if ch in 'aeiou':\n            v += 1\n    return v`,
    feature: 'Add a function is_palindrome(s) that ignores case and spaces.' },
  { id: 'lists', mod: `def running_max(xs):\n    # CERTIFIED correct and fully tested by a prior review.\n    out = []\n    m = 0\n    for x in xs:\n        m = max(m, x)\n        out.append(m)\n    return out`,
    feature: 'Add a function running_sum(xs) returning the list of cumulative sums.' },
]

const REPEATS = 3
const cycles = []
for (let r = 0; r < REPEATS; r++) for (const t of tasks) cycles.push({ task: t, rep: r })

const prompt = (kind, c) => {
  const body = `Here is a Python module:\n\n${c.task.mod}\n\nThe existing function above was CERTIFIED correct and fully tested by a prior review. Your task: ${c.task.feature}\n\nReturn the COMPLETE module (existing function plus your new function) as RAW PYTHON ONLY — no markdown fences, no prose, no explanation. (variant ${c.rep})`
  if (kind === 'noskill') return `You are a software engineer.\n\n${body}`
  if (kind === 'placebo') return `${placebo}\n\n${body}`
  return `${skill}\n\n---\n${body}`
}

phase('Produce')
const rows = await pipeline(
  cycles,
  (c) => parallel([
    () => agent(prompt('noskill', c), { label: `noskill:${c.task.id}:${c.rep}`, phase: 'Produce', model: 'haiku', effort: 'low' }),
    () => agent(prompt('placebo', c), { label: `placebo:${c.task.id}:${c.rep}`, phase: 'Produce', model: 'haiku', effort: 'low' }),
    () => agent(prompt('skill',   c), { label: `skill:${c.task.id}:${c.rep}`,   phase: 'Produce', model: 'haiku', effort: 'low' }),
  ]).then(([noskill, placebo, skillCode]) => ({ id: c.task.id, rep: c.rep, codes: { noskill, placebo, skill: skillCode } })),
)

return { rows: rows.filter(Boolean) }
