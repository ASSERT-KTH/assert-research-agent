#!/usr/bin/env python3
"""PreToolUse(file edits): changing a committed pre-registration needs the human.

Moving a bar after results exist is how a dead hypothesis stays alive.
Claude Code (Edit/Write/MultiEdit, tool_input.file_path) gets "ask": the
human approves in the harness. Codex (apply_patch, paths inside the patch
in tool_input.command) cannot ask yet, so the edit is denied and the
operator makes it.
"""

from __future__ import annotations

from pathlib import Path

from _common import PREREG_DIR, emit, git, patch_paths, read_event

event = read_event()
cwd = event.get("cwd") or "."
tool_input = event.get("tool_input") or {}
codex = event.get("tool_name") == "apply_patch"
targets = patch_paths(tool_input.get("command", "")) if codex else [tool_input.get("file_path", "")]
targets = [t for t in targets if t]
if not targets:
    raise SystemExit(0)

top = git(cwd, "rev-parse", "--show-toplevel").strip()
if not top:
    raise SystemExit(0)


def committed_prereg(target: str) -> str | None:
    try:
        rel = (Path(cwd) / target).resolve().relative_to(Path(top).resolve()).as_posix()
    except ValueError:
        return None
    return rel if rel.startswith(PREREG_DIR + "/") and git(top, "ls-files", rel).strip() else None


hits = [rel for rel in map(committed_prereg, targets) if rel]
if hits:
    rules = (
        "Add an 'Amendments' entry (date, whether any of the data was seen yet, what, why) and commit it. "
        "Amended before the data was seen: still confirmatory. After: the amended part is EXPLORATORY. "
        "A moved threshold also gets a 'Bar moved' entry: which direction, on what evidence."
    )
    if codex:
        decision = "deny"
        reason = (
            f"{', '.join(hits)}: committed pre-registration. Codex hooks cannot ask the human, so this edit is "
            f"refused: stop and ask the operator to make or approve it. {rules}"
        )
    else:
        decision = "ask"
        reason = f"{', '.join(hits)}: committed pre-registration. If you proceed: {rules}"
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}})
