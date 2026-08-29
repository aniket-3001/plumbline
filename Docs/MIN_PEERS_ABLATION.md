# Ablation: how many formula peers a row needs

`detect_dead_cells` flags a typed constant sitting in a row whose other cells all
hold one formula shape. How many such peers must a row have before that means
anything? The original code said three, chosen by argument. This measures it — and
ends up answering a different question than the one it asked, because the threshold
turned out to be a proxy for something else.

Every arm runs on the same 21 workbooks and the same 53 seeded errors, and **each
arm's exclusion list is recomputed at its own settings** — a mismatch there charges
the more sensitive arm for the extra pre-existing cells it correctly finds, which is
the same bug as the v2 → v3 row of the changelog in a third form.

Read in order: what the benchmark said, why that reading was wrong, what reading the
findings by hand showed instead, and what shipped once the real signal was built.

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

## Decision, after building the thing the labelling pointed at

The hand-labelling said peer *count* was a proxy, and that the real signal was
**block membership**: every clear false positive was a cross-block comparison,
where the candidate sat in one block of the row and its "peers" in another.

So `_peers_in_block` was built. A block is a run of cells on one regular stride --
sheets lay out either densely (`C D E F`) or on a spacer rhythm (`C _ E _ G`), and
both are one block; what separates two blocks is a change of rhythm or a stretch of
unrelated content. A peer counts only if the candidate is on that stride and inside
that span.

Then all four combinations were measured, each with its exclusion list recomputed at
its own settings:

| Arm | Precision | Recall | F1 | Recall *silent* | Pre-existing (unverified) |
|---|---|---|---|---|---|
| no contiguity, `min_peers=3` | 1.000 | 0.868 | 0.929 | 0.767 | 368 |
| no contiguity, `min_peers=2` | 1.000 | **0.981** | **0.991** | **0.967** | 397 |
| contiguity, `min_peers=3` | 1.000 | 0.811 | 0.896 | 0.667 | 360 |
| **contiguity, `min_peers=2`** | 1.000 | **0.924** | **0.961** | **0.867** | **362** |

**Shipped: contiguity with `min_peers = 2`.** Against the previous default it finds
three more seeded errors (0.868 → 0.924, and silent recall 0.767 → 0.867) while the
unverified population goes *down*, 368 → 362. It is the only arm that improves both.

Two things this settles, and one it does not:

- **The threshold was never the precision knob it appeared to be.** Precision is
  1.000 in all four arms. What lowering it actually did was admit cross-block
  comparisons, and block membership is what excludes those. Fixing the right thing
  made the threshold cheap.
- **Contiguity alone is a loss.** At `min_peers=3` it costs three true positives and
  buys nothing measurable. It only pays as the thing that makes `2` safe.
- **`no contiguity, min_peers=2` still scores highest**, and is still not shipped.
  Its extra 0.057 of recall comes with 35 more unverified findings, and the hand
  labelling above is what those look like.

## What this still gets wrong

Contiguity assumes the corruption is **one cell wide**. Two shapes defeat it, both
real, both from `scott_neal__38672`, and both now pinned as tests:

```
row 32:  R32 '=S32+1'  S32 '=T32+1'  T32 '=U32+1'  U32 603  V32 602  W32 601
```

Sibling blocks in that row (`K..P`, `Y..AC`) each carry exactly one trailing
constant, so `U32` and `V32` were both formulas once. `U32` is still found — it sits
next to live formulas. `V32` is not, because its only neighbour is dead too.

```
row 64:  ... W64 327 | Y64 212  Z64 211
```

Here the entire two-cell block was overwritten, so nothing in the row can vouch for
it. No layout rule recovers this; it would need the labels, which is Layer 2's job.

**And the benchmark cannot see either failure.** The seeder injects at most one
error per row, so every seeded dead cell is exactly the case contiguity handles
best. The +0.056 recall it measures is therefore an over-estimate for workbooks
whose corruption is wider than a single cell. That is the same shape of blindness
this document opened with, found again on the other side of the decision, and it is
the reason the two tests exist: they are the part of the truth the score omits.

## Reproducing

```bash
PY scripts/seed_corpus.py --refresh-pre-existing --min-peers 3
PY scripts/run_baseline.py --max-proofs 25 --min-peers 3 --out contig_p3.json
PY scripts/seed_corpus.py --refresh-pre-existing --min-peers 2
PY scripts/run_baseline.py --max-proofs 25 --min-peers 2 --out contig_p2.json
```

Add `--no-contiguous` to both commands in a pair for the other two arms. The refresh
must always match the run: an exclusion list computed at different settings than the
audit charges the audit for pre-existing cells it correctly finds, which is the
v2 → v3 bug in the changelog and it recurs every time this is forgotten.
