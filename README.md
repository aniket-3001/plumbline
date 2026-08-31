# Plumbline

**Audits spreadsheets and proves every finding by recomputation.**

A plumb line is the reference instrument that tells you whether a structure is actually true.
This is that, for a financial model.

> Status: **in development.** Built for the micro1 Agentic Workflows Hackathon (2026).
> See [`Docs/DESIGN.md`](Docs/DESIGN.md) for the architecture and evaluation plan.

---

## Who this is for

**Anyone who has to sign off on a spreadsheet they did not build.** An analyst
handed a model by a colleague who has left. A founder checking the numbers a
contractor produced. An ops lead who inherited the forecast three reorgs ago.

The common thread is not the job title — it is being accountable for numbers you
did not personally derive, in a file too large to check by hand.

## The bottleneck

You cannot verify four thousand formulas by eye, and nothing tells you which cells
deserve attention. Today that leaves three options: spend two days spot-checking,
buy a $2,000/year add-in that flags structural smells without understanding what the
model *means*, or sign and hope.

This is not a niche problem. Panko's synthesis of seven field audits found **94% of
operational spreadsheets contain errors**, at a 5.2% cell error rate. Auditing them
is already a paid professional service that banks commission before lending.

And the error that matters is not the one that breaks the sheet. A broken reference
announces itself. A subtotal quietly summing the wrong rows does not — it just flows
into a decision.

## What it does

```bash
plumbline audit yourmodel.xlsx
```

```
Plumbline - yourmodel.xlsx
  1,395 formula cells checked

  PROVED  Sheet1!AI74  (formula differs from the rest of its row)
          is        =+AH73
          should be =+AH74
          AI74: -50000 -> 2.3845 (+50002.3845)

  PROVED  Sheet1!AG55  (typed-in value where a formula belongs)
          is        -4000
          should be =+AF55
          set AF55 -4000 -> -3000: AG55 as-is -4000 -> -4000 (no response);
                                   as formula -> -3000 (responds)
```

Four seconds. Findings are ordered by what they cost you, and every one carries the
word **proved** — meaning we repaired the cell, recomputed the workbook, and watched
the number move. **No delta, no finding.**

The second one is the case that should worry you. Someone typed a constant over a
formula. It is *correct today*, so repairing it changes nothing and no amount of
reading spots it. We prove it by nudging the input it should depend on: a live
formula follows, this cell doesn't. It isn't a number any more, it's a monument.

## Why not just ask a model?

We measured that, because it is the obvious objection. Same workbooks, same seeds,
a direct prompt to the same model:

| | Direct prompt | Plumbline |
|---|---|---|
| Recall on **silent** errors | 0.294 | **0.824** |

Nothing in the formula text says whether a typed constant is data or a frozen
formula. Reading cannot settle it. Only changing an input and watching the cell fail
to respond can.

## Does it work

| | Simple baseline | Plumbline |
|---|---|---|
| Precision | 0.011 | **1.000** |
| F1 | 0.021 | **0.990** |
| Cells you must judge, per workbook | 247 | **17** |

21 real Enron workbooks, 53 injected errors, same cases for both arms. The baseline
finds the errors too — and buries them in 4,777 false ones. That baseline is not a
strawman; it is this tool with its contributions switched off.

**Full workings, caveats and the four-arm ablation:
[`Docs/EVALUATION.md`](Docs/EVALUATION.md).**


## Architecture

1. **Deterministic extraction** — dependency graph, pattern breaks, hardcoded constants, off-by-one
   ranges, broken references, orphans. No model involved.
2. **Semantic interpretation** — minimal subgraph plus surrounding labels, never the whole sheet.
   *What is this cell supposed to be?*
3. **Verification** — recompute to prove or disprove each claim. Unsupported claims are dropped.
4. **Triage** — confirmed / cleared / escalated. **Plumbline never edits your workbook.**

**Layer 2 is fenced, not load-bearing.** It never decides whether a cell is wrong —
recomputation has already done that before the model is called. It supplies intent
and an explanation, and every cell reference it returns is checked against the graph
before display. **Every number in this README comes from the deterministic arm**, and
none of them depend on a model or an API key.

Layers 1, 3 and 4 are measured by `scripts/run_arms.py`, which runs the detectors
alone, then with screening, then with proof, on identical cases. Layer 2's guard is
exercised against real API responses in
[`Docs/AGENT_TRAJECTORIES.md`](Docs/AGENT_TRAJECTORIES.md); whether its
*explanations* are good would need human judgement, and that has not been run.

## Improvement Changelog

Every meaningful experiment, its evidence, and the decision it drove — including the
ones that were removed. Measurements are on **21 real Enron workbooks**, unless a row
says otherwise; the full record is in [`Docs/EVALUATION.md`](Docs/EVALUATION.md).

The short version: **not one of the first three improvements touched a detector.**
All three were bugs in the measurement harness, and the detector's own code was
identical throughout. That is what the hot take at the bottom is about.

### Building the machinery

| Stage | What was tried, and why | Evidence | Decision |
|---|---|---|---|
| **Baseline** | Detectors only, reporting every anomaly as found — the reasonable basic way to do this, and what a rule-based auditor does | **F1 0.022**, precision 0.011, recall 1.000. Finds all 53 seeded errors and buries them in **4,607 false positives**, 5,057 cells handed to the analyst | **Established the starting point.** Recall was never the problem; usable precision was |
| PoC | Structural pattern-break detection, no model, to establish a floor before adding anything | Seeded fixture: 1 finding, 0 false positives across 12 formula cells. `C11: 27000 → 30000 (+3000)`, propagating `C13: 45000 → 42000 (−3000)` — both deltas exactly the omitted Rent line | **Kept.** Deterministic detection alone finds a real class of error and proves it. This is the floor any model layer must beat |
| PoC | Counterfactual recomputation via `Evaluator.set_cell_value`, the obvious API | Returned the **unchanged** value 27000 for the "repaired" cell — it sets `.value` but leaves the formula AST intact | **Removed.** Silently produces fake proofs. For a tool whose product *is* the proof, that is the worst available failure |
| PoC | Counterfactual by swapping in a new `XLFormula` and calling `build_code()` | `C11 = 0.0` while dependent `C13 = 72000.0` — internally inconsistent, both wrong. The constructor never populates range terms | **Removed.** See [`Docs/DESIGN.md`](Docs/DESIGN.md) §6b |
| PoC | Patch a copy with openpyxl, write it, re-parse | Correct deltas, correct propagation, untouched columns unchanged | **Kept.** Slower, but it is the identical code path as the original parse. Soundness outranks speed here |
| Coverage | Measure xlcalculator's function coverage on the corpus | First estimate 98.4%, from 100 workbooks. On 1,500 workbooks: **93.0%** — and `INDEX`, which the first pass claimed was absent, is the **5th most-used function, 46,587 uses** | **Sample-size rule adopted:** no coverage claim from under 1,000 workbooks. Added `INDEX`, `NORMINV`, `VALUE`, `HLOOKUP` → ~98.9% |
| Coverage | Implement `OFFSET` and `INDIRECT` to close the last gap | They build references at runtime, so no static dependency graph exists — and every Plumbline analysis rests on that graph | **Refused by design.** Listed in `UNSUPPORTED_BY_DESIGN` and named in every audit's blind-spots section, rather than analysed wrongly |
| Determinism | Static scan for volatile functions (`RAND`, `NOW`, …) | `RAND` in **2.67%** of formula cells (45,550). xlcalculator *supports* it, so it never surfaces as a coverage gap — it just makes two evaluations disagree, and a proof is a comparison of two evaluations | **Both guards kept.** A static scan misses *contamination* (a cell with no `RAND` that depends on one); an empirical two-run check can be fooled by coincidence. Volatile workbooks are refused, not audited |
| Precision | Dead-cell detector, first version: flag typed constants sitting among formulas | 40 false positives on one workbook. Real sheets have carry-forward rows mixing typed inputs with formulas (`A7=data, B7=30468, C7==+B7`) | **Reworked** |
| Precision | Screen candidates by batch in-place replacement | Cascaded: repairs fed each other and **all 41 candidates were discarded, including the seeded error** | **Removed.** A screen that can discard a true positive is worse than no screen |
| **Main contribution** | Screen by evaluating each candidate's formula in a far-right scratch column | A1 references are literal text, so a formula means the same thing anywhere on its own sheet. One extra parse for the whole workbook, no original cell touched, no cascade. **TP 2/2, FP 0** (was TP 2, FP 40) | **Kept.** See `SCRATCH_COL` in `audit.py` |
| **Ablation** | The dead-cell detector required 3 formula peers in a row, a number chosen by argument. Swept it against 2 | Benchmark says 2 wins outright: recall 0.868 → **0.981**, F1 0.929 → **0.991**, precision unchanged at 1.000. But all 29 extra findings are *pre-existing*, and pre-existing findings are excluded from scoring — so the benchmark shows the benefit and is **structurally blind to the cost**. Reading all 29 by hand: ~3 real, ~10 ordinary data flagged wrongly, ~16 unverifiable zeros | **Shipped the arm with the worse score**, and read the 29 by hand instead of accepting the number. That labelling is what identified cross-block comparison as the real signal — which the next row acts on, and which then made `2` safe after all. `--min-peers` makes the sweep repeatable |
| **v5 → v6** | Detection ran down rows only, which the report had admitted for the whole project. Line items run down rows and periods across columns, so a growth-rate or running-total column was invisible | The column pass immediately produced 235 findings the row pass missed, and on `darrell_schoolcraft__7407` went from 1 to 124 — it was flagging **column totals** as breaks, because along a run of values the total is the only cell with a different formula. Totals are in every spreadsheet ever written | **Aggregates are filtered before the majority vote.** Filtering after leaves the total counting as a deviant, so a line holding both a total and a real error has two deviants and reports nothing. Unverified findings fell row 250 → 116 and column 235 → 44, with seed detection unchanged |
| **v5 → v6** | *Then* measured, on a corpus re-seeded along both axes so the question could actually be asked | Row-only vs row+column on that corpus: recall **0.750 → 0.981**, F1 **0.857 → 0.990**, precision 1.000 in both. Twelve more real errors | **Kept.** A sample of the 114 extra unverified findings was hand-read: `Feb01!R34/S34/T34` are three parallel columns each pointing one row past their neighbours' pattern — one dragged formula, replicated |
| **Benchmark** | Seeding only ever planted errors along rows | The column pass recovered **zero** of 53 seeds — not because it was useless, but because no error was ever placed where it could see one | **A detector cannot be judged against a benchmark that never poses its question.** Seeding takes an axis, one seed per column as well as per row |
| **v4 → v5** | The hand-labelling said peer count was a *proxy*: every clear false positive was a **cross-block** comparison, candidate in one block of the row and its "peers" in another. Built `_peers_in_block` — a block is a run on one regular stride, so `C D E F` and `C _ E _ G` are each one block | With block membership enforced, `min_peers = 2` becomes safe: recall **0.868 → 0.924**, silent recall **0.767 → 0.867**, and the unverified pre-existing population goes **down**, 368 → 362. Precision is 1.000 in all four arms, so the threshold was never the precision knob it looked like | **Kept — the first change to a detector rather than the harness.** Blind spot pinned as tests: contiguity assumes corruption is one cell wide, and the seeder only ever injects one error per row, so the benchmark cannot see that limit. Both failing shapes are documented in [`Docs/MIN_PEERS_ABLATION.md`](Docs/MIN_PEERS_ABLATION.md) |
| Scale | Prove every finding | One full workbook re-parse per finding. A 10,387-formula workbook ran for minutes at 674 MB and the corpus run could not finish | **Capped**, and the cap is recorded as `proof_truncated` so a truncated audit can never be read as a clean one |

### Fixing the measurement

| Stage | What was tried, and why | Evidence | Decision |
|---|---|---|---|
| **v1 → v2** | The proof cap sliced the findings list, so bounding runtime silently deleted detections | Four workbooks scored **0 true positives** because the deleted findings included the seeded errors — ten of the twenty misses. Recall **0.630 → 0.722**; silent-error recall **0.562 → 0.719** | **Budget now caps proofs only.** Every detected cell is still reported; those past the budget carry `not attempted: proof budget exhausted` and are counted in `proof_deferred` |
| **v2 → v3** | Pre-existing findings were computed with one detector out of two, so every pre-existing *dead cell* surfaced later as a false positive | On `scott_neal__38672`, six typed constants in `=Z41+1` counter rows — real hardcoding, in the file Enron shipped — were charged to Plumbline. **11 of 13 false positives were this one bug.** Precision **0.750 → 0.975** | **Kept.** `pre_existing_findings` now runs the same detectors and the same screen the audit runs, and a test asserts the two agree cell for cell |
| v2 → v3 | *Control for the above:* correcting an exclusion list is exactly how a miss gets laundered into "not our problem" | Recall unchanged to four decimals (0.7222 → 0.7222). A test asserts that across all 54 seeds, **none** appears in any exclusion list | **Kept as a standing test**, not a one-off check |
| **v3 → v4** | Seeds could flip a row's majority | Detection is majority-vote within a row. On `john_zufferli__16801` row 34, seeding two of three `=AVERAGE(x10:x32)` cells made the corrupted pair the majority and the untouched `I34` the outlier: two false negatives and one false positive, all three the benchmark's fault | **At most one seed per row.** A benchmark must not ask a tool to find something that, by its own definition, is no longer there. Re-seeded: **precision 1.000, recall 0.868, F1 0.929**, and `john_zufferli` goes from 0 found / 1 false positive to 1 found / 0 |
| Seeding | First seeder only knew how to shorten `SUM` ranges | Found nothing on real workbooks — real Enron formulas are plain references like `=D19` | **Added `_shift_first_reference()`**, the pointing slip |
| Seeding | Seeds landing on empty cells read `0` and are trivially detectable | Would have inflated every recall figure | **Not hidden — classified.** Every seed is labelled `obvious` / `realistic` / `silent`, and recall is reported per class. A single blended figure lets a detector that only catches loud breakage look identical to one that catches silent corruption |

### The model layer

| Stage | What was tried, and why | Evidence | Decision |
|---|---|---|---|
| Layer 2 | Hallucination guard: reject any cell reference not in the context | Replaying a **real** trajectory, the guard rejected a **correct** answer. It enumerated peer addresses and refs from the cell's own two formulas, but never looked inside the peer formulas it had printed — so citing `P8`, shown in the prompt as `Q8: =+P8`, counted as a hallucination | **Fixed.** `_known_cells` now parses the rendered prompt, so the guard and the system prompt mean the same thing by "the context". A guard that punishes correct reasoning gets switched off, and then it protects nothing |
| Layer 2 | Column label = the first string found in the column | Financial models label columns with computed dates. Row 3 of `chris_germany__1938` is `=+T3+1` across the sheet, so the model was told `Column label: =+T3+1` — not a label, and not what anyone sees on screen | **Fixed.** Formula text is never passed through as a label; the prompt says `(none found)` instead. Old workbooks often carry no cached values, and "no label" is the honest answer |
| Layer 2 | Evaluate the model layer against a stub | A model layer exercised only against a stub is not evidence of anything | **Split into `dump` / `replay`.** Real prompts, real replies, real guard — see [`Docs/AGENT_TRAJECTORIES.md`](Docs/AGENT_TRAJECTORIES.md). Trajectories 01 and 02 are live `claude-opus-5` responses; `replay` re-validates them offline with no key |
| Layer 2 | First live call against the real API | The reply contained `→` and `—`. Printing either to a Windows console on a legacy code page raises `UnicodeEncodeError`, so an audit that had already produced valid deterministic findings would crash while displaying them | **Model output is folded to ASCII at the boundary.** It is untrusted text, and this was not hypothetical — it happened on call one |


## Documentation

| | |
|---|---|
| [`Docs/REPRODUCTION.md`](Docs/REPRODUCTION.md) | Clean-machine setup, exact commands, expected output, versions, runtime, cost |
| [`Docs/EVALUATION.md`](Docs/EVALUATION.md) | The full measurement record: how success was defined, every arm, every caveat |
| [`Docs/DESIGN.md`](Docs/DESIGN.md) | Architecture, why each layer exists, and what the evaluation taught (§6d) |
| [`Docs/AGENT_TRAJECTORIES.md`](Docs/AGENT_TRAJECTORIES.md) | Whole-pipeline traces and the Layer 2 agent, with its instructions |
| [`Docs/MIN_PEERS_ABLATION.md`](Docs/MIN_PEERS_ABLATION.md) | The threshold sweep, hand-labelled, and why the worse-scoring arm shipped |

## Reproduction

Full clean-machine guide: [`Docs/REPRODUCTION.md`](Docs/REPRODUCTION.md).
~3.5 GB, ~40 minutes, and **$0** — the deterministic arm calls no model API and needs no key.

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest tests/ -q          # 192 passed, ~10s, no data needed
.venv/Scripts/python.exe scripts/fetch_corpus.py      # 993 MB, resumable
.venv/Scripts/python.exe scripts/build_eval_corpus.py --scan 900 --target 40
.venv/Scripts/python.exe scripts/seed_corpus.py --seeds-per-workbook 4 --seed 42
.venv/Scripts/python.exe scripts/run_baseline.py --max-proofs 25
```

To see the product rather than the benchmark, on any `.xlsx` of your own:

```bash
.venv/Scripts/python.exe -m plumbline.cli audit yourmodel.xlsx --report audit.md
```

## Data

[Enron Spreadsheet Corpus](https://figshare.com/articles/dataset/Enron_Spreadsheets_and_Emails/1221767)
(Hermans & Murphy-Hill, ICSE 2015), DOI `10.6084/m9.figshare.1221767`, **CC BY 4.0** — 16,189 unique
real spreadsheets from a real company. Errors are seeded against Panko's taxonomy to give exact
ground truth. No private or personal data is used, and no credentials appear in this repository.

## What existed before, and what this project adds

**Existed:** [xlcalculator](https://github.com/bradbase/xlcalculator) (MIT) for formula evaluation ·
the Enron corpus (CC BY 4.0) · Panko's error taxonomy and prevalence data · Nixon & O'Hara's
evaluation of commercial audit tools · Schmitz & Jannach's prior error-finding work on this corpus.

**Added here:** the structural detector suite, the minimal-subgraph context extractor, the
recomputation-backed verification gate, the triage and escalation policy, the Panko-grounded seeding
harness, and the evaluation harness with its ablation.

## The main failure mode

**Plumbline checks whether a model is internally consistent. It cannot tell you whether
the model is right.**

Everything here rests on one assumption: that cells doing the same job should have the
same formula shape, so a cell that breaks its row's pattern is worth looking at. That
assumption holds well on real spreadsheets, and it is also the ceiling. A model where
every formula in a row is legitimately different gives Plumbline nothing to compare
against — and the audit will report *no problems proved*, which reads like a clean bill
of health and is not one. Every report states this in a "What this audit did not check"
section for exactly that reason.

The sharper version: **a model can be perfectly consistent and completely wrong.** If the
discount rate is 4% and should be 11%, every formula referencing it is uniform, no pattern
breaks, nothing to prove, silence. That error is worth more than every error Plumbline
finds, and Plumbline is structurally incapable of seeing it. Judging whether the business
logic is correct is a job for the analyst, and the tool is built to support that judgement
rather than replace it — it never edits a workbook, and every report says a qualified
reviewer must confirm each finding before any change is made.

Three narrower limits, all measured rather than estimated:

- **~7% of formula cells use a function the engine does not implement** (93.0% coverage
  measured across 1,500 workbooks; ~98.9% after the four functions added here). `OFFSET`
  and `INDIRECT` are refused *by design*, since they build references while the workbook
  runs and no static dependency graph exists.
- **Volatile workbooks are refused, not audited.** `RAND` appears in 2.67% of formula
  cells. A proof is a comparison of two evaluations, and with `RAND` in the dependency
  cone the two differ for reasons that have nothing to do with the finding.
- **The recall figure is against seeded errors, not all errors.** 306 findings in the
  corpus were already in Enron's files and are excluded from scoring, because no ground
  truth exists for them. See *How to read these numbers* above.


## Hot take

**Most agent evaluations are measuring their own harness, and the number moves when you
fix the harness, so it looks like progress.**

This project's F1 went from 0.680 to 0.830 across three improvements. The detectors' code
was byte-identical throughout. Every point came from fixing the benchmark:

- a runtime cap that sliced the findings list instead of the proof queue, so bounding cost
  silently deleted detections — 10 of 20 misses, four workbooks scoring zero
- an answer key built by different code than the answer, so pre-existing dead cells in
  Enron's own files were charged as false positives — 11 of 13 of them
- a seeder that could put two errors in a three-formula row, making the *correct* cell the
  outlier — the benchmark scoring the tool for not finding something it had deleted

None of that was visible in the summary. `recall 0.630` is a perfectly plausible number
for a hard problem. It was visible in about fifteen minutes of dumping every individual
miss with its row context and reading them.

The uncomfortable part is the shape they share. Each bug was a **second implementation of
something that already existed once** — the cap re-derived "the findings", the exclusion
list re-derived "what the detectors find", the seeder re-derived "what a row's majority
is". Every eval harness is full of these, because a harness is by definition a
reimplementation of the system's own semantics for scoring purposes. They drift silently,
and the drift is always charged to the model.

So the claim: when an agent benchmark reports a number, the prior should be that some of
it is harness. **A benchmark result is not evidence until someone has read the individual
failures.** Not sampled them — read them. If a project cannot show you what its misses
actually looked like, it does not yet know what it measured.

The defence is not vigilance. It is collapsing the second implementation into the first —
here, one `pre_existing_findings` that calls the audit's own detectors at the audit's own
settings, with a test asserting the two agree cell for cell — and where the copy cannot be
removed, a test that asserts the two agree. Three such tests exist now, and each one was
written *after* the bug it would have caught.


## AI Disclosure

This project was developed with assistance from **Claude Code** (Anthropic) as an AI pair-programming assistant for implementation, test authoring, and documentation drafting. All system architecture, mathematical verification contracts, error taxonomy mapping, benchmark design, and final code reviews were directed and verified by the author.


## Licence

MIT — see [`LICENSE`](LICENSE).
