#!/usr/bin/env python3
"""SessionStart: inject ../system-prompt.md as additional context.

This is how a harness config (which cannot replace the system prompt)
makes the discipline present in every session, on both Claude Code and
Codex. The path is resolved from the real script location, so it works
through the claude/scripts and codex/scripts symlinks.
"""

from __future__ import annotations

from pathlib import Path

from _common import emit, read_event

read_event()
text = (Path(__file__).resolve().parent / ".." / "system-prompt.md").read_text(encoding="utf-8")
emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}})
