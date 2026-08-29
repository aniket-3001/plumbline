# Pipeline trace - scott_neal__38672__6th floorplan 01.30a.xlsx

*10.6s, min_peers=2*

## 0 readiness

**Tool.** `determinism.find_volatile + determinism.check`

**Returned.** `{"volatile": "no volatile functions found", "determinism": "stable across two runs (150 cells compared)"}`

**Decision.** proceed

**Why.** Two evaluations of the same workbook agree, so a difference between them can be attributed to a repair rather than to noise.

## 1 detect

**Tool.** `detect_pattern_breaks + detect_dead_cells(min_peers=2)`

**Returned.** `{"formula_cells": 400, "pattern_breaks": 10, "dead_candidates": 71}`

**Decision.** pass every candidate to the screen

**Why.** Detection is deliberately loose. Precision is bought downstream, by recomputation, not by guessing harder here.

## 2 screen

**Tool.** `screen_dead_cells (evaluates each candidate formula in a scratch column)`

**Returned.** `{"kept": 4, "dropped": 67}`

**Dropped.**

- `{"cell": "Floor Plan!W3", "value": "662", "would_be": "=X3+1"}`
- `{"cell": "Floor Plan!X3", "value": "5", "would_be": "=Y3+1"}`
- `{"cell": "Floor Plan!AC3", "value": "850", "would_be": "=AD3+1"}`
- `{"cell": "Floor Plan!P32", "value": "670", "would_be": "=Q32+1"}`
- `{"cell": "Floor Plan!AC32", "value": "800", "would_be": "=AD32+1"}`
- `{"cell": "Floor Plan!Q35", "value": "6", "would_be": "=R35+1"}`
- `{"cell": "Floor Plan!W35", "value": "387", "would_be": "=X35+1"}`
- `{"cell": "Floor Plan!J41", "value": "5", "would_be": "=K41+1"}`

**Decision.** discard 67 of 71 candidates

**Why.** A typed constant among formulas is usually just data. Only one whose value equals what the row's formula would produce looks like a frozen formula. This step took the dead-cell detector from 40 false positives to 0 on the workbook that first exposed it.

## 3 prove

**Tool.** `prove (write a repaired copy, re-parse, compare; or perturb an input)`

**Returned.** `{"attempted": 14, "proved": 11, "unproved": 3, "deferred_budget": 0}`

**Proved.**

- `{"cell": "Sheet1!K7", "detector": "pattern_break", "proof": "K7: 1219 -> 1216 (-3)"}`
- `{"cell": "Floor Plan!I14", "detector": "pattern_break", "proof": "I14: 24 -> 1 (-23)"}`
- `{"cell": "Floor Plan!I21", "detector": "pattern_break", "proof": "I21: 2 -> 4 (+2)"}`
- `{"cell": "Floor Plan!I26", "detector": "pattern_break", "proof": "I26: 12 -> 1 (-11)"}`
- `{"cell": "Floor Plan!H38", "detector": "pattern_break", "proof": "H38: 136 -> 0 (-136)"}`
- `{"cell": "Floor Plan!AA84", "detector": "pattern_break", "proof": "AA84: 1 -> 160 (+159)"}`

**Not proved.**

- `{"cell": "Floor Plan!I40", "outcome": "repair changes nothing; not reported"}`
- `{"cell": "Floor Plan!C76", "outcome": "repair changes nothing; not reported"}`
- `{"cell": "Floor Plan!J78", "outcome": "recomputation failed: ValueExcelError"}`

**Decision.** 11 findings survive; 3 are demoted to suspected

**Why.** This is the only gate that can promote a suspicion to a finding. A repair that changes no number proves nothing and is reported as suspected, never as an error.

## 5 triage

**Tool.** `report.render_markdown`

**Returned.** `{"proved": 11, "suspected": 3, "blind_spots_declared": true}`

**Decision.** report, do not act

**Human checkpoint.** Plumbline never edits a workbook. Every report names a cell, a proposed formula, and the recomputed consequence, and states that a qualified reviewer must confirm each finding before any change is made. Proved and suspected are kept in separate sections so the two are never conflated, and the report always ends with what was NOT checked.
