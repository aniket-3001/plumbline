"""Run the deterministic audit over the seeded corpus and score it.

This is the baseline arm: structural detection plus recomputation proof, no model
involved. It is the floor every later arm has to beat, and running it standalone
is what makes the ablation in the changelog mean anything.

Usage:
    python scripts/run_baseline.py
    python scripts/run_baseline.py --strict   # unproved findings do not count
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="unproved findings do not count")
    ap.add_argument("--limit", type=int, default=0, help="only run N workbooks")
    ap.add_argument(
        "--max-proofs",
        type=int,
        default=40,
        help="cap proofs per workbook; 0 for no cap. Proving re-parses the workbook "
        "once per finding, so a 10,000-formula sheet can otherwise run for many minutes.",
    )
    ap.add_argument(
        "--min-peers",
        type=int,
        default=0,
        help="how many formula peers a row needs before a typed constant in it counts "
        "as a dead cell. 0 uses audit.MIN_ROW_PEERS. Sweep it to see the "
        "precision/recall trade rather than arguing about it.",
    )
    ap.add_argument(
        "--no-contiguous",
        action="store_true",
        help="drop the requirement that a dead cell's peers sit next to it. Scores the "
        "pre-contiguity detector; the exclusion list must be refreshed to match.",
    )
    ap.add_argument("--out", default="baseline.json", help="filename under results/")
    args = ap.parse_args()

    from plumbline.audit import MIN_ROW_PEERS, audit
    from plumbline.scoring import Scorecard, score

    manifests = sorted(SEEDED.glob("*.truth.json"))
    if not manifests:
        print("no seeded workbooks -- run scripts/seed_corpus.py first", file=sys.stderr)
        return 1
    if args.limit:
        manifests = manifests[: args.limit]

    print(f"auditing {len(manifests)} seeded workbooks"
          f"{' (strict: proof required)' if args.strict else ''}\n")

    total = Scorecard()
    rows, skipped = [], []
    started = time.time()

    for mpath in manifests:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        wb = SEEDED / manifest["seeded"]
        if not wb.exists():
            continue

        t0 = time.time()
        # Determinism was already established during screening; skip the re-check
        # so the timing reflects the audit itself.
        report = audit(wb, check_determinism=False, max_proofs=args.max_proofs,
                       min_peers=args.min_peers or MIN_ROW_PEERS,
                       contiguous=not args.no_contiguous)
        elapsed = time.time() - t0

        if report.skipped:
            skipped.append({"workbook": wb.name, "reason": report.skipped})
            print(f"  [skip] {wb.name[:52]:52} {report.skipped[:40]}")
            continue

        findings = [
            {"sheet": f.sheet, "cell": f.cell, "proved": f.proved, "detector": f.detector}
            for f in report.findings
        ]
        card = score(findings, manifest, require_proof=args.strict)
        total = total.merge(card)

        rows.append(
            {
                "workbook": wb.name,
                "formula_cells": report.formula_cells,
                "seeds": manifest["seed_count"],
                "findings": len(report.findings),
                "proved": len(report.proved),
                "seconds": round(elapsed, 2),
                "detected": report.detected,
                "proof_truncated": report.proof_truncated,
                "proof_deferred": report.proof_deferred,
                **card.to_dict(),
            }
        )
        print(
            f"  {wb.name[:46]:46} seeds {manifest['seed_count']:2d}  "
            f"found {card.true_positives:2d}  fp {card.false_positives:3d}  "
            f"proved {card.proved:2d}  "
            f"{('defer ' + str(report.proof_deferred)) if report.proof_deferred else '       '}"
            f"{elapsed:6.1f}s",
            flush=True,   # long run: progress must be visible while it happens
        )

        RESULTS.mkdir(exist_ok=True)
        (RESULTS / "baseline_partial.json").write_text(
            json.dumps({"summary": total.to_dict(), "workbooks": rows}, indent=2),
            encoding="utf-8",
        )

    summary = total.to_dict()
    summary |= {
        "workbooks": len(rows),
        "skipped": len(skipped),
        "strict": args.strict,
        "total_seconds": round(time.time() - started, 1),
    }

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / ("baseline_strict.json" if args.strict else args.out)
    out.write_text(
        json.dumps({"summary": summary, "workbooks": rows, "skipped": skipped}, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 66)
    print(f"  ARM: deterministic audit{' (strict)' if args.strict else ''}")
    print("=" * 66)
    print(f"  workbooks           {summary['workbooks']}  ({summary['skipped']} skipped)")
    print(f"  seeded errors       {total.true_positives + total.false_negatives}")
    print(f"  found               {total.true_positives}")
    print(f"  missed              {total.false_negatives}")
    print(f"  false positives     {total.false_positives}")
    print(f"  pre-existing hits   {total.pre_existing_hits}  (excluded from scoring)")
    print()
    print(f"  precision           {total.precision:.3f}")
    print(f"  recall              {total.recall:.3f}")
    print(f"  F1                  {total.f1:.3f}")
    print(f"  proof rate          {total.proof_rate:.3f}")
    print()
    print(f"  min row peers       {args.min_peers or MIN_ROW_PEERS}")
    print()
    print("  recall by difficulty:")
    for d in ("obvious", "realistic", "silent"):
        b = total.by_difficulty.get(d, {"found": 0, "missed": 0})
        n = b["found"] + b["missed"]
        if n:
            print(f"    {d:10} {total.recall_for(d):.3f}   ({b['found']}/{n})")
    deferred = sum(r.get("proof_deferred", 0) for r in rows)
    capped = sum(1 for r in rows if r.get("proof_truncated"))
    if deferred:
        print()
        print(f"  proof budget        {args.max_proofs} per workbook")
        print(f"  hit the budget      {capped} workbook(s), {deferred} finding(s) reported")
        print("                      but not proved. Detection is unaffected.")
    print(f"\n  wall clock          {summary['total_seconds']}s")
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
