# Pipeline trace - chris_germany__1938__Mar2002_EstateGas.xlsx

*2.1s, min_peers=2*

## 0 readiness

**Tool.** `determinism.find_volatile + determinism.check`

**Returned.** `{"volatile": "no volatile functions found", "determinism": "stable across two runs (150 cells compared)"}`

**Decision.** proceed

**Why.** Two evaluations of the same workbook agree, so a difference between them can be attributed to a repair rather than to noise.

## 1 detect

**Tool.** `detect_pattern_breaks + detect_dead_cells(min_peers=2)`

**Returned.** `{"formula_cells": 1396, "pattern_breaks": 1, "dead_candidates": 28}`

**Decision.** pass every candidate to the screen

**Why.** Detection is deliberately loose. Precision is bought downstream, by recomputation, not by guessing harder here.

## 2 screen

**Tool.** `screen_dead_cells (evaluates each candidate formula in a scratch column)`

**Returned.** `{"kept": 1, "dropped": 27}`

**Dropped.**

- `{"cell": "Sheet1!E7", "value": "10000", "would_be": "=+D7"}`
- `{"cell": "Sheet1!E10", "value": "-10000", "would_be": "=+D10"}`
- `{"cell": "Sheet1!E11", "value": "3.04", "would_be": "=+D11"}`
- `{"cell": "Sheet1!E25", "value": "5000", "would_be": "=+D25"}`
- `{"cell": "Sheet1!E26", "value": "2.25", "would_be": "=+D26"}`
- `{"cell": "Sheet1!E28", "value": "-5000", "would_be": "=+D28"}`
- `{"cell": "Sheet1!E29", "value": "2.25", "would_be": "=+D29"}`
- `{"cell": "Sheet1!E34", "value": "6000", "would_be": "=+D34"}`

**Decision.** discard 27 of 28 candidates

**Why.** A typed constant among formulas is usually just data. Only one whose value equals what the row's formula would produce looks like a frozen formula. This step took the dead-cell detector from 40 false positives to 0 on the workbook that first exposed it.

## 3 prove

**Tool.** `prove (write a repaired copy, re-parse, compare; or perturb an input)`

**Returned.** `{"attempted": 2, "proved": 2, "unproved": 0, "deferred_budget": 0}`

**Proved.**

- `{"cell": "Sheet1!U8", "detector": "pattern_break", "proof": "U8: 10000 -> 2.1562 (-9997.8438)"}`
- `{"cell": "Sheet1!AH25", "detector": "dead_cell", "proof": "set AG25 5000 -> 6000: AH25 as-is 5000 -> 5000 (no response); as formula -> 6000 (responds)"}`

**Decision.** 2 findings survive; 0 are demoted to suspected

**Why.** This is the only gate that can promote a suspicion to a finding. A repair that changes no number proves nothing and is reported as suspected, never as an error.

## 5 triage

**Tool.** `report.render_markdown`

**Returned.** `{"proved": 2, "suspected": 0, "blind_spots_declared": true}`

**Decision.** report, do not act

**Human checkpoint.** Plumbline never edits a workbook. Every report names a cell, a proposed formula, and the recomputed consequence, and states that a qualified reviewer must confirm each finding before any change is made. Proved and suspected are kept in separate sections so the two are never conflated, and the report always ends with what was NOT checked.
