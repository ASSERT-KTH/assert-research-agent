"""Shared helpers for research-agent hooks.

Claude Code and Codex use the same hook protocol: event JSON on stdin,
decision JSON on stdout, exit 0. Hooks stay silent when they have nothing
to say.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Repo conventions, overridable per project via environment.
PREREG_DIR = os.environ.get("RESEARCH_PREREG_DIR", "prereg")
RESULTS_DIR = os.environ.get("RESEARCH_RESULTS_DIR", "results")
REPORT_FILES = os.environ.get("RESEARCH_REPORT_FILES", "REPORT.md,NOTES.md,README.md").split(",")
RUN_PATTERN = re.compile(os.environ.get("RESEARCH_RUN_PATTERN", r"(^|[\s/])experiments/\S+"))
# Group 1 names the experiment a run belongs to; its pre-registration must name it too.
EXPERIMENT_PATTERN = re.compile(
    os.environ.get("RESEARCH_EXPERIMENT_PATTERN", r"""(?:^|[\s/])(experiments/[^\s/'";|&)]+)""")
)
EXPLORE_DIR = os.environ.get("RESEARCH_EXPLORE_DIR", "explore")
EXPLORE_PATTERN = re.compile(os.environ.get("RESEARCH_EXPLORE_PATTERN", r"(^|[\s/])explore/\S+"))
MODE_LABELS = ("CONFIRMATORY", "EXPLORATORY")


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


def repo_root(cwd: str) -> Path:
    """Top of the git work tree, or cwd outside a repo."""
    return Path(git(cwd, "rev-parse", "--show-toplevel").strip() or cwd)


def patch_paths(patch: str) -> list[str]:
    """Files touched by a Codex apply_patch payload (Add/Update/Delete File, Move to)."""
    return re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$", patch, re.M)


AMEND_RULES = (
    "Add an 'Amendments' entry (date, whether any of the data was seen yet, what, why) and commit it. "
    "Amended before the data was seen: still confirmatory. After: the amended part is EXPLORATORY. "
    "A moved threshold also gets a 'Bar moved' entry: which direction, on what evidence."
)


def committed_preregs(cwd: str, target: str) -> list[str]:
    """Committed pre-registrations (repo-relative) that target, a path or glob relative to cwd, designates."""
    top = git(cwd, "rev-parse", "--show-toplevel").strip()
    if not top:
        return []
    path = Path(cwd).resolve() / target
    path = Path(os.path.normpath(path)) if any(c in target for c in "*?[") else path.resolve()
    try:
        rel = path.relative_to(Path(top).resolve()).as_posix()
    except ValueError:
        return []
    if not rel.startswith(PREREG_DIR + "/") and rel != PREREG_DIR:
        return []
    tracked = git(top, "ls-files", PREREG_DIR).splitlines()
    return [p for p in tracked if p == rel or fnmatch.fnmatchcase(p, rel) or p.startswith(rel.rstrip("/") + "/")]


# Commands whose path arguments are all written (or removed); cp/install/rsync write only their last.
_WRITERS = {"tee", "mv", "rm", "truncate", "touch", "chmod", "ln", "unlink", "shred"}
_INPLACE = {"sed", "perl", "ruby", "gsed"}
_GIT_WRITERS = {"rm", "mv", "checkout", "restore", "reset"}
_SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "|&"}
_REDIRECTS = {">", ">>", ">|", "&>", "&>>"}


def shell_write_targets(cmd: str) -> list[str]:
    """Paths a shell command writes, best effort: redirections, tee, in-place editors, mv/cp/rm, git rm/mv/checkout."""
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = cmd.split()
    targets: list[str] = []
    segment: list[str] = []
    for i, tok in enumerate([*tokens, ";"]):
        if tok in _SEPARATORS:
            targets += _segment_writes(segment)
            segment = []
        elif tok in _REDIRECTS and i + 1 < len(tokens):
            targets.append(tokens[i + 1])
        elif not (i > 0 and tokens[i - 1] in _REDIRECTS):
            segment.append(tok)
    return targets


def _segment_writes(words: list[str]) -> list[str]:
    while words and (("=" in words[0] and not words[0].startswith("-")) or words[0] in {"sudo", "env", "command"}):
        words = words[1:]
    if not words:
        return []
    prog, args = os.path.basename(words[0]), words[1:]
    paths = [a for a in args if not a.startswith("-")]
    if prog in _WRITERS:
        return paths
    if prog in {"cp", "install", "rsync"}:
        return paths[-1:]
    if prog in _INPLACE and any(a.startswith("-i") or a == "--in-place" or a.startswith("-pi") for a in args):
        return paths
    if prog == "git" and paths and paths[0] in _GIT_WRITERS:
        return paths[1:]
    return []


def added_text(cwd: str, path: str) -> str:
    """Text added to path since HEAD; the whole file if untracked or no HEAD."""
    if git(cwd, "ls-files", path).strip() and git(cwd, "rev-parse", "--verify", "-q", "HEAD").strip():
        diff = git(cwd, "diff", "HEAD", "-U0", "--", path).splitlines()
        return "\n".join(line[1:] for line in diff if line.startswith("+") and not line.startswith("+++"))
    try:
        return (repo_root(cwd) / path).read_text(encoding="utf-8")
    except OSError:
        return ""
