"""Hooks against throwaway git repos: confirmatory and exploratory paths."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parent.parent / "hooks"


def run_hook(name: str, event: dict) -> dict:
    """The hook's JSON output, {} when it stays silent."""
    out = subprocess.run(
        [sys.executable, str(HOOKS / name)], input=json.dumps(event), capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout) if out.stdout.strip() else {}


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def commit_all(repo: Path, msg: str) -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    (tmp_path / "README.md").write_text("x\n")
    commit_all(tmp_path, "init")
    return tmp_path


def gate(repo: Path, cmd: str) -> dict:
    return run_hook("gate_run.py", {"cwd": str(repo), "tool_input": {"command": cmd}})


def denied(out: dict) -> bool:
    return bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_unrelated_command_silent(repo: Path) -> None:
    assert gate(repo, "ls -la") == {}


def test_confirmatory_denied_without_prereg(repo: Path) -> None:
    out = gate(repo, "python experiments/run.py")
    assert denied(out)
    assert "explore skill" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_confirmatory_allowed_with_committed_prereg(repo: Path) -> None:
    (repo / "prereg").mkdir()
    (repo / "prereg" / "a.md").write_text("Mode: CONFIRMATORY\n")
    commit_all(repo, "prereg")
    assert gate(repo, "python experiments/run.py") == {}


def test_confirmatory_denied_with_dirty_prereg(repo: Path) -> None:
    (repo / "prereg").mkdir()
    (repo / "prereg" / "a.md").write_text("v1\n")
    commit_all(repo, "prereg")
    (repo / "prereg" / "a.md").write_text("v2\n")
    assert denied(gate(repo, "python experiments/run.py"))


def test_exploratory_denied_without_log(repo: Path) -> None:
    assert denied(gate(repo, "python explore/look.py"))


def test_exploratory_allowed_with_uncommitted_log(repo: Path) -> None:
    (repo / "explore").mkdir()
    (repo / "explore" / "2026-10-21-look.md").write_text("Mode: EXPLORATORY\n")
    assert gate(repo, "python explore/look.py") == {}


def test_exploratory_needs_no_prereg_but_confirmatory_still_does(repo: Path) -> None:
    (repo / "explore").mkdir()
    (repo / "explore" / "log.md").write_text("Mode: EXPLORATORY\n")
    assert gate(repo, "python explore/look.py") == {}
    assert denied(gate(repo, "python experiments/run.py"))


def stop(repo: Path, active: bool = False) -> dict:
    return run_hook("check_report.py", {"cwd": str(repo), "stop_hook_active": active})


def test_report_missing_blocks(repo: Path) -> None:
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    assert stop(repo)["decision"] == "block"


@pytest.mark.parametrize("label", ["CONFIRMATORY", "EXPLORATORY"])
def test_labelled_report_passes(repo: Path, label: str) -> None:
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    (repo / "README.md").write_text(f"x\n## 2026-10-21 a — {label}\n")
    assert stop(repo) == {}


def test_unlabelled_report_blocks(repo: Path) -> None:
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    (repo / "README.md").write_text("x\n## 2026-10-21 a — GO\n")
    out = stop(repo)
    assert out["decision"] == "block" and "neither" in out["reason"]


def test_label_already_committed_does_not_count(repo: Path) -> None:
    (repo / "README.md").write_text("x\nEXPLORATORY old entry\n")
    commit_all(repo, "old")
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    (repo / "README.md").write_text("x\nEXPLORATORY old entry\nnew unlabelled entry\n")
    assert stop(repo)["decision"] == "block"


def test_untracked_report_labelled_passes(repo: Path) -> None:
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    (repo / "REPORT.md").write_text("## a — EXPLORATORY\n")
    assert stop(repo) == {}


def test_stop_hook_active_silent(repo: Path) -> None:
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    assert stop(repo, active=True) == {}
