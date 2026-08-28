"""Score detector output against seeded ground truth.

The rules here decide whether the headline number is honest, so each one is
written down with its reasoning rather than buried in an expression.

**Pre-existing findings are excluded, not counted as false positives.** Real Enron
workbooks already contain real anomalies. A detector that flags one has arguably
done its job; calling that an error would understate precision and would also
reward a detector that stays quiet. They are reported in their own column so the
number stays visible instead of vanishing.

**Results are split by difficulty.** A blended figure lets a detector that only
catches cells that broke loudly (`obvious`) look identical to one that catches
silent corruption (`realistic`, `silent`) -- and only the second is worth having.

**Proof rate is tracked separately from recall.** Finding a cell and proving it
are different claims, and Plumbline's whole promise is the second one. A finding
without a proof is a suspicion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DIFFICULTIES = ("obvious", "realistic", "silent")


@dataclass
class Scorecard:
    """One arm's performance on one workbook, or summed across many."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    pre_existing_hits: int = 0
    proved: int = 0
    by_difficulty: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def proof_rate(self) -> float:
        """Of the seeded errors we found, how many did we actually prove?"""
        return self.proved / self.true_positives if self.true_positives else 0.0

    def recall_for(self, difficulty: str) -> float:
        d = self.by_difficulty.get(difficulty)
        if not d:
            return 0.0
        denom = d["found"] + d["missed"]
        return d["found"] / denom if denom else 0.0

    def merge(self, other: "Scorecard") -> "Scorecard":
        merged = Scorecard(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
            pre_existing_hits=self.pre_existing_hits + other.pre_existing_hits,
            proved=self.proved + other.proved,
        )
        for key in set(self.by_difficulty) | set(other.by_difficulty):
            a = self.by_difficulty.get(key, {"found": 0, "missed": 0})
            b = other.by_difficulty.get(key, {"found": 0, "missed": 0})
            merged.by_difficulty[key] = {
                "found": a["found"] + b["found"],
                "missed": a["missed"] + b["missed"],
            }
        return merged

    def to_dict(self) -> dict:
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "pre_existing_hits": self.pre_existing_hits,
            "proved": self.proved,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "proof_rate": round(self.proof_rate, 4),
            "recall_by_difficulty": {
                d: round(self.recall_for(d), 4) for d in DIFFICULTIES if d in self.by_difficulty
            },
            "by_difficulty": self.by_difficulty,
        }


def score(
    findings: list[dict],
    manifest: dict,
    *,
    require_proof: bool = False,
) -> Scorecard:
    """Compare one arm's findings against one workbook's ground truth.

    `findings` are dicts with at least `sheet`, `cell`, and optionally `proved`.
    `require_proof` models the strict contract: an unproved finding is not a
    finding at all, which is how Plumbline itself is meant to behave.
    """
    seeds = {(s["sheet"], s["cell"]): s for s in manifest["seeds"]}
    pre_existing = {
        tuple(ref.split("!", 1)) for ref in manifest.get("pre_existing_findings", []) if "!" in ref
    }

    card = Scorecard()
    for d in DIFFICULTIES:
        card.by_difficulty.setdefault(d, {"found": 0, "missed": 0})

    seen: set[tuple[str, str]] = set()
    for finding in findings:
        key = (finding["sheet"], finding["cell"])
        if require_proof and not finding.get("proved", False):
            continue
        if key in seen:
            continue  # two detectors agreeing is one finding, not two
        seen.add(key)

        if key in seeds:
            card.true_positives += 1
            if finding.get("proved"):
                card.proved += 1
        elif key in pre_existing:
            # An anomaly that was already in the workbook. Not ours to score.
            card.pre_existing_hits += 1
        else:
            card.false_positives += 1

    for key, seed in seeds.items():
        difficulty = seed.get("difficulty", "realistic")
        bucket = card.by_difficulty.setdefault(difficulty, {"found": 0, "missed": 0})
        if key in seen:
            bucket["found"] += 1
        else:
            card.false_negatives += 1
            bucket["missed"] += 1

    return card


def summarise(cards: dict[str, list[Scorecard]]) -> dict:
    """Roll per-workbook scorecards up into one row per arm."""
    return {
        arm: (
            [c for c in per_workbook] and
            _fold(per_workbook).to_dict() | {"workbooks": len(per_workbook)}
        )
        for arm, per_workbook in cards.items()
    }


def _fold(cards: list[Scorecard]) -> Scorecard:
    total = Scorecard()
    for c in cards:
        total = total.merge(c)
    return total
