---
name: preregister
description: Write a pre-registration (hypothesis, data range, procedure, statistic and α, decision rule, number of tests, GO/STOP/DISASTER) into prereg/ before a confirmatory run of any experiment, benchmark, ablation or evaluation. Use before the first run of anything whose result will decide or confirm something, when the operator asks "does X help?", and when promoting an exploratory finding to a confirmatory test.
---

# Pre-register before measuring

A result read against a table written *after* it is a negotiation, not a
measurement. Write the table first, commit it, then run. This is what makes
a result **CONFIRMATORY**: the analysis can no longer change after the data
is seen. Anything else is exploratory (use the `explore` skill).

## Steps

1. **Name the premise** you are least inclined to check. If it is cheap to
   measure, measure it now, before building on it.
2. Create `prereg/<yyyy-mm-dd>-<slug>.md` with the template below. Every
   field is filled; "unknown" is allowed only for THE BASELINE, and then
   measuring it is the first run.
3. **Check the data is unseen.** The DATA RANGE must not overlap anything
   looked at during exploration (`explore/` logs list what was seen). If
   it does, pick a held-out split, a later time range or a new sample.
   Promoting an exploratory finding: every fork the exploration chose
   (window, subset, threshold) becomes a fixed parameter in PROCEDURE.
4. **Count the tests.** m = every hypothesis × every metric × every subset
   this registration will test. Name the correction (Holm by default) and
   the per-test thresholds it implies.
5. Sanity-check the criterion:
   - **Right quantity?** Would the number still be the right one if it
     came back exactly as hoped? If a hoped-for result would not change
     the decision, you registered the wrong number.
   - **Can it fail? Can it pass?** A bar that fails at any non-zero error
     rate, or demands precision below the instrument's resolution, decides
     nothing.
6. Put the verdict in the tool: the script that produces the number also
   prints `CONFIRMATORY` and `GO` / `STOP` / `DISASTER` / `UNJUDGED` from
   these thresholds.
7. `git add prereg/… && git commit -m "prereg: <slug>"`. The run gate hook
   refuses runs under `experiments/` until this commit exists; the commit
   date is the proof the bar came before the data.

## Amendments

- **Before any data is seen:** edit, add an `## Amendments` entry (date,
  what, why), commit. Still confirmatory.
- **After any data is seen:** the amended part is exploratory. Say so in
  the entry and in the report; do not present it under the original
  verdict.

## Template

```markdown
# <slug>

Mode: CONFIRMATORY
Premise checked first: <sentence> — <how, result>

Hypothesis:      <claim>; H0: <null>
Data range:      <exactly which data>; unseen because <disjoint from explore/… / collected after this commit>
Procedure:       <script path, commit, every parameter fixed>
Statistic, α:    <test statistic, sidedness>, α = <…>
Tests (m):       <m> — <list>; correction: <Holm / none because m = 1>

1. THE NUMBER    <quantity, unit, window>
2. THE BASELINE  <value now, measured the same way> (or: unknown → first run)
3. GO            <threshold> → <what ships>
4. STOP          <threshold> → <abandon; what instead>
5. THE DISASTER  <result> → halt, because <why>; include "impossible" outcomes
6. THE LIMITS    <what this design cannot answer whatever it returns>
Control arm:     <laziest alternative, measured in the same run, interleaved>
Instrument check: <known-answer input and its expected output>
Origin:          <none / explore/<file>.md — the exploration that generated this hypothesis>

## Amendments
<empty; "date, data seen yet? (no → confirmatory / yes → exploratory), what, why">

## Bar moved
<empty; append "date, direction (tighter/looser), evidence" if ever edited>
```
