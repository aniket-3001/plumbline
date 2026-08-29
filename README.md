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

Layers 1 and 2 also run standalone as evaluation baselines, so each layer's contribution is measured
on identical cases.

## Improvement Changelog

Every meaningful experiment, its evidence, and the decision it drove — including the ones that were
removed. Measurements are on **21 real Enron workbooks with 54 seeded errors**, unless a row says
otherwise.

### Headline

|  | v1 | v2 | v3 |
|---|---|---|---|
| **Precision** | 0.739 | 0.750 | **0.975** |
| **Recall** | 0.630 | 0.722 | **0.722** |
| **F1** | 0.680 | 0.736 | **0.830** |
| Recall, *silent* errors | 0.562 | 0.719 | **0.719** |
| TP / FP / FN | 34 / 12 / 20 | 39 / 13 / 15 | 39 / 1 / 15 |

Same workbooks, same 54 errors, one fix isolated per step, so every movement is attributable.
Raw results: [`v1`](results/baseline_v1_truncating.json),
[`v2`](results/baseline_v2_budget_fixed.json), [`v3`](results/baseline_v3_accounting_fixed.json).

**Not one of those three fixes touched a detector.** All three were in the measurement harness. The
detector scored 0.630 recall in v1 and 0.722 in v3 while its code stayed the same; the difference is
that the benchmark stopped charging the tool for its own bugs. That is the most useful thing this
project learned, and it was only visible because the misses were read cell by cell rather than
summarised.

### Building the machinery

| Stage | What was tried, and why | Evidence | Decision |
|---|---|---|---|
| PoC | Structural pattern-break detection, no model, to establish a floor before adding anything | Seeded fixture: 1 finding, 0 false positives across 12 formula cells. `C11: 27000 → 30000 (+3000)`, propagating `C13: 45000 → 42000 (−3000)` — both deltas exactly the omitted Rent line | **Kept.** Deterministic detection alone finds a real class of error and proves it. This is the floor any model layer must beat |
| PoC | Counterfactual recomputation via `Evaluator.set_cell_value`, the obvious API | Returned the **unchanged** value 27000 for the "repaired" cell — it sets `.value` but leaves the formula AST intact | **Removed.** Silently produces fake proofs. For a tool whose product *is* the proof, that is the worst available failure |
| PoC | Counterfactual by swapping in a new `XLFormula` and calling `build_code()` | `C11 = 0.0` while dependent `C13 = 72000.0` — internally inconsistent, both wrong. The constructor never populates range terms | **Removed.** See [`Docs/DESIGN.md`](Docs/DESIGN.md) §6b |
| PoC | Patch a copy with openpyxl, write it, re-parse | Correct deltas, correct propagation, untouched columns unchanged | **Kept.** Slower, but it is the identical code path as the original parse. Soundness outranks speed here |
| Coverage | Measure xlcalculator's function coverage on the corpus | First estimate 98.4%, from 100 workbooks. On 1,500 workbooks: **93.0%** — and `INDEX`, which the first pass claimed was absent, is the **5th most-used function, 46,587 uses** | **Sample-size rule adopted:** no coverage claim from under 1,000 workbooks. Added `INDEX`, `NORMINV`, `VALUE`, `HLOOKUP` → ~98.9% |
| Coverage | Implement `OFFSET` and `INDIRECT` to close the last gap | They build references at runtime, so no static dependency graph exists — and every Plumbline analysis rests on that graph | **Refused by design.** Listed in `UNSUPPORTED_BY_DESIGN` and named in every audit's blind-spots section, rather than analysed wrongly |
| Determinism | Static scan for volatile functions (`RAND`, `NOW`, …) | `RAND` in **2.67%** of formula cells (45,550). xlcalculator *supports* it, so it never surfaces as a coverage gap — it just makes two evaluations disagree, and a proof is a comparison of two evaluations | **Both guards kept.** A static scan misses *contamination* (a cell with no `RAND` that depends on one); an empirical two-run check can be fooled by coincidence. Volatile workbooks are refused, not audited |
| Precision | Dead-cell detector, first version: flag typed constants sitting among formulas | 40 false positives on one workbook. Real sheets have carry-forward rows mixing typed inputs with formulas (`A7=data, B7=30468, C7==+B7`) | **Reworked** |
| Precision | Screen candidates by batch in-place replacement | Cascaded: repairs fed each other and **all 41 candidates were discarded, including the seeded error** | **Removed.** A screen that can discard a true positive is worse than no screen |
| Precision | Screen by evaluating each candidate's formula in a far-right scratch column | A1 references are literal text, so a formula means the same thing anywhere on its own sheet. One extra parse for the whole workbook, no original cell touched, no cascade. **TP 2/2, FP 0** (was TP 2, FP 40) | **Kept.** See `SCRATCH_COL` in `audit.py` |
| Scale | Prove every finding | One full workbook re-parse per finding. A 10,387-formula workbook ran for minutes at 674 MB and the corpus run could not finish | **Capped**, and the cap is recorded as `proof_truncated` so a truncated audit can never be read as a clean one |

### Fixing the measurement

| Stage | What was tried, and why | Evidence | Decision |
|---|---|---|---|
| **v1 → v2** | The proof cap sliced the findings list, so bounding runtime silently deleted detections | Four workbooks scored **0 true positives** because the deleted findings included the seeded errors — ten of the twenty misses. Recall **0.630 → 0.722**; silent-error recall **0.562 → 0.719** | **Budget now caps proofs only.** Every detected cell is still reported; those past the budget carry `not attempted: proof budget exhausted` and are counted in `proof_deferred` |
| **v2 → v3** | Pre-existing findings were computed with one detector out of two, so every pre-existing *dead cell* surfaced later as a false positive | On `scott_neal__38672`, six typed constants in `=Z41+1` counter rows — real hardcoding, in the file Enron shipped — were charged to Plumbline. **11 of 13 false positives were this one bug.** Precision **0.750 → 0.975** | **Kept.** `pre_existing_findings` now runs the same detectors and the same screen the audit runs, and a test asserts the two agree cell for cell |
| v2 → v3 | *Control for the above:* correcting an exclusion list is exactly how a miss gets laundered into "not our problem" | Recall unchanged to four decimals (0.7222 → 0.7222). A test asserts that across all 54 seeds, **none** appears in any exclusion list | **Kept as a standing test**, not a one-off check |
| Seeding | Seeds could flip a row's majority | Detection is majority-vote within a row. On `john_zufferli__16801` row 34, seeding two of three `=AVERAGE(x10:x32)` cells made the corrupted pair the majority and the untouched `I34` the outlier: two false negatives and one false positive, all three the benchmark's fault | **At most one seed per row.** A benchmark must not ask a tool to find something that, by its own definition, is no longer there |
| Seeding | First seeder only knew how to shorten `SUM` ranges | Found nothing on real workbooks — real Enron formulas are plain references like `=D19` | **Added `_shift_first_reference()`**, the pointing slip |
| Seeding | Seeds landing on empty cells read `0` and are trivially detectable | Would have inflated every recall figure | **Not hidden — classified.** Every seed is labelled `obvious` / `realistic` / `silent`, and recall is reported per class. A single blended figure lets a detector that only catches loud breakage look identical to one that catches silent corruption |

### The model layer

| Stage | What was tried, and why | Evidence | Decision |
|---|---|---|---|
| Layer 2 | Hallucination guard: reject any cell reference not in the context | Replaying a **real** trajectory, the guard rejected a **correct** answer. It enumerated peer addresses and refs from the cell's own two formulas, but never looked inside the peer formulas it had printed — so citing `P8`, shown in the prompt as `Q8: =+P8`, counted as a hallucination | **Fixed.** `_known_cells` now parses the rendered prompt, so the guard and the system prompt mean the same thing by "the context". A guard that punishes correct reasoning gets switched off, and then it protects nothing |
| Layer 2 | Column label = the first string found in the column | Financial models label columns with computed dates. Row 3 of `chris_germany__1938` is `=+T3+1` across the sheet, so the model was told `Column label: =+T3+1` — not a label, and not what anyone sees on screen | **Fixed.** Formula text is never passed through as a label; the prompt says `(none found)` instead. Old workbooks often carry no cached values, and "no label" is the honest answer |
| Layer 2 | Evaluate the model layer against a stub | A model layer exercised only against a stub is not evidence of anything | **Split into `dump` / `replay`.** Real prompts, real replies, real guard — see [`Docs/AGENT_TRAJECTORIES.md`](Docs/AGENT_TRAJECTORIES.md), which states plainly that replies 01 and 02 came from Claude Opus 5 in a Claude Code session rather than the API, because this machine has no key |


## Reproduction

Full clean-machine guide: [`Docs/REPRODUCTION.md`](Docs/REPRODUCTION.md).
~3.5 GB, ~40 minutes, and **$0** — the deterministic arm calls no model API and needs no key.

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest tests/ -q          # 143 passed, ~5s, no data needed
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

## Licence

MIT — see [`LICENSE`](LICENSE).
