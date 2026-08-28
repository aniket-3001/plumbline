"""Seed the evaluation corpus with errors and write the ground-truth manifests.

Usage:
    python scripts/seed_corpus.py --seeds-per-workbook 4
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import warnings
from collections import Counter
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

EVAL = ROOT / "data" / "eval_corpus"
SEEDED = ROOT / "data" / "seeded"
RESULTS = ROOT / "results"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-per-workbook", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    from plumbline.seeding import seed_workbook

    books = sorted(p for p in EVAL.glob("*.xlsx"))
    if not books:
        print("no workbooks in data/eval_corpus -- run build_eval_corpus.py", file=sys.stderr)
        return 1

    SEEDED.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    manifests, skipped = [], []
    by_class, by_difficulty = Counter(), Counter()

    print(f"seeding {len(books)} workbooks (rng seed {args.seed})\n")
    for book in books:
        try:
            manifest = seed_workbook(book, SEEDED, rng, max_seeds=args.seeds_per_workbook)
        except Exception as exc:  # noqa: BLE001
            skipped.append({"workbook": book.name, "reason": f"{type(exc).__name__}: {exc}"})
            print(f"  [skip] {book.name[:58]:58} {type(exc).__name__}")
            continue
        if not manifest:
            skipped.append({"workbook": book.name, "reason": "no viable seed sites"})
            print(f"  [skip] {book.name[:58]:58} no viable seed sites")
            continue

        manifests.append(manifest)
        for s in manifest["seeds"]:
            by_class[s["panko_class"]] += 1
            by_difficulty[s["difficulty"]] += 1
        classes = "".join(sorted({s["panko_class"][0].upper() for s in manifest["seeds"]}))
        print(f"  [ok]   {book.name[:58]:58} {manifest['seed_count']} seeds  {classes}")

    total = sum(by_class.values())
    summary = {
        "workbooks_seeded": len(manifests),
        "workbooks_skipped": len(skipped),
        "total_seeds": total,
        "by_panko_class": dict(by_class),
        "by_difficulty": dict(by_difficulty),
        "rng_seed": args.seed,
        "seeds_per_workbook_cap": args.seeds_per_workbook,
        "skipped": skipped,
        "manifests": manifests,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "seeding.json").write_text(json.dumps(summary, indent=2, default=str), "utf-8")

    print(f"\nseeded {len(manifests)} workbooks, {total} errors, skipped {len(skipped)}")
    print("\nby Panko class:")
    for k, v in by_class.most_common():
        print(f"  {k:14} {v:4d}  ({100 * v / total:4.1f}%)")
    print("\nby difficulty:")
    for k in ("obvious", "realistic", "silent"):
        v = by_difficulty.get(k, 0)
        print(f"  {k:14} {v:4d}  ({100 * v / total:4.1f}%)")
    print(f"\nwrote {(RESULTS / 'seeding.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
