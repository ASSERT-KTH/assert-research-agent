---
name: preregister
description: Write a pre-registration (number, baseline, GO/STOP/DISASTER, limits) into prereg/ before running any experiment, benchmark, ablation or evaluation. Use before the first run of anything whose result will decide something, and whenever the operator asks "does X help?".
---

# Pre-register before measuring

A result read against a table written *after* it is a negotiation, not a
measurement. Write the table first, commit it, then run.

## Steps

1. **Name the premise** you are least inclined to check. If it is cheap to
   measure, measure it now, before building on it.
2. Create `prereg/<yyyy-mm-dd>-<slug>.md` with the template below. Every
   field is filled; "unknown" is allowed only for THE BASELINE, and then
   measuring it is the first run.
3. Sanity-check the criterion:
   - **Right quantity?** Would the number still be the right one if it
     came back exactly as hoped? If a hoped-for result would not change
     the decision, you registered the wrong number.
   - **Can it fail? Can it pass?** A bar that fails at any non-zero error
     rate, or demands precision below the instrument's resolution, decides
     nothing.
4. Put the verdict in the tool: the script that produces the number also
   prints `GO` / `STOP` / `DISASTER` / `UNJUDGED` from these thresholds.
5. `git add prereg/… && git commit -m "prereg: <slug>"`. The run gate hook
   refuses experiment runs until this commit exists.

## Template

```markdown
# <slug>

Premise checked first: <sentence> — <how, result>

1. THE NUMBER    <quantity, unit, window>
2. THE BASELINE  <value now, measured the same way> (or: unknown → first run)
3. GO            <threshold> → <what ships>
4. STOP          <threshold> → <abandon; what instead>
5. THE DISASTER  <result> → halt, because <why>; include "impossible" outcomes
6. THE LIMITS    <what this design cannot answer whatever it returns>
Control arm:     <laziest alternative, measured in the same run, interleaved>
Instrument check: <known-answer input and its expected output>

## Bar moved
<empty; append "date, direction (tighter/looser), evidence" if ever edited>
```
