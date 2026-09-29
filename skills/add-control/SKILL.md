---
name: add-control
description: Add a control arm to an experiment — the laziest alternative and the unchanged baseline, measured in the same run, interleaved, with the arm recorded per observation. Use when a rate, speedup or success count is about to be reported, or when a result is compared against "before" or against an absolute bar.
---

# Add a control

A verdict without a control is an artefact. Every rate needs the same rate
measured on the thing you did not change; without one the tool prints
`UNJUDGED`, not a verdict.

## Steps

1. **Pick the arms.**
   - `baseline`: the thing you did not change.
   - `lazy`: the cheapest change that could also explain the effect (a
     one-line alternative, a fixed parameter, a trivial heuristic).
   - `treatment`: the idea.
   Compare treatment against `lazy`, not only against `baseline`.
2. **Interleave, don't sequence.** Assign the arm per unit of work at the
   moment of work (round-robin or seeded random), never A-for-an-hour then
   B-for-an-hour: environment drift will be measured instead.
3. **Record the arm** in each output row at decision time. Never infer the
   arm from what the output looks like.
4. **Same window, same unit, same instrument** for all arms.
5. **Small n?** Before saying observations contradict a hypothesis, compute
   the probability of those observations under it (e.g. three negatives at
   a 9/21 base rate: (9/21)³ ≈ 0.079 — ordinary).
6. Update the tool so it prints `UNJUDGED` when any arm has no observations.
