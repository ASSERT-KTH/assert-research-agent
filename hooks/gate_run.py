#!/usr/bin/env python3
"""PreToolUse(Bash): no experiment run without a committed pre-registration.

An experiment run is a shell command matching RESEARCH_RUN_PATTERN
(default: anything invoking a path under experiments/). It is allowed only
if PREREG_DIR holds at least one committed .md file with no uncommitted
edits — i.e. GO/STOP/DISASTER were fixed before the number exists.
"""

from __future__ import annotations

from _common import PREREG_DIR, RUN_PATTERN, changed_paths, emit, git, read_event

event = read_event()
cmd = (event.get("tool_input") or {}).get("command", "")
cwd = event.get("cwd") or "."

if not RUN_PATTERN.search(cmd):
    raise SystemExit(0)

tracked = [p for p in git(cwd, "ls-files", PREREG_DIR).splitlines() if p.endswith(".md")]
dirty = [p for p in changed_paths(cwd) if p.startswith(PREREG_DIR + "/")]

reason = None
if not tracked:
    reason = f"No committed pre-registration in {PREREG_DIR}/. Use the preregister skill, commit it, then run."
elif dirty:
    reason = f"Pre-registration has uncommitted edits ({', '.join(dirty)}). Commit it before running, so the bar is fixed before the result."

if reason:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}})
