# Solution video — script and shot list

**Deliverable 03. Up to 5 minutes.** This script runs to **4:20**, leaving room to
breathe rather than filling the ceiling. Every command is real, every number comes
from a committed file in `results/`, and the whole live portion executes in about
ten seconds.

The brief names six beats. Each has its own scene here, and the demo still gets the
largest single block, because the brief also says the goal is *something a real
person would want to use*.

| Brief requires (p.7) | Scene |
|---|---|
| Begin with the problem and simple baseline | 0:00–0:35 |
| One realistic execution, start to finish | 0:35–1:50 |
| Show the final comparison | 2:20–3:00 |
| Briefly explain the changelog | 3:00–3:35 |
| The change that contributed most | 3:35–4:00 |
| One experiment you removed | 4:00–4:20 |

**Word budget: ~610 words at ~150 wpm ≈ 245 s of speech in a 260 s runtime.** The
per-scene counts are real. Read it once against a timer before recording.

---

## Before you record

```bash
PY -m pytest tests/ -q          # 189 passed
PY scripts/smoke.py             # all 18 documented commands work
```

Green smoke means every command and number below is current.

- Terminal font **≥ 16pt**, wide enough that the audit line doesn't wrap.
- `openpyxl` prints `WARNING:root:Defined name…` on 25-year-old files. The commands
  below already pipe it away with `2>/dev/null`.
- README open in a second window at *How this was evaluated*.

---

## 0:00 – 0:35 · The problem, and what people do today *(84 words)*

*On screen: a real Enron spreadsheet in Excel, scrolling.*

> You've inherited a financial model. The person who built it has left. You have to
> sign off on the numbers going into a board pack.
>
> Ninety-four percent of real spreadsheets contain errors. This one has seventeen
> hundred formulas. Checking them by hand takes about five hours, so nobody does it —
> you spot-check, and you hope.
>
> The alternative today is a rule-based auditor: it flags structural anomalies and
> hands you a list. We'll come back to what that list actually looks like.

---

## 0:35 – 1:50 · The product, running *(171 words)*

```bash
plumbline audit "data/seeded/chris_germany__1938__Mar2002_EstateGas.xlsx" 2>/dev/null
```

*Let it run. ~4.5 s. Don't fill the silence — the speed is the point.*

```
Plumbline - chris_germany__1938__Mar2002_EstateGas.xlsx
  1,395 formula cells checked

  PROVED  Sheet1!AI74  (formula differs from the rest of its row)
          is        =+AH73
          should be =+AH74
          AI74: -50000 -> 2.3845 (+50002.3845)
  ...
  PROVED  Sheet1!AG55  (typed-in value where a formula belongs)
          is        -4000
          should be =+AF55
          set AF55 -4000 -> -3000: AG55 as-is -4000 -> -4000 (no response);
                                   as formula -> -3000 (responds)
```

> Four seconds. And notice the word **proved**.
>
> *(point at AI74)* This row carries values across — every cell reads the one to its
> left. This one reads one row **up**. A dragged formula. We don't just flag it: we
> repair it, recompute the entire workbook, and show you the number moves. **Fifty
> thousand.** That's why it's at the top — the list is ordered by what it costs you.
>
> *(point at AG55)* This one is harder, and it's the one that should worry you.
> Someone typed minus four thousand over a formula. It is **correct today**. Nothing
> looks wrong. Repairing it changes nothing at all.
>
> So we prove it another way — nudge the input it should depend on. A live formula
> follows. This one sits there. It isn't a number any more, it's a monument. The day
> someone updates that input, the model goes silently wrong and nobody knows.

---

## 1:50 – 2:20 · Why you can trust it *(77 words)*

```bash
plumbline audit forecast.xlsx 2>/dev/null
```

```
Plumbline - forecast.xlsx
  not audited: volatile: 1 volatile cell(s) using RAND
```

> This workbook uses `RAND`. Our proof compares two calculations — on a sheet like
> this they differ for reasons that have nothing to do with any error. So we
> **refuse to audit it**, rather than hand you proofs that don't reproduce.

*Switch to `audit.md`, scroll to the blind-spots section.*

> Every report ends with what we did **not** check — including a class of error we
> know we now miss. We never edit your workbook, and every finding says a qualified
> reviewer should confirm it before you change anything.

---

## 2:20 – 3:00 · Does it actually work *(112 words)*

*On screen: README, "How this was evaluated".*

> Twenty-one real Enron workbooks, fifty-three planted errors, same cases for every
> arm. Our primary metric was fixed before the first run.
>
> Against the same detector with our contributions switched off: **F1 zero-point-zero-two
> to zero-point-nine-nine.** That baseline finds the errors too — and buries them in
> four thousand false ones. That's the rule-based auditor from the opening, and it's
> why analysts don't use them.
>
> In the analyst's own currency: seventeen hundred formulas to check manually, two
> hundred and forty-seven flagged by the baseline, **seventeen** by us — with
> evidence attached.
>
> And we asked a language model directly. On the silent errors — the invisible ones —
> a direct prompt found **29 percent**. We found **82**.

---

## 3:00 – 3:35 · The changelog *(76 words)*

*On screen: scroll the Improvement Changelog.*

> Every meaningful experiment is here with its evidence and what we decided.
>
> The one I'd point at: we swept a detector threshold, and the benchmark said
> lowering it was free — better recall, precision untouched. So we read the
> twenty-nine new findings by hand. About ten were ordinary data columns, flagged
> wrongly. Precision only held because those land in a bucket the score can't see.
>
> **We shipped the setting with the worse benchmark score**, and wrote down why.

---

## 3:35 – 4:00 · The change that mattered most *(64 words)*

> It wasn't a detector. It was discovering our own **benchmark** was lying to us.
>
> A runtime cap meant to bound cost was silently deleting detections. Four workbooks
> scored zero true positives — not because we missed anything, but because the
> findings were thrown away before scoring. Ten of twenty misses.
>
> For most of this project, the thing being measured was the measurement.

---

## 4:00 – 4:20 · One we removed *(64 words)*

> Our first repair used the obvious library call — set the cell, recompute. It
> returned the **unchanged** value: it sets the value but leaves the formula tree
> alone.
>
> So the tool would have said "repairing this changes nothing" for cells where
> repairing changes everything. **Fake proofs, silently.** For a tool whose entire
> product is proof, that's the worst available bug. Removed. We write a patched copy
> and re-parse instead.

---

## Close *(within 4:20 — say over the last shot)*

```bash
plumbline audit yourmodel.xlsx --report audit.md
```

> Point it at your own model. Deterministic, no API key, nothing to pay. Nothing
> reaches you that we couldn't prove.

---

## Shot list

| # | Shot | Duration |
|---|---|---|
| 1 | Enron sheet in Excel, scrolling | 35s |
| 2 | **Live:** `plumbline audit …EstateGas.xlsx` | 75s |
| 3 | **Live:** refusal, then `audit.md` blind spots | 30s |
| 4 | README, *How this was evaluated* | 40s |
| 5 | README, Improvement Changelog | 35s |
| 6 | Changelog rows: proof budget, then removed experiment | 45s |
| 7 | **Live:** `--report audit.md`, close | 20s |

Shots 2, 3 and 7 are the same terminal — two windows total.

### Making the refusal fixture

```python
from openpyxl import Workbook
wb = Workbook(); ws = wb.active
ws["A1"] = 100
for c in range(2, 8):
    ws.cell(row=1, column=c, value=f"={chr(64+c-1)}1*1.05")
ws["B3"] = "=RAND()*100"
wb.save("forecast.xlsx")
```

### If you overrun

You have 40 s of headroom before the 5:00 ceiling, so overrunning is unlikely. If
you do, cut in this order:

1. The `audit.md` blind-spots pan in shot 3 (−15 s) — the README covers it.
2. The middle finding in shot 2 — show only `AI74` and `AG55` (−15 s).
3. Shot 1 → static screenshot instead of scrolling (−10 s).

Do **not** cut scenes 5–7. They are three separately-required beats.

### One number to be careful with

The **29% vs 82%** comparison is like-for-like: both figures come from the same 12
workbooks and the same seeds. The README's headline silent-recall figure is 97%, but
that is the larger v6 corpus and the model arm was never re-run there — quoting 97
against 29 would compare two different question papers. This project's hot take is
about exactly that mistake, so making it on camera would be unfortunate.
