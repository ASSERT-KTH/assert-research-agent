"""Hooks against throwaway git repos: confirmatory and exploratory paths."""

from __future__ import annotations

import json
import os
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


def prereg(repo: Path, name: str, text: str, commit: bool = True) -> None:
    (repo / "prereg").mkdir(exist_ok=True)
    (repo / "prereg" / name).write_text(text)
    if commit:
        commit_all(repo, f"prereg {name}")


AUDIT_HEAD = 'schema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/audit-v1.json"\n\n'
LOG = '+++\nschema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/exploration-log-v1.json"\nmode = "exploratory"\nholdout = []\ndata_seen = []\n+++\n# look\n'


def valid(*experiments: str, extra: str = "") -> str:
    """A machine-readable pre-registration (CONVENTIONS.md, Study) licensing experiments."""
    return (
        "+++\n"
        'schema = "https://github.com/ASSERT-KTH/assert-research-agent/blob/main/schemas/prereg-v1.json"\n'
        'mode = "confirmatory"\nhypothesis = "h"\nnull = "h0"\n'
        f"experiments = {json.dumps(list(experiments))}\n"
        'data = ["data/test"]\nstatistic = "t"\nalpha = 0.05\nm = 1\ncorrection = "none"\n'
        f'go = "g"\nstop = "s"\ndisaster = "d"\n{extra}'
        "+++\n\n# body\n"
    )


def test_confirmatory_allowed_with_matching_committed_prereg(repo: Path) -> None:
    prereg(repo, "a.md", valid("experiments/run.py"))
    assert gate(repo, "python experiments/run.py --seed 1") == {}


@pytest.mark.parametrize(
    "text, problem",
    [
        ("Procedure: experiments/run.py\n", "no TOML front matter"),
        (valid("experiments/run.py").replace("alpha = 0.05", "alpha = 5"), "alpha"),
        (valid("experiments/run.py").replace("m = 1", "m = 3"), 'correction "none" with m = 3'),
        (valid("experiments/run.py").replace('data = ["data/test"]\n', ""), "data must be"),
        (valid("experiments/run.py", extra='[[amendments]]\ndate = "d"\n'), "amendments"),
    ],
)
def test_confirmatory_denied_with_invalid_front_matter(repo: Path, text: str, problem: str) -> None:
    prereg(repo, "a.md", text)
    out = gate(repo, "python experiments/run.py")
    assert denied(out) and problem in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_confirmatory_needs_osaudit_run_when_audit_toml(repo: Path) -> None:
    (repo / "audit.toml").write_text(AUDIT_HEAD + '[paper]\ntex = ["p.tex"]\n')
    prereg(repo, "a.md", valid("experiments/run.py"))
    out = gate(repo, "python experiments/run.py")
    assert denied(out) and "osaudit run --prereg prereg/a.md" in out["hookSpecificOutput"]["permissionDecisionReason"]
    cmd = "osaudit run --prereg prereg/a.md --input data/test -o results/r.json -- python experiments/run.py"
    assert gate(repo, cmd) == {}


def test_study_dirs_from_audit_toml(repo: Path) -> None:
    (repo / "audit.toml").write_text(AUDIT_HEAD + '[study]\nprereg = "registrations"\nexperiments = "exp"\n')
    (repo / "registrations").mkdir()
    (repo / "registrations" / "a.md").write_text(valid("exp/run.py"))
    commit_all(repo, "prereg")
    assert denied(gate(repo, "python exp/other.py"))
    assert gate(repo, "osaudit run --prereg registrations/a.md -o results/r.json -- python exp/run.py") == {}
    assert gate(repo, "python experiments/run.py") == {}  # not an experiment directory here
    assert denied(gate(repo, "echo x >> registrations/a.md"))


def test_confirmatory_denied_when_prereg_names_other_experiment(repo: Path) -> None:
    prereg(repo, "a.md", "Procedure: experiments/other.py\n")
    out = gate(repo, "python experiments/run.py")
    assert denied(out) and "names experiments/run.py" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_confirmatory_denied_when_matching_prereg_uncommitted(repo: Path) -> None:
    prereg(repo, "a.md", "Procedure: experiments/run.py\n", commit=False)
    assert denied(gate(repo, "python experiments/run.py"))


def test_confirmatory_experiment_directory(repo: Path) -> None:
    prereg(repo, "a.md", valid("experiments/abl/"))
    assert gate(repo, "bash experiments/abl/run.sh") == {}
    assert denied(gate(repo, "bash experiments/abl2/run.sh"))


def test_confirmatory_every_experiment_in_command_needs_prereg(repo: Path) -> None:
    prereg(repo, "a.md", "Procedure: experiments/a.py\n")
    assert denied(gate(repo, "python experiments/a.py && python experiments/b.py"))


def test_confirmatory_denied_with_dirty_matching_prereg(repo: Path) -> None:
    prereg(repo, "a.md", "Procedure: experiments/run.py v1\n")
    prereg(repo, "a.md", "Procedure: experiments/run.py v2\n", commit=False)
    assert denied(gate(repo, "python experiments/run.py"))


def test_confirmatory_dirty_unrelated_prereg_does_not_block(repo: Path) -> None:
    prereg(repo, "a.md", valid("experiments/run.py"))
    prereg(repo, "b.md", "Procedure: experiments/other.py (draft)\n", commit=False)
    assert gate(repo, "python experiments/run.py") == {}


def test_exploratory_denied_without_log(repo: Path) -> None:
    assert denied(gate(repo, "python explore/look.py"))


def test_exploratory_allowed_with_uncommitted_log(repo: Path) -> None:
    (repo / "explore").mkdir()
    (repo / "explore" / "2026-10-21-look.md").write_text(LOG)
    assert gate(repo, "python explore/look.py") == {}


def test_exploratory_needs_no_prereg_but_confirmatory_still_does(repo: Path) -> None:
    (repo / "explore").mkdir()
    (repo / "explore" / "log.md").write_text(LOG)
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


def guard(repo: Path, event: dict) -> dict:
    return run_hook("guard_prereg.py", {"cwd": str(repo), **event})


def decision(out: dict) -> str | None:
    return out.get("hookSpecificOutput", {}).get("permissionDecision")


def test_guard_claude_asks_on_committed_prereg(repo: Path) -> None:
    prereg(repo, "a.md", "x\n")
    out = guard(repo, {"tool_name": "Edit", "tool_input": {"file_path": str(repo / "prereg" / "a.md")}})
    assert decision(out) == "ask"


def test_guard_claude_silent_on_uncommitted_prereg_and_other_files(repo: Path) -> None:
    prereg(repo, "a.md", "x\n", commit=False)
    assert guard(repo, {"tool_name": "Write", "tool_input": {"file_path": str(repo / "prereg" / "a.md")}}) == {}
    assert guard(repo, {"tool_name": "Edit", "tool_input": {"file_path": str(repo / "README.md")}}) == {}


def apply_patch(*headers: str) -> dict:
    body = "\n".join(f"*** {h}\n+x" for h in headers)
    return {"tool_name": "apply_patch", "tool_input": {"command": f"*** Begin Patch\n{body}\n*** End Patch"}}


def test_guard_codex_denies_committed_prereg_absolute_and_relative(repo: Path) -> None:
    prereg(repo, "a.md", "x\n")
    assert decision(guard(repo, apply_patch(f"Update File: {repo / 'prereg' / 'a.md'}"))) == "deny"
    assert decision(guard(repo, apply_patch("Update File: README.md", "Delete File: prereg/a.md"))) == "deny"


def test_guard_codex_silent_on_new_prereg_and_other_files(repo: Path) -> None:
    assert guard(repo, apply_patch("Add File: prereg/new.md")) == {}
    assert guard(repo, apply_patch("Update File: README.md")) == {}


SHELL_WRITES = [
    "echo 'alpha=0.1' >> prereg/a.md",
    "echo x >prereg/a.md",
    "printf x | tee -a prereg/a.md",
    "sed -i 's/0.05/0.1/' prereg/a.md",
    "perl -pi -e 's/a/b/' prereg/a.md",
    "mv prereg/a.md prereg/b.md",
    "rm -f prereg/*.md",
    "rm -rf prereg",
    "cp /tmp/x.md prereg/a.md",
    "git checkout -- prereg/a.md",
    "cd . && FOO=1 sudo truncate -s0 prereg/a.md",
    "echo x > ./prereg/../prereg/a.md",
]

SHELL_OK = [
    "cat prereg/a.md",
    "cat prereg/a.md > /tmp/copy.md",
    "grep -n alpha prereg/a.md 2>&1 | head",
    "cp prereg/a.md /tmp/backup.md",
    "cat > prereg/new.md <<'EOF'\nMode: CONFIRMATORY\nEOF",
    "git add prereg/new.md && git commit -m 'prereg: new'",
    "git diff prereg/a.md",
]


@pytest.mark.parametrize("cmd", SHELL_WRITES)
def test_shell_write_to_committed_prereg_denied(repo: Path, cmd: str) -> None:
    prereg(repo, "a.md", "Procedure: experiments/run.py\n")
    out = gate(repo, cmd)
    assert denied(out) and "from the shell" in out["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.parametrize("cmd", SHELL_OK)
def test_shell_read_or_new_prereg_allowed(repo: Path, cmd: str) -> None:
    prereg(repo, "a.md", "Procedure: experiments/run.py\n")
    assert gate(repo, cmd) == {}


def test_shell_write_absolute_path_denied(repo: Path) -> None:
    prereg(repo, "a.md", "x\n")
    assert denied(gate(repo, f"echo x >> {repo / 'prereg' / 'a.md'}"))


def test_shell_write_from_subdirectory_denied(repo: Path) -> None:
    prereg(repo, "a.md", "x\n")
    (repo / "sub").mkdir()
    out = run_hook("gate_run.py", {"cwd": str(repo / "sub"), "tool_input": {"command": "echo x >> ../prereg/a.md"}})
    assert denied(out)


def fake_osaudit(tmp_path: Path, exit_code: int, output: str) -> dict[str, str]:
    """An `osaudit` on PATH that prints output and exits with exit_code, for the Stop hook."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / "osaudit"
    exe.write_text(f"#!/bin/sh\necho '{output}'\nexit {exit_code}\n")
    exe.chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}


def stop_with(repo: Path, env: dict[str, str]) -> dict:
    out = subprocess.run(
        [sys.executable, str(HOOKS / "check_report.py")],
        input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True, check=True, env=env,
    )
    return json.loads(out.stdout) if out.stdout.strip() else {}


def labelled_results(repo: Path) -> None:
    (repo / "audit.toml").write_text(AUDIT_HEAD + '[paper]\ntex = ["p.tex"]\n')
    commit_all(repo, "audit")
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    (repo / "REPORT.md").write_text("## a — CONFIRMATORY\n")


def test_stop_reports_osaudit_findings(repo: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    labelled_results(repo)
    env = fake_osaudit(tmp_path_factory.mktemp("o"), 1, "results/r.json:1: study/data-reused: x")
    out = stop_with(repo, env)
    assert out["decision"] == "block" and "study/data-reused" in out["reason"]


def test_stop_silent_when_osaudit_clean(repo: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    labelled_results(repo)
    assert stop_with(repo, fake_osaudit(tmp_path_factory.mktemp("o"), 0, "")) == {}


def test_stop_skips_osaudit_without_audit_toml(repo: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    (repo / "results").mkdir()
    (repo / "results" / "r.json").write_text("{}")
    (repo / "REPORT.md").write_text("## a — EXPLORATORY\n")
    assert stop_with(repo, fake_osaudit(tmp_path_factory.mktemp("o"), 1, "finding")) == {}


def test_exploratory_denied_with_log_without_schema(repo: Path) -> None:
    (repo / "explore").mkdir()
    (repo / "explore" / "log.md").write_text(LOG.replace("schema", "schemaa"))
    out = gate(repo, "python explore/look.py")
    assert denied(out) and "schema must be" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_confirmatory_denied_without_schema(repo: Path) -> None:
    prereg(repo, "a.md", "\n".join(l for l in valid("experiments/run.py").splitlines() if not l.startswith("schema")))
    out = gate(repo, "python experiments/run.py")
    assert denied(out) and "schema must be" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_runs_denied_when_audit_toml_has_no_schema(repo: Path) -> None:
    (repo / "audit.toml").write_text('[paper]\ntex = ["p.tex"]\n')
    prereg(repo, "a.md", valid("experiments/run.py"))
    (repo / "explore").mkdir()
    (repo / "explore" / "log.md").write_text(LOG)
    for cmd in ("osaudit run --prereg prereg/a.md -o results/r.json -- python experiments/run.py",
                "python explore/look.py"):
        out = gate(repo, cmd)
        assert denied(out) and "audit.toml must start with schema" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert gate(repo, "ls") == {}


@pytest.mark.parametrize("cmd", [
    "cat experiments/run.py",
    "grep -n alpha experiments/run.py explore/look.py",
    "git log --oneline -- experiments/",
    "ls experiments/ && wc -l experiments/run.py",
])
def test_reading_experiment_code_is_not_a_run(repo: Path, cmd: str) -> None:
    assert gate(repo, cmd) == {}


@pytest.mark.parametrize("cmd", [
    "python3 experiments/run.py",
    "cd . && FOO=1 uv run python experiments/run.py",
    "nohup bash experiments/run.sh &",
    "./experiments/run.sh",
    "sbatch experiments/job.sh",
    "timeout 60 python3.12 explore/look.py",
])
def test_executing_experiment_code_is_a_run(repo: Path, cmd: str) -> None:
    assert denied(gate(repo, cmd))
