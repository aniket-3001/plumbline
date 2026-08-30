"""The mandatory baseline-vs-solution comparison, as three arms on identical cases.

    python scripts/run_arms.py --max-proofs 25

The brief requires a simple baseline representing "a reasonable basic way to handle
the task before your solution", scored on the same cases with the same method, and a
comparison showing the size of the improvement. These are those arms.

  naive     Detectors only, and without any of this project's ideas in them: a
            typed constant is flagged whenever its row holds formulas of one shape,
            wherever in the row they sit. Everything found is reported as found.
  block     Adds `_peers_in_block`: the peers must belong to the same block of the
            row as the candidate, so a data column is no longer compared against a
            formula block elsewhere in its row.
  screened  Adds the scratch-column screen: a typed constant is only a dead cell if
            its value equals what the row's formula would produce.
  full      Adds proof by recomputation: apply the repair and show the numbers move,
            or perturb an input and show a frozen cell fails to respond. A finding
            that cannot be demonstrated is demoted to *suspected* and reported in a
            separate section.

**On fairness.** The temptation with a baseline is to build a strawman, and a
strawman would make every number here worthless. So the naive arm is not a worse
tool -- it is *this* tool with the two contributions removed. Same detectors, same
corpus, same seeds, same scorer. The delta between arms is therefore attributable to
one named contribution each, rather than to a comparison rigged at the start.

An earlier version of this file got that wrong in a way worth recording: `naive`
called `detect_dead_cells` at its defaults, so once block membership landed in the
detector the baseline silently inherited it, and its false positives fell from 4,420
to 109. The baseline was quietly improving as the tool improved, which is the exact
mechanism that makes a comparison flattering and meaningless.

**Each arm computes its own exclusion list**, in-process, at that arm's settings.
Pre-existing findings are excluded because Enron's files are full of anomalies with
no ground truth; an arm that detects more of them must not be charged for the extra.
Computing the list per arm rather than refreshing the shared manifests also means
this script never mutates state another run might be reading.

The naive arm is also a fair description of what a rule-based auditor does: flag
structural anomalies and hand the analyst a list. That is the "manual process people
use today" shape from the brief, and the documented failure of the commercial tools.

**`full` is scored the way the product actually behaves**, which is not the way I first
scored it. The first version required a proof for a finding to count, on the reasoning
that the product promises recomputation behind everything. That was wrong twice over.
The product does not discard unproved findings -- it demotes them to a *Suspected*
section, clearly separated from proved ones, and shows them to a human. And the proof
budget caps proofs per workbook, so strict scoring measured the budget rather than the
gate: recall fell 0.868 -> 0.604 and F1 0.929 -> 0.753, almost all of it findings that
were never *disproved*, only never *reached*.

So proof rate is reported as its own row instead. This makes the honest shape of the
result visible: **proof does not improve F1, and is not supposed to.** It changes what
the analyst can trust about each finding, which is a property F1 cannot express. The
screen is what buys precision; the proof is what makes a finding checkable.
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

SEEDED = ROOT / "data" / "seeded"
RESULTS = ROOT / "results"

ARMS = ("naive", "block", "screened", "full")

#: `naive` runs the detector as it was before block membership existed.
CONTIGUOUS = {"naive": False, "block": True, "screened": True, "full": True}


def run_arm(arm: str, manifests: list[Path], *, max_proofs: int) -> dict:
    """One arm over every workbook. Only `arm` changes between calls."""
    from plumbline.audit import (
        AXES,
        MIN_ROW_PEERS,
        _formulas_by_sheet,
        _load,
        detect,
        prove,
        screen_dead_cells,
    )
    from plumbline.scoring import Scorecard, score
    from plumbline.seeding import pre_existing_findings

    total, rows = Scorecard(), []
    started = time.time()
    print(f"\n{'=' * 66}\n  ARM: {arm}\n{'=' * 66}", flush=True)

    for mpath in manifests:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        wb = SEEDED / manifest["seeded"]
        if not wb.exists():
            continue

        t0 = time.time()
        contiguous = CONTIGUOUS[arm]
        model, _ = _load(str(wb))
        sheets = _formulas_by_sheet(model)

        # Through `audit.detect`, not a private copy of it. Calling the detectors
        # directly is how this file silently went on measuring the row-only tool
        # after the shipped one gained a column pass -- the mandatory comparison
        # then described a product that does not exist.
        findings, dead = detect(
            str(wb), sheets, min_peers=MIN_ROW_PEERS, contiguous=contiguous, axes=AXES
        )

        # The contributions, added one at a time.
        findings += dead if arm in ("naive", "block") else screen_dead_cells(str(wb), dead)
        if arm == "full":
            head = findings[:max_proofs] if max_proofs else findings
            findings = prove(str(wb), head) + findings[len(head):]

        elapsed = time.time() - t0
        payload = [
            {"sheet": f.sheet, "cell": f.cell, "proved": f.proved, "detector": f.detector}
            for f in findings
        ]
        # Every arm is scored identically, matching what the product does: an unproved
        # finding is still reported, in a separate section, for a human to judge.
        # This arm's own exclusion list, so a more sensitive arm is not charged for
        # the extra pre-existing anomalies it correctly finds.
        source = Path(manifest["source"])
        scoped = dict(manifest)
        if source.exists():
            scoped["pre_existing_findings"] = pre_existing_findings(
                source, min_peers=MIN_ROW_PEERS, contiguous=contiguous
            )
        card = score(payload, scoped, require_proof=False)
        total = total.merge(card)
        rows.append({
            "workbook": wb.name,
            "seeds": manifest["seed_count"],
            "reported": len(payload),
            "seconds": round(elapsed, 2),
            **card.to_dict(),
        })
        print(f"  {wb.name[:46]:46} reported {len(payload):3d}  "
              f"tp {card.true_positives:2d}  fp {card.false_positives:3d}  {elapsed:5.1f}s",
              flush=True)

    summary = total.to_dict()
    summary["arm"] = arm
    summary["workbooks"] = len(rows)
    summary["total_seconds"] = round(time.time() - started, 1)
    summary["reported_total"] = sum(r["reported"] for r in rows)
    return {"summary": summary, "workbooks": rows}


def table(results: dict[str, dict]) -> str:
    """The comparison the brief asks for: same metric, every arm, same cases."""
    def g(arm, key):
        return results[arm]["summary"][key]

    lines = [
        "| Metric | naive (baseline) | + block | + screen | + proof (shipped) |",
        "|---|---|---|---|---|",
    ]
    for label, key, fmt in (
        ("Precision", "precision", "{:.3f}"),
        ("Recall", "recall", "{:.3f}"),
        ("F1", "f1", "{:.3f}"),
        ("True positives", "true_positives", "{}"),
        ("False positives", "false_positives", "{}"),
        ("Cells reported to the analyst", "reported_total", "{}"),
        ("Findings carrying a proof", "proved", "{}"),
    ):
        cells = " | ".join(fmt.format(g(a, key)) for a in ARMS)
        lines.append(f"| {label} | {cells} |")
    for d in ("obvious", "realistic", "silent"):
        cells = " | ".join(f"{results[a]['summary']['recall_by_difficulty'][d]:.3f}" for a in ARMS)
        lines.append(f"| Recall, *{d}* | {cells} |")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--max-proofs", type=int, default=25)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    manifests = sorted(SEEDED.glob("*.truth.json"))
    if not manifests:
        print("no seeded workbooks -- run scripts/seed_corpus.py first", file=sys.stderr)
        return 1
    if args.limit:
        manifests = manifests[: args.limit]

    results = {a: run_arm(a, manifests, max_proofs=args.max_proofs) for a in ARMS}

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "arms.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    md = table(results)
    (RESULTS / "arms.md").write_text(md + "\n", encoding="utf-8")

    print(f"\n{'=' * 66}\n  COMPARISON\n{'=' * 66}")
    print(md)
    print("\nwrote results/arms.json and results/arms.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
