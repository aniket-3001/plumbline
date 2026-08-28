"""Tests for the scoring rules that decide whether the headline number is honest."""

from __future__ import annotations

import pytest

from plumbline.scoring import Scorecard, score

MANIFEST = {
    "seeds": [
        {"sheet": "S", "cell": "A1", "difficulty": "realistic"},
        {"sheet": "S", "cell": "A2", "difficulty": "silent"},
        {"sheet": "S", "cell": "A3", "difficulty": "obvious"},
    ],
    "pre_existing_findings": ["S!Z9"],
}


def f(cell, proved=True, sheet="S"):
    return {"sheet": sheet, "cell": cell, "proved": proved}


class TestScoring:
    def test_counts_hits_and_misses(self):
        card = score([f("A1"), f("A2")], MANIFEST)
        assert card.true_positives == 2
        assert card.false_negatives == 1

    def test_pre_existing_findings_are_excluded_not_penalised(self):
        """A real anomaly already in the workbook is not our false positive.

        Scoring it as one would understate precision and would reward a detector
        that stays quiet about genuine problems.
        """
        card = score([f("Z9")], MANIFEST)
        assert card.false_positives == 0
        assert card.pre_existing_hits == 1

    def test_genuine_false_positive_is_counted(self):
        card = score([f("B7")], MANIFEST)
        assert card.false_positives == 1

    def test_duplicate_findings_count_once(self):
        """Two detectors agreeing on a cell is one finding, not two."""
        card = score([f("A1"), f("A1")], MANIFEST)
        assert card.true_positives == 1

    def test_proof_rate_is_separate_from_recall(self):
        """Finding a cell and proving it are different claims."""
        card = score([f("A1", proved=True), f("A3", proved=False)], MANIFEST)
        assert card.true_positives == 2
        assert card.proved == 1
        assert card.proof_rate == 0.5

    def test_require_proof_demotes_unproved_findings_to_misses(self):
        card = score([f("A1", proved=True), f("A3", proved=False)], MANIFEST, require_proof=True)
        assert card.true_positives == 1
        assert card.false_negatives == 2

    def test_recall_is_split_by_difficulty(self):
        """A blended number would hide a detector that only catches loud breakage."""
        card = score([f("A3")], MANIFEST)
        assert card.recall_for("obvious") == 1.0
        assert card.recall_for("realistic") == 0.0
        assert card.recall_for("silent") == 0.0

    def test_empty_findings_scores_zero_not_crash(self):
        card = score([], MANIFEST)
        assert card.recall == 0.0
        assert card.precision == 0.0
        assert card.f1 == 0.0
        assert card.false_negatives == 3


class TestScorecardMath:
    def test_perfect_score(self):
        card = score([f("A1"), f("A2"), f("A3")], MANIFEST)
        assert card.precision == 1.0
        assert card.recall == 1.0
        assert card.f1 == 1.0

    def test_f1_is_the_harmonic_mean(self):
        card = Scorecard(true_positives=1, false_positives=1, false_negatives=3)
        assert card.precision == 0.5
        assert card.recall == 0.25
        assert card.f1 == pytest.approx(2 * 0.5 * 0.25 / 0.75)

    def test_merge_sums_everything(self):
        a = score([f("A1")], MANIFEST)
        b = score([f("A2")], MANIFEST)
        merged = a.merge(b)
        assert merged.true_positives == 2
        assert merged.by_difficulty["realistic"]["found"] == 1
        assert merged.by_difficulty["silent"]["found"] == 1
