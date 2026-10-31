#!/usr/bin/env python3
"""Stop: new results need a written record that says which mode produced them, and an audit.

If the results directory changed but no report file did, the agent is sent
back to record the outcome (report-result skill). If a report did change but
the added text carries neither CONFIRMATORY nor EXPLORATORY, it is sent back
to label it. When osaudit.toml exists and osaudit is installed, `osaudit
results` and `osaudit study` run on the repo and their findings send the agent
back too. Fires at most once per stop (stop_hook_active), so it cannot loop.
"""

from __future__ import annotations

import shutil
import subprocess

from _common import MODE_LABELS, added_text, changed_paths, emit, read_event, repo_root, study


def osaudit_findings(cwd: str) -> str:
    exe = shutil.which("osaudit")
    if exe is None:
        return ""
    out = []
    for check in ("results", "study"):
        try:
            r = subprocess.run([exe, check, "--root", str(repo_root(cwd))], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as e:
            out.append(f"osaudit {check}: {e}")
            continue
        if r.returncode != 0:
            out.append((r.stdout + r.stderr).strip())
    return "\n".join(out)


event = read_event()
if event.get("stop_hook_active"):
    raise SystemExit(0)

cwd = event.get("cwd") or "."
s = study(cwd)
changed = changed_paths(cwd)
results = [p for p in changed if p.startswith(s.results + "/")]
reported = [p for p in changed if p in s.report]

reason = None
if results and not reported:
    reason = (
        f"{len(results)} changed path(s) under {s.results}/ but no report updated "
        f"({', '.join(s.report)}). Use the report-result skill: mode (CONFIRMATORY/EXPLORATORY), "
        "decisive number both arms, three counts, what was not run. A negative result counts."
    )
elif results and not any(label in added_text(cwd, p) for p in reported for label in MODE_LABELS):
    reason = (
        f"Report updated ({', '.join(reported)}) but the new entry says neither CONFIRMATORY nor EXPLORATORY. "
        "Label it (report-result skill): confirmatory only if run under a committed pre-registration on unseen data."
    )
elif results and s.osaudit_toml:
    findings = osaudit_findings(cwd)
    if findings:
        reason = f"osaudit reports findings on the new results (CONVENTIONS.md):\n{findings}"

if reason:
    emit({"decision": "block", "reason": reason})
