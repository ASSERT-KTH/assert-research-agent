# Agentic Scientific Method

> your agent can do better science if taught so

Agentic infrastructure for doing scientific research in our field. A
**research agent** is either:

- a **config on top of an existing harness** — [`claude/`](claude/) for
  Claude Code, [`codex/`](codex/) for Codex, more to come; or
- a **dedicated harness** — _to come_.

Both carry the same discipline, written once in
[`system-prompt.md`](system-prompt.md).

## The discipline 🔬

TLDR: **you are not trying to find out whether you are right.
You are trying to find out what is true.**

A working discipline for deciding by measurement instead of argument:

- 🔁 the loop — premise, measure, register, control, instrument, decide, record
- 📝 pre-registration — GO / STOP / DISASTER written down *before* any result exists
- 🔀 confirmatory vs exploratory — every result says which; only the first confirms
- 🧨 the premise, not the logic, is what kills a result
- 🧪 validate the instrument where the answer is already known
- 🐌 measure the laziest alternative in the same breath
- 📏 units, magnitude and tails before celebrating a delta
- 🔢 small n, proxies, and honest reporting of what was *not* run

## Pre-registration 📝

The central concept. Before any number exists, write down what each
possible number will mean — and commit it:

```
1. THE NUMBER    what is measured, in what unit, over what window
2. THE BASELINE  what it is now, measured the same way
3. GO            the result that means ship it
4. STOP          the result that means abandon it, and what instead
5. THE DISASTER  the result that means halt immediately
6. THE LIMITS    what this design cannot answer whatever it returns
```

Then run, and read the verdict off the table. If you decide what a number
means *after* seeing it, you are not measuring, you are negotiating.

In a research agent this is enforced, not just advised:

- the `preregister` skill writes `prereg/<date>-<slug>.md`, with a TOML
  front matter (hypothesis, data, α, m, correction, GO/STOP/DISASTER) that
  tools can read;
- a hook **refuses to run an experiment** until a committed, valid
  pre-registration names it (git history is the timestamp proving it came
  first);
- a hook **asks the human** (Claude Code) or **refuses** (Codex, whose hooks
  cannot ask) before a committed pre-registration is edited, and the edit
  must record whether the data was seen yet, which way the bar moved and on
  what evidence.

## Confirmatory vs exploratory 🔀

The formal difference: **could the analysis still change after seeing the
data?**

- ✅ **Confirmatory** — before any data is looked at, a timestamped git
  commit fixes the hypothesis, the data range, the procedure, the test
  statistic and α, the decision rule, and the number of tests m. The
  p-value then means what it says, P(reject | H0) ≤ α, and a correction
  such as Holm works because m is known. Amendments are allowed before the
  data is seen, as new commits.
- 🔭 **Exploratory** — some choice was made after seeing results: running
  the exploration because a pilot came out empty, a window picked because
  it looked clean, a subset kept, a threshold placed at a gap. Each fork
  depends on the data, so the real number of tests is unknown and p-values
  and CIs are not calibrated. Exploration estimates effect sizes and
  generates hypotheses; it **never confirms**.

An exploratory finding becomes confirmatory only by a new pre-registration
that fixes its forks as parameters and runs on data nobody has seen —
reserve the holdout before the first look.

How the infrastructure supports both:

- `experiments/<name>` runs are confirmatory: gated on a committed
  `prereg/*.md` that names `experiments/<name>`.
- `explore/` runs are exploratory: allowed without a pre-registration, but
  only once a fork log `explore/<date>-<slug>.md` exists (`explore` skill).
- Every report entry is labelled `CONFIRMATORY` or `EXPLORATORY`; the stop
  hook sends the agent back if new results come with an unlabelled entry.
- Every results file is written by `osaudit run --prereg` or `--explore`,
  which records the mode in its provenance (see below).

## Specification and audit: CONVENTIONS.md and osaudit 📜

[`CONVENTIONS.md`](CONVENTIONS.md) is the single specification of a
research repository, from the first pre-registration to the paper: layout
and `audit.toml [study]`, pre-registration and exploration-log formats, the
results `provenance` block, and the rules on numbers, quotes and references.
It lives here because this is where the process starts.

Two tools enforce it at two moments:

- 🤖 **during** the work, the research agent (this repo) refuses actions:
  an unregistered run, an exploratory run without a log, an edit of a
  committed pre-registration;
- 🔎 **afterwards**, [osaudit](https://github.com/ASSERT-KTH/osaudit) checks
  the repository alone, without trusting whoever did the work:
  - `osaudit run --prereg FILE` refuses a confirmatory run that would not
    pass the audit, then records `mode` and `study` in the result;
  - `osaudit study` proves every confirmatory result was pre-registered
    (`study/not-preregistered`), on registered experiments and data
    (`study/prereg-mismatch`), not amended without a record or after the
    data was seen (`study/amended`), and on data no exploration touched,
    by path or by sha256 (`study/data-reused`);
  - `osaudit numbers` flags a paper number traced to exploratory results
    whose paragraph does not say so (`numbers/exploratory-unlabelled`).

When the experimental repository has an `audit.toml`, the hooks require
confirmatory runs to go through `osaudit run --prereg`, and the stop hook
runs `osaudit results` and `osaudit study` (when installed) on new results.

## How a research agent is built 🧱

Three layers, from always-on to on-demand to enforced:

- 💬 **Prompt** — `system-prompt.md`, the discipline itself. Loaded into
  every session by a `SessionStart` hook that reads `../system-prompt.md`
  (harness configs cannot replace the system prompt, but can inject context). Shapes how the agent *reasons*.
- 🧰 **Skills** — [`skills/`](skills/), one `SKILL.md` per procedure,
  loaded only when the task matches its description. Same format for Claude
  Code and Codex. Turn principles into steps and templates:
  - `preregister` — premise check, hypothesis, unseen data range, α, m, GO/STOP/DISASTER table, committed before a confirmatory run
  - `explore` — holdout reserved, fork log kept as choices are made, output labelled EXPLORATORY, ends in hypotheses to pre-register
  - `validate-instrument` — known-answer check, units, coverage, median/top1
  - `add-control` — baseline + laziest-alternative arms, interleaved, arm recorded
  - `report-result` — mode label first, fixed reporting order, negatives as loud as positives
- 🪝 **Hooks** — [`hooks/`](hooks/), small Python scripts run by the harness
  on lifecycle events. They do not rely on the model remembering; they
  check the repo. Same JSON protocol on both harnesses. Silent unless
  something is wrong.
  - `inject_discipline.py` (`SessionStart`) — injects `system-prompt.md`
  - `gate_run.py` (`PreToolUse` Bash) — denies a confirmatory run unless a committed pre-registration with valid front matter names that experiment (and, with `audit.toml`, unless it goes through `osaudit run --prereg`), an exploratory run without a fork log, and any shell command writing a committed pre-registration (redirection, `tee`, `sed -i`, `mv`/`cp`/`rm`, `git checkout`/`restore`…; best effort, an interpreter writing the file is not caught)
  - `guard_prereg.py` (`PreToolUse` Edit/Write on Claude, `apply_patch` on Codex) — asks (Claude) or denies (Codex) before a committed pre-registration changes
  - `check_report.py` (`Stop`) — sends the agent back once if `results/` changed but no report was written, the new entry is not labelled CONFIRMATORY/EXPLORATORY, or `osaudit results`/`study` report findings

Rule of thumb: if the model *should* know it → prompt; if it is a
procedure with a template → skill; if forgetting it silently corrupts a
result → hook.

## Repo conventions 📁

The hooks assume this layout in the experimental repository (normative
version: [`CONVENTIONS.md`](CONVENTIONS.md)). Override the directories in
`audit.toml [study]` (shared with osaudit) or with environment variables,
which take precedence:

- `experiments/` — confirmatory entry points (`[study] experiments`,
  `RESEARCH_EXPERIMENTS_DIR`); a shell command touching a path here is a
  *confirmatory run* (`RESEARCH_RUN_PATTERN`, a regex);
  `experiments/<name>` (first component, a script or a directory) is the
  experiment it runs, and a committed pre-registration must contain that
  path (`RESEARCH_EXPERIMENT_PATTERN`, a regex whose group 1 is the path)
- `prereg/` — pre-registrations, one `.md` per question (`[study] prereg`, `RESEARCH_PREREG_DIR`)
- `explore/` — exploratory scripts and their fork logs; a shell command
  touching a path here is an *exploratory run* (`RESEARCH_EXPLORE_PATTERN`,
  a regex; logs in `[study] explore`, `RESEARCH_EXPLORE_DIR`)
- `results/` — results JSON with provenance (`[study] results`, `RESEARCH_RESULTS_DIR`)
- `REPORT.md` — the written record (`[study] report`, `RESEARCH_REPORT_FILES`, comma-separated)

## Install ⚙️

### Claude Code

`claude/` is a Claude Code plugin (`.claude-plugin/plugin.json`, skills,
`hooks/hooks.json`). Try it without installing:

```sh
claude --plugin-dir /path/to/assert-research-agent/claude
```

Skills then appear as `research-agent:preregister` etc.

### Codex

Check out this repo at `~/.codex/research-agent`, then:

```sh
cat ~/.codex/research-agent/codex/config.toml >> ~/.codex/config.toml
ln -s ~/.codex/research-agent/skills/* ~/.codex/skills/
```

Codex asks you to trust non-managed hooks once: run `/hooks`.

### Any other agent

No harness support? Use the prompt alone: drop it at the root of the
experimental repository as `AGENTS.md`.

```sh
curl -o AGENTS.md https://raw.githubusercontent.com/ASSERT-KTH/assert-research-agent/main/system-prompt.md
```

## Layout 🗺️

```
system-prompt.md   the discipline (single source of truth)
CONVENTIONS.md     the specification of a research repository (shared with osaudit)
skills/            shared SKILL.md procedures
hooks/             shared hook scripts
tests/             hook tests (pytest tests/)
claude/            Claude Code plugin (symlinks to skills/ and hooks/)
codex/             Codex config.toml snippet (symlinks to skills/ and hooks/)
```

## The rule 📐

**Any experimental repository for research must run under a research
agent — or at least carry the discipline as its `AGENTS.md`.**

Experimental repository = any repo where code is run to produce a number that
someone will believe: benchmarks, ablations, evaluations, measurement
harnesses, reproduction packages, artifacts attached to a paper. If a result
leaves the repo and lands in a slide, an issue, or a paper, the repo is in
scope.

## License

MIT
