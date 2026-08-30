# Plumbline

**Audits spreadsheets and proves every finding by recomputation.**

A plumb line is the reference instrument that tells you whether a structure is actually true.
This is that, for a financial model.

> Status: **in development.** Built for the micro1 Agentic Workflows Hackathon (2026).
> See [`Docs/DESIGN.md`](Docs/DESIGN.md) for the architecture and evaluation plan.

---

## Who this is for

**A financial analyst who inherited a model they did not build** — the colleague who wrote it has
left — **and who must sign off on numbers going into a board pack or a lender submission.**

## The bottleneck

They cannot verify four thousand formulas by hand, and they have no way to know which cells deserve
attention. Today they have three options: spend two days spot-checking, buy a $2,000/year Windows
add-in that flags structural smells without understanding what the model *means*, or sign and hope.

This is not a rare problem. Panko's synthesis of seven field audits of operational spreadsheets found
**94% contained errors**, with a 5.2% cell error rate. Model audit is already a paid professional
service that banks commission to reassure lenders.

## Why solving it is valuable

The error that matters is not the one that makes the sheet break — it is the one that makes the sheet
quietly wrong. A broken reference announces itself. A subtotal that sums the wrong rows does not, and
it flows into a decision.

## What Plumbline does differently

Two kinds of tool exist already, and each fails in a documented way:

| Approach | Strength | Documented failure |
|---|---|---|
| Rule-based auditors (OAK, PerfectXL, Spreadsheet Detective) | Exact structural checks | ["Failed where label-pattern recognition was required"](https://arxiv.org/pdf/1001.4293) — they see that a formula breaks a pattern, not that a cell labelled *Total Q3* is summing Q2 |
| LLM assistants | Read labels, infer intent | Cannot compute; hallucinate cell references. Practitioners call them *"assistive, not autonomous"* |

Plumbline is the bridge. A deterministic engine computes and constrains; a model interprets labels and
intent; and **nothing reaches the user unless it is tied to a specific cell and a recomputation that
demonstrates it.** A claim that cannot be proved is escalated to a human, never shown as a finding.

## Architecture

1. **Deterministic extraction** — dependency graph, pattern breaks, hardcoded constants, off-by-one
   ranges, broken references, orphans. No model involved.
2. **Semantic interpretation** — minimal subgraph plus surrounding labels, never the whole sheet.
   *What is this cell supposed to be?*
3. **Verification** — recompute to prove or disprove each claim. Unsupported claims are dropped.
4. **Triage** — confirmed / cleared / escalated. **Plumbline never edits your workbook.**

**What is measured, and what is not.** Layers 1, 3 and 4 are measured: `scripts/run_arms.py`
runs the detectors alone, then with screening, then with proof, on identical cases — see
*Baseline vs solution* below.

**Layer 2 is fenced, not load-bearing.** It never decides whether a cell is
wrong; recomputation has already done that before the model is called. It supplies intent —
*what was this cell for?* — and an explanation, and every cell reference it returns is checked
against the graph before display. So every headline number in this README comes from
the deterministic arm and none of them depend on a model.

What *is* measured about models is the harder question: whether one is needed for detection at
all. It is not — see *Does the structural machinery earn its place?* below, where a direct prompt
to the same model finds 29% of silent errors against recomputation's 82%. Layer 2's guard is
exercised on real API responses ([`Docs/AGENT_TRAJECTORIES.md`](Docs/AGENT_TRAJECTORIES.md))
rather than only unit-tested. Whether its *explanations* are good would need human judgement, and
that has not been run.

## Improvement Changelog

Every meaningful experiment, its evidence, and the decision it drove — including the ones that were
removed. Measurements are on **21 real Enron workbooks with 54 seeded errors**, unless a row says
otherwise.

### Baseline vs solution

The brief's mandatory comparison. Four arms, **identical cases, identical scorer** —
each one adds exactly one of this project's contributions. `python scripts/run_arms.py`

| Metric | naive (baseline) | + block | + screen | + proof (shipped) |
|---|---|---|---|---|
| **Precision** | 0.011 | 0.315 | **1.000** | **1.000** |
| **Recall** | 1.000 | 0.943 | 0.924 | 0.924 |
| **F1** | 0.022 | 0.472 | **0.961** | **0.961** |
| True positives | 53 | 50 | 49 | 49 |
| False positives | **4,607** | 109 | **0** | **0** |
| Cells reported to the analyst | 5,057 | 521 | 411 | 411 |
| Findings carrying a proof | 0 | 0 | 0 | **35** |

**The baseline is not a strawman** — it is this tool with every contribution removed,
on the same corpus, seeds and scorer. It also describes what a rule-based auditor
does: flag structural anomalies and hand over the list. It finds **all 53** seeded
errors. It buries them in 4,607 false ones, which is the documented failure of the
commercial tools and the reason an analyst cannot use them.

Each arm computes **its own exclusion list** at its own settings, so a more sensitive
arm is never charged for the extra pre-existing anomalies it correctly finds.

Three things worth reading carefully, because none is the shape a comparison table
usually has:

- **Recall falls monotonically, and that is the trade being made.** 1.000 → 0.924.
  Each gate costs a true positive or two and removes hundreds to thousands of false
  ones. The baseline's perfect recall is worthless at precision 0.011.
- **The screen does most of the work**, 0.472 → 0.961, by asking one question of each
  candidate: does this typed constant equal what the row's formula would produce?
- **Proof does not improve F1, and is not meant to.** Precision, recall and F1 are
  identical with and without it. What changes is that 35 findings arrive carrying a
  recomputation the analyst can rerun instead of an assertion they must trust. F1
  cannot express that, which is why proof rate is its own row.

Two mistakes in building this table are worth recording, since both would have
flattered the result:

- I first scored the proof arm **strictly**, an unproved finding not counting at all,
  and got F1 0.753 — proof appearing to *hurt*. That measured the proof budget, not
  the gate: those findings were never disproved, only never reached. It also is not
  what the product does, which demotes them to a *Suspected* section.
- The `naive` arm originally called the detector at its defaults, so when block
  membership landed the **baseline silently inherited it** and its false positives
  fell from 4,607 to 109. A baseline that improves as the tool improves makes the
  comparison meaningless. `naive` is now pinned to the pre-contiguity detector.

### Headline

| | v1 | v2 | v3 | v4 | **v5** |
|---|---|---|---|---|---|
| **Precision** | 0.739 | 0.750 | 0.975 | 1.000 | **1.000** |
| **Recall** | 0.630 | 0.722 | 0.722 | 0.868 | **0.924** |
| **F1** | 0.680 | 0.736 | 0.830 | 0.929 | **0.961** |
| Recall, *obvious* | 0.500 | 0.500 | 0.500 | 1.000 | **1.000** |
| Recall, *realistic* | 0.750 | 0.750 | 0.750 | 1.000 | **1.000** |
| Recall, *silent* | 0.562 | 0.719 | 0.719 | 0.767 | **0.867** |
| TP / FP / FN | 34/12/20 | 39/13/15 | 39/1/15 | 46/0/7 | **49/0/4** |

21 real Enron workbooks. v1–v3 share one corpus of 54 seeded errors with a single fix
isolated per step, so every movement is attributable. v4 re-seeds (53 errors) because its
fix is *in* the seeder, so it is a new benchmark rather than the next rung of that ladder;
v5 is the first change to a **detector** rather than to the harness, and shares v4's corpus.

Raw results: [`v1`](results/baseline_v1_truncating.json) ·
[`v2`](results/baseline_v2_budget_fixed.json) ·
[`v3`](results/baseline_v3_accounting_fixed.json) ·
[`v4`](results/baseline_v4_seeding_fixed.json) ·
[`v5`](results/baseline_v5_contiguity.json)

**Not one of the v1→v3 fixes touched a detector.** All three were in the measurement
harness. The detector scored 0.630 recall in v1 and 0.722 in v3 while its code stayed
identical; the difference is that the benchmark stopped charging the tool for its own bugs.
That is the most useful thing this project learned, and it was only visible because the
misses were read cell by cell rather than summarised.

### Does the structural machinery earn its place?

The deterministic numbers cannot answer that. This can: the brief's other named
baseline shape, **one direct prompt with basic instructions**, given the same
workbooks and scored the same way. `python scripts/run_llm_baseline.py`

| Metric | deterministic | direct-prompt LLM |
|---|---|---|
| Precision | 1.000 | 1.000 |
| Recall | **0.889** | 0.519 |
| F1 | **0.941** | 0.683 |
| Recall, *realistic* | 1.000 | 0.900 |
| **Recall, *silent*** | **0.824** | **0.294** |

Both arms are perfectly precise. The model simply misses more — and it misses
*exactly* where this project claims to matter. **Silent** errors are correct today
and wrong once an input moves; a direct prompt finds 29% of them, recomputation
finds 82%. That is not a prompting failure. Nothing in the formula text says whether
a typed constant is data or a frozen formula, so no amount of reading can settle it.
Only changing an input and watching the cell fail to respond can.

**This run is partial and the table above says so honestly.** It covers **12 of 21
workbooks**, stopping when the API account ran out of credit ~$4.85 in, so the
deterministic column is recomputed on those same 12 rather than quoted from the
full-corpus run. Comparing it against the headline 0.924 would be comparing
different corpora. Raw per-workbook data, marked `"complete": false`, is in
[`results/llm_baseline.json`](results/llm_baseline.json).

Not a strawman: same model (`claude-opus-5`), same effort, formulas in reading order
with row labels — what a human auditor would have. And it gets **its own exclusion
list**, computed by running it over the untouched originals too; without that, the 79
pre-existing Enron oddities it correctly spotted would have been charged against it
as false positives, which is the identical bug that cost the deterministic arm 11.

### How to read these numbers

**Precision and recall are measured against the seeded errors only.** The audit also
returns 362 findings that were already in the original Enron files. Those are excluded
from scoring — not counted as hits, not counted against precision — because nobody knows
the ground truth for a 25-year-old workbook, and guessing it would be inventing the
answer key.

So `precision 1.000` means something narrower than it looks: **every finding was either
an error we planted or a cell that was already anomalous before we touched the file.**
The detector produced nothing that was neither. It does **not** mean the 362 are all real
defects. Some clearly are — on `scott_neal__38672`, six typed constants sit inside
`=Z41+1` counter rows, which is textbook hardcoding in the file Enron shipped — but that
is a spot check, not a measurement, and it is not claimed as one.

That exclusion rule is also the one place this benchmark could flatter itself, by quietly
reclassifying a miss as "not our problem". Three things stop it, and all three are
enforced rather than argued:

- Exclusions are computed on the **unseeded original**, so a seeded error cannot appear
  in one. A test checks this across all 53 seeds on every run.
- Exclusions are computed with the **same detectors at the same settings** as the audit.
  A mismatch in either direction is a scoring bug, and both directions have happened here
  — see the v2 → v3 row, and `--min-peers` below.
- Recall did not move when the exclusion list was corrected (0.7222 → 0.7222), which is
  the control that fix needed.

**Proof rate (0.696) is lower than recall on purpose.** Proving a finding costs one full
workbook re-parse, so a per-workbook budget applies; findings past it are still reported,
marked `not attempted: proof budget exhausted`, and counted as unproved. Four workbooks
hit the budget. A higher proof rate is available by raising `--max-proofs`, and it would
mean less than it appears to.


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
| [`Docs/DESIGN.md`](Docs/DESIGN.md) | Architecture, why each layer exists, and what the evaluation taught (§6d) |
| [`Docs/AGENT_TRAJECTORIES.md`](Docs/AGENT_TRAJECTORIES.md) | Whole-pipeline traces and the Layer 2 agent, with its instructions |
| [`Docs/MIN_PEERS_ABLATION.md`](Docs/MIN_PEERS_ABLATION.md) | The threshold sweep, hand-labelled, and why the worse-scoring arm shipped |
| [`Docs/VIDEO_SCRIPT.md`](Docs/VIDEO_SCRIPT.md) | Script and shot list for the solution video |

## Reproduction

Full clean-machine guide: [`Docs/REPRODUCTION.md`](Docs/REPRODUCTION.md).
~3.5 GB, ~40 minutes, and **$0** — the deterministic arm calls no model API and needs no key.

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest tests/ -q          # 186 passed, ~10s, no data needed
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
- **The recall figure is against seeded errors, not all errors.** 362 findings in the
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


## Licence

MIT — see [`LICENSE`](LICENSE).
