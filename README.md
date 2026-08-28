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

*To be filled as the project iterates. Every meaningful experiment gets an entry with its evidence
and the decision it drove, including experiments that were removed.*

| Stage | What was tried and why | Evidence | Decision / learning |
|---|---|---|---|
| — | — | — | — |

## Reproduction

See [`Docs/REPRODUCTION.md`](Docs/REPRODUCTION.md) *(pending)*.

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
