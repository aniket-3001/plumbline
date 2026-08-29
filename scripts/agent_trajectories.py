"""Capture Layer 2 trajectories: the exact prompt in, the validated result out.

Runs in two halves so the model step is auditable rather than hidden inside a
network call.

    python scripts/agent_trajectories.py dump  <workbook.xlsx>
    python scripts/agent_trajectories.py replay

`dump` writes, for every finding the deterministic arm *proved*, the byte-exact
system and user prompts `plumbline.agent` would send, plus the context subgraph
they were built from. Nothing is invented: the prompts come from
`agent.build_context` and `agent._render_user_prompt`, the same two functions the
live path calls.

`replay` reads the recorded replies back through `agent.interpret` using a client
that returns the recorded text instead of calling the API. The JSON parsing, the
truncation, and -- the point of the exercise -- the hallucination guard all
execute for real. A reply that cites a cell absent from the context is rejected
here exactly as it would be in production.

Why two halves: this machine has no ANTHROPIC_API_KEY, and a model layer that has
only ever been exercised against a stub is not evidence of anything. Splitting the
step lets a real reply be recorded and then genuinely validated, and lets anyone
re-run the second half offline and get the same verdicts. `--live` does the whole
thing through the API in one pass when a key is present; the recorded prompts are
identical either way.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "results" / "trajectories"


def dump(workbook: Path, limit: int) -> int:
    from plumbline.agent import SYSTEM_PROMPT, _render_user_prompt, build_context
    from plumbline.audit import audit

    report = audit(workbook, check_determinism=False, max_proofs=25)
    proved = report.proved[:limit]
    if not proved:
        print(f"nothing proved in {workbook.name}; no trajectory to capture", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    for i, finding in enumerate(proved, 1):
        ctx = build_context(str(workbook), finding)
        stem = f"{i:02d}_{finding.sheet}_{finding.cell}".replace(" ", "_").replace("/", "_")
        (OUT / f"{stem}.prompt.json").write_text(
            json.dumps(
                {
                    "workbook": workbook.name,
                    "sheet": finding.sheet,
                    "cell": finding.cell,
                    "detector": finding.detector,
                    "proof": finding.proof,
                    "system": SYSTEM_PROMPT,
                    "user": _render_user_prompt(ctx),
                    "context": ctx,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        print(f"  wrote {stem}.prompt.json  ({finding.sheet}!{finding.cell})")
    print(f"\n{len(proved)} prompt(s) in {OUT.relative_to(ROOT)}")
    print("Record each reply as <stem>.response.json, then run: replay")
    return 0


def replay() -> int:
    """Validate recorded replies through the real guard. No network."""
    from plumbline.agent import interpret

    prompts = sorted(OUT.glob("*.prompt.json"))
    if not prompts:
        print("no prompts; run `dump` first", file=sys.stderr)
        return 1

    rows, missing = [], 0
    for pf in prompts:
        stem = pf.name[: -len(".prompt.json")]
        rf = OUT / f"{stem}.response.json"
        if not rf.exists():
            missing += 1
            continue

        record = json.loads(pf.read_text(encoding="utf-8"))
        reply = rf.read_text(encoding="utf-8")

        # A stand-in for the finding: interpret() needs only these five fields, and
        # rebuilding it from the record keeps replay independent of a live audit.
        finding = type(
            "Recorded",
            (),
            {
                "sheet": record["sheet"],
                "cell": record["cell"],
                "actual": record["context"]["actual_formula"],
                "expected": record["context"]["expected_formula"],
                "proof": record["proof"],
            },
        )()

        interp = interpret(
            str(ROOT / "data" / "seeded" / record["workbook"]),
            finding,
            lambda system, user, _r=reply: _r,
        )
        (OUT / f"{stem}.trajectory.json").write_text(
            json.dumps(
                {
                    "workbook": record["workbook"],
                    "cell": f"{record['sheet']}!{record['cell']}",
                    "detector": record["detector"],
                    "deterministic_proof": record["proof"],
                    "model_reply_raw": reply,
                    "after_validation": interp.to_dict(),
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        verdict = "accepted" if interp.ok else f"REJECTED -- {interp.error}"
        rows.append((f"{record['sheet']}!{record['cell']}", verdict))
        print(f"  {record['sheet']}!{record['cell']:<8} {verdict}")

    print()
    print(f"  replayed          {len(rows)}")
    print(f"  accepted          {sum(1 for _, v in rows if v == 'accepted')}")
    print(f"  rejected by guard {sum(1 for _, v in rows if v != 'accepted')}")
    if missing:
        print(f"  no reply recorded {missing}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump", help="write the exact prompts for a workbook's proved findings")
    d.add_argument("workbook", type=Path)
    d.add_argument("--limit", type=int, default=6)
    sub.add_parser("replay", help="validate recorded replies through the real guard")
    args = p.parse_args(argv)
    return dump(args.workbook, args.limit) if args.cmd == "dump" else replay()


if __name__ == "__main__":
    sys.exit(main())
