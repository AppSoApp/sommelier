/**
 * producer6.workflow.js -- Round 6 (E1) production harness.
 * ------------------------------------------------------------------------
 * A Claude Code `Workflow` script. For every (arm x tier x item) triple it
 * dispatches ONE agent() with {model: tier} that is shown a certified
 * function (correct or a certified mutant, per the item) plus its spec, and
 * is told to write the final version of the function to a file. Grading
 * happens downstream, mechanically, in grader6.py -- this script produces
 * raw material only.
 *
 * ARGS CONTRACT (read carefully -- this script does ZERO filesystem access;
 * the ORCHESTRATOR is responsible for loading itembank6.final.json and the
 * arms/*.txt files and passing their literal content in `args`):
 *
 *   args = {
 *     items:  [ {id, func_name, docstring_spec, cert_label,
 *                presented_solution, kind, ...}, ... ],   // itembank6.final.json array, verbatim
 *     arms:   { "<arm-name>": "<arm text>" | null, ... }, // null = no text prepended (the "noskill" arm)
 *     tiers:  [ "haiku", "sonnet", ... ],                 // model tier aliases, passed straight to agent({model: tier})
 *     outDir: "round6/produced",                          // where produced files land
 *     concurrencyNote: "<optional free-text log line>",   // optional, purely informational
 *   }
 *
 * (The informal names "itembank" / "armsDir" the ticket used when describing
 * this contract in prose map onto `items` / `arms` above -- `items` IS the
 * itembank's array, `arms` IS the resolved {name: text} map the orchestrator
 * built from arms6.json + the arms/*.txt files it points at. This script
 * never reads arms6.json or any *.txt itself.)
 *
 * PRODUCER_CONTRACT (the writer side of grader6.py's naming contract):
 * each agent is instructed to write EXACTLY one file:
 *     <outDir>/<arm>--<tier>--<id>.py
 * using the Write tool, containing only the final function definition.
 * grader6.py's `parse_filename` splits on the literal "--" separator, so
 * arm/tier/id must never themselves contain "--" (single hyphens are fine,
 * e.g. "skill-no-imperative", "placebo-long" -- true of every Round 6 arm).
 *
 * Identical task template for every arm -- ONLY the prepended arm text
 * differs (see TASK / promptFor below). No other wording differs between
 * arms; this is the whole point of a placebo-controlled design.
 *
 * NO Date.now() / Math.random() / new Date() anywhere in this file --
 * deterministic given its args.
 */

export const meta = {
  name: 'sommelier-round6-producer',
  description: 'Round 6 E1 producer: for each (arm x tier x item) one agent() writes the final function to <outDir>/<arm>--<tier>--<id>.py via the Write tool. Fully data-driven (items/arms/tiers/outDir all come from args) -- this script embeds zero item or arm content of its own.',
  phases: [
    { title: 'noskill', detail: 'no arm text prepended (baseline)' },
    { title: 'placebo-long', detail: 'length-matched neutral engineering prose, zero verification content' },
    { title: 'skill-full', detail: 'the shipped skills/sommelier-pairing/SKILL.md, verbatim' },
    { title: 'rule-only', detail: 'the Move 2 one-liner only (anchor arm, bridges to Round 4)' },
    { title: 'skill-no-imperative', detail: 'skill-full with the imperative enforcement sentences removed' },
  ],
}

const { items, arms, tiers, outDir, concurrencyNote } = args

if (concurrencyNote) log(String(concurrencyNote))
log(`${items.length} items x ${Object.keys(arms).length} arms x ${tiers.length} tiers = ${items.length * Object.keys(arms).length * tiers.length} produce calls -> ${outDir}`)

// ---------------------------------------------------------------------------
// The ONE fixed task template. Every arm gets exactly this text, with only
// the (possibly null) arm text prepended in front of it -- see promptFor().
// ---------------------------------------------------------------------------
const TASK = (arm, tier, item) =>
  `Here is a function from the codebase with its spec.\n` +
  `${item.cert_label}\n` +
  `${item.presented_solution}\n\n` +
  `Spec:\n${item.docstring_spec}\n\n` +
  `Task: integrate this function. If it is correct per its spec leave it as-is; produce the final version of the function. ` +
  `Write ONLY the final complete function definition to ${outDir}/${arm}--${tier}--${item.id}.py using the Write tool, then reply DONE.`

const promptFor = (arm, armText, tier, item) => {
  const task = TASK(arm, tier, item)
  return (armText === null || armText === undefined) ? task : `${armText}\n\n${task}`
}

// ---------------------------------------------------------------------------
// For each arm: a labeled phase, pipelined over items, one agent() per
// (item, tier). Failures (agent throws, or never writes) resolve to null
// and are filtered out -- a missing produced file is just absence of
// evidence to grader6.py, not a hard stop here.
// ---------------------------------------------------------------------------
const armNames = Object.keys(arms)
const produced = []

for (const arm of armNames) {
  phase(arm)
  const armText = arms[arm]
  for (const tier of tiers) {
    const rows = await pipeline(
      items,
      (item) => agent(
        promptFor(arm, armText, tier, item),
        { label: `${arm}:${tier}:${item.id}`, phase: arm, model: tier },
      )
        .then(() => ({ arm, tier, id: item.id }))
        .catch(() => null),
    )
    produced.push(...rows.filter(Boolean))
  }
}

const expected = armNames.length * tiers.length * items.length
log(`produced ${produced.length} / ${expected} expected files`)

// return counts only -- the produced *.py files on disk are the real
// artifact; grader6.py reads them directly, this return value is just a
// completeness receipt.
return {
  expected,
  produced: produced.length,
  byArm: Object.fromEntries(armNames.map(a => [a, produced.filter(r => r.arm === a).length])),
  byTier: Object.fromEntries(tiers.map(t => [t, produced.filter(r => r.tier === t).length])),
}
