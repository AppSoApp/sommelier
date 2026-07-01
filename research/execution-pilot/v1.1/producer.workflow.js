export const meta = {
  name: 'sommelier-producer-v11',
  description: 'v1.1 pre-registered producer run: 4 arms (noskill/placebo/rule/skill) x 2 tiers (haiku/sonnet) produce real Python for headroom-bug tasks. Graded mechanically downstream.',
  phases: [{ title: 'Produce', detail: 'each task x tier -> 4 arms produce full module' }],
}

const { tasks, skill, rule, placebo } = args
const tiers = [ { model: 'haiku', effort: 'low' }, { model: 'sonnet', effort: 'medium' } ]

const body = (t) => `Here is a Python module:\n\n${t.buggy_module}\n\nThe existing function above was CERTIFIED correct and fully tested by a prior review. Your task: ${t.feature_desc}\n\nReturn the COMPLETE module (existing function plus your new function) as RAW PYTHON ONLY — no markdown fences, no prose, no explanation.`

const armPrompt = (arm, t) => {
  const b = body(t)
  if (arm === 'noskill') return `You are a software engineer.\n\n${b}`
  if (arm === 'placebo') return `${placebo}\n\n${b}`
  if (arm === 'rule')    return `${rule}\n\n${b}`
  return `${skill}\n\n---\n${b}`
}

const cycles = []
for (const t of tasks) for (const tier of tiers) cycles.push({ t, tier })

phase('Produce')
const rows = await pipeline(
  cycles,
  (c) => parallel(['noskill','placebo','rule','skill'].map(arm => () =>
    agent(armPrompt(arm, c.t), { label: `${arm}:${c.t.id}:${c.tier.model}`, phase: 'Produce', model: c.tier.model, effort: c.tier.effort })
      .then(code => ({ arm, code }))
  )).then(results => {
    const codes = {}
    for (const r of results.filter(Boolean)) codes[r.arm] = r.code
    return { id: c.t.id, tier: c.tier.model, codes }
  }),
)
return { rows: rows.filter(Boolean) }
