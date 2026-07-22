# Margaux 🍷 — the sommelier who never cooks

```
            ___
           ')_(`
           |   |          "I don't cook. I pair, I taste,
           |   |            and I send it back if it's corked."
           |   |
          .'   '.
         /  ( )  \        swirl · sniff · sip · spit
        |   ( )   |       ─────────────────────────
         \       /        VERIFIED · REFUTED · PARTIAL
          '.___.'
         ___|_|___
        (_________)   ~ Margaux, at your service ~
```

Meet **Margaux**, the sommelier behind `sommelier`.

Margaux never touches a pan. She can't sear, she won't chop. Her entire craft is
three things: **compose the pairing, taste every pour, and match the right bottle
to the right plate.** The kitchen cooks. Margaux decides what belongs together and
whether it's good enough to leave the cellar.

## What a sommelier actually does here

- **She composes the flight first.** Before anything is poured, Margaux lays out
  the whole menu — every course, every pairing — as a written card. That card is
  the PRD + file-scoped tickets: each dish knows its wine, and no two pours fight
  over the same glass. *(① Tekton — design)*
- **She tastes every glass; the label means nothing.** A bottle says "grand cru"?
  Margaux swirls, sniffs, sips — and reproduces the claim herself.
  `VERIFIED / REFUTED / PARTIAL`. A corked pour goes back, no matter what the label
  promised. Then one last pass down the table: *did any course go out unchecked?* —
  until the answer is none. *(② Sim Francisco — don't settle)*
- **She pairs, and pairing is the whole art.** The bold reduction gets the bold
  red; the delicate crudo gets the crisp white; the bread basket doesn't need a
  vintage at all. Each ticket gets the model tier that fits it — the humblest
  bottle that still passes the taste. *(③ Custom Universe — delegate)*
- **She's honest about the cellar.** Margaux didn't grow the grapes. The bottles
  are borrowed — Karpathy's minimalism, the old YAGNI rule, the habit of never
  trusting a number you haven't re-poured yourself. She just knows what goes with
  what.

## Why a sommelier and not a chef

A chef makes the food. A **sommelier makes nothing** — and that's the point. The
orchestrator never writes code. Its craft is *pairing* (which model cooks which
ticket), *tasting* (re-measuring every claim), and *composing the flight* (the PRD
and its tickets). Margaux runs the room without ever lifting a knife.

**The flight is the plan. The pours are your agents. The pairing is delegation.**
**Margaux just decides what belongs together — and sends back what's corked.**

---

*Honesty note: Margaux is charming, but the cellar log is mixed, not spotless — read
all five rounds in [`BENCHMARKS.md`](./BENCHMARKS.md). Three tastings came back null
or worse: she never beat a length-matched placebo, and on one mechanically-graded
round she trended *worse* on feature correctness. Round 4 poured her first real
win — the DON'T SETTLE verify rule, tasted on its own as a condensed digest, lifted
bug-fix-behind-a-"certified"-label from 0–2% (placebo) to **29% haiku / 44% sonnet**
(sonnet p ≈ 6×10⁻⁸; haiku just misses the 10⁻⁴ bar at ≈1.4×10⁻⁴). Round 5 added trade-offs, not triumphs: tier-routing runs **~19%
cheaper** than an all-Opus pour, but fanning out in parallel on small tasks came in
**~1.75× slower** than just doing it serially. She ships on discipline and
transparency, not on a clean sweep — three losses, one real win, two trade-offs, all
on the record.*
