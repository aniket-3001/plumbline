"""Tests for the hard case: a subtotal that is correct today and dead tomorrow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from poc import detect_row_pattern_breaks, load_formulas  # noqa: E402
from sensitivity_probe import find_dead_cells, probe  # noqa: E402

HARD = ROOT / "tests" / "fixtures" / "quarterly_pl_hardcoded.xlsx"
HARD_TRUTH = ROOT / "tests" / "fixtures" / "quarterly_pl_hardcoded.truth.json"
CLEAN = ROOT / "tests" / "fixtures" / "quarterly_pl.xlsx"


@pytest.fixture(scope="module")
def truth() -> dict:
    return json.loads(HARD_TRUTH.read_text(encoding="utf-8"))


def test_value_checks_cannot_see_it():
    """The premise of the hard case: today, the number is simply correct.

    If this ever fails, the fixture has stopped being hard and the evaluation
    result built on it is worthless.
    """
    from xlcalculator import Evaluator, ModelCompiler

    ev = Evaluator(ModelCompiler().read_and_parse_archive(str(HARD)))
    # 21000 Salaries + 6000 Marketing + 3000 Rent
    assert float(ev.evaluate("P&L!C11")) == 30000
    # and Operating Income therefore ties too
    assert float(ev.evaluate("P&L!C13")) == 42000


def test_formula_pattern_detector_alone_misses_it():
    """The off-by-one detector only looks at formula cells, so a constant is invisible to it.

    This is why the probe exists. Documenting it as a test keeps the two
    techniques honestly separated in the evaluation.
    """
    formulas = load_formulas(str(HARD))["P&L"]
    flagged = {f.cell for f in detect_row_pattern_breaks(formulas)}
    assert "C11" not in flagged


def test_probe_finds_and_proves_the_dead_cell(truth):
    seeded = truth["seeded_errors"][0]
    suspects = find_dead_cells(str(HARD), "P&L")

    assert len(suspects) == 1, f"expected 1 suspect, got {[s['cell'] for s in suspects]}"
    assert suspects[0]["cell"] == seeded["cell"]
    assert suspects[0]["expected_formula"] == seeded["expected_formula"]

    result = probe(str(HARD), "P&L", suspects[0])
    assert result["probed"]
    assert result["proved_dead"], "the hardcoded total must be proved disconnected"
    assert not result["suspect_moved"], "a dead cell must not respond to its inputs"
    assert result["control_moved"], "the control arm must respond, or the proof is vacuous"
    # Perturbing one input by +1000 must move the live formula by exactly +1000.
    assert result["divergence"] == 1000


def test_no_false_positive_on_clean_workbook():
    """The workbook with no hardcoded cells must yield no suspects."""
    assert find_dead_cells(str(CLEAN), "P&L") == []


def test_proof_requires_a_responsive_control():
    """proved_dead must be False whenever the control arm did not move.

    Without this, a cell whose inputs happen not to matter would be reported as
    dead -- a false positive dressed up as a proof.
    """
    suspects = find_dead_cells(str(HARD), "P&L")
    result = probe(str(HARD), "P&L", suspects[0])
    assert result["proved_dead"] == ((not result["suspect_moved"]) and result["control_moved"])
