export const meta = {
  name: 'sommelier-speed-test',
  description: 'Wall-clock: single-agent serial vs sommelier parallel fan-out on independent-file work. mode via args.',
  phases: [{ title: 'Run' }],
}
const mode = (typeof args !== 'undefined' && args && args.mode) ? args.mode : 'serial'
const PROJECTS = 3
const FUNCS = [
  ['reverse_string(s)', 'return s reversed'],
  ['is_even(n)', 'return True if n is even'],
  ['factorial(n)', 'return n! (0!=1)'],
  ['gcd(a,b)', 'greatest common divisor'],
  ['celsius_to_f(c)', 'Celsius to Fahrenheit'],
  ['count_words(s)', 'number of whitespace-separated words'],
  ['max_of_list(xs)', 'max value, or None if empty'],
  ['nth_fibonacci(n)', 'nth Fibonacci, fib(0)=0, fib(1)=1'],
]
phase('Run')
// projects run SEQUENTIALLY (await in a for-loop) so per-arm wall-clock is isolated;
// within a project: serial = 1 agent does all 8; parallel = 8 agents, one each.
for (let p = 0; p < PROJECTS; p++) {
  if (mode === 'serial') {
    await agent(
      `Implement these 8 independent Python functions (project ${p}). Return one module, raw python only:\n` +
      FUNCS.map(f => `- def ${f[0]}: ${f[1]}`).join('\n'),
      { label: `serial:p${p}`, phase: 'Run', model: 'sonnet', effort: 'low' })
  } else {
    await parallel(FUNCS.map((f, i) => () =>
      agent(`Implement one Python function, raw python only:\ndef ${f[0]}: ${f[1]}`,
        { label: `par:p${p}:f${i}`, phase: 'Run', model: 'sonnet', effort: 'low' })))
  }
}
return { mode, projects: PROJECTS, functions_per_project: FUNCS.length }
