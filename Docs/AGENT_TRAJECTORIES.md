# Agent Trajectories

Three recorded runs of Layer 2 — the only layer where a model speaks — on real
findings from a real Enron workbook, with the exact prompt in and the validated
result out.

Files are in [`results/trajectories/`](../results/trajectories/):
`*.prompt.json` (what was sent), `*.response.json` (what came back),
`*.trajectory.json` (what survived validation).

---

## How these were produced, exactly

The machine this was built on has no `ANTHROPIC_API_KEY`. Rather than ship a
model layer that had only ever been run against a stub, the step was split:

```bash
PY scripts/agent_trajectories.py dump data/seeded/chris_germany__1938__Mar2002_EstateGas.xlsx
PY scripts/agent_trajectories.py replay
```

`dump` writes the byte-exact system and user prompts, built by
`agent.build_context` and `agent._render_user_prompt` — the same two functions the
live path calls. Nothing about the prompt is reconstructed or idealised.

**The replies in `01` and `02` were written by Claude Opus 5 reading those exact
prompts in a Claude Code session, not returned by the Anthropic API.** That is the
honest description and it is the one that matters when reading these files: the
prompt is real, the workbook is real, the reasoning is a real model's, and the
delivery channel was a chat session instead of an HTTP request. With a key set,
`--live` sends the identical prompts through `agent.anthropic_client()`.

`replay` feeds each recorded reply back through `agent.interpret` with a client
that returns the recorded text. The JSON parsing, the truncation, and the
hallucination guard all execute for real, and anyone can re-run the verdicts
offline and get the same answers.

---

## What the three cases show

| | Cell | Reply | Guard |
|---|---|---|---|
| 01 | `Sheet1!U8` | pointing slip in a carry-forward chain | accepted |
| 02 | `Sheet1!AH25` | frozen formula, deliberateness unclear | accepted |
| 03 | `Sheet1!AH25` | **adversarial**, hand-written | **rejected** |

**01 — the model adds what recomputation cannot.** The deterministic arm proves
`U8` should read `=+T8` and does not: `10000 → 2.1562`. It cannot say *why that
shape*. The model reads the chain — `Q8` reads `P8`, `R8` reads `Q8`, on to `Y8`
— and identifies a one-row vertical slip, the signature of a formula dragged from
the row above. It answers `deliberate: false` and gives the evidence.

**02 — the model declines to guess.** `AH25` holds a typed `5000` where its row
holds carry-forward formulas, and `5000` is exactly what `AG25` reports today, so
nothing on the sheet looks wrong. Asked whether the override was deliberate, the
model answers `null` and says the labels do not tell it. That is the intended
behaviour: the system prompt states plainly that "the labels do not indicate the
intent" is a correct answer, because an audit tool that manufactures a motive is
worse than one that reports uncertainty.

**03 — the guard fires on real data.** A hand-written reply cites `AJ40` and
`Summary!B12`. Neither is in the context. Both are stripped, `ok` is set false,
and the interpretation never reaches the report. A fabricated reference to another
tab is precisely the claim an analyst cannot cheaply check, so it is the one that
must not escape.

---

## What replaying these actually found

The guard was **too strict**, and only a real trajectory showed it.

Reply `01` cited `P8`. The prompt lists the peer `Q8: =+P8`, so `P8` was on the
model's screen — citing it is reasoning from the evidence. The guard rejected it
anyway, because it enumerated peer *addresses* and the references inside the
cell's own two formulas, and never looked inside the peer formulas it had printed.

Two definitions of "the context" had drifted apart: the one in the system prompt
(what the model is shown) and the one in `_known_cells` (a hand-maintained list).
`_known_cells` now parses the rendered prompt itself, so there is one definition
and it is the text the model reads. Cross-sheet references stay rejected, which is
the case that matters.

This is the argument for keeping trajectories as an artifact rather than a demo.
A unit test with a hand-built context would have passed, because the hand-built
context would have contained whatever the guard already knew about.
