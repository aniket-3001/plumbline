# Solution video — 3-minute script

**Deliverable 03.** Demo-led pitch. Every command is real, every number is from a
committed file in `results/`, and the whole live portion runs in about 8 seconds.

**Why 3 minutes and not the permitted 5.** Judges have a stack of these. A tight
demo that respects their time is itself an argument about the product. But the brief
requires six specific beats, so none is dropped — the methodology ones are delivered
as voiceover over a scrolling README rather than as their own scenes.

| Brief requires | Where it lands |
|---|---|
| The problem and the simple baseline | 0:00–0:20 |
| One realistic execution, start to finish | 0:20–1:35 |
| The final comparison | 1:55–2:20 |
| Walk through the changelog | 2:20–2:45 |
| The change that contributed most | 2:20–2:45 |
| One experiment you removed | 2:20–2:45 |

**Word budget: ~450 words at ~150 wpm.** The counts below are real — ad-lib past
them and you will run over. Read it once against a timer before recording.

---

## Before you record

```bash
PY -m pytest tests/ -q          # 189 passed
PY scripts/smoke.py             # all 18 documented commands work
```

If smoke is green, every command and every number in this script is current.

- Terminal font **≥ 16pt**, window wide enough that the audit line doesn't wrap.
- `openpyxl` prints `WARNING:root:Defined name…` on these 25-year-old files. The
  commands below already pipe it away with `2>/dev/null`.
- README open in a second window, scrolled to the results tables.

---

## 0:00 – 0:20 · The problem *(52 words)*

*On screen: a real Enron spreadsheet open in Excel, scrolling.*

> You've inherited a financial model. The person who built it has left. You have to
> sign off on the numbers going into a board pack.
>
> Ninety-four percent of real spreadsheets contain errors. You cannot check four
> thousand formulas by hand — so today you spot-check, and hope.

---

## 0:20 – 1:35 · The product, running *(165 words)*

```bash
plumbline audit "data/seeded/chris_germany__1938__Mar2002_EstateGas.xlsx" 2>/dev/null
```

*Let it run. ~4.5 seconds. Don't fill the silence — the speed is the point.*

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

> Four seconds, fourteen hundred formulas. And notice the word **proved**.
>
> *(point at AI74)* This row carries values across — every cell reads the one to its
> left. This one reads one row **up**. A dragged formula. We don't just flag it: we
> repair it, recompute the entire workbook, and show you the number moves. **Fifty
> thousand.** That's why it's at the top — the list is ordered by what it costs you.
>
> *(point at AG55)* This one's harder, and it's the one that should worry you.
> Someone typed minus four thousand over a formula. It is **correct today**. Nothing
> looks wrong. Repairing it changes nothing.
>
> So we prove it a different way — nudge the input it should depend on. A live
> formula follows. This one sits there. It isn't a number any more, it's a monument.
> The day someone updates that input, the model goes silently wrong and nobody knows.

---

## 1:35 – 1:55 · Why you can trust it *(58 words)*

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
>
> Every report ends with what we did **not** check. We never edit your workbook.

---

## 1:55 – 2:20 · Does it actually work *(63 words)*

*On screen: README, the two results tables.*

> Twenty-one real Enron workbooks, fifty-three planted errors. Against the same
> detector with our contributions switched off: **F1 from zero-point-zero-two to
> zero-point-nine-nine.** That baseline finds the errors too — and buries them in
> four thousand false ones.
>
> We also asked a language model directly. On the silent errors — the invisible ones
> — a direct prompt found **29 percent**. We found **82**.

---

## 2:20 – 2:45 · What we learned *(70 words)*

*On screen: scroll the Improvement Changelog.*

> The biggest single improvement wasn't a detector. It was discovering that our own
> **benchmark** was lying to us. A runtime cap was silently deleting detections —
> four workbooks scored zero for reasons that had nothing to do with detection.
>
> And one we deleted: our first repair used the obvious library call. It returned
> the unchanged value — **fake proofs**, silently. For a tool whose product is
> proof, that's the worst possible bug. Gone.

---

## 2:45 – 3:00 · Close *(45 words)*

```bash
plumbline audit yourmodel.xlsx --report audit.md
```

> Point it at your own model. It's deterministic, needs no API key, and costs
> nothing to run. Every finding arrives with a recomputation you can rerun yourself.
>
> Nothing reaches you that we couldn't prove.

---

## Shot list

| # | Shot | Duration |
|---|---|---|
| 1 | Enron sheet in Excel, scrolling | 20s |
| 2 | **Live:** `plumbline audit …EstateGas.xlsx` | 75s |
| 3 | **Live:** `plumbline audit forecast.xlsx` → refusal | 20s |
| 4 | README results tables | 25s |
| 5 | README Improvement Changelog, scrolling | 25s |
| 6 | **Live:** `--report audit.md`, tab to the file | 15s |

Shots 2, 3 and 6 are the same terminal window — you need two windows total.

### Making the refusal fixture

`forecast.xlsx` is one snippet to create, and being a plain forecast sheet with a
`RAND` in it makes the refusal legible on camera:

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

Cut in this order — each is the least load-bearing thing remaining:

1. §1:35 refusal (−20s). Costs the trust beat, which the report's blind-spots
   section covers anyway.
2. The middle finding in shot 2 — show only `AI74` and `AG55` (−15s).
3. Shot 1 → a static screenshot instead of scrolling (−8s).

Do **not** cut §2:20. It carries three of the six required beats.

### One number to be careful with

The **29% vs 82%** comparison is like-for-like: both come from the same 12 workbooks
and the same seeds. The README's headline silent-recall figure is 97%, but that is
the larger v6 corpus, and the model arm was never re-run there — quoting 97 against
29 would be comparing two different question papers. This project's own hot take is
about exactly that mistake, so making it on camera would be unfortunate.
