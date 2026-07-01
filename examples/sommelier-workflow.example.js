/**
 * sommelier-workflow.example.js
 * ------------------------------------------------------------------------
 * A real, runnable dynamic Workflow (Claude Code `Workflow` tool) that drives
 * the sommelier discipline end to end. It is the executable form of the three
 * moves in `skills/sommelier-pairing`:
 *
 *   ①  DESIGN  (Tekton)         — the plan is file-scoped tickets, not prose.
 *   ②  DON'T SETTLE (Sim Fran.) — every claim is re-measured; nothing merges
 *                                 on a self-reported "done".
 *   ③  DELEGATE (Custom Univ.)  — a model tier per ticket; cheapest that passes.
 *
 * The orchestrator (this script, run by Opus) never writes code — it decomposes,
 * dispatches Sonnet implementers in parallel over DISJOINT files, gates each
 * ticket on re-measured evidence + an Opus review, runs a completeness critic,
 * and only then merges.
 *
 * HOW TO RUN
 *   Ask Claude Code:  "run examples/sommelier-workflow.example.js with the
 *   Workflow tool, args = { task, tickets }"  — or paste it into the Workflow
 *   tool's `script`. Pass your own tickets via `args` (see DEFAULT below).
 *
 * NOTE: illustrative. Implementers return a structured PATCH (evidence) rather
 * than writing files, so the example is safe to run anywhere. For a real fleet,
 * swap the implementer to `isolation: 'worktree'` and let it edit files.
 */

export const meta = {
  name: 'sommelier-workflow-example',
  description: 'Example: PRD + file-scoped parallel tickets, tier-paired implementers, evidence+review gate per ticket, completeness critic, merge — the sommelier discipline as a runnable Workflow.',
  phases: [
    { title: 'Design',   detail: 'freeze the PRD; verify tickets own disjoint files' },
    { title: 'Implement',detail: 'Sonnet implementers, one per disjoint ticket, in parallel' },
    { title: 'Gate',     detail: 'Opus re-measures the metric + reviews; APPROVE or reopen' },
    { title: 'Critic',   detail: 'Opus completeness pass — what was skipped?' },
  ],
}

// ── ① DESIGN — the contract. Each ticket owns EXACT files, states ONE behavior,
//     carries a metric that will be RE-MEASURED at the gate, and names a tier.
const DEFAULT = {
  task: 'Add token-bucket rate limiting to the public API.',
  tickets: [
    { id: 'limiter',  files: ['src/ratelimit/tokenBucket.ts'],       contract: 'export limit(key, cost): Decision (allow/deny + retryAfter)', metric: 'unit tests for burst + refill pass; tsc clean' },
    { id: 'mw',       files: ['src/middleware/rateLimit.ts'],         contract: 'Express middleware calling limit(); 429 + Retry-After on deny', metric: 'integration test: 11th req in 10/s window → 429' },
    { id: 'wire',     files: ['src/api/router.ts'],                   contract: 'mount rateLimit middleware on the public router only',        metric: '0 admin routes rate-limited; public routes covered' },
    { id: 'config',   files: ['src/config/rateLimit.ts'],            contract: 'typed limits per route-group, read from env with defaults',    metric: 'tsc clean; defaults documented' },
  ],
}

const { task, tickets } = (typeof args !== 'undefined' && args && args.tickets) ? args : DEFAULT

phase('Design')
log(`PRD (frozen): ${task}`)

// File-ownership lock — the parallelism primitive. No two tickets may write one file.
const owner = new Map()
for (const t of tickets) for (const f of t.files) {
  if (owner.has(f)) throw new Error(`file-ownership conflict: ${f} is claimed by "${owner.get(f)}" and "${t.id}" — split or serialize before dispatch`)
  owner.set(f, t.id)
}
log(`${tickets.length} tickets own ${owner.size} disjoint files → safe to run in parallel`)

const PATCH = {
  type: 'object', additionalProperties: false,
  required: ['files', 'patch', 'self_check'],
  properties: {
    files:      { type: 'array', items: { type: 'string' }, description: 'files this patch writes (must equal the ticket\'s owned files)' },
    patch:      { type: 'string', description: 'the unified diff / full file contents implementing the contract — NO scope beyond the ticket' },
    self_check: { type: 'string', description: 'how the success metric was met, in the implementer\'s own words (a CLAIM, to be re-measured)' },
  },
}

const VERDICT = {
  type: 'object', additionalProperties: false,
  required: ['metric_reproduced', 'verdict', 'why'],
  properties: {
    metric_reproduced: { type: 'boolean', description: 'did YOU re-measure the metric (not trust the self_check)?' },
    verdict:           { type: 'string', enum: ['APPROVE', 'REOPEN'] },
    why:               { type: 'string' },
  },
}

// ②③ pipeline: each ticket flows implement → gate independently (no barrier),
//    so ticket B is being reviewed while ticket C is still being implemented.
const results = await pipeline(
  tickets,
  // ── ③ DELEGATE: implementation → Sonnet (mid tier). Contract in, patch out.
  (t) => agent(
    `You are a Sonnet implementer. Implement EXACTLY this ticket and nothing more (YAGNI).\n` +
    `Files you may write (only these): ${t.files.join(', ')}\n` +
    `Contract: ${t.contract}\nSuccess metric: ${t.metric}\n` +
    `Return the patch and a self_check. Do not add infra the ticket didn't ask for.`,
    { label: `impl:${t.id}`, phase: 'Implement', model: 'sonnet', effort: 'medium', schema: PATCH /*, isolation: 'worktree' for a real fleet */ }
  ).then(patch => ({ t, patch })),

  // ── ② DON'T SETTLE: Opus gate. Re-measure the metric; never trust self_check.
  (prev) => {
    if (!prev || !prev.patch) return null
    const { t, patch } = prev
    const stray = (patch.files || []).filter(f => !t.files.includes(f))
    return agent(
      `You are an Opus reviewer + verifier for ticket "${t.id}". Do NOT trust the implementer's self_check.\n` +
      `Contract: ${t.contract}\nMetric (RE-MEASURE it yourself): ${t.metric}\n` +
      (stray.length ? `⚠ patch touches files outside its ownership: ${stray.join(', ')} — that alone is a REOPEN.\n` : '') +
      `Patch:\n${patch.patch}\n\nReproduce the metric. APPROVE only if it genuinely holds; else REOPEN with why.`,
      { label: `gate:${t.id}`, phase: 'Gate', model: 'opus', effort: 'high', schema: VERDICT }
    ).then(v => ({ id: t.id, files: t.files, verdict: v, patch: patch.patch }))
  },
)

const done = results.filter(Boolean)
const merged  = done.filter(r => r.verdict && r.verdict.metric_reproduced && r.verdict.verdict === 'APPROVE')
const reopen  = done.filter(r => !merged.includes(r))
log(`gate: ${merged.length} APPROVE (evidence re-measured), ${reopen.length} reopened → ${reopen.map(r => r.id).join(', ') || 'none'}`)

// ② completeness critic — what did the whole set skip? (loop-until-dry in a real run)
phase('Critic')
const critic = await agent(
  `Completeness critic for: ${task}\nMerged tickets: ${merged.map(r => r.id).join(', ')}\n` +
  `Reopened: ${reopen.map(r => `${r.id} (${r.verdict?.why || 'n/a'})`).join('; ') || 'none'}\n` +
  `Adversarially hunt for what was skipped — a claim never re-measured, a file never touched, an edge ` +
  `case dropped, a metric quietly relaxed, a route left uncovered. List concrete follow-up tickets, or say "dry".`,
  { label: 'completeness-critic', phase: 'Critic', model: 'opus', effort: 'high' }
)

// Merge only evidence + APPROVE. Reopened tickets and critic findings become the next round.
return {
  task,
  merged: merged.map(r => ({ id: r.id, files: r.files })),
  reopened: reopen.map(r => ({ id: r.id, why: r.verdict?.why })),
  next_round: critic,
}
