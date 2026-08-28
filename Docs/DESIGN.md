# Spreadsheet Audit Agent — Design

Status: **decisions locked 2026-08-28.** Companion to `HACKATHON_BRIEF.md`,
`CANDIDATE_IDEAS.md`, `WINNING_PATTERNS.md`.

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

## 7. What existed before vs what we add *(ground rule 2)*

**Existed:** xlcalculator (MIT formula engine), the Enron corpus (CC BY 4.0), Panko's error taxonomy
and prevalence data, Nixon & O'Hara's tool evaluation, Schmitz & Jannach's prior error-finding work.

**We add:** the structural detector suite, the minimal-subgraph context extractor, the
recomputation-backed verification gate, the triage/escalation policy, the Panko-grounded seeding
harness, and the evaluation harness with its ablation.
