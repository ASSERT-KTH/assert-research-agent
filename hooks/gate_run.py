#!/usr/bin/env python3
"""PreToolUse(Bash): every run is either confirmatory or exploratory, and says so.

- Confirmatory run: a shell command matching RESEARCH_RUN_PATTERN (default:
  a path under experiments/). Allowed only if PREREG_DIR holds at least one
  committed .md file with no uncommitted edits — i.e. hypothesis, data
  range, procedure, α, decision rule and m were fixed before the data.
- Exploratory run: a command matching RESEARCH_EXPLORE_PATTERN (default: a
  path under explore/). Allowed without a pre-registration, but only once a
  fork log (.md in EXPLORE_DIR) exists, so data-dependent choices are
  written down as they are made.
"""

from __future__ import annotations

from _common import (
    EXPLORE_DIR,
    EXPLORE_PATTERN,
    PREREG_DIR,
    RUN_PATTERN,
    changed_paths,
    emit,
    git,
    read_event,
    repo_root,
)

event = read_event()
cmd = (event.get("tool_input") or {}).get("command", "")
cwd = event.get("cwd") or "."

reason = None
if RUN_PATTERN.search(cmd):
    tracked = [p for p in git(cwd, "ls-files", PREREG_DIR).splitlines() if p.endswith(".md")]
    dirty = [p for p in changed_paths(cwd) if p.startswith(PREREG_DIR + "/")]
    if not tracked:
        reason = (
            f"No committed pre-registration in {PREREG_DIR}/, so this run cannot be confirmatory. "
            "Use the preregister skill and commit it; or, to look at data first, use the explore skill "
            f"and run from {EXPLORE_DIR}/ (results are then EXPLORATORY)."
        )
    elif dirty:
        reason = f"Pre-registration has uncommitted edits ({', '.join(dirty)}). Commit it before running, so the bar is fixed before the result."
elif EXPLORE_PATTERN.search(cmd):
    logs = list((repo_root(cwd) / EXPLORE_DIR).glob("*.md"))
    if not logs:
        reason = (
            f"Exploratory run without a fork log. Use the explore skill: open {EXPLORE_DIR}/<date>-<slug>.md, "
            "reserve the holdout, then log every data-dependent choice as you make it."
        )

if reason:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})
