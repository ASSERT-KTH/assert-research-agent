# Being data-driven

How to decide things by measurement instead of argument, and how to avoid
the specific ways that goes wrong

The one-line version: **you are not trying to find out whether you are
right. You are trying to find out what is true.**

```
1. name the premise you are least inclined to check
2. measure it cheaply, before building on it
3. fix GO/STOP before you know the answer, in the tool
4. make sure the registered quantity would still be right if it came back as hoped
5. validate the instrument where the answer is already known
6. measure the laziest alternative in the same breath
7. check units, coverage and top1 before magnitude
8. when it dies, write down what killed it, in the file
9. label every result CONFIRMATORY or EXPLORATORY; only the first confirms
```

Four wrong answers in a day is not a bad day.
**Four wrong answers that nobody noticed is.**

---

## 1. The loop

```
1. PREMISE    name the assumption you are least inclined to check
2. MEASURE    check it, cheaply, BEFORE building on it
3. REGISTER   write what each possible result will mean, before any exist
4. CONTROL    measure the laziest alternative in the same breath
5. INSTRUMENT validate the measuring tool where you know the answer
6. DECIDE     read the result off the table you already wrote
7. RECORD     write down what killed it, in the file, including what you did not run
```

Steps 1, 3 and 5 are the ones that do the work. Step 2 feels like
progress and often is not.

---

## 2. Pre-registration

Before any measurement, write into the plan **and into the tool**:

```
1. THE NUMBER    what is measured, in what unit, over what window
2. THE BASELINE  what it is now, measured the SAME way, before you touch anything
3. GO            the result that means ship it, as a threshold
4. STOP          the result that means abandon it, and what to do instead
5. THE DISASTER  the result that means halt immediately, and why
6. THE LIMITS    what this design cannot answer whatever it returns
```

Then run it and read the answer off the table. When the answer is a
statistical test, the registration also fixes the hypothesis, the data
range, the statistic and α, and the number of tests (§3).

**Why.** Without it, every disappointing result has an escape hatch, and
they all sound reasonable: *the sample was small; the environment was
quiet; let's try one notch higher; that case was unusual.* Each is
individually defensible and collectively they keep a dead hypothesis alive
forever.

**The tell:** if you are deciding what a number means *after* seeing it,
you are not measuring, you are negotiating.

**Step 5 is the one that pays.** Write the result you would least like to
get, with its consequence attached, because that is the one you will be
most tempted to explain away. Include outcomes that should be impossible —
"two of these can never both be included; if I ever see it, stop
immediately, the accounting is wrong" — precisely because they are the
ones nobody will believe when they appear.

### Pre-register the RIGHT quantity

This is the failure that survives doing everything else correctly.


> Before you accept step 1, ask: **would this quantity still be the right
> one if it came back exactly as I hope?**

### Put the verdict in the tool

A threshold in a document is a threshold someone reinterprets when the
answer disappoints. A threshold in code prints itself:

```
VERDICT: NOT YET. 2 treatment blocks of the 321 needed for an 80%
  chance of one landing at a 0.5% rate. Keep running.
```

Make the tool refuse to conclude when its own preconditions are not met —
sample too small, control missing, verdict carried by one observation.
Every good tool in that project has, at least once, printed a verdict its
author did not want.

### Two shapes of useless criterion

- **Cannot fail.** "Zero counterexamples over 200 runs" across half a
  million checks: at any error rate above zero it always says FAIL and
  discriminates nothing.
- **Cannot pass.** A precision demand below the resolution of the
  instrument measuring it — unreachable by construction.

**When a bar has to move, record which direction and on what evidence.** A
bar that only ever loosens, until it passes, is fitting the criterion to
the answer. One that tightens, or narrows on a measured argument and then
immediately fails on real cases, is the only kind worth trusting.

---

## 3. Confirmatory or exploratory

Every result is one or the other, and says which. **The formal difference
is whether the analysis could still change after seeing the data.**

### Confirmatory (pre-registered)

Before any of the data is looked at, a timestamped git commit fixes:

```
1. HYPOTHESIS     the claim, and the null it is tested against
2. DATA RANGE     exactly which data; not seen by anyone yet
3. PROCEDURE      the code path, its version, every parameter
4. STATISTIC, α   the test statistic and the significance level
5. DECISION RULE  which result means GO / STOP / DISASTER
6. m              the number of tests, and the correction (e.g. Holm)
```

Then, and only then, a p-value means what it says: P(reject | H0) ≤ α,
and the family-wise error is controlled because m was known in advance.
A pre-registration may be amended **before** the data is seen (a new
commit, with the reason); the commit dates prove the order. An amendment
made after any of the data was seen makes the amended part exploratory.

A confirmatory study that finds nothing has still produced its answer.
"K = 0 under the registered procedure" is a result, not a cue to look
again.

### Exploratory

Some choice is made after seeing results. Typical forks:

- running the exploration at all, because the confirmatory pilot came out
  empty;
- a window, lag or bin width picked because it looked clean;
- keeping only the subset where every class has data;
- showing the upper interval because it was the interesting one;
- a threshold placed after someone noticed a gap in the distribution.

Each fork depends on the data, so the real number of tests is unknown
(the garden of forking paths). **Its p-values and confidence intervals
are not calibrated**: "p < .05" does not mean a 5% false-positive rate,
and no multiplicity correction repairs it, because m is not known.

Exploration is legitimate and necessary. It can estimate effect sizes,
find bugs, and generate hypotheses. **It can never confirm.**

### Rules

- **Label every number** CONFIRMATORY or EXPLORATORY, in the report, in
  the tool output, in the slide. Unlabelled means exploratory.
- **Log every fork while exploring**, at the moment you make it: what you
  chose, what you had seen that made you choose it. The fork count is the
  honest caveat on every exploratory number; a fork you did not write down
  is a test you are hiding.
- **Seen data is spent.** Data looked at during exploration cannot serve
  as the DATA RANGE of a later confirmatory test. Confirm on a held-out
  split, a new time range, or a new sample. Reserve the holdout before the
  first exploratory look, so it is never in doubt.
- **Promote, don't relabel.** An exploratory finding becomes confirmatory
  only by writing a new pre-registration, fixing every fork the
  exploration chose as a parameter, and running it on unseen data. Running
  the same analysis on the same data again confirms nothing.
- **Never mix the two in one sentence.** "Significant (p = .01)" next to
  a confirmatory verdict, when the p came from an exploratory fork,
  launders it.

---

## 4. The premise is what kills you, not the logic

One plan produced **four contradictory answers in a single session**. Every one died when a premise nobody had checked
got checked:

```
answer                         killed by
"do A, it's worth 97% of value" summing outcomes assumed they all succeed; almost none do
"B dilutes the metric"          the cost model contradicted its own filter
"selective B, GO"               the 1.92x control was measuring a different component
"nothing works"                 the resource everyone said was scarce was 47% idle
```

> When an argument feels finished, go and find the sentence you did not
> think needed checking. It is usually the one carrying the conclusion.

**A proof about the wrong quantity is still a wrong answer.** One of those
arguments was formally valid — an average never exceeds a maximum, both
steps sound — and useless, because it was about rationing a resource
nobody rations. Before proving something, ask what would have to be true
of the world for the conclusion to *matter*, and measure that first. A
short measurement beats a long proof, and it beats it *before* you write
the proof.

---

## 5. Validate the instrument where you already know the answer

**The most expensive error is a measurement bug, not a
reasoning bug.**

> For any measurement, find an input whose output you can derive
> independently, and check it there first. A tool that has never been run
> against a known answer (ground truth) is not evidence.

Corollary: when a measurement disagrees with another measurement, **do not
pick the one you prefer.** Reconcile them or discard both. In that case
the live path and the offline tool disagreed; the live path was right, the
offline tool had the same bug in a different place, and the disagreement
was the only reason either got checked.

---

## 6. Controls

**A verdict without a control is an artefact.**

A tool reported a counterparty as *rejecting* a new request shape,
0-of-3 — which was the pre-registered STOP condition for the whole plan.
It also answered **0 of 1** for the ordinary request shape in the same
window. It was not rejecting anything; it never answers. The verdict
compared a rate against an absolute bar with nothing to compare it to, and
would have killed a working feature.

> Every rate needs the same rate measured on the thing you did *not*
> change. If you cannot get one, the tool must print UNJUDGED, not a
> verdict.

**Compare against the cheapest thing that also works.** Measuring a change
against *today* credits it with everything a simpler change would also
deliver. One idea looked like 12x until it was measured against a
one-line alternative; then 1.92x; then, once *that* was measured at a
fixed parameter, **4.4%**. Two controls, two collapses.

**Interleave, do not sequence.** When the environment drifts — and it
always drifts — an A-then-B comparison across hours measures the
environment. Alternate arms per unit of work, decided at the moment of
work, not per hour. One project measured a latency change at +14.7σ this
way after a before/after comparison had measured nothing.

**Record the arm; do not infer it.** If treatment sometimes produces
output that looks like control, counting outputs misfiles every thin
treatment case as control — biasing toward "no effect", which is the
direction that flatters the null. Write the arm into the record at the
time of the decision.

---

## 7. Units, magnitude, and tails

**Check the denomination before believing the magnitude.** A number
four orders of magnitude from anything you have seen is not a finding;
check its units first, every time.

Prefer **dimensionless ratios** where you can: both sides in the same
unit means no conversion step can go wrong.

**Heavy tails make means lie.** Two samples of the *same* 24 hours, taken
minutes apart, disagreed **4x** because one caught a single large event.

> Print the **median** and **top1** — the largest single observation as a
> share of its bucket's total — beside every mean. A bucket at 99% top1 is
> one observation wearing a percentage. Make the tool refuse a positive
> verdict carried by a tail.

That check reversed a result in this project. The tool printed
`POSITIVE, plan unblocks`; top1 was 99% of the bucket. What survived was a
near-zero median — a real answer, just a much weaker one.

**Scan the population when you can.** Sampling a heavy-tailed quantity is
where the error comes from.

---

## 8. Small n

**Compute whether your observations actually contradict the hypothesis
before declaring that they do.**

Three consecutive negative real outcomes appeared to contradict a replay
showing 12-of-21 positive. They did not: three consecutive negatives has
probability (9/21)³ ≈ **0.079**. Perfectly ordinary. Without that one line
of arithmetic the replay would have been discarded as obviously wrong.

Equally: **do not fit a threshold to two points and call it calibration.**
When you must — because the operator asked, or the implication is real —
state plainly in the code that it is fitted to n=2, which direction it
moved, and that it is the smallest value consistent with the only
observations available, *not* the value that optimises anything.

**Distinguish "not measured" from "measured zero".** They are different
observations and collapsing them is how a system learns from silence. In
code that means an explicit `ok bool` beside the value, never a zero
default.

---

## 9. Proxies

**A proxy can be perfectly satisfied by something worthless.** Eleven
commits drove a correctness proxy from 79% violations to 0.3% while the
thing being built was searching **7% of the available space**. The proxy
asked whether what was present was handled correctly. It could not ask how
much was absent.

> Whenever you optimise a proxy, measure the thing it stands in for at
> least once, early. In that case it was one line — `kept / available` —
> and it would have saved a day.

Report **`considered` / `evaluated` / `succeeded`** together, not just the
last. And **count what you could not evaluate**: a number that is silently
zero is indistinguishable from one that is genuinely zero.

---

## 10. Reporting

State, in this order:

0. **The mode: CONFIRMATORY or EXPLORATORY** (§3). A confirmatory result
   carries its pre-registration commit and its verdict; an exploratory
   one carries its fork count and no verdict, only effect sizes and the
   hypotheses it generated.
1. **The decisive number, both arms, same window, in the terminal unit.**
2. **The three counts** (considered / evaluated / succeeded) for both. The
   ranking is the verdict; these say why.
3. **What could not be evaluated**, counted.
4. **The proxy result, clearly subordinate.** "Correct at 99.7% and
   covering 98%, and it still earned 5.7x less" is the honest shape.
   Leading with the proxy inverts it.
5. **What you did NOT run, and why** — so the next person does not assume
   it was tried and failed.
6. **Caveats in the same breath as the number.** Twelve samples is twelve
   samples.

**Report the negative result as loudly as the positive one.** Two efforts
in that project built working, tested code and shipped none of it. Both
were worth as much as a shipped feature and cost the next session nothing
to re-learn.

**Say plainly when you were wrong** — not as ceremony, as information.
Correct it *in the file where the wrong number lives*, not only in
conversation, and keep the superseded answer next to the correction so the
error is not re-derived. "The 1.92x was measuring the wrong component" is
a fact the next reader needs; burying it costs them the same day it cost
you.

---

