# Solution video — script and shot list

**Deliverable 03. Max 5 minutes.** This is the script; the recording is yours to make.

Every command below is real and has been run. Every number is from a committed file
in `results/`. Nothing here needs staging, and if a take goes wrong the commands can
simply be re-run.

**Before recording:** `PY -m pytest tests/ -q` → `153 passed`, and check
`data/seeded/` is populated. Total runtime of everything shown live is ~30 seconds;
the baseline numbers are read from committed JSON rather than re-run, which is
stated on screen.

---

## 0:00 – 0:35 · The problem, and the baseline

> An analyst inherits a financial model they did not build. The person who wrote it
> has left. They have to sign off on numbers going into a board pack.
>
> They cannot check four thousand formulas by hand. Panko's synthesis of seven field
> audits found ninety-four percent of operational spreadsheets contain errors.
>
> The error that matters isn't the one that breaks the sheet. A broken reference
> announces itself. A subtotal that sums the wrong rows does not — and it flows into
> a decision.
>
> Two kinds of tool exist. Rule-based auditors see that a formula breaks a pattern
> but not what the sheet *means*. LLM assistants read labels and infer intent, but
> they can't compute, and they hallucinate cell references.
>
> **The baseline for this project is the first of those: structural detection with no
> model in the loop.** Everything is measured against it.

*On screen: the README's "Who this is for" section.*

---

## 0:35 – 1:35 · One realistic execution, start to finish

Real Enron workbook, seeded with a known error.

```bash
plumbline audit data/seeded/chris_germany__1938__Mar2002_EstateGas.xlsx
```

*Let it run. ~2 seconds, 1,396 formula cells.*

```
PROVED  Sheet1!U8  (formula differs from the rest of its row)
        is        =+T7
        should be =+T8
        U8: 10000 -> 2.1562 (-9997.8438)

PROVED  Sheet1!AH25  (typed-in value where a formula belongs)
        is        5000
        should be =+AG25
        set AG25 5000 -> 6000: AH25 as-is 5000 -> 5000 (no response);
                               as formula -> 6000 (responds)
```

> Two findings, and the difference between them is the whole idea.
>
> `U8` is in a carry-forward chain — every cell reads the one to its left. `U8`
> reads one row *up*. A dragged formula. We prove it by repairing the cell,
> recomputing the workbook, and showing you the number moves: ten thousand becomes
> two point one six.
>
> `AH25` is harder. Someone typed five thousand over a formula. **It is correct
> today** — five thousand is exactly what the formula would give. Repairing it
> changes nothing, so there's no delta to show.
>
> So we prove it differently. Nudge the input it should depend on: `AG25` goes to
> six thousand. A live formula would follow. `AH25` sits there. It's not a number
> any more, it's a monument — and the day someone updates that input, the model is
> silently wrong.
>
> **No delta, no finding.** Nothing reaches the analyst that isn't tied to a cell
> and a recomputation they can rerun.

*Optional, 10s: `--report audit.md`, scroll to the "What this audit did not check"
section.* → Every report states its blind spots and says a qualified reviewer must
confirm each finding. Plumbline never edits your workbook.

---

## 1:35 – 2:15 · The final comparison

*On screen: the README headline table.*

| | v1 | v2 | v3 | v4 | **v5** |
|---|---|---|---|---|---|
| Precision | 0.739 | 0.750 | 0.975 | 1.000 | **1.000** |
| Recall | 0.630 | 0.722 | 0.722 | 0.868 | **0.924** |
| F1 | 0.680 | 0.736 | 0.830 | 0.929 | **0.961** |
| Recall, *silent* | 0.562 | 0.719 | 0.719 | 0.767 | **0.867** |

> Twenty-one real Enron workbooks, fifty-three seeded errors from Panko's taxonomy.
> F1 from 0.68 to 0.96.
>
> Recall is split by difficulty on purpose. **Silent** errors are the ones that are
> correct today and diverge once an input moves — the class a human auditor cannot
> catch by reading numbers, because there is nothing to see.
>
> And one caveat that belongs on screen next to the number: precision of 1.000 means
> every finding was either an error we planted or a cell that was *already* anomalous
> in Enron's file. Three hundred and sixty-two of those are excluded from scoring,
> because nobody knows the ground truth for a twenty-five-year-old workbook and
> guessing it would be inventing the answer key.

---

## 2:15 – 3:15 · The changelog, and the change that mattered most

*On screen: the README Improvement Changelog.*

> **The change that contributed most was a bug in the benchmark, not the detector.**
>
> Proving a finding re-parses the workbook, so a big sheet could run for minutes. I
> capped it. The cap sliced the findings list — which meant a limit on *runtime*
> silently deleted *detections*.
>
> Four workbooks scored zero true positives. Not because the detector missed
> anything: because the findings it made were thrown away before scoring. Ten of the
> twenty misses. Fixing it took recall from 0.630 to 0.722, and on silent errors from
> 0.562 to 0.719.
>
> The budget now caps proofs only. Everything detected is still reported; what runs
> past the budget says "not attempted: proof budget exhausted".
>
> The second one is the same shape. Enron's files are full of pre-existing anomalies,
> so they're excluded from scoring — but the exclusion list was built by *different
> code* than the audit, running one detector out of two. So every pre-existing dead
> cell got charged to us as a false positive. Eleven of thirteen. Precision 0.750 to
> 0.975.
>
> Neither of those touched a detector. **For most of this project, the thing being
> measured was the measurement.**

---

## 3:15 – 4:00 · An experiment I removed

> Two, and they're worth a minute because both were wrong in a way that doesn't
> look wrong.
>
> **First: how to recompute a repaired cell.** xlcalculator has
> `Evaluator.set_cell_value`, the obvious API. It returned the *unchanged* value —
> it sets `.value` but leaves the formula tree alone. So the tool would have
> reported "repairing this changes nothing" for cells where repairing changes
> everything. Fake proofs, silently. For a tool whose product *is* the proof,
> that's the worst available failure. Removed. We write a patched copy and re-parse
> — slower, identical code path.
>
> **Second: how to screen dead cells.** The detector was drowning in false
> positives, so I screened candidates by replacing them all in place and
> recomputing. It cascaded — the repairs fed each other, and it discarded all
> forty-one candidates including the seeded error I was trying to find. A screen
> that can throw away a true positive is worse than no screen. Removed.
>
> What replaced it: evaluate each candidate's formula in a scratch column far to
> the right. A1 references are literal text, so a formula means the same thing
> anywhere on its own sheet. One extra parse, no original cell touched, nothing
> cascades. Forty false positives to zero.

---

## 4:00 – 4:50 · The hot take

> **Most agent evaluations are measuring their own harness, and the number moves
> when you fix the harness, so it looks like progress.**
>
> Three bugs cost me 0.15 of F1, and they shared one shape: each was a **second
> implementation of something that already existed once.** The cap re-derived "the
> findings". The exclusion list re-derived "what the detectors find". The seeder
> re-derived "what a row's majority is" — and could put two errors in a
> three-formula row, making the *correct* cell the outlier, so the benchmark scored
> me for not finding something it had deleted.
>
> That's what an eval harness structurally *is*: a reimplementation of the system's
> own semantics, for scoring. They drift. The drift gets charged to the model.
>
> None of it was visible in the summary. `recall 0.630` is a perfectly plausible
> number for a hard problem. All three were visible in fifteen minutes of dumping
> every individual miss with its row context and reading them.
>
> **A benchmark result is not evidence until someone has read the individual
> failures.** Not sampled them. Read them.
>
> One last thing, and it's the reason I believe that. I swept a detector threshold.
> The benchmark said lowering it was free — recall 0.868 to 0.981, precision
> unchanged. So I read the twenty-nine extra findings by hand. About ten were
> ordinary data columns, flagged wrong. Precision held at 1.000 only because those
> land in the excluded bucket the score can't see.
>
> **I shipped the threshold with the worse benchmark score**, and wrote down why.

---

## 4:50 – 5:00 · Close

```bash
plumbline audit yourmodel.xlsx --report audit.md
```

> Deterministic. No API key. Zero cost. Reproducible from a clean machine in about
> forty minutes, and every number in this video comes from a JSON file in the repo.

---

## Shot list

| # | Shot | Source |
|---|---|---|
| 1 | README "Who this is for" | `README.md` |
| 2 | Live: `plumbline audit …EstateGas.xlsx` | terminal, ~2s |
| 3 | Optional: `audit.md`, blind-spots section | `--report` |
| 4 | Headline results table | `README.md` |
| 5 | Improvement Changelog, "Fixing the measurement" | `README.md` |
| 6 | Changelog rows for the two removed experiments | `README.md` |
| 7 | Hot take | `README.md` |
| 8 | Ablation table | `Docs/MIN_PEERS_ABLATION.md` |

**Watch for:** terminal font ≥ 16pt; `WARNING:root:Defined name…` lines from openpyxl
reading 25-year-old files are harmless noise — either scroll past or pipe through
`grep -v WARNING`.
