---
name: validate-instrument
description: Check a measurement tool (script, benchmark harness, metric, parser, log analysis) against an input whose answer is known independently, before trusting its output. Use when a new measurement tool is written or changed, when two measurements disagree, or when a number is orders of magnitude off anything seen before.
---

# Validate the instrument where the answer is known

The most expensive error is a measurement bug, not a reasoning bug. A tool
never run against ground truth is not evidence.

## Steps

1. **Find a known-answer input.** Derive the expected output by hand or by
   an independent path: a tiny hand-built dataset, a degenerate case (empty,
   single item, all-identical), a case where treatment == control so the
   delta must be 0.
2. **Run the tool on it** and compare. Write the check as a test
   (`tests/test_instrument_*.py` or equivalent) so it keeps running: one
   known-positive, one known-negative, one boundary case (CONVENTIONS.md,
   Results).
3. **No clock.** An instrument reads the time anchor from `$OSAUDIT_NOW`,
   never `now()` or a file time, so a rerun gives the same numbers
   (`results/wall-clock`).
4. **Check denomination first**: units, window, what the denominator counts.
   Prefer dimensionless ratios.
5. **Check coverage**: print `considered / evaluated / succeeded`, and count
   what could not be evaluated. "Not measured" must be distinguishable from
   "measured zero" (an explicit `ok` flag, never a zero default).
6. **Check tails**: print median and top1 (largest observation as share of
   its bucket) beside every mean. Refuse a positive verdict carried by one
   observation.
7. **Two measurements disagree?** Do not pick the one you prefer. Reconcile
   them or discard both; record which was wrong and why.

## Output

One line in the pre-registration's "Instrument check" field: input, expected,
observed, pass/fail. If it failed, fix the tool before any real run.
