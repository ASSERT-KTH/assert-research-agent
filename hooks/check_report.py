#!/usr/bin/env python3
"""Stop: new results without a written record block the stop once.

If RESULTS_DIR changed but none of RESEARCH_REPORT_FILES did, the agent
is sent back to record the outcome (report-result skill). Fires at most
once per stop (stop_hook_active), so it cannot loop.
"""

from __future__ import annotations

from _common import REPORT_FILES, RESULTS_DIR, changed_paths, emit, read_event

event = read_event()
if event.get("stop_hook_active"):
    raise SystemExit(0)

changed = changed_paths(event.get("cwd") or ".")
results = [p for p in changed if p.startswith(RESULTS_DIR + "/")]
reported = [p for p in changed if p in REPORT_FILES]

if results and not reported:
    emit({
        "decision": "block",
        "reason": (
            f"{len(results)} changed path(s) under {RESULTS_DIR}/ but no report updated "
            f"({', '.join(REPORT_FILES)}). Use the report-result skill: decisive number both arms, "
            "three counts, what was not run. A negative result counts."
        ),
    })
