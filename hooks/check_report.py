#!/usr/bin/env python3
"""Stop: new results need a written record that says which mode produced them.

If RESULTS_DIR changed but none of RESEARCH_REPORT_FILES did, the agent is
sent back to record the outcome (report-result skill). If a report did
change but the added text carries neither CONFIRMATORY nor EXPLORATORY,
it is sent back to label it. Fires at most once per stop
(stop_hook_active), so it cannot loop.
"""

from __future__ import annotations

from _common import MODE_LABELS, REPORT_FILES, RESULTS_DIR, added_text, changed_paths, emit, read_event

event = read_event()
if event.get("stop_hook_active"):
    raise SystemExit(0)

cwd = event.get("cwd") or "."
changed = changed_paths(cwd)
results = [p for p in changed if p.startswith(RESULTS_DIR + "/")]
reported = [p for p in changed if p in REPORT_FILES]

reason = None
if results and not reported:
    reason = (
        f"{len(results)} changed path(s) under {RESULTS_DIR}/ but no report updated "
        f"({', '.join(REPORT_FILES)}). Use the report-result skill: mode (CONFIRMATORY/EXPLORATORY), "
        "decisive number both arms, three counts, what was not run. A negative result counts."
    )
elif results and not any(label in added_text(cwd, p) for p in reported for label in MODE_LABELS):
    reason = (
        f"Report updated ({', '.join(reported)}) but the new entry says neither CONFIRMATORY nor EXPLORATORY. "
        "Label it (report-result skill): confirmatory only if run under a committed pre-registration on unseen data."
    )

if reason:
    emit({"decision": "block", "reason": reason})
