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
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_SCHEMA = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/audit-v1.json"
MODE_LABELS = ("CONFIRMATORY", "EXPLORATORY")


@dataclass(frozen=True)
class Study:
    """Repo conventions (CONVENTIONS.md, Repository): environment, else audit.toml [study], else defaults."""

    prereg: str
    explore: str
    experiments: str
    results: str
    report: list[str]
    run_pattern: re.Pattern[str]
    # Group 1 names the experiment a run belongs to; its pre-registration must name it too.
    experiment_pattern: re.Pattern[str]
    explore_pattern: re.Pattern[str]
    audit_toml: bool
    # Why audit.toml is not usable (no or wrong schema URL), or None.
    audit_problem: str | None


def study(cwd: str) -> Study:
    top = repo_root(cwd)
    toml: dict = {}
    problem = None
    try:
        data = tomllib.loads((top / "audit.toml").read_text(encoding="utf-8"))
        toml = data.get("study", {})
        if data.get("schema") != AUDIT_SCHEMA:
            problem = f'audit.toml must start with schema = "{AUDIT_SCHEMA}"'
    except OSError:
        pass
    except tomllib.TOMLDecodeError as e:
        problem = f"audit.toml: {e}"

    def get(key: str, env: str, default: str) -> str:
        return os.environ.get(env) or str(toml.get(key) or default)

    report = os.environ.get("RESEARCH_REPORT_FILES")
    exp = get("experiments", "RESEARCH_EXPERIMENTS_DIR", "experiments")
    explore = get("explore", "RESEARCH_EXPLORE_DIR", "explore")
    return Study(
        prereg=get("prereg", "RESEARCH_PREREG_DIR", "prereg"),
        explore=explore,
        experiments=exp,
        results=get("results", "RESEARCH_RESULTS_DIR", "results"),
        report=report.split(",") if report else list(toml.get("report") or ["REPORT.md", "NOTES.md", "README.md"]),
        run_pattern=re.compile(os.environ.get("RESEARCH_RUN_PATTERN") or rf"(^|[\s/]){re.escape(exp)}/\S+"),
        experiment_pattern=re.compile(
            os.environ.get("RESEARCH_EXPERIMENT_PATTERN") or rf"""(?:^|[\s/])({re.escape(exp)}/[^\s/'";|&)]+)"""
        ),
        explore_pattern=re.compile(os.environ.get("RESEARCH_EXPLORE_PATTERN") or rf"(^|[\s/]){re.escape(explore)}/\S+"),
        audit_toml=(top / "audit.toml").is_file(),
        audit_problem=problem,
    )


# Front matter formats (CONVENTIONS.md, Study; schemas/). osaudit holds the same checks.
FRONT = re.compile(r"\A\+\+\+[ \t]*\n(.*?)\n\+\+\+[ \t]*(?:\n|\Z)", re.DOTALL)
SCHEMAS = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/"
PREREG_SCHEMA = SCHEMAS + "prereg-v1.json"
LOG_SCHEMA = SCHEMAS + "exploration-log-v1.json"
TEXT_FIELDS = ("hypothesis", "null", "statistic", "go", "stop", "disaster")
LIST_FIELDS = ("experiments", "data")
CORRECTIONS = ("holm", "bonferroni", "hochberg", "benjamini-hochberg", "none")


def front_matter(text: str) -> tuple[dict | None, str]:
    m = FRONT.match(text)
    if not m:
        return None, "no TOML front matter (+++ ... +++ at the top)"
    try:
        return tomllib.loads(m.group(1)), ""
    except tomllib.TOMLDecodeError as e:
        return None, f"front matter: {e}"


def log_problems(text: str) -> list[str]:
    """What makes text not a valid exploration log; [] when valid."""
    fm, why = front_matter(text)
    if fm is None:
        return [why]
    out = [] if fm.get("schema") == LOG_SCHEMA else [f'schema must be "{LOG_SCHEMA}"']
    if fm.get("mode") != "exploratory":
        out.append('mode must be "exploratory"')
    out += [f"{k} must be a list of paths" for k in ("holdout", "data_seen") if not isinstance(fm.get(k), list)]
    return out


def prereg_problems(text: str) -> list[str]:
    """What makes text not a valid pre-registration; [] when valid."""
    fm, why = front_matter(text)
    if fm is None:
        return [why]
    out = [] if fm.get("schema") == PREREG_SCHEMA else [f'schema must be "{PREREG_SCHEMA}"']
    if fm.get("mode") != "confirmatory":
        out.append('mode must be "confirmatory"')
    out += [f"{k} must be a non-empty string" for k in TEXT_FIELDS if not (isinstance(fm.get(k), str) and fm[k].strip())]
    out += [
        f"{k} must be a non-empty list of paths"
        for k in LIST_FIELDS
        if not (isinstance(fm.get(k), list) and fm[k] and all(isinstance(p, str) and p for p in fm[k]))
    ]
    alpha, n = fm.get("alpha"), fm.get("m")
    if not (isinstance(alpha, float) and 0 < alpha < 1):
        out.append("alpha must be a number in (0, 1)")
    if not (isinstance(n, int) and not isinstance(n, bool) and n >= 1):
        out.append("m must be an integer >= 1, the number of tests")
    if fm.get("correction") not in CORRECTIONS:
        out.append(f"correction must be one of {', '.join(CORRECTIONS)}")
    elif fm["correction"] == "none" and isinstance(n, int) and n > 1:
        out.append(f'correction "none" with m = {n} tests')
    amendments = fm.get("amendments", [])
    if not isinstance(amendments, list) or not all(
        isinstance(a, dict) and isinstance(a.get("data_seen"), bool) and all(str(a.get(k, "")).strip() for k in ("date", "what", "why"))
        for a in amendments
    ):
        out.append("each [[amendments]] needs date, data_seen (true/false), what, why")
    return out


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
    prereg = study(cwd).prereg
    if not rel.startswith(prereg + "/") and rel != prereg:
        return []
    tracked = git(top, "ls-files", prereg).splitlines()
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
