"""Tests for the error-seeding harness.

These matter more than they look. The seeded workbooks *are* the ground truth, so
a bug here does not fail loudly -- it silently produces a benchmark that measures
something other than what we claim.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plumbline  # noqa: F401,E402
from plumbline.seeding import (  # noqa: E402
    Seed,
    _majority_rows,
    _shift_first_reference,
    _shift_range_end,
    _swap_function,
    seed_workbook,
)

CLEAN = ROOT / "tests" / "fixtures" / "quarterly_pl.xlsx"


class TestMutations:
    def test_shift_range_end_drops_one_row(self):
        assert _shift_range_end("=SUM(B8:B10)", -1) == "=SUM(B8:B9)"

    def test_shift_range_end_returns_none_without_a_range(self):
        assert _shift_range_end("=B8*2", -1) is None

    def test_shift_range_end_refuses_to_go_above_row_one(self):
        assert _shift_range_end("=SUM(A1:A1)", -1) is None

    def test_shift_reference_moves_a_plain_reference(self):
        assert _shift_first_reference("=D19", -1) == "=D18"
        assert _shift_first_reference("=D19*2", -1) == "=D18*2"

    def test_shift_reference_leaves_ranges_alone(self):
        """Ranges belong to the other mutation, so the classes stay distinct."""
        assert _shift_first_reference("=SUM(B8:B10)", -1) is None

    def test_shift_reference_respects_absolute_anchors(self):
        """A $-anchored row was anchored on purpose; moving it is a different error."""
        assert _shift_first_reference("=D$19", -1) is None

    def test_swap_function(self):
        assert _swap_function("=SUM(B8:B10)", "SUM", "AVERAGE") == "=AVERAGE(B8:B10)"
        assert _swap_function("=B8-B9", "SUM", "AVERAGE") is None


class TestMajorityRows:
    def test_requires_unanimity(self):
        """A row containing a deviation is not a safe place to seed.

        Row 11 of the clean fixture holds the original off-by-one, so it must not
        be offered as a seeding site -- the majority has to survive the seed.
        """
        from poc import load_formulas

        rows = _majority_rows(load_formulas(str(CLEAN))["P&L"])
        assert 5 in rows and 13 in rows   # unanimous rows
        assert 11 not in rows             # already contains C11's deviation

    def test_ignores_rows_with_too_few_members(self):
        assert _majority_rows({"A1": "=B1", "A2": "=B2"}) == {}


class TestDifficulty:
    @pytest.mark.parametrize(
        "panko,changed,value,expected",
        [
            ("hardcoding", False, 100, "silent"),
            ("mechanical", True, 0, "obvious"),
            ("mechanical", True, None, "obvious"),
            ("mechanical", True, "<error:X>", "obvious"),
            ("mechanical", True, 45.75, "realistic"),
            ("logic", True, 1234, "realistic"),
        ],
    )
    def test_classification(self, panko, changed, value, expected):
        seed = Seed(
            seed_id="t",
            panko_class=panko,
            sheet="S",
            cell="A1",
            original_formula="=B1",
            seeded_formula="=B2",
            description="",
            detectable_by=[],
            seeded_value=value,
            value_changed=changed,
        )
        assert seed.classify_difficulty() == expected


class TestSeedWorkbook:
    def test_produces_a_manifest_and_a_file(self, tmp_path):
        manifest = seed_workbook(CLEAN, tmp_path, random.Random(7), max_seeds=3)
        assert manifest is not None
        assert (tmp_path / CLEAN.name).exists()
        assert manifest["seed_count"] == len(manifest["seeds"]) > 0

    def test_records_pre_existing_findings_separately(self, tmp_path):
        """The clean fixture already contains C11. A detector hitting it is not a
        false positive, and conflating the two would understate precision."""
        manifest = seed_workbook(CLEAN, tmp_path, random.Random(7), max_seeds=3)
        assert "P&L!C11" in manifest["pre_existing_findings"]

    def test_every_seed_is_verified_to_have_done_something(self, tmp_path):
        """A seed that changes nothing is noise in the ground truth, not an error.

        Hardcoding is the deliberate exception: it is defined by being identical
        today and only diverging later.
        """
        manifest = seed_workbook(CLEAN, tmp_path, random.Random(7), max_seeds=3)
        for seed in manifest["seeds"]:
            if seed["panko_class"] == "hardcoding":
                assert seed["value_changed"] is False
                assert seed["difficulty"] == "silent"
            else:
                assert seed["value_changed"] is True

    def test_seeded_file_matches_the_manifest(self, tmp_path):
        """The file on disk must contain exactly what the manifest claims."""
        from openpyxl import load_workbook

        manifest = seed_workbook(CLEAN, tmp_path, random.Random(7), max_seeds=3)
        wb = load_workbook(tmp_path / CLEAN.name)
        for seed in manifest["seeds"]:
            actual = wb[seed["sheet"]][seed["cell"]].value
            expected = seed["seeded_formula"]
            if isinstance(expected, str):
                assert actual == expected
            else:
                assert float(actual) == pytest.approx(float(expected))

    def test_is_deterministic_for_a_given_seed(self, tmp_path):
        """Same RNG seed, same injected errors -- or the evaluation is not reproducible."""
        a = seed_workbook(CLEAN, tmp_path / "a", random.Random(11), max_seeds=3)
        b = seed_workbook(CLEAN, tmp_path / "b", random.Random(11), max_seeds=3)
        assert [(s["cell"], s["panko_class"]) for s in a["seeds"]] == [
            (s["cell"], s["panko_class"]) for s in b["seeds"]
        ]


class TestPreExistingFindings:
    """The benchmark's own accounting, which is easy to get wrong quietly."""

    @staticmethod
    def _messy_workbook(path):
        """A row of `=Bn+1` counters with a typed constant spliced in -- the exact
        shape of the real hardcoding found across the Enron corpus."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "S"
        ws["A1"] = 1
        for col in range(2, 9):
            ws.cell(row=1, column=col, value=f"={chr(64 + col - 1)}1+1")
        ws["E1"] = 5          # dead cell: the right value, but typed, not computed
        ws["A3"] = 10
        for col in range(2, 9):
            ws.cell(row=3, column=col, value=f"=SUM($A$3:{chr(64 + col - 1)}3)")
        ws["F3"] = "=SUM($A$3:D3)"   # pattern break
        wb.save(path)
        return path

    def test_finds_dead_cells_not_only_pattern_breaks(self, tmp_path):
        from plumbline.seeding import pre_existing_findings

        path = self._messy_workbook(tmp_path / "messy.xlsx")
        found = pre_existing_findings(path)
        # Both detectors must contribute. Running only the pattern-break detector
        # made every pre-existing dead cell surface later as a false positive.
        assert "S!E1" in found, f"dead cell missed: {found}"
        assert "S!F3" in found, f"pattern break missed: {found}"

    def test_agrees_cell_for_cell_with_what_the_audit_reports(self, tmp_path):
        from plumbline.audit import audit
        from plumbline.seeding import pre_existing_findings

        path = self._messy_workbook(tmp_path / "messy2.xlsx")
        report = audit(path, check_determinism=False)
        assert set(pre_existing_findings(path)) == {
            f"{f.sheet}!{f.cell}" for f in report.findings
        }

    def test_a_clean_workbook_has_nothing_pre_existing(self, tmp_path):
        from openpyxl import Workbook

        from plumbline.seeding import pre_existing_findings

        wb = Workbook()
        ws = wb.active
        ws["A1"] = 5
        for col in range(2, 8):
            ws.cell(row=1, column=col, value=f"={chr(64 + col - 1)}1+1")
        path = tmp_path / "clean.xlsx"
        wb.save(path)
        assert pre_existing_findings(path) == []


class TestSeedsNeverFlipTheMajority:
    def test_at_most_one_seed_per_row(self, tmp_path):
        """Two seeds in one row can make the correct cells the minority, so the
        benchmark would be scoring the tool for finding the untouched cell."""
        import random

        from openpyxl import Workbook

        from plumbline.seeding import plan_seeds

        wb = Workbook()
        ws = wb.active
        ws.title = "S"
        for row in range(1, 6):
            ws.cell(row=row, column=1, value=row)
            for col in range(2, 6):
                ws.cell(row=row, column=col, value=f"=SUM($A${row}:{chr(64 + col - 1)}{row})")
        path = tmp_path / "rows.xlsx"
        wb.save(path)

        plan = plan_seeds(path, random.Random(0), max_seeds=8)
        rows = [(c["sheet"], "".join(ch for ch in c["cell"] if ch.isdigit())) for c in plan]
        assert len(rows) == len(set(rows)), f"two seeds landed in one row: {plan}"
