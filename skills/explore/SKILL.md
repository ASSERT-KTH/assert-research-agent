---
name: explore
description: Run an exploratory analysis honestly — open a fork log in explore/, record every data-dependent choice as it is made, label all output EXPLORATORY, and end with hypotheses to pre-register on unseen data. Use when looking at data without a committed pre-registration, after a confirmatory test came out empty and you want to look further, when picking a window, subset or threshold by eye, or when the operator asks "what's in the data?".
---

# Explore, and say so

Exploratory = some choice of the analysis was made after seeing results.
Then the real number of tests is unknown, p-values and confidence intervals
are not calibrated, and nothing found can be confirmed by this data. It can
estimate effect sizes and generate hypotheses. That is its whole job.

## Steps

1. **Reserve the holdout first.** Before the first look, write down which
   data you will *not* touch (a split, a later range, a fresh sample), as
   paths in `holdout`. It is the future confirmatory `data`. If no data is
   left, say so: findings will stay exploratory until new data exists.
2. **Open the log** `explore/<yyyy-mm-dd>-<slug>.md` from the template
   below. Exploratory scripts live under `explore/` too; the run gate lets
   them run without a pre-registration once a log exists.
3. **Log every fork at the moment you make it**: what you chose, the
   alternatives, what you had seen that made you choose. Running the
   exploration at all counts as a fork when it follows an empty
   confirmatory result. So does dropping a subset, picking a window, lag,
   bin or threshold, and choosing which interval or plot to show.
4. **Label output.** Every printed table, figure title and report line
   carries `EXPLORATORY`. Report effect sizes with intervals and the fork
   count; write "uncalibrated" next to any p-value or CI. Never print
   GO/STOP from an exploratory run.
5. **Record what data was seen** in the front matter's `data_seen`, so the
   next pre-registration can prove its range is disjoint (`osaudit` refuses
   a confirmatory run whose input overlaps it). When a run produces a
   results file, run it as
   `osaudit run --explore explore/<file>.md --input <data> -o results/<name>.json -- <command>`:
   the result records its mode, and its inputs' sha256 count as seen even
   under another name.
6. **Close with hypotheses**, each stated so it can be pre-registered: the
   claim, every fork turned into a fixed parameter, and the unseen data it
   would be tested on. Promote one with the `preregister` skill
   (`Origin: explore/<file>.md`).

## Template

The front matter is machine-readable (CONVENTIONS.md, Study); paths, not prose.

```markdown
+++
mode = "exploratory"
holdout = ["data/test"]          # reserved before the first look (or [] — findings stay exploratory)
data_seen = ["data/train.csv"]   # every path looked at, kept current
+++

# <slug>

Why exploring: <question; or "confirmatory prereg/<file>.md came out <result>">

## Forks
1. <date> chose <X> over <alternatives> because <what was seen>
2. …
Fork count: <n>

## Findings
- <effect size, interval (uncalibrated), n, median/top1> — EXPLORATORY

## Hypotheses to pre-register
- H: <claim>; fixed: <fork 2 → parameter, …>; test on: <holdout>
```
