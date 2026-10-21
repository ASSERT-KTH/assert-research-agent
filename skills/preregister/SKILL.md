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
   front-matter key is filled; in the body, "unknown" is allowed only for
   THE BASELINE, and then measuring it is the first run.
3. **Check the data is unseen.** No path in `data` may overlap a
   `data_seen` path of an `explore/` log, or be (a copy of) an input of an
   exploratory run. If it does, pick a held-out split, a later time range or
   a new sample. Promoting an exploratory finding: every fork the
   exploration chose (window, subset, threshold) becomes a fixed parameter.
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
   refuses to run `experiments/<name>` (a script, or a directory of them)
   until a committed pre-registration lists that exact path in
   `experiments` and its front matter is valid. The commit date proves the
   bar came before the data.
8. **Run through osaudit**, so the result records its mode and
   registration (required by the gate when `audit.toml` exists):

   ```sh
   osaudit run --prereg prereg/<file>.md --input data/test -o results/<name>.json \
     -- python experiments/<name>.py data/test
   ```

   osaudit refuses before running if the experiment or an input is not
   registered, the registration changed without an amendment, or an input
   was already seen by an exploratory run. `osaudit study` re-checks it
   later, from git alone.

## Amendments

Only with the human's approval (the guard hook asks, or refuses on Codex;
shell writes are refused). Append an `[[amendments]]` table in the front
matter and commit it:

- **Before any data is seen:** `data_seen = false`. Still confirmatory.
- **After any data is seen:** `data_seen = true`. The result is exploratory
  (`study/amended`); say so in the report, never under the original
  verdict.

## Template

The front matter is the machine-readable part (CONVENTIONS.md, Study); every
key is mandatory except `amendments`, and `schema` is exactly the URL shown
([`schemas/prereg-v1.json`](../../schemas/prereg-v1.json)). The body is for humans.

```markdown
+++
schema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/prereg-v1.json"   # mandatory, exactly this
mode = "confirmatory"
hypothesis = "<claim>"
null = "<H0>"
experiments = ["experiments/<name>.py"]   # every experiment this licenses
data = ["data/<unseen range>"]            # every input path; none seen in explore/
statistic = "<test statistic, sidedness>"
alpha = 0.05
m = 1                                     # number of tests in this registration
correction = "none"                       # holm|bonferroni|hochberg|benjamini-hochberg|none (none only if m = 1)
go = "<threshold> → <what ships>"
stop = "<threshold> → <abandon; what instead>"
disaster = "<result> → halt, because <why>; include impossible outcomes"
+++

# <slug>

Premise checked first: <sentence> — <how, result>
Data unseen because: <disjoint from explore/<file>.md data_seen / collected after this commit>
Origin: <none / explore/<file>.md — the exploration that generated this hypothesis>

1. THE NUMBER    <quantity, unit, window>
2. THE BASELINE  <value now, measured the same way> (or: unknown → first run)
3. GO / STOP / DISASTER: see front matter
4. THE LIMITS    <what this design cannot answer whatever it returns>
Control arm:     <laziest alternative, measured in the same run, interleaved>
Instrument check: <known-answer input and its expected output>
Fixed parameters: <every fork from the exploration, now a constant>

## Bar moved
<empty; append "date, direction (tighter/looser), evidence" if ever edited>
```
