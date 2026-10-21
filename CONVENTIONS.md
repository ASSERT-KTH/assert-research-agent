# Conventions of a research repository

A study is trustworthy when every claim in it can be traced, mechanically, to the evidence that supports it, and when every confirmatory claim can be shown to have been fixed before its data was seen.
This document states what a research repository must contain, and in which format, from the first pre-registration to the paper.
It is the single specification shared by two tools, which enforce it at two moments:

- the **research agent** (this repository: prompt, skills, hooks) enforces it *while the work is done*, by refusing actions;
- [**osaudit**](https://github.com/ASSERT-KTH/osaudit) checks it *afterwards*, from the repository alone, without trusting whoever did the work.

Each rule is normative (MUST) and names the failure it prevents. Rule ids (`study/…`, `numbers/…`) are those printed by `osaudit`; `hook:<name>` is the research-agent hook that enforces it during the work.

## Repository

- The repository root holds `audit.toml`, which declares where the study, the paper, the results and the ledgers are. *Prevents: an audit that silently checks nothing because it looked in the wrong place.*
- `[study]` in `audit.toml` names the study directories; every key is optional and read by both tools (the hooks also accept the environment variables `RESEARCH_PREREG_DIR`, `RESEARCH_EXPLORE_DIR`, `RESEARCH_RESULTS_DIR`, `RESEARCH_REPORT_FILES`, which take precedence). *Prevents: two tools disagreeing on where the pre-registrations are.*

```toml
[study]
prereg = "prereg"            # pre-registrations, one .md per question
explore = "explore"          # exploratory scripts and their logs
experiments = "experiments"  # confirmatory entry points, experiments/<name>
results = "results"          # results JSON files (when [results] files is not declared)
report = ["REPORT.md", "NOTES.md", "README.md"]   # the written record
```
- The paper is LaTeX sources or a PDF. When both exist, the LaTeX sources are audited. *Prevents: auditing a stale PDF that no longer matches the sources.*
- A Markdown document that states results (a findings file, a report) carries TOML front matter (`+++ ... +++`) with its structured data, starting with `schema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/document-v1.json"`, and is declared in `[paper] md`; its numbers are then audited as a paper's. A Markdown file without front matter is not audited. *Prevents: results stated in Markdown, the usual form of a findings file, escaping the audit that a paper gets.*
- Every structured data file names its schema in a mandatory `schema` key: the URL of a versioned JSON Schema in [`schemas/`](schemas/) of this repository (`https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/<name>-v<n>.json`). A missing or unknown URL is a defect (`schema/missing`, `schema/unknown`; refused by `hook:gate_run`). The schemas: [`prereg-v1`](schemas/prereg-v1.json) (pre-registration front matter), [`exploration-log-v1`](schemas/exploration-log-v1.json), [`document-v1`](schemas/document-v1.json) (front matter of an audited Markdown document), [`provenance-v1`](schemas/provenance-v1.json) (results provenance, written by `osaudit run`). *Prevents: a data file whose format cannot be found, checked or evolved; whoever finds one is led back to these conventions.*
- Every machine-readable file of the audit (configuration, derivations, ledgers) is TOML. *Prevents: two parsers, two sets of quoting rules, two ways to be wrong.*
- An entry of `audit.toml` that matches nothing in the paper is a defect, and is reported. *Prevents: allow-lists and derivations that outlive the text they justified.*

## Study

Every result is **confirmatory** or **exploratory**. The difference is whether the analysis could still change after seeing the data. Only a confirmatory result confirms; an exploratory one estimates effect sizes and generates hypotheses, and its p-values and intervals are not calibrated.

### Pre-registration (confirmatory)

- A confirmatory run is a run of `experiments/<name>` (a script, or a directory of them) under a pre-registration `prereg/<yyyy-mm-dd>-<slug>.md` that names it, committed before the run with no uncommitted change (`hook:gate_run`, `study/not-preregistered`). *Prevents: a bar written after the result, and a registration for one experiment used to license another.*
- A pre-registration is not a plan, and is never named `plan*`. Plans are working scratch, edited during execution and often not committed; predictions kept only in a plan have no verifiable date. *Prevents: "pre-registered" claims that rest on a gitignored file last touched seconds before the results were committed.*
- A pre-registration is Markdown that starts with TOML front matter between `+++` lines. Every field below is mandatory, except `amendments` (`hook:gate_run`, `study/not-preregistered`). *Prevents: a registration no tool can read, so its α, its m and its data are whatever someone later says they were.*

```toml
+++
schema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/prereg-v1.json"
mode = "confirmatory"
hypothesis = "the treatment raises the pass rate"
null = "the pass rate is unchanged"
experiments = ["experiments/passrate.py"]   # every experiment it licenses (paths or directories)
data = ["data/test"]                        # the data range: every input path, none seen yet
statistic = "one-sided Fisher exact test on pass counts"
alpha = 0.05
m = 3                                       # number of tests this registration makes
correction = "holm"                         # holm|bonferroni|hochberg|benjamini-hochberg|none
go = "Holm-adjusted p < 0.05 and +5 points over the lazy arm"
stop = "adjusted p >= 0.05, or under +5 points"
disaster = "baseline pass rate differs from the recorded baseline by > 2 points"

[[amendments]]                              # zero or more
date = "2026-10-21"
data_seen = false
what = "alpha 0.05 -> 0.01"
why = "three more tests added to the family"
+++
```

- `correction = "none"` only when `m = 1`. *Prevents: a family of tests, each at α.*
- Every input of a confirmatory run is inside `data`, and the command runs one of `experiments` (`study/prereg-mismatch`). *Prevents: a registration on the test set, run on the training set.*
- A committed pre-registration is changed only by appending an `[[amendments]]` entry in the same commit, with the human's approval (`hook:guard_prereg` asks on Claude Code, refuses on Codex; `hook:gate_run` refuses shell writes). An amendment made after any of the data was seen has `data_seen = true`, and the result is then exploratory (`study/amended`). *Prevents: a bar that moves until it passes.*
- A result is judged against the pre-registration as committed at the run's commit; later edits do not change an earlier result. *Prevents: rewriting history to fit, and punishing an honest later amendment.*

### Exploration (exploratory)

- An exploratory run is a run from `explore/`, allowed without a pre-registration once an exploration log `explore/<yyyy-mm-dd>-<slug>.md` exists (`hook:gate_run`). *Prevents: forks taken and never written down.*
- An exploration log starts with TOML front matter, and its body lists every fork as it is made: what was chosen, over what, because of what was seen. *Prevents: an unknown number of tests behind every exploratory number.*

```toml
+++
schema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/exploration-log-v1.json"
mode = "exploratory"
holdout = ["data/test"]          # reserved before the first look, for the confirmatory run
data_seen = ["data/train.csv"]   # every path looked at, kept current
+++
```

- **Seen data is spent.** No input of a confirmatory run is an input of an exploratory or unlabelled run (same sha256, under any name), nor overlaps a log's `data_seen` (`study/data-reused`). *Prevents: confirming a hypothesis on the data that suggested it.*
- An exploratory finding becomes confirmatory only through a new pre-registration that fixes its forks as parameters and runs on data nobody has seen. *Prevents: relabelling.*

### Runs and reports

- Every run that produces a results file goes through `osaudit run`, labelled: `--prereg prereg/<file>.md` for a confirmatory run (refused unless the result would pass `osaudit study`), `--explore explore/<file>.md` for an exploratory one. A results file without a mode is unlabelled: never confirmatory. *Prevents: a mode claimed after the fact.*
- Every entry of the report says `CONFIRMATORY` or `EXPLORATORY` (`hook:check_report`). A confirmatory entry carries its pre-registration and verdict; an exploratory one its log, fork count and effect sizes, and no verdict. *Prevents: an exploratory p-value reported under a confirmatory verdict.*
- A number of the paper traced to exploratory results says "exploratory" in its paragraph (`numbers/exploratory-unlabelled`). *Prevents: a reader taking a forked p-value at face value.*

## Numbers

- Every number printed in the paper is a results value, a declared derivation of results values, or an allow-list entry with a reason (`numbers/untraced`). *Prevents: an untraced number, such as a breakdown found in no results file, and different when recomputed.*
- Results are JSON files produced by a committed instrument; a value is named `<file stem>.<key>.<key>…`. *Prevents: numbers copied by hand from a terminal.*
- A printed number with d decimals matches a value v when it equals v, or 100·v for a percent, within half a unit of its last digit. *Prevents: false alarms on correct rounding (0.6745 printed 67.5%, or 67.4% when rounding half to even).*
- A number that is a sum, difference, product or share of results values is declared in `[[numbers.derive]]` with its expression (`value = "296"`, `expr = "survey.responses - survey.complete"`). *Prevents: derived numbers that no one can recompute, and a matcher that guesses derivations.*
- A declared derivation that evaluates to another value than the printed one is a defect (`numbers/derive-mismatch`). *Prevents: a number that drifted after the results were regenerated.*
- An expression that names a value absent from the results is a defect (`numbers/derive-unknown`). *Prevents: derivations over results that were renamed or removed.*
- A number that is not produced by the study (a year, a count published by a cited source, a parameter of the method) is allow-listed with `reason`, and with `cite` when it comes from a source (`[[numbers.allow]]`). *Prevents: an unexplained exemption.*
- A number taken from a cited source agrees with that source, verbatim. "Equals" is said only of equal numbers. *Prevents: a count claimed to equal a published count that differs from it in the fourth digit.*
- A number inside a verbatim quote is audited as part of the quote, not as a number. *Prevents: reporting a source's numbers as the study's.*
- Counts of parts add up to the whole that the text states, and each part is named ("8 runs: 6 pass, of which 1 with all tests skipped, 2 cannot start"). *Prevents: arithmetic that does not close.*
- The same quantity has the same value in every section; a different population is named and its difference explained ("1,204 of the 1,500 responses are complete, the 296 others are partial"). *Prevents: counts that silently differ across sections.*

## Results

- Every results file is a JSON object with a `provenance` block: `command` (argv), `cwd`, `inputs` (each `path` with its `sha256`), `commit` (git commit of the instruments), `now` (time anchor, ISO 8601 with time zone), and, for a labelled run, `mode` (`confirmatory` or `exploratory`) with `study` (the path of its pre-registration or exploration log). `osaudit run` writes it (`results/no-provenance`). *Prevents: results that cannot be tied to the command, the data and the registration they claim.*

```json
"provenance": {
  "schema": "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/provenance-v1.json",
  "command": ["python", "experiments/passrate.py", "data/test"],
  "cwd": ".",
  "inputs": [{"path": "data/test", "sha256": "9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c9f2c"}],
  "commit": "3b1e7a0c3b1e7a0c3b1e7a0c3b1e7a0c3b1e7a0c",
  "now": "2026-10-21T10:00:00+00:00",
  "mode": "confirmatory",
  "study": "prereg/2026-10-21-passrate.md",
  "osaudit": "0.4.0"
}
```
- Results are produced from committed instruments: the instruments (`[results] instruments` in `audit.toml`) are unchanged since the recorded commit (`results/stale`). A results file that depends on only some of them declares them in `[[results.depends]]` (`file`, `instruments`). *Prevents: results of a version of the code that no longer exists, without rerunning every instrument for every change.*
- An input is a frozen snapshot: a directory input hashes as the manifest of its files, so a live directory (a log store that grows every day) never matches its record (`results/input-changed`, `results/input-missing`, with `--inputs`). *Prevents: results that no one can recompute, even with the same code.*
- Re-running the recorded command at the recorded time anchor prints the same results (`results/not-reproduced`, with `--rerun`). *Prevents: results that no instrument can produce any more, and numbers edited by hand.*
- An instrument never reads the clock or a file time: a time-dependent value (an age, a duration until now) is computed against the anchor in `$OSAUDIT_NOW`, recorded as `provenance.now` (`results/wall-clock`). A justified exception carries `osaudit: allow results/wall-clock -- <reason>` in a comment on the same line. *Prevents: values that shift between runs, such as ages computed against `now()` at analysis time, or against the modification time of a file.*
- A results file made by a person (a manual check of an automated classifier) is declared in `[[results.manual]]` with `file`, `by`, `date`, `reason`, and is exempt from provenance. *Prevents: a human judgment passed off as an instrument output, or rejected for not being one.*
- An exemption or a dependency entry that applies to nothing, inline or in `audit.toml`, is a defect (`results/unused`). *Prevents: exemptions that outlive the code they justified.*
- Every instrument is tested on a known-positive, a known-negative and a boundary case (the `validate-instrument` skill; not yet checked by a tool). *Prevents: trusting the numbers of an unvalidated instrument.*

## Quotes

- Every verbatim quote with a citation in the same sentence has an entry in the quote ledger, the `[[quotes]]` entries of `audit.toml` (`quotes/no-entry`). *Prevents: a quote no one checked.*
- A ledger entry records the citation `key`, the full sentence `text` verbatim, the `version` read (`publisher`, `author-pdf`, `preprint`, `reprint`, `abstract`, `secondary`), its `url`, the `page`, the `date` read and the `status` (`verified` or `unverified`), optionally the `claim` it supports. *Prevents: losing which text was actually read.*
- The quote of the paper is verbatim in the entry's text; `[...]` marks a cut (`quotes/mismatch`). *Prevents: a quote reworded, or attributed to a text that does not contain it.*
- The page cited is the page recorded (`quotes/page`), and an entry read in a paged version records its page (`quotes/no-page`). *Prevents: a page no one read.*
- Only a `verified` entry is quoted (`quotes/unverified`); an entry that matches no quote is removed (`quotes/unused`). *Prevents: quoting before checking, and a ledger that drifts from the paper.*
- A quote is `verified` only when its wording was matched against the version read; a summary by a search engine or a model is never a version read. *Prevents: a sentence that summaries attribute to an author, but that is not in the text.*
- The version read is the version cited; when they differ, the numbers and pages are those of the version cited, or the citation changes. *Prevents: citing a published version with the numbers of its preprint, which differ.*
- A quote from an abstract has no page and the ledger says `abstract`; a page read from a reprint is not the page of the original. *Prevents: invented page numbers.*
- A shortened quote keeps the scope of the full sentence; the ledger holds the full sentence. *Prevents: a truncated quote that widens the author's claim, such as a quote that drops "some of".*

## References

- A source is cited for a position it holds, not for one it refutes or does not address; the ledger entry records the claim the citation supports. *Prevents: citing a paper for the position it refutes, or a study of one measure for another measure.*
- Every BibTeX entry describes a paper that exists, with its authors, year and DOI: [check-hallucinations](https://github.com/ASSERT-KTH/check-hallucinations) is silent on the `.bib` (a separate tool, not an `osaudit` check). *Prevents: references with an invented title, or a real title with invented authors, year or DOI.*
- Every cross-reference resolves, and the text names what it points to. *Prevents: text pointing to an example removed in an earlier revision.*

## Reviews

- Every finding of an automated reviewer is a claim, verified by a tool before it is acted on. *Prevents: changing the author's prose for a style defect that the reviewer reported and the prose checker does not confirm.*
- A verified finding is reported with the tool output that confirms it; an unconfirmed finding is reported as unconfirmed, never acted on. *Prevents: reviewer hallucinations entering the paper as corrections.*
