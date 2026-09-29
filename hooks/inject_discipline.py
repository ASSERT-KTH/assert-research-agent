#!/usr/bin/env python3
"""SessionStart: inject system-prompt.md as additional context.

This is how a plugin (which cannot replace the system prompt) makes the
discipline present in every session, on both Claude Code and Codex.
"""

from __future__ import annotations

from _common import ROOT, emit, read_event

read_event()
text = (ROOT / "system-prompt.md").read_text(encoding="utf-8")
emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}})
