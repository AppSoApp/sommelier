# `skill-no-imperative.txt` — removal log

`arms/skill-no-imperative.txt` is `arms/skill-full.txt` (byte-identical copy of the
shipped `skills/sommelier-pairing/SKILL.md`, sha256
`e6a2f1ae38113b3dd21a818ba656aeb77c06115f928f820b649826b76d332001`) with **only** the
imperative enforcement wording removed. No other text was added, reworded, or
reordered. Every removal below is a straight deletion of an exact substring; nothing
was rephrased to compensate, and the surrounding sentences were checked to still read
as valid, complete English after the deletion (see "resulting text" per item).

Three deletions were made, corresponding to three of the four fragments named in the
ticket. See the note at the end on the fourth ("the MUST in the one-liner").

## Removal 1 — the REFUTED enforcement sentence

- **Location:** `SKILL.md` line 98 (Move 2, opening sentence of the paragraph that
  follows the VERIFIED/REFUTED/PARTIAL definition).
- **Exact text removed** (including its own line and trailing newline):
  ```
  **On REFUTED you MUST edit the code to make the check pass — in the same change, now.**
  ```
- **Why the whole sentence, not just the "MUST…now" clause:** the sentence is
  `On REFUTED <imperative clause>.` — deleting only the imperative clause
  (`you MUST edit the code to make the check pass — in the same change, now`) would
  leave the dangling fragment `On REFUTED .`, which is not a sentence. The entire
  sentence is itself the imperative-enforcement unit (its only content besides "On
  REFUTED" is the command), so it was removed in full to keep the file grammatical.
- **Resulting text at that point** (line 97 blank line, then straight into what was
  line 99 minus Removal 2 below):
  ```
  blocks merge exactly like an unfixed REFUTED.

  "It was certified" is not a reason to leave a
  failing check failing — the certification is exactly what you just refuted. A
  **REFUTED-but-unfixed claim is the failure mode this move exists to stop.**
  ```

## Removal 2 — "Naming the bug is not resolving it."

- **Location:** `SKILL.md` line 99, first sentence of the paragraph (immediately
  after the sentence removed in Removal 1).
- **Exact text removed** (including the trailing space that joined it to the next
  sentence on the same line):
  ```
  Naming the bug is not resolving it. 
  ```
- **Why:** this sentence is a rhetorical dismissal of excuses for leaving a bug
  unfixed — enforcement register, not descriptive content. Removing it (with its
  trailing space) leaves the next sentence, `"It was certified" is not a reason to
  leave a failing check failing…`, as a clean paragraph opener with no dangling
  punctuation or capitalization break.

## Removal 3 — "rewrite it now" in the Move 2 one-liner

- **Location:** `SKILL.md` line 82, inside the Move 2 one-line blockquote (the same
  blockquote used verbatim as `arms/rule-only.txt`).
- **Original sentence:**
  ```
  If any is wrong, rewrite it now — and leave the `assert` that proves it.
  ```
- **Exact text removed:**
  ```
  rewrite it now — and 
  ```
  (the imperative verb phrase plus the coordinating "— and " that joined it to the
  next clause, so the remainder reads as one clean clause rather than two dangling
  halves)
- **Resulting sentence:**
  ```
  If any is wrong, leave the `assert` that proves it.
  ```
- **Why "rewrite it now" and not just "now":** the ticket names this fragment as
  `"REWRITE it now"` — the verb+adverb pair carries the enforcement force (an
  instruction to act immediately), not the adverb alone. Removing only "now" would
  have left "rewrite it" standing, which is still a bare command to fix the code
  right there — arguably the exact wording under test. Removing the full verb phrase
  is the more faithful ablation.

## Note on the fourth named fragment — "the MUST in the one-liner"

The ticket's example list includes, as a fourth fragment, "the MUST in the
one-liner." A literal, case-sensitive search of the one-liner blockquote (`SKILL.md`
lines 79–83, reproduced verbatim in `arms/rule-only.txt`) found **no occurrence of
the word "MUST" (any case) anywhere in that blockquote** — its only imperative
enforcement phrase is "rewrite it now," already removed as Removal 3 above. Treating
items 2 ("REWRITE it now") and 4 ("the MUST in the one-liner") as pointing at the
same single location (the one imperative clause the one-liner contains) accounts for
all four named fragments with exactly three deletions.

## What was deliberately left untouched

- `SKILL.md` line 38: "...that dependency **must** be verified (Move 2) — or refuted
  and fixed." This is the only other occurrence of "must" (lowercase) in the
  document. It sits in the Overview guardrails, stating a general principle ("build
  only on verified code"), not a forceful "do X now, no excuses" enforcement
  sentence like the three removed above — it names no immediate deadline, no "now,"
  and no dismissal of excuses. It was left in place because (a) it is not one of the
  four fragments the ticket names, (b) removing "must be" from that clause breaks
  its grammar (`"...that dependency verified (Move 2)..."` is not a sentence) and
  the ticket calls for deletion, not rewording, and (c) it is lowercase, so it does
  not match the self-check's target string `MUST`.
- Every other imperative-mood sentence in the skill that is not specifically about
  enforcing an immediate fix to a REFUTED claim (e.g., "STOP.", "run it on `0`, `1`,
  empty, and a negative," "Do not build on unverified code," "YAGNI — just do it")
  was left untouched. The ticket scopes the ablation to "the imperative enforcement
  wording" — the REFUTED-fix-it-now register specifically named by its four
  examples — not the skill's instructional voice in general; stripping the latter
  would no longer be a scalpel ablation of one hypothesized ingredient.

## Self-check

- `MUST` (any case) present in `skill-no-imperative.txt`: **No.**
- `REWRITE` (any case) present in `skill-no-imperative.txt`: **No.**
- The file differs from `skill-full.txt` by exactly the three deletions documented
  above and nothing else — verified with
  `diff arms/skill-full.txt arms/skill-no-imperative.txt`, which shows only the two
  changed lines corresponding to Removals 1+2 (adjacent, same paragraph) and
  Removal 3.
