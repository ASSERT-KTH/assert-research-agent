#!/usr/bin/env python3
"""PreToolUse(file edits): changing a committed pre-registration needs the human.

Moving a bar after results exist is how a dead hypothesis stays alive.
Claude Code (Edit/Write/MultiEdit, tool_input.file_path) gets "ask": the
human approves in the harness. Codex (apply_patch, paths inside the patch
in tool_input.command) cannot ask yet, so the edit is denied and the
operator makes it. Shell writes are refused by gate_run.
"""

from __future__ import annotations

from _common import AMEND_RULES, committed_preregs, emit, patch_paths, read_event

event = read_event()
cwd = event.get("cwd") or "."
tool_input = event.get("tool_input") or {}
codex = event.get("tool_name") == "apply_patch"
targets = patch_paths(tool_input.get("command", "")) if codex else [tool_input.get("file_path", "")]

hits = sorted({p for t in targets if t for p in committed_preregs(cwd, t)})
if hits:
    if codex:
        decision = "deny"
        reason = (
            f"{', '.join(hits)}: committed pre-registration. Codex hooks cannot ask the human, so this edit is "
            f"refused: stop and ask the operator to make or approve it. {AMEND_RULES}"
        )
    else:
        decision = "ask"
        reason = f"{', '.join(hits)}: committed pre-registration. If you proceed: {AMEND_RULES}"
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}})
