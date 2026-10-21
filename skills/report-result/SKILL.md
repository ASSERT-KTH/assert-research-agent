---
name: report-result
description: Record an experiment outcome — positive, negative or null — in the repo's report file in a fixed order, next to its pre-registration. Use after any run that produced a decisive number, when a hypothesis dies, when a previous number turns out wrong, or before telling the operator "it works".
---

# Report the result

Read the verdict off the pre-registered table; do not reinterpret it. Write
it in the file (REPORT.md by default), not only in the conversation.

## Mode first

Every report entry is headed `CONFIRMATORY` or `EXPLORATORY`; an unlabelled
entry is exploratory. The `check_report` hook sends you back if a new entry
carries neither label.

- **CONFIRMATORY**: run under a committed pre-registration, on its unseen
  data range, with no amendment after the data was seen. Carries the
  verdict and the per-test thresholds after correction for m.
- **EXPLORATORY**: anything else, including a confirmatory run whose
  analysis changed after seeing data. Carries the fork count and the
  `explore/` log, effect sizes with "uncalibrated" intervals, no verdict,
  and the hypotheses it generated.

## Order

1. **Decisive number**, all arms, same window, terminal unit, and the
   pre-registered verdict (GO / STOP / DISASTER / UNJUDGED) — confirmatory
   only. Exploratory: effect size, interval (uncalibrated), fork count.
2. **Three counts** per arm: considered / evaluated / succeeded.
3. **Not evaluated**, counted.
4. **Proxy result**, clearly subordinate to the decisive number.
5. **Not run, and why** — so nobody assumes it was tried and failed.
6. **Caveats in the same breath**: n, median and top1 beside means,
   fitted-to-n thresholds stated as such.

## Rules

- A negative result is reported as loudly as a positive one.
- A premise that killed the idea is written down: "killed by: <premise>".
- **Wrong earlier?** Correct it where the wrong number lives, keep the
  superseded value next to the correction: `~~1.92x~~ 4.4% (the 1.92x
  measured the wrong component)`.
- Link the pre-registration file and the commit that produced the number.
- Every number comes from a results file written by `osaudit run`; copy it,
  never retype it. When `audit.toml` exists, the stop hook runs `osaudit
  results` and `osaudit study`, and a finding sends you back. In the paper, a
  number from exploratory results says "exploratory" in its paragraph
  (`numbers/exploratory-unlabelled`).

- A confirmatory null is the answer ("K = 0 under the registered
  procedure"). Looking further is a new, exploratory entry, never an
  addendum to the confirmatory one.

## Templates

```markdown
## <date> <slug> — CONFIRMATORY — <VERDICT>

Prereg: prereg/<file>.md · commit <sha> · m = <…>, correction <…>

- Decisive: <treatment> vs <lazy> vs <baseline> (<unit>, <window>), p = <…> vs threshold <…>
- Counts: considered/evaluated/succeeded — T <a/b/c>, L <…>, B <…>
- Not evaluated: <n, why>
- Proxy: <…>
- Not run: <what, why>
- Caveats: n=<…>, median <…>, top1 <…%>
- Killed by / next: <…>
```

```markdown
## <date> <slug> — EXPLORATORY

Log: explore/<file>.md · <n> forks · data seen: <…>

- Effect: <size>, interval <…> (uncalibrated), n=<…>, median <…>, top1 <…%>
- Forks that shaped it: <the ones this number depends on>
- Not run: <what, why>
- Hypotheses to pre-register: <claim → holdout>
```
