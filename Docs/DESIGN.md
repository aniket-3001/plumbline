# Spreadsheet Audit Agent — Design

Status: **decisions locked 2026-08-28.** Companion to `REPRODUCTION.md` and
`MIN_PEERS_ABLATION.md`.

---

## 0. Gating facts (verified, not assumed)

| Question | Answer | Source |
|---|---|---|
| Is the Enron corpus downloadable? | **Yes** — figshare, DOI [10.6084/m9.figshare.1221767](https://figshare.com/articles/dataset/Enron_Spreadsheets_and_Emails/1221767) | Hermans, 2014 |
| Licence of the corpus? | **CC BY 4.0.** Hermans: *"the whole set is creative commons, so do what you like"* | figshare |
| Format problem? | **Solved for us** — the figshare version is already `.xlsx`. (Macros stripped; we do not need VBA) | EuSpRIG note |
| Scale? | 265,586 attachments → 51,572 Excel files → **16,189 unique by MD5** | Hermans & Murphy-Hill, ICSE 2015 |
| Originals if ever needed | [SheetJS/enron_xls](https://github.com/SheetJS/enron_xls) mirror, original formats, MD5-deduped | — |

**The `.xls` conversion time sink I flagged does not exist.** That risk is closed.

### Engine licences

| Library | Licence | Note |
|---|---|---|
| **xlcalculator** | **MIT** | ✅ chosen |
| xlsx-evaluate | MIT | fork/alternative |
| pycel | GPL-3.0 | good graph export, copyleft |
| formulas | EUPL 1.1+ | weak copyleft, own obligations |
| HyperFormula | GPLv3 / commercial | best graph API, but OSS licence is "open-source projects and evaluation use only" |

**Action item:** confirm each LICENSE file in-repo before shipping. Search results were explicit that
they could not surface a definitive statement for pycel and formulas. Not legal advice.

---

## 1. Locked decisions

**Engine: `xlcalculator` (MIT), Python.**
MIT keeps us free of copyleft obligations on our own code, and Python is the better host language for
the agent, the seeding harness and the evaluation. HyperFormula has the nicer dependency-graph API
but GPLv3 plus a TypeScript/Python split is friction we do not need.

*Known trade-off:* xlcalculator likely has thinner function coverage than pycel/formulas. Its README
maintains a function-coverage comparison table across xlcalculator, pycel, formulas and Koala — use
it to size the gap. **Mitigation: we report formula coverage as a published metric rather than hiding
it** (see §5).

**Data: Enron corpus (CC BY 4.0), seeded errors for ground truth.**

**Human checkpoint: the agent never edits a workbook.** It emits a report for a qualified reviewer.
Satisfies ground rules 4 and 5 by construction.

---

## 2. The user (naming this is worth a rubric point)

> **A financial analyst who has inherited a model they did not build** — the colleague who wrote it
> has left — **and who must sign off on numbers going into a board pack or a lender submission.**

They cannot verify four thousand formulas by hand. They have no way to know which cells deserve
attention. Their name goes on the output. Today they either spend two days spot-checking, buy a
$2,000/year Windows add-in that flags structural smells without understanding what the model *means*,
or they sign and hope.

Why it matters: [Panko's synthesis of seven field audits](http://panko.shidler.hawaii.edu/SSR/Mypapers/whatknow.htm)
found **94% of operational spreadsheets contain errors**, cell error rate 5.2%. Model audit is
already a paid professional service commissioned by banks to reassure lenders.

---

## 3. Architecture — why each layer exists

The design follows a documented division of labour, not an invented one.
[Nixon & O'Hara](https://arxiv.org/pdf/1001.4293) found commercial rule-based auditors **"failed
where label-pattern recognition was required."** LLM-only tools have the mirror failure: practitioners
report them as *"assistive, not autonomous"* because they cannot compute and they hallucinate
references.

### Layer 1 — Deterministic extraction *(lever: better tools)*
Parse workbook → dependency graph. No model involved. Produces candidate anomalies with exact
addresses:
- **Pattern break** — cell whose R1C1-normalised formula differs from its row/column neighbours
- **Hardcoded constant** inside a formula region ([a studied error class](https://arxiv.org/pdf/0803.0169))
- **Range off-by-one** — SUM range does not cover the contiguous block it appears to target
- **Broken references** — `#REF!`, `#VALUE!`, `#DIV/0!`
- **Orphans** — computed cells nothing depends on
- **Cross-sheet inconsistency**

### Layer 2 — Semantic interpretation *(lever: better context)*
For each candidate, extract a **minimal subgraph plus surrounding row/column labels** — never the
whole sheet. (FoRepBench had to do the same thing: nearest table, header, few sample rows, because
whole sheets do not fit the window.) The model answers: *what is this cell supposed to be?*

This is precisely the capability the rule-based tools lack.

### Layer 3 — Verification *(lever: verification)*
**Nothing reaches the user unless it is tied to a cell address and a recomputation that demonstrates
it.** If the model claims "this should sum B2:B13, not B2:B12," we recompute both and report the
delta. A claim that cannot be tied to a recomputation is dropped or escalated — never shown as a
finding.

This is the anti-hallucination gate, and it is mechanically enforceable, which means it is also
measurable (§5).

### Layer 4 — Triage
- **Confirmed** — recomputation proves divergence from stated intent
- **Cleared** — pattern break explained by labels (a deliberately different row)
- **Escalated** — ambiguous, goes to the human

---

## 4. Seeding taxonomy (grounded in Panko, not invented)

Seeding realism is the single biggest threat to this project's credibility. These judges sell rubric
quality professionally; artificial errors produce a fake-easy benchmark and they will see it.

Seed against Panko's classification:

| Class | Description | Example seed |
|---|---|---|
| **Mechanical** | Typing and pointing slips | Reference shifted one row; digit transposed |
| **Logic** | Wrong formula or algorithm | Average where a weighted average is required |
| **Omission** | Something left out of the model | A cost line absent from a total. *Hardest class to detect* |
| **Hardcoding** | Input value buried in a formula | `=B4*1.07` where 1.07 should be a referenced assumption |

**The deliberately hard case**, handed to us by practitioner literature:

> *"Errors tend to hide in places that feel like they don't need checking — subtotals that balance
> despite incorrect line items beneath them."*

A subtotal that reconciles while the lines under it are wrong. Compensating errors. Structural checks
pass, the arithmetic ties, and a human auditor's eye slides right over it.

---

## 5. Evaluation

**Cases:** ≥10 Enron workbooks (target 15–20), seeded across all four classes, including ≥1
compensating-error case. Same workbooks for every arm.

**Baselines** — deliberately fair, per the brief:
1. **Direct prompt** — hand the model the sheet (chunked as needed), ask it to find errors. This is
   the PDF's named "one direct prompt" baseline.
2. **Structural detectors alone** — Layer 1 with no model. Proxy for the commercial rule-based tools.
3. *Reference point:* [Schmitz & Jannach, "Finding Errors in the Enron Spreadsheet Corpus"](https://web-ainf.aau.at/pub/jannach/files/Conference_VL_HCC_2016.pdf)
   (VL/HCC 2016) — published pre-LLM work on this exact corpus.

Running arms 1 and 2 separately gives us the **ablation that IS the changelog** — each layer's
contribution measured on identical cases.

**Metrics:**

| Metric | Why |
|---|---|
| **F1 on seeded errors** (precision + recall) | Primary. Exact, because ground truth is by construction |
| **Proof rate** — % of findings with an attached verified recomputation | Measures Layer 3 doing its job |
| **Hallucinated-reference rate** | Findings pointing at cells that do not exist or claims unsupported by the graph |
| **Human review minutes per workbook** | The user's actual currency |
| **Formula coverage %** | Honesty metric. "We audited N% of formula cells; here is what we could not parse" |

Publishing coverage rather than hiding it is deliberate — the brief's integrity check rewards it, and
concealing a known limitation is how a submission fails before scoring.

---

## 6. Open risks

| Risk | Mitigation |
|---|---|
| Seeded errors unrealistic → fake-easy benchmark | Seed strictly to Panko's taxonomy; include compensating errors; publish the seeding script |
| xlcalculator function coverage gaps | Explicit skip policy; publish coverage %; check the README comparison table early |
| Enron sheets are mostly data, not formulas | Only ~24% contain formulas — filter to formula-bearing workbooks before sampling |
| Precision collapse on real (unseeded) sheets | Report findings on unseeded workbooks separately; a human spot-check on a sample |
| Licence non-compliance | Verify every LICENSE file in-repo before shipping; state versions in the reproduction guide |

---

## 6b. Implementation findings from the proof of concept (2026-08-28)

**xlcalculator's in-memory counterfactual APIs silently return wrong numbers.** This matters more
than it sounds: the entire product claim is *"we prove findings by recomputation,"* so a broken
recompute path does not fail loudly — it ships **fake proofs**.

Two approaches were tried and both are unusable:

| Approach | What happens |
|---|---|
| `Evaluator.set_cell_value(addr, "=SUM(C8:C10)")` | Sets `.value` to the formula *string* but leaves `.formula` and its AST intact. `evaluate()` still returns the **old** number. Looks like a successful repair that changed nothing |
| Replace `cell.formula` with a new `XLFormula(...)`, then `model.build_code()` | The constructor does not populate `terms` / `associated_cells`, so range lookups resolve to nothing. Returned `C11 = 0.0` while the dependent `C13 = 72000.0` — **internally inconsistent**, and neither value is correct |

**Adopted approach: patch a copy with openpyxl, write it, re-parse with `ModelCompiler`.** Slower,
but it goes through the identical code path as the original parse, so the counterfactual is
trustworthy. For a tool whose product *is* the proof, correctness of the recompute path outranks its
speed.

Verified on the fixture: `C11: 27000 -> 30000 (+3000)`, propagating to `C13: 45000 -> 42000 (-3000)`.
The omitted Rent line is 3000/quarter, so both deltas are exactly right.

**Second finding:** xlcalculator returns its own `Number` wrapper type, not Python numerics. It fails
`format()` and compares unexpectedly. Everything crossing the boundary out of the engine goes through
a `native()` coercion.

**Consequence for the evaluation:** any future speed optimisation of the counterfactual path needs a
differential test against the write-and-reparse ground truth, or we risk reintroducing silent
wrongness into the one thing we promise is sound.

---

## 6c. Coverage measured on the real corpus (2026-08-29)

### Headline: **93.0% of formula cells are evaluable**

Sample of 1,500 workbooks (seed 17), **1,706,537 formula cells**. Compile check: **72/80 workbooks
(90%)** actually compile under `ModelCompiler`, failing with `MemoryError` (1), `AttributeError` (2),
`ValueError` (1), `KeyError` (4). *Readable is not compilable* — both numbers matter.

**This corrects an earlier figure of 98.4% taken from a 100-workbook sample.** That sample was not
representative, and the error was not random: it produced a confident claim that `INDEX` "does not
appear in this corpus at all," explained by a plausible story about 2001-era spreadsheets predating
the `INDEX/MATCH` idiom. `INDEX` is in fact the **5th most-used function, 46,587 uses**. The story
was a rationalisation of a sampling artefact. Sample size for any coverage claim is now 1,000+.

### The gap is concentrated and cheap to close

| Implement | Uses | Coverage after |
|---|---|---|
| `INDEX` | 46,587 | 95.7% |
| `NORMINV` | 40,984 | **98.1%** |
| `VALUE` | 7,435 | 98.5% |
| `HLOOKUP` | 6,563 | 98.9% |
| `OFFSET` | 5,516 | 99.2% |
| `SUBTOTAL` | 4,127 | 99.5% |
| `TEXT` | 3,212 | 99.7% |
| `DATEVALUE` | 2,968 | 99.8% |

Two functions recover 73% of the gap. `NORMINV` is `scipy.stats.norm.ppf`, and scipy is already an
xlcalculator dependency. `INDEX` is a straightforward array indexer. **Decision: extend the function
registry rather than switch engines.**

`NORMINV` at 41k uses and `RAND` at 46k is a fingerprint of what Enron actually was — an energy
trading firm running Monte Carlo risk simulations.

### Serious finding: volatile functions break the proof mechanism

**`RAND` appears in 45,550 cells — 2.67% of the corpus.** xlcalculator *supports* it, so it does not
show up as a coverage gap. That makes it more dangerous, not less.

Our entire product claim is proof-by-recomputation: evaluate baseline, evaluate counterfactual,
report the delta. On a workbook containing `RAND`, **every evaluation returns different numbers**, so
the delta between two runs is noise. The tool would emit confident, precise, meaningless proofs —
the same failure class as the `set_cell_value` bug in §6b, and just as silent.

Mitigations, in order of preference:
1. **Detect and freeze.** Before auditing, replace volatile calls (`RAND`, `RANDBETWEEN`, `NOW`,
   `TODAY`) with their current cached values, then audit the frozen workbook.
2. **Detect and exclude.** Skip findings whose dependency cone touches a volatile cell, and say so.
3. **Never: audit anyway.** A proof that cannot be reproduced is not a proof.

Regardless of choice, **the evaluation must include a determinism check**: evaluate the same workbook
twice and assert identical results before trusting any delta computed from it.

`OFFSET` and `INDIRECT` (5,516 + 2,644 cells, 0.5%) are a separate architectural problem, not merely
missing functions — they construct references at runtime, so the dependency graph is not statically
knowable. Out of scope; report as unauditable.

---

## 6d. What the first real evaluation actually taught (2026-08-29)

Five baseline runs over 21 real seeded Enron workbooks. The numbers moved from
precision 0.739 / recall 0.630 to precision 1.000 / recall 0.924, and **the
detectors' code was identical for the first three of those steps.** Only v5, the
last of them, changed a detector at all.

That is the finding, and it is uncomfortable enough to be worth stating plainly:
for most of this project, the thing being measured was the measurement harness.

### The three harness bugs, and what they have in common

| | Bug | Cost | Shape |
|---|---|---|---|
| 1 | A runtime cap sliced the findings list rather than the proof queue | 10 of 20 misses; four workbooks scored zero | A budget changed what the tool *claimed to have looked at* |
| 2 | Exclusions computed with one detector of two | 11 of 13 false positives | The answer key was built by different code than the answer |
| 3 | Two seeds in a three-formula row | 2 misses, 1 false positive | The benchmark asked for something it had deleted |

All three share a structure: **a second implementation of something that already
existed once.** The cap re-derived "the findings", the exclusion list re-derived
"what the detectors find", and the seeder re-derived "what a row's majority is".
Each copy drifted, and each drift was scored against the tool.

The defence adopted is not vigilance, it is collapse: there is now exactly one
`pre_existing_findings` and it calls the audit's own detectors at the audit's own
settings, and a test asserts the two agree cell for cell. Where a second
implementation could not be removed, a test asserts the two agree.

### Why none of this showed up as a failing test

Every one of these bugs was invisible to the test suite and visible in about
fifteen minutes of reading individual missed cells. The summary said
`recall 0.630`, which is a plausible-looking number for a hard problem; nothing
about it suggested that four workbooks had scored zero for a reason unrelated to
detection.

**A metric that can absorb a bug without looking wrong is not an alarm.** The
practice that found all three was dumping every miss and every false positive with
its row context and reading them. That is now how a run is reviewed, not an
occasional deep dive.

### The exclusion rule is load-bearing, and therefore dangerous

362 of the audit's findings are pre-existing anomalies in Enron's own files. They
are excluded from scoring because there is no ground truth for a 25-year-old
workbook and inventing one would be worse than not scoring them.

This is correct and it is also the single mechanism by which this benchmark could
flatter itself: quietly widen the exclusion list and every miss becomes "not our
problem". Three properties hold it shut, and all three are enforced in tests
rather than argued in a doc:

1. Exclusions are computed on the **unseeded original**, so a seeded error cannot
   land in one. Checked across all 53 seeds, every run.
2. Exclusions use the **same detectors at the same settings**. Mismatch in either
   direction is a scoring bug; both directions have now happened.
3. When the exclusion list was corrected, **recall did not move** (0.7222 →
   0.7222). That is the control, and without it the precision gain from 0.750 to
   0.975 would be unreadable.

`precision 1.000` therefore means something narrower than it looks: every finding
was either a planted error or a cell already anomalous before we touched the file.
It does not mean the 362 are all genuine defects. Some plainly are — six typed
constants inside `=Z41+1` counter rows on `scott_neal__38672` — but that is a spot
check and is not reported as a measurement.

### The one detector question that survived

After the harness was fixed, all seven remaining misses were a single thing: dead
cells in rows holding exactly **two** formula peers, blocked by a hardcoded
`len(peers) < 3`.

Two peers agreeing is thinner evidence than five, so the threshold was defensible
as written — but it was chosen by argument, not measurement, and it turned out to
be the only thing standing between the audit and every miss it had left. It is now
`MIN_ROW_PEERS`, swept by `--min-peers`, with each arm's exclusion list recomputed
at its own threshold so the comparison is not confounded by bug 2 in a third form.


## 7. What existed before vs what we add *(ground rule 2)*

**Existed:** xlcalculator (MIT formula engine), the Enron corpus (CC BY 4.0), Panko's error taxonomy
and prevalence data, Nixon & O'Hara's tool evaluation, Schmitz & Jannach's prior error-finding work.

**We add:** the structural detector suite, the minimal-subgraph context extractor, the
recomputation-backed verification gate, the triage/escalation policy, the Panko-grounded seeding
harness, and the evaluation harness with its ablation.
