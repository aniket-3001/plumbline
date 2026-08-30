# Evaluation

The full measurement record: how success was defined, what was compared against
what, and every caveat that belongs next to a number. The README carries the
headline and the changelog; this carries the workings.

Everything here is reproducible offline at no cost — see
[`REPRODUCTION.md`](REPRODUCTION.md).

---

## How this was evaluated

**Primary metric: F1 on seeded errors.** Fixed in [`Docs/DESIGN.md`](DESIGN.md)
§5 before the first evaluation ran, along with the corpus, the baselines and the
scoring rule. Ground truth is exact because the errors are injected, so precision
and recall are counted rather than judged.

**What a good result looks like, and when we said so.** The target set in advance
was a detector that beats the structural baseline on F1 *without* losing precision —
because for an audit tool a false positive costs more than a miss. An analyst who
chases two dead ends stops trusting the third finding. We did **not** set a numeric
threshold in advance, and saying otherwise afterwards would be inventing the target
to fit the result. What we did fix in advance is the rule that decided every
subsequent tradeoff, and it is why the `min_peers` ablation shipped the arm with the
*worse* benchmark score.

**Cases: 21 real workbooks, 53 injected errors.** Same cases for every arm. Errors
are drawn from Panko's taxonomy and stratified by difficulty, because a single
blended recall figure lets a detector that only catches loud breakage look identical
to one that catches silent corruption.

### The comparison, in the brief's format

| Metric | Manual process today | Simple baseline | Plumbline | Change |
|---|---|---|---|---|
| **Primary outcome (F1)** | — | 0.021 | **0.990** | **+0.969** |
| Cells the analyst must judge, per workbook | 1,774 | 247 | **17** | **−99%** vs manual |
| Human time per workbook | ~5 h | ~2 h | **~8 min** | see note |
| Cost per workbook | analyst time | $0 | **$0** | no API, no key |
| Machine time per workbook | — | ~5 s | ~33 s | slower on purpose |

*Human time is an estimate, not a measurement, and the assumption is stated so you
can disagree with it: ~10 s to read a formula and its neighbours during a full manual
sweep, ~30 s to adjudicate a cell something has flagged. The measured input is the
cell counts, which come from [`results/arms.json`](../results/arms.json). Nobody
actually does the 5-hour sweep — that is the point, and it is why the honest
comparison for the manual column is "spot-check and hope".*

Plumbline is **slower per workbook than the naive detector and that is deliberate**:
the extra 28 seconds are spent recomputing the workbook to prove findings, which is
what turns 247 cells to squint at into 17 with evidence attached.

### The rubric we propose

The brief's sample format has one primary outcome; a spreadsheet audit needs four
numbers, because "found it" and "can show you why" are different achievements. If
you would rather score this project on its own terms, these are the numbers we would
use, and all four are in [`results/`](../results/):

| | What it measures | Why it earns a place |
|---|---|---|
| **Precision** | Of what we report, how much is real | The product-critical one. A tool that cries wolf is worse than no tool |
| **Recall, split by difficulty** | Of what is there, how much we find — separately for *obvious*, *realistic* and *silent* | Blending them hides whether the hard class works at all |
| **Proof rate** | Share of findings carrying a recomputation the reader can rerun | This is the product's actual claim, and F1 cannot express it |
| **Unverified findings** | Cells reported that ground truth cannot adjudicate | The honesty metric. It is the bucket the score cannot see, and it is where a detector hides its costs |

### The challenging case, and what it revealed

`darrell_schoolcraft__7407` is an hourly-volume sheet: rows 7–30 are values, row 31
is `=SUM(E7:E30)`. When column-wise detection was added, findings on this one
workbook went from 1 to **124** — the detector was flagging the **column totals** as
errors, because along a run of values the total is the only cell with a different
formula. Totals are in every spreadsheet ever written.

What it revealed is the thing this project is really about: **the benchmark called
that free.** Every one of those 124 cells is pre-existing, so it lands in the
excluded bucket and precision looked untouched. The bug was caught by reading the
number by hand, not by the score. Aggregates are now filtered before the majority
vote, and a genuinely wrong total is a declared blind spot rather than a silent one.


## Baseline vs solution

The brief's mandatory comparison. Four arms, **identical cases, identical scorer** —
each one adds exactly one of this project's contributions. `python scripts/run_arms.py`

| Metric | naive (baseline) | + block | + screen | + proof (shipped) |
|---|---|---|---|---|
| **Precision** | 0.011 | 0.197 | 1.000 | 1.000 |
| **Recall** | 1.000 | 0.981 | 0.981 | 0.981 |
| **F1** | 0.021 | 0.328 | 0.990 | 0.990 |
| True positives | 52 | 51 | 51 | 51 |
| False positives | 4,777 | 208 | 0 | 0 |
| Cells reported to the analyst | 5,187 | 565 | 357 | 357 |
| Findings carrying a proof | 0 | 0 | 0 | 32 |

**The baseline is not a strawman** — it is this tool with every contribution removed,
on the same corpus, seeds and scorer. It also describes what a rule-based auditor
does: flag structural anomalies and hand over the list. It finds **52 of 53** seeded
errors. It buries them in 4,777 false ones, which is the documented failure of the
commercial tools and the reason an analyst cannot use them.

Each arm computes **its own exclusion list** at its own settings, so a more sensitive
arm is never charged for the extra pre-existing anomalies it correctly finds.

Three things worth reading carefully, because none is the shape a comparison table
usually has:

- **Recall falls slightly, and that is the trade being made.** 1.000 → 0.981.
  Each gate costs a true positive or two and removes hundreds to thousands of false
  ones. The baseline's near-perfect recall is worthless at precision 0.011.
- **The screen does most of the work**, 0.328 → 0.990, by asking one question of each
  candidate: does this typed constant equal what the row's formula would produce?
- **Proof does not improve F1, and is not meant to.** Precision, recall and F1 are
  identical with and without it. What changes is that 32 findings arrive carrying a
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
  fell by an order of magnitude. A baseline that improves as the tool improves makes the
  comparison meaningless. `naive` is now pinned to the pre-contiguity detector.

## The v1–v6 record

| | v1 | v2 | v3 | v4 | v5 |
|---|---|---|---|---|---|
| **Precision** | 0.739 | 0.750 | 0.975 | 1.000 | **1.000** |
| **Recall** | 0.630 | 0.722 | 0.722 | 0.868 | **0.924** |
| **F1** | 0.680 | 0.736 | 0.830 | 0.929 | **0.961** |
| Recall, *obvious* | 0.500 | 0.500 | 0.500 | 1.000 | **1.000** |
| Recall, *realistic* | 0.750 | 0.750 | 0.750 | 1.000 | **1.000** |
| Recall, *silent* | 0.562 | 0.719 | 0.719 | 0.767 | **0.867** |
| TP / FP / FN | 34/12/20 | 39/13/15 | 39/1/15 | 46/0/7 | **49/0/4** |

**v6 detects down columns as well as across rows**, and it is deliberately *not* a
sixth column above. Measuring a column detector needs a corpus containing column
errors, so v6 re-seeds along both axes — a different corpus, and therefore a
different benchmark. Quoting 0.981 against v5's 0.924 would be comparing two
different question papers.

The attributable comparison is both arms on the **same v6 corpus**, each with its
own exclusion list:

| | row only | **row + column** |
|---|---|---|
| Precision | 1.000 | **1.000** |
| Recall | 0.750 | **0.981** |
| F1 | 0.857 | **0.990** |
| Recall, *silent* | 0.793 | **0.966** |
| TP / FP / FN | 39 / 0 / 13 | **51 / 0 / 1** |

Twelve more real errors at unchanged precision. It costs 114 more unverified
pre-existing findings, and a sample of those was read by hand rather than trusted:
`Feb01!R34`, `S34` and `T34` are three parallel columns each pointing one row past
the pattern their neighbours follow — one dragged formula, replicated. Real errors,
in the file Enron shipped.

21 real Enron workbooks. v1–v3 share one corpus of 54 seeded errors with a single fix
isolated per step, so every movement is attributable. v4 re-seeds (53 errors) because its
fix is *in* the seeder, so it is a new benchmark rather than the next rung of that ladder;
v5 is the first change to a **detector** rather than to the harness, and shares v4's corpus.

Raw results: [`v1`](../results/baseline_v1_truncating.json) ·
[`v2`](../results/baseline_v2_budget_fixed.json) ·
[`v3`](../results/baseline_v3_accounting_fixed.json) ·
[`v4`](../results/baseline_v4_seeding_fixed.json) ·
[`v5`](../results/baseline_v5_contiguity.json)

**Not one of the v1→v3 fixes touched a detector.** All three were in the measurement
harness. The detector scored 0.630 recall in v1 and 0.722 in v3 while its code stayed
identical; the difference is that the benchmark stopped charging the tool for its own bugs.
That is the most useful thing this project learned, and it was only visible because the
misses were read cell by cell rather than summarised.

## Does the structural machinery earn its place?

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

**This run is partial, and on the older corpus.** It covers **12 of 21 workbooks**,
stopping when the API account ran out of credit ~$4.85 in, so the deterministic
column is recomputed on those same 12 rather than quoted from any full-corpus run.
It was measured on the **v5** corpus and has not been re-run on v6, because that
costs money this project no longer has. Both columns come from the same 12
workbooks and the same seeds, so the comparison between them stands; neither should
be read against the v6 figures above. Raw per-workbook data, marked `"complete": false`, is in
[`results/llm_baseline.json`](../results/llm_baseline.json).

Not a strawman: same model (`claude-opus-5`), same effort, formulas in reading order
with row labels — what a human auditor would have. And it gets **its own exclusion
list**, computed by running it over the untouched originals too; without that, the 79
pre-existing Enron oddities it correctly spotted would have been charged against it
as false positives, which is the identical bug that cost the deterministic arm 11.

## How to read these numbers

**Precision and recall are measured against the seeded errors only.** The audit also
returns 306 findings that were already in the original Enron files. Those are excluded
from scoring — not counted as hits, not counted against precision — because nobody knows
the ground truth for a 25-year-old workbook, and guessing it would be inventing the
answer key.

So `precision 1.000` means something narrower than it looks: **every finding was either
an error we planted or a cell that was already anomalous before we touched the file.**
The detector produced nothing that was neither. It does **not** mean the 306 are all real
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

