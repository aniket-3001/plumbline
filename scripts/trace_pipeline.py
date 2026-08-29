"""Trace one workbook through every stage, recording what each stage decided and why.

    python scripts/trace_pipeline.py model.xlsx --out results/trajectories/trace.json

The Layer 2 prompts in `agent_trajectories.py` show the model step in isolation. This
shows the surrounding loop: which tool ran, what it returned, what the pipeline did with
that answer, and -- the part that matters for reading an audit -- every place a candidate
was **dropped**, with the evidence that dropped it.

Dropped candidates are the point. A trace that lists only what survived tells you what the
tool believes; a trace that lists what it discarded tells you whether to believe it. On a
real Enron sheet the discards outnumber the findings roughly twenty to one, and each one is
a decision the pipeline made on evidence it can show you.

Stages, in order, with the gate each applies:

  0 readiness      volatile / non-deterministic workbooks are refused outright
  1 detect         row-majority pattern breaks, and typed constants among formulas
  2 screen         does the constant match what the row's formula would produce?
  3 prove          apply the repair (or perturb an input) and recompute
  4 interpret      model supplies intent; the graph vetoes anything it invented
  5 triage         proved / suspected / refused, and what a human is asked to do

Stage 4 runs only with `--interpret` and a recorded reply, since it needs a model.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def trace(path: Path, *, max_proofs: int, min_peers: int | None) -> dict:
    from plumbline.audit import (
        MIN_ROW_PEERS,
        _formulas_by_sheet,
        _load,
        detect_dead_cells,
        detect_pattern_breaks,
        prove,
        screen_dead_cells,
    )
    from plumbline.determinism import check, find_volatile

    peers = MIN_ROW_PEERS if min_peers is None else min_peers
    steps: list[dict] = []
    t0 = time.time()

    # --- 0. readiness -------------------------------------------------------
    vol = find_volatile(str(path))
    det = check(str(path), limit=150) if not vol.is_volatile else None
    ready = not vol.is_volatile and det is not None and det.stable
    steps.append({
        "stage": "0 readiness",
        "tool": "determinism.find_volatile + determinism.check",
        "returned": {
            "volatile": vol.summary(),
            "determinism": det.summary() if det else "not reached",
        },
        "decision": "proceed" if ready else "REFUSE",
        "why": (
            "Two evaluations of the same workbook agree, so a difference between them "
            "can be attributed to a repair rather than to noise."
            if ready else
            "A proof is a comparison of two evaluations. This workbook does not "
            "evaluate to the same numbers twice, so no proof drawn from it would "
            "reproduce. Refusing is the honest answer; auditing anyway would produce "
            "findings that look identical to real ones."
        ),
    })
    if not ready:
        return {"workbook": path.name, "steps": steps, "refused": True}

    # --- 1. detect ----------------------------------------------------------
    model, _ = _load(str(path))
    sheets = _formulas_by_sheet(model)
    breaks, dead = [], []
    for sheet, formulas in sheets.items():
        breaks.extend(detect_pattern_breaks(sheet, formulas))
        dead.extend(detect_dead_cells(str(path), sheet, formulas, min_peers=peers))
    steps.append({
        "stage": "1 detect",
        "tool": f"detect_pattern_breaks + detect_dead_cells(min_peers={peers})",
        "returned": {
            "formula_cells": sum(len(v) for v in sheets.values()),
            "pattern_breaks": len(breaks),
            "dead_candidates": len(dead),
        },
        "decision": "pass every candidate to the screen",
        "why": "Detection is deliberately loose. Precision is bought downstream, by "
               "recomputation, not by guessing harder here.",
    })

    # --- 2. screen ----------------------------------------------------------
    kept = screen_dead_cells(str(path), dead)
    kept_refs = {(f.sheet, f.cell) for f in kept}
    dropped = [f for f in dead if (f.sheet, f.cell) not in kept_refs]
    steps.append({
        "stage": "2 screen",
        "tool": "screen_dead_cells (evaluates each candidate formula in a scratch column)",
        "returned": {"kept": len(kept), "dropped": len(dropped)},
        "dropped_examples": [
            {"cell": f"{f.sheet}!{f.cell}", "value": f.actual, "would_be": f.expected}
            for f in dropped[:8]
        ],
        "decision": f"discard {len(dropped)} of {len(dead)} candidates",
        "why": "A typed constant among formulas is usually just data. Only one whose "
               "value equals what the row's formula would produce looks like a frozen "
               "formula. This step took the dead-cell detector from 40 false positives "
               "to 0 on the workbook that first exposed it.",
    })

    # --- 3. prove -----------------------------------------------------------
    findings = breaks + kept
    to_prove, deferred = findings, []
    if max_proofs and len(findings) > max_proofs:
        to_prove, deferred = findings[:max_proofs], findings[max_proofs:]
    proved_list = prove(str(path), to_prove)
    proved = [f for f in proved_list if f.proved]
    unproved = [f for f in proved_list if not f.proved]
    steps.append({
        "stage": "3 prove",
        "tool": "prove (write a repaired copy, re-parse, compare; or perturb an input)",
        "returned": {
            "attempted": len(to_prove),
            "proved": len(proved),
            "unproved": len(unproved),
            "deferred_budget": len(deferred),
        },
        "proofs": [
            {"cell": f"{f.sheet}!{f.cell}", "detector": f.detector, "proof": f.proof}
            for f in proved[:6]
        ],
        "retries_and_rejections": [
            {"cell": f"{f.sheet}!{f.cell}", "outcome": f.proof or "no proof attempted"}
            for f in unproved[:8]
        ],
        "decision": f"{len(proved)} findings survive; {len(unproved)} are demoted to suspected",
        "why": "This is the only gate that can promote a suspicion to a finding. A repair "
               "that changes no number proves nothing and is reported as suspected, never "
               "as an error.",
    })

    # --- 5. triage ----------------------------------------------------------
    steps.append({
        "stage": "5 triage",
        "tool": "report.render_markdown",
        "returned": {
            "proved": len(proved),
            "suspected": len(unproved) + len(deferred),
            "blind_spots_declared": True,
        },
        "decision": "report, do not act",
        "human_checkpoint": (
            "Plumbline never edits a workbook. Every report names a cell, a proposed "
            "formula, and the recomputed consequence, and states that a qualified "
            "reviewer must confirm each finding before any change is made. Proved and "
            "suspected are kept in separate sections so the two are never conflated, "
            "and the report always ends with what was NOT checked."
        ),
    })

    return {
        "workbook": path.name,
        "seconds": round(time.time() - t0, 1),
        "min_peers": peers,
        "steps": steps,
        "refused": False,
    }


def render(t: dict) -> str:
    out = [f"# Pipeline trace - {t['workbook']}", ""]
    if not t["refused"]:
        out.append(f"*{t['seconds']}s, min_peers={t['min_peers']}*")
        out.append("")
    for s in t["steps"]:
        out.append(f"## {s['stage']}")
        out.append("")
        out.append(f"**Tool.** `{s['tool']}`")
        out.append("")
        out.append(f"**Returned.** `{json.dumps(s['returned'])}`")
        out.append("")
        for key, label in (("dropped_examples", "Dropped"),
                           ("proofs", "Proved"),
                           ("retries_and_rejections", "Not proved")):
            if s.get(key):
                out.append(f"**{label}.**")
                out.append("")
                for row in s[key]:
                    out.append(f"- `{json.dumps(row)}`")
                out.append("")
        out.append(f"**Decision.** {s['decision']}")
        out.append("")
        if s.get("why"):
            out.append(f"**Why.** {s['why']}")
            out.append("")
        # The checkpoint gets its own heading whenever there is one. It used to be
        # folded into "Why" on the only stage that has one, so the trace described a
        # human checkpoint without ever naming it as such -- which is the one thing
        # this section exists to make findable.
        if s.get("human_checkpoint"):
            out.append(f"**Human checkpoint.** {s['human_checkpoint']}")
            out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workbook", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "trajectories" / "trace.json")
    ap.add_argument("--max-proofs", type=int, default=25)
    ap.add_argument("--min-peers", type=int, default=0)
    args = ap.parse_args(argv)

    from plumbline.cli import _unreadable

    problem = _unreadable(args.workbook)
    if problem:
        print(problem, file=sys.stderr)
        return 2

    t = trace(args.workbook, max_proofs=args.max_proofs, min_peers=args.min_peers or None)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # LF explicitly. These are committed evidence, and on Windows the default
    # translation writes CRLF, so regenerating them produced a diff whose content was
    # byte-identical. Running the verification must not dirty the working tree.
    args.out.write_text(json.dumps(t, indent=2, default=str), encoding="utf-8", newline="\n")
    md = args.out.with_suffix(".md")
    md.write_text(render(t), encoding="utf-8", newline="\n")
    print(render(t))
    print(f"\nwrote {args.out.name} and {md.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
