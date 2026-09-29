"""Shared helpers for research-agent hooks.

Claude Code and Codex use the same hook protocol: event JSON on stdin,
decision JSON on stdout, exit 0. Hooks stay silent when they have nothing
to say.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Repo conventions, overridable per project via environment.
PREREG_DIR = os.environ.get("RESEARCH_PREREG_DIR", "prereg")
RESULTS_DIR = os.environ.get("RESEARCH_RESULTS_DIR", "results")
REPORT_FILES = os.environ.get("RESEARCH_REPORT_FILES", "REPORT.md,NOTES.md,README.md").split(",")
RUN_PATTERN = re.compile(os.environ.get("RESEARCH_RUN_PATTERN", r"(^|[\s/])experiments/\S+"))


def read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def emit(payload: dict) -> None:
    print(json.dumps(payload))


def git(cwd: str, *args: str) -> str:
    """Run git; return stdout, or '' when not a repo / git fails."""
    try:
        out = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout if out.returncode == 0 else ""


def changed_paths(cwd: str) -> list[str]:
    """Paths with uncommitted changes (staged, unstaged or untracked)."""
    return [line[3:].strip() for line in git(cwd, "status", "--porcelain").splitlines()]
