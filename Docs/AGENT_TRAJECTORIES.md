# Agent Trajectories

Runs of the pipeline on real Enron workbooks, recorded so that the path from
instruction to result can be followed step by step: which tool ran, what it
returned, what the pipeline did with that answer, where a candidate was dropped,
where something was retried, and where a human is required.

Everything here is in [`results/trajectories/`](../results/trajectories/) and can be
regenerated offline.

There is exactly **one model-driven agent** in this system — Layer 2, semantic
interpretation. That is deliberate, and the reason is in [§B](#b--layer-2-the-only-agent).
The rest of the pipeline is deterministic tooling, and it is traced here too, because
the interesting decisions are mostly its.

---

## A — Whole-pipeline traces

```bash
PY scripts/trace_pipeline.py data/seeded/chris_germany__1938__Mar2002_EstateGas.xlsx \
    --out results/trajectories/trace_estategas.json
```

Three traces, chosen to cover the outcomes that actually occur:

| Trace | Workbook | What it shows |
|---|---|---|
| [`trace_estategas`](../results/trajectories/trace_estategas.md) | `chris_germany__1938` | The screen discarding 27 of 28 candidates |
| [`trace_floorplan`](../results/trajectories/trace_floorplan.md) | `scott_neal__38672` | Proof failures and demotions |
| [`trace_refused`](../results/trajectories/trace_refused.md) | volatile fixture | A workbook refused before any audit runs |

### The stages, and the gate each applies

```
0 readiness   volatile / non-deterministic workbooks are refused outright
1 detect      row-majority pattern breaks; typed constants sitting among formulas
2 screen      does the constant equal what the row's formula would produce?
3 prove       apply the repair (or perturb an input) and recompute
4 interpret   model supplies intent; the graph vetoes anything it invented
5 triage      proved / suspected / refused, and what the human is asked to do
```

### Trace 1 — how tools respond, and what gets thrown away

On `chris_germany__1938`, 1,395 formula cells:

```
1 detect    pattern_breaks 2 - dead_candidates 28
2 screen    kept 2 - dropped 26
              Sheet1!E7      10000      would be =+D7
              Sheet1!E8      2.1562     would be =+D8
              Sheet1!E10     -10000     would be =+D10
3 prove     attempted 4 - proved 4 - unproved 0
              Sheet1!U46  U46: 0 -> -6800 (-6800)
              Sheet1!AI74  AI74: -50000 -> 2.3845 (+50002.3845)
5 triage    proved 4 - report, do not act
```

**The 26 discards are the point.** A trace listing only survivors tells you what
the tool believes; a trace listing what it discarded tells you whether to believe
it. A constant sitting in a row of carry-forward formulas *looks* like a frozen
formula, and the screen answers with the number that settles it: the row's formula
would not produce that value, so it is ordinary typed data. This step took the
dead-cell detector from 40 false positives to 0.

Detection runs along **both axes** here, via `audit.detect` -- the single definition
of what this project detects. An earlier version of this script called the detectors
directly and so kept tracing a row-only pipeline after the shipped one gained a
column pass, which is a trace of a product the reader does not have.

### Trace 2 — retries, failures, and demotion

`scott_neal__38672` attempts 13 proofs and 4 fail:

```
Floor Plan!N58     repair changes nothing; not reported
Floor Plan!C76     repair changes nothing; not reported
Floor Plan!J78     recomputation failed: ValueExcelError
Floor Plan!K40     repair changes nothing; not reported
```

The first two are the interesting case. Both genuinely break their row's pattern, so
detection was right, but correcting them moves no number — the cell is unreferenced,
or the change cancels. **No delta, no finding.** They are demoted to *Suspected* and
shown to a human rather than reported as errors.

The third is a tool failure, not a verdict: the repaired workbook would not evaluate.
It is recorded as what it is. An audit that silently swallowed a failed recomputation
would be claiming to have checked something it did not check.

### Trace 3 — refusal

```
0 readiness   volatile: 1 volatile cell(s) using RAND
              determinism: not reached
              DECISION: REFUSE
```

A proof is a comparison of two evaluations. With `RAND` anywhere in the dependency
cone the two differ for reasons unrelated to any finding, so every "proof" would be
noise that looks exactly like signal. The workbook is refused before detection runs.
9% of the corpus is refused this way.

### The human checkpoint

Stage 5 is where the pipeline stops. **Plumbline never edits a workbook** — it has no
write path to the original file at all. Every report gives a cell, a proposed formula,
and the recomputed consequence in money terms; keeps *proved* and *suspected* in
separate sections so the two can never be conflated; ends with what was **not**
checked; and states that a qualified reviewer must confirm each finding before any
change is made.

That last part is in the artifact rather than the documentation on purpose. A blind
spot disclosed only in a README is not disclosed to the person reading the audit.

---

## B — Layer 2, the only agent

### How these were produced, exactly

```bash
PY scripts/agent_trajectories.py dump <workbook.xlsx> --live   # needs a key
PY scripts/agent_trajectories.py replay                        # offline, always
```

`dump` writes the byte-exact system and user prompts, built by `agent.build_context`
and `agent._render_user_prompt` — the same two functions the live path calls. Nothing
about the prompt is reconstructed or idealised.

**Replies `01` and `02` are real Anthropic API responses**, `claude-opus-5` with
adaptive thinking at `medium` effort, recorded verbatim from `--live`. An earlier
version of this file described them as written by Claude Opus 5 in a Claude Code
session, because the machine had no key at the time; a key later became available
and they were regenerated through the API. The prompts did not change.

`replay` is the half that matters for reproducibility, and it needs **no key and no
network**: it feeds each recorded reply back through `agent.interpret`, so the JSON
parsing, the ASCII folding, and the hallucination guard all execute for real. Anyone
can re-run the verdicts offline and get the same answers.

`replay` feeds each recorded reply back through `agent.interpret` with a client that
returns the recorded text. JSON parsing, truncation, and the hallucination guard all
execute for real, and anyone can re-run the verdicts offline.

### The agent's instructions

The full system prompt is in `src/plumbline/agent.py` and in every
`*.prompt.json`. Three rules define the job, and each exists because a model in an
audit tool is a liability unless fenced:

1. **The model never decides whether something is an error.** Recomputation already
   did. The model supplies *intent* — what was this cell for? — and an explanation.
   It cannot set `proved`.
2. **The model never sees the whole sheet.** It gets the cell, its row peers, its
   precedents, and the surrounding labels. The two prompts here are 389 and 471
   characters.
3. **Every claim is checked against the graph before display.** A cell reference not
   in the context is stripped and the interpretation is marked failed.

### The three cases

| | Cell | Reply | Guard |
|---|---|---|---|
| 01 | `Sheet1!U8` | pointing slip in a carry-forward chain | accepted |
| 02 | `Sheet1!AH25` | frozen formula, deliberateness unclear | accepted |
| 03 | `Sheet1!AH25` | **adversarial**, hand-written to fail | **rejected** |

01 and 02 are live API replies; 03 is hand-written and labelled as such in its own
file, because a guard has to be shown firing on something and the model did not
oblige by hallucinating.

**01 — the model adds what recomputation cannot.** The deterministic arm proves `U8`
should read `=+T8` and does not: `10000 → 2.1562`. It cannot say *why that shape*. The
model reads the chain — `Q8` reads `P8`, `R8` reads `Q8`, on to `Y8` — and identifies a
one-row vertical slip, the signature of a formula dragged from the row above. It
answers `deliberate: false` and gives the evidence.

**02 — the model declines to guess.** `AH25` holds a typed `5000` where its row holds
carry-forward formulas, and `5000` is exactly what `AG25` reports today, so nothing on
the sheet looks wrong. Asked whether the override was deliberate, the model answers
`null` and says the labels do not tell it. That is the intended behaviour: the system
prompt states that "the labels do not indicate the intent" is a correct answer, because
an audit tool that manufactures a motive is worse than one that reports uncertainty.

**03 — the guard fires on real data.** A hand-written reply cites `AJ40` and
`Summary!B12`. Neither is in the context. Both are stripped, `ok` is set false, and the
interpretation never reaches the report. A fabricated reference to another tab is
precisely the claim an analyst cannot cheaply check.

### What replaying these actually found

The guard was **too strict**, and only a real trajectory showed it.

Reply `01` cited `P8`. The prompt lists the peer `Q8: =+P8`, so `P8` was on the model's
screen — citing it is reasoning from the evidence. The guard rejected it anyway, because
it enumerated peer *addresses* and the references inside the cell's own two formulas,
and never looked inside the peer formulas it had printed.

Two definitions of "the context" had drifted apart: the one in the system prompt (what
the model is shown) and the one in `_known_cells` (a hand-maintained list).
`_known_cells` now parses the rendered prompt itself, so there is one definition and it
is the text the model reads. Cross-sheet references stay rejected, which is the case
that matters.

A second bug surfaced the same way: `build_context` took the first string in a column as
the column label, and financial models label columns with computed dates. Row 3 of
`chris_germany__1938` is `=+T3+1` across the sheet, so the model was being told
`Column label: =+T3+1` — not a label, not what anyone sees on screen, and an invitation
to reason about a header that does not exist.

This is the argument for keeping trajectories as an artifact rather than a demo. A unit
test with a hand-built context would have passed, because the hand-built context would
have contained whatever the guard already knew about.
