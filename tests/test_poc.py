"""Regression tests for the PoC detection + proof loop."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from poc import (  # noqa: E402
    detect_row_pattern_breaks,
    load_formulas,
    normalise,
    prove,
    rebase,
)

FIXTURE = ROOT / "tests" / "fixtures" / "quarterly_pl.xlsx"
TRUTH = ROOT / "tests" / "fixtures" / "quarterly_pl.truth.json"


@pytest.fixture(scope="module")
def truth() -> dict:
    return json.loads(TRUTH.read_text(encoding="utf-8"))


def test_normalise_collapses_same_pattern():
    """Cells doing the same thing in different columns must normalise identically."""
    assert normalise("=SUM(B8:B10)", row=11, col=2) == normalise("=SUM(C8:C10)", row=11, col=3)


def test_normalise_separates_different_pattern():
    """An off-by-one range must NOT collapse onto the majority shape."""
    assert normalise("=SUM(C8:C9)", row=11, col=3) != normalise("=SUM(C8:C10)", row=11, col=3)


def test_normalise_leaves_absolute_refs_anchored():
    """$-anchored references are absolute, so they must not become offsets."""
    assert normalise("=B8*$Z$1", row=11, col=2) == "=R[-3]C[0]*R1C26"


def test_rebase_translates_between_columns():
    assert rebase("=SUM(B8:B10)", 11, 2, 11, 3) == "=SUM(C8:C10)"


def test_detects_exactly_the_seeded_error(truth):
    formulas = load_formulas(str(FIXTURE))["P&L"]
    findings = detect_row_pattern_breaks(formulas)
    seeded = truth["seeded_errors"][0]

    assert len(findings) == 1, f"expected 1 finding, got {[f.cell for f in findings]}"
    assert findings[0].cell == seeded["cell"]
    assert findings[0].expected == seeded["expected_formula"]


def test_proof_shows_real_delta_and_propagation(truth):
    formulas = load_formulas(str(FIXTURE))["P&L"]
    finding = detect_row_pattern_breaks(formulas)[0]
    prove(str(FIXTURE), "P&L", finding, sorted(formulas))

    assert finding.proved, "a seeded error must produce a non-zero delta"
    # Rent is 3000/quarter; omitting it understates Total Opex by exactly that.
    assert finding.baseline_value == 27000
    assert finding.repaired_value == 30000
    assert finding.delta == 3000

    # And it must propagate: Operating Income was overstated by the same amount.
    impacted = dict((ref, (b, a)) for ref, b, a in finding.impacted)
    assert "C13" in impacted, "the error must be shown to reach Operating Income"
    before, after = impacted["C13"]
    assert before - after == 3000


def test_untouched_columns_are_not_flagged():
    """No false positives on the three correct quarters."""
    formulas = load_formulas(str(FIXTURE))["P&L"]
    flagged = {f.cell for f in detect_row_pattern_breaks(formulas)}
    assert flagged.isdisjoint({"B11", "D11", "E11", "B5", "C5", "D5", "E5"})
