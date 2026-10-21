#!/usr/bin/env python3
"""PreToolUse(Bash): every run is either confirmatory or exploratory, and says so.

- Confirmatory run: a shell command matching RESEARCH_RUN_PATTERN (default:
  a path under experiments/). Each experiment it invokes (EXPERIMENT_PATTERN,
  default experiments/<name>) must be named by a pre-registration committed
  in PREREG_DIR with no uncommitted edits — i.e. hypothesis, data range,
  procedure, α, decision rule and m were fixed for *this* experiment before
  the data. If the custom RUN_PATTERN names no experiment, any committed
  pre-registration is accepted.
- Exploratory run: a command matching RESEARCH_EXPLORE_PATTERN (default: a
  path under explore/). Allowed without a pre-registration, but only once a
  fork log (.md in EXPLORE_DIR) exists, so data-dependent choices are
  written down as they are made.

Any shell command that writes a committed pre-registration (redirection,
tee, sed -i, mv/cp/rm, git checkout/restore…) is refused on both harnesses:
the edit tools are guarded by guard_prereg, and the shell must not be the
way around it. Writing a new, uncommitted pre-registration is allowed.
"""

from __future__ import annotations

from _common import (
    AMEND_RULES,
    EXPERIMENT_PATTERN,
    EXPLORE_DIR,
    EXPLORE_PATTERN,
    PREREG_DIR,
    RUN_PATTERN,
    changed_paths,
    committed_preregs,
    emit,
    git,
    read_event,
    repo_root,
    shell_write_targets,
)


def committed_preregs_naming(cwd: str, ref: str) -> list[str]:
    """Pre-registrations whose committed (HEAD) text contains ref."""
    hits = git(cwd, "grep", "-l", "-F", ref, "HEAD", "--", f"{PREREG_DIR}/*.md").splitlines()
    return [h.split(":", 1)[1] for h in hits]


def confirmatory_reason(cwd: str, cmd: str) -> str | None:
    dirty = {p for p in changed_paths(cwd) if p.startswith(PREREG_DIR + "/")}
    refs = sorted(set(EXPERIMENT_PATTERN.findall(cmd)))
    if not refs:
        tracked = [p for p in git(cwd, "ls-files", PREREG_DIR).splitlines() if p.endswith(".md")]
        if not tracked:
            return (
                f"No committed pre-registration in {PREREG_DIR}/, so this run cannot be confirmatory. "
                "Use the preregister skill and commit it; or, to look at data first, use the explore skill "
                f"and run from {EXPLORE_DIR}/ (results are then EXPLORATORY)."
            )
        if dirty:
            return f"Pre-registration has uncommitted edits ({', '.join(sorted(dirty))}). Commit it before running, so the bar is fixed before the result."
        return None
    for ref in refs:
        preregs = committed_preregs_naming(cwd, ref)
        if not preregs:
            return (
                f"No committed pre-registration in {PREREG_DIR}/ names {ref}, so this run cannot be confirmatory. "
                f"Use the preregister skill (its Procedure line names {ref}) and commit it; or, to look at data "
                f"first, use the explore skill and run from {EXPLORE_DIR}/ (results are then EXPLORATORY)."
            )
        stale = sorted(dirty.intersection(preregs))
        if stale:
            return f"Pre-registration for {ref} has uncommitted edits ({', '.join(stale)}). Commit it before running, so the bar is fixed before the result."
    return None


event = read_event()
cmd = (event.get("tool_input") or {}).get("command", "")
cwd = event.get("cwd") or "."

written = sorted({p for t in shell_write_targets(cmd) for p in committed_preregs(cwd, t)})

reason = None
if written:
    reason = (
        f"{', '.join(written)}: committed pre-registration, written from the shell. Refused on every harness: "
        f"stop and ask the operator to make or approve the edit. {AMEND_RULES}"
    )
elif RUN_PATTERN.search(cmd):
    reason = confirmatory_reason(cwd, cmd)
elif EXPLORE_PATTERN.search(cmd):
    if not list((repo_root(cwd) / EXPLORE_DIR).glob("*.md")):
        reason = (
            f"Exploratory run without a fork log. Use the explore skill: open {EXPLORE_DIR}/<date>-<slug>.md, "
            "reserve the holdout, then log every data-dependent choice as you make it."
        )

if reason:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})
