# Ablation: how many formula peers a row needs

`detect_dead_cells` flags a typed constant sitting in a row whose other cells all
hold one formula shape. How many such peers must a row have before that means
anything? The original code said three, chosen by argument. This measures it.

Both arms run on the same 21 workbooks and the same 53 seeded errors, and **each
arm's exclusion list is recomputed at its own threshold** — a mismatch there
charges the more sensitive arm for the extra pre-existing cells it correctly
finds, which is the same bug as the v2 → v3 row of the changelog in a third form.

## What the benchmark says

| | `min_peers = 3` | `min_peers = 2` |
|---|---|---|
| Precision | 1.000 | 1.000 |
| Recall | 0.868 | **0.981** |
| F1 | 0.929 | **0.991** |
| Recall, *silent* | 0.767 | **0.967** |
| TP / FP / FN | 46 / 0 / 7 | **52 / 0 / 1** |
| Pre-existing (excluded) | 368 | 397 |

Read at face value this is not close. `min_peers = 2` finds six of the seven
remaining seeded errors and costs nothing: precision stays at 1.000.

## Why that reading is wrong

Precision stays at 1.000 because the 29 extra findings are **pre-existing**, and
pre-existing findings are excluded from scoring — there is no ground truth for a
25-year-old workbook. So the benchmark reports the benefit of lowering the
threshold and is structurally blind to its cost. Every additional false positive
lands in the one bucket the score cannot see.

The 29 were therefore read by hand. These are **judgements, not ground truth**,
and they are recorded so someone can disagree with a specific one.

### `darrell_schoolcraft__7594` — `MANUAL` sheet, 7 findings, **all wrong**

```
B28 '=+B27+1'   C28 'FIN 2'   D28 52      G28 '=+G27+1'   H28 'LIBERAL'   I28 83
B29 '=+B28+1'   C29 'FIN 3'   D29 53      G29 '=+G28+1'   H29 'STC 1'     I29 126
B30 '=+B29+1'   C30 'FIN 4'   D30 54      G30 '=+G29+1'   H30 'STC 2'     I30 127
B31 '=+B30+1'   C31 'TATE'    D31 135     G31 '=+G30+1'   H31 'STC 3'     I31 128
B32 '=+B31+1'   C32 'HOLCOMB' D32 1660    G32 '=+G31+1'   H32 'STC 4'     I32 129
```

The sheet is a lookup table of three side-by-side blocks — `(B,C,D)`, `(G,H,I)`,
`(Q,R,S)` — each `(row number, name, meter id)`. `B` and `G` are the row counters
and they are the peers. `D` and `I` are **meter IDs**, which is data.

They pass the screen because meter IDs sometimes run consecutively: `D28..D30` is
`52,53,54`, so `D28` equals `D27+1` by coincidence. `D31 = 135` and `D32 = 1660`
break the run and are not flagged, which is the tell — a real counter column would
be flagged along its whole length, not in patches.

### `darron_c_giron__8011` — 19 findings, mixed

`ENRON MIDWEST P&L!J114 = 40093.20499999914`, where `C114` and `E114` both hold
`=+C25+C33+C64+...`. The floating-point residue in that literal is the signature of
a **computed value pasted over a formula**. This one is real, and it is exactly the
error class this project exists to catch.

`J13 = 19143914` and `L13 = 5104956` on the `NET SALES` row, where `E13` and `G13`
hold `=SUM(E9:E12)`, are plausibly real for the same reason, though less certainly.

The other sixteen are on the `Physical` sheet and almost all evaluate to **0**:
`D13`, `K13`, `D35`, `K35`, `D47`, `K47`, `F60`, `K60`, `M60`, `K62`, … A cell
holding `0` where the peer formula also produces `0` supplies no evidence either
way. They are not obviously wrong; they are unverifiable, which for a tool whose
product is proof is not much better.

`Physical` also repeats the block structure: `(B,D)`, `(I,K)`, `(Q,S,U)` are three
copies of one report, so `S` and `U` being the peers of `D` and `K` is again a
cross-block comparison.

### `mike_carson__27556` — 2 findings, 1 wrong

`Options!D19 = 48.3` with `B19 = '=B18'` and `C19 = '=C18'` looks real: `D` is
inside the carry-forward block.

`Options!F16 = 1` is not. Row 16 is `B16 '=B15' · C16 "Dec '01" · D16 '=D15' ·
E16 '40 mp' · F16 1 · G16 1.5`. The peers `B16` and `D16` are the carry-forward
block; `E`, `F`, `G` are a strike-price data block. `F16` is data.

### Tally

| | Count |
|---|---|
| Look genuinely wrong (real hardcoding) | ~3 |
| Look like ordinary data, wrongly flagged | ~10 |
| Unverifiable (value is `0`; no evidence either way) | ~16 |

Estimated precision on the newly-surfaced population: **roughly 0.2–0.4.** Poor,
and poor in the way that matters — a spurious `PROVED` sends an analyst to a cell
that was never wrong, which is the failure mode this project's whole design is
organised against.

## Decision

**Ship `MIN_ROW_PEERS = 3`, the arm with the worse benchmark score.**

The benchmark prefers `2` by 0.06 F1 and cannot see what it costs. Six more
seeded errors is a real gain, but it comes with roughly ten spurious proved
findings per corpus, and precision is the product-critical metric for an audit
tool: an analyst who chases two dead ends stops trusting the third finding, and
then the tool is worth nothing regardless of its recall.

`--min-peers` is exposed on both `run_baseline.py` and `seed_corpus.py` so the
sweep is repeatable rather than a claim.

## What this actually points at

Peer *count* is a proxy for the thing that matters, and the hand-labelling shows
what that thing is: **every clear false positive is a cross-block comparison.** In
`MANUAL` the peers are `B` and `G` with data columns between them; in `Physical`
they are `S` and `U` while the candidate is in the `(I,K)` block; in `Options` the
peers are `B` and `D` while `F` belongs to a strike-price block.

The right discriminator is contiguity — whether the candidate sits *inside* the run
of cells that share the shape, rather than in a different block of the same row.
That is a detector change rather than a threshold change, it is the natural next
piece of work, and it is not implemented here. `min_peers = 3` suppresses most
cross-block cases only incidentally, by requiring more peers than a two-block row
usually offers.
