---
name: report-result
description: Record an experiment outcome — positive, negative or null — in the repo's report file in a fixed order, next to its pre-registration. Use after any run that produced a decisive number, when a hypothesis dies, when a previous number turns out wrong, or before telling the operator "it works".
---

# Report the result

Read the verdict off the pre-registered table; do not reinterpret it. Write
it in the file (REPORT.md by default), not only in the conversation.

## Order

1. **Decisive number**, all arms, same window, terminal unit, and the
   pre-registered verdict (GO / STOP / DISASTER / UNJUDGED).
2. **Three counts** per arm: considered / evaluated / succeeded.
3. **Not evaluated**, counted.
4. **Proxy result**, clearly subordinate to the decisive number.
5. **Not run, and why** — so nobody assumes it was tried and failed.
6. **Caveats in the same breath**: n, median and top1 beside means,
   fitted-to-n thresholds stated as such.

## Rules

- A negative result is reported as loudly as a positive one.
- A premise that killed the idea is written down: "killed by: <premise>".
- **Wrong earlier?** Correct it where the wrong number lives, keep the
  superseded value next to the correction: `~~1.92x~~ 4.4% (the 1.92x
  measured the wrong component)`.
- Link the pre-registration file and the commit that produced the number.

## Template

```markdown
## <date> <slug> — <VERDICT>

Prereg: prereg/<file>.md · commit <sha>

- Decisive: <treatment> vs <lazy> vs <baseline> (<unit>, <window>)
- Counts: considered/evaluated/succeeded — T <a/b/c>, L <…>, B <…>
- Not evaluated: <n, why>
- Proxy: <…>
- Not run: <what, why>
- Caveats: n=<…>, median <…>, top1 <…%>
- Killed by / next: <…>
```
