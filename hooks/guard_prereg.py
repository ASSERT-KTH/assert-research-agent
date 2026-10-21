#!/usr/bin/env python3
"""PreToolUse(Edit|Write): editing a committed pre-registration asks the human.

Moving a bar after results exist is how a dead hypothesis stays alive.
Allowed, but only with a human in the loop and the direction recorded.
"""

from __future__ import annotations

from pathlib import Path

from _common import PREREG_DIR, emit, git, read_event

event = read_event()
cwd = event.get("cwd") or "."
target = (event.get("tool_input") or {}).get("file_path", "")
if not target:
    raise SystemExit(0)

top = git(cwd, "rev-parse", "--show-toplevel").strip()
if not top:
    raise SystemExit(0)
try:
    rel = Path(target).resolve().relative_to(Path(top).resolve()).as_posix()
except ValueError:
    raise SystemExit(0)

if rel.startswith(PREREG_DIR + "/") and git(top, "ls-files", rel).strip():
    emit({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"{rel} is a committed pre-registration. If you proceed, add an 'Amendments' entry "
            "(date, whether any of the data was seen yet, what, why) and commit it. Amended before the data "
            "was seen: still confirmatory. After: the amended part is EXPLORATORY. A moved threshold also "
            "gets a 'Bar moved' entry: which direction, on what evidence."
        ),
    }})
