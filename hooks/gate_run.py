#!/usr/bin/env python3
"""PreToolUse(Bash): every run is either confirmatory or exploratory, and says so.

Directories come from `study(cwd)`: environment, else audit.toml [study] (CONVENTIONS.md).
An audit.toml without its schema URL (audit-v1) blocks every run until fixed.

A run is a command that executes a script: through an interpreter or runner
(python, bash, uv run, osaudit run, sbatch, ...) or by its path. Reading code
(cat, grep, git log) never is.

- Confirmatory run: a run matching the run pattern (default: a path under
  experiments/). Each experiment it invokes (experiments/<name>) must be
  named by a pre-registration committed in the prereg directory, with no
  uncommitted edits and a valid TOML front matter (hypothesis, data, α, m, ...)
  — i.e. fixed for *this* experiment before the data. When audit.toml exists,
  the run must also go through `osaudit run --prereg <file>`, so the result
  records its mode and osaudit refuses a run on data already seen. If a custom
  run pattern names no experiment, any committed pre-registration is accepted.
- Exploratory run: a command matching the explore pattern (default: a path
  under explore/). Allowed without a pre-registration, but only once a fork
  log (.md in the explore directory) with valid front matter (schema URL,
  mode, holdout, data_seen) exists, so data-dependent choices are written
  down as they are made.

Any shell command that writes a committed pre-registration (redirection,
tee, sed -i, mv/cp/rm, git checkout/restore…) is refused on both harnesses:
the edit tools are guarded by guard_prereg, and the shell must not be the
way around it. Writing a new, uncommitted pre-registration is allowed.
"""

from __future__ import annotations

from _common import (
    AMEND_RULES,
    Study,
    changed_paths,
    committed_preregs,
    emit,
    executed,
    git,
    log_problems,
    prereg_problems,
    read_event,
    repo_root,
    shell_write_targets,
    study,
)


def committed_preregs_naming(cwd: str, s: Study, ref: str) -> list[str]:
    """Pre-registrations whose committed (HEAD) text contains ref."""
    hits = git(cwd, "grep", "-l", "-F", ref, "HEAD", "--", f"{s.prereg}/*.md").splitlines()
    return [h.split(":", 1)[1] for h in hits]


def confirmatory_reason(cwd: str, s: Study, cmd: str, run: str) -> str | None:
    dirty = {p for p in changed_paths(cwd) if p.startswith(s.prereg + "/")}
    refs = sorted(set(s.experiment_pattern.findall(run)))
    if not refs:
        tracked = [p for p in git(cwd, "ls-files", s.prereg).splitlines() if p.endswith(".md")]
        if not tracked:
            return (
                f"No committed pre-registration in {s.prereg}/, so this run cannot be confirmatory. "
                "Use the preregister skill and commit it; or, to look at data first, use the explore skill "
                f"and run from {s.explore}/ (results are then EXPLORATORY)."
            )
        if dirty:
            return f"Pre-registration has uncommitted edits ({', '.join(sorted(dirty))}). Commit it before running, so the bar is fixed before the result."
        return None
    for ref in refs:
        preregs = committed_preregs_naming(cwd, s, ref)
        if not preregs:
            return (
                f"No committed pre-registration in {s.prereg}/ names {ref}, so this run cannot be confirmatory. "
                f"Use the preregister skill (its experiments list names {ref}) and commit it; or, to look at data "
                f"first, use the explore skill and run from {s.explore}/ (results are then EXPLORATORY)."
            )
        stale = sorted(dirty.intersection(preregs))
        if stale:
            return f"Pre-registration for {ref} has uncommitted edits ({', '.join(stale)}). Commit it before running, so the bar is fixed before the result."
        valid = [p for p in preregs if not prereg_problems(git(cwd, "show", f"HEAD:./{p}"))]
        if not valid:
            problems = "; ".join(prereg_problems(git(cwd, "show", f"HEAD:./{preregs[0]}")))
            return f"{preregs[0]} is not a machine-readable pre-registration: {problems}. See the preregister skill (TOML front matter), commit, then run."
        if s.audit_toml and not any(f"--prereg {p}" in cmd or f"--prereg={p}" in cmd for p in valid):
            return (
                f"audit.toml exists: run it as `osaudit run --prereg {valid[0]} --input <data> -o {s.results}/<name>.json -- <command>`, "
                "so the result records its mode and pre-registration (CONVENTIONS.md, Runs and reports)."
            )
    return None


event = read_event()
cmd = (event.get("tool_input") or {}).get("command", "")
cwd = event.get("cwd") or "."
s = study(cwd)
run = executed(cmd)  # only what executes a script is a run; reading code is not

written = sorted({p for t in shell_write_targets(cmd) for p in committed_preregs(cwd, t)})

reason = None
if written:
    reason = (
        f"{', '.join(written)}: committed pre-registration, written from the shell. Refused on every harness: "
        f"stop and ask the operator to make or approve the edit. {AMEND_RULES}"
    )
elif s.audit_problem and (s.run_pattern.search(run) or s.explore_pattern.search(run)):
    reason = f"{s.audit_problem} (CONVENTIONS.md, Repository). Fix it before any run."
elif s.run_pattern.search(run):
    reason = confirmatory_reason(cwd, s, cmd, run)
elif s.explore_pattern.search(run):
    logs = sorted((repo_root(cwd) / s.explore).glob("*.md"))
    if not logs:
        reason = (
            f"Exploratory run without a fork log. Use the explore skill: open {s.explore}/<date>-<slug>.md, "
            "reserve the holdout, then log every data-dependent choice as you make it."
        )
    elif all(log_problems(p.read_text(encoding="utf-8")) for p in logs):
        problems = "; ".join(log_problems(logs[0].read_text(encoding="utf-8")))
        reason = (
            f"No valid exploration log in {s.explore}/ ({logs[0].name}: {problems}). "
            "See the explore skill (TOML front matter with schema, mode, holdout, data_seen)."
        )

if reason:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})
