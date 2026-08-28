"""Tests for the Excel functions Plumbline adds to xlcalculator's registry."""

from __future__ import annotations

import pytest
from xlcalculator import FUNCTIONS
from xlcalculator.xlfunctions import xlerrors
from xlcalculator.xlfunctions.func_xltypes import Array

import plumbline  # noqa: F401  -- import registers the functions
from plumbline.functions import ADDED, UNSUPPORTED_BY_DESIGN


@pytest.mark.parametrize("name", ADDED)
def test_registered(name):
    assert name in FUNCTIONS


class TestIndex:
    GRID = Array([[1, 2, 3], [4, 5, 6]])

    def test_two_dimensional(self):
        assert FUNCTIONS["INDEX"](self.GRID, 2, 3) == 6
        assert FUNCTIONS["INDEX"](self.GRID, 1, 1) == 1

    def test_row_vector_takes_single_index(self):
        assert FUNCTIONS["INDEX"](Array([[1, 2, 3]]), 2) == 2

    def test_column_vector_takes_single_index(self):
        assert FUNCTIONS["INDEX"](Array([[1], [2], [3]]), 3) == 3

    def test_is_one_indexed_like_excel(self):
        """Excel counts from 1. An off-by-one here would silently corrupt lookups."""
        assert FUNCTIONS["INDEX"](Array([[10, 20, 30]]), 1) == 10

    def test_out_of_range_is_a_ref_error(self):
        assert isinstance(FUNCTIONS["INDEX"](Array([[1, 2, 3]]), 9), xlerrors.RefExcelError)
        assert isinstance(FUNCTIONS["INDEX"](self.GRID, 1, 99), xlerrors.RefExcelError)

    def test_array_form_is_refused_not_guessed(self):
        """row_num=0 means 'whole column' inside an array formula.

        Returning a scalar there would be quietly wrong, so we refuse instead.
        """
        assert isinstance(FUNCTIONS["INDEX"](self.GRID, 0, 1), xlerrors.ValueExcelError)

    def test_two_dimensional_without_column_is_refused(self):
        assert isinstance(FUNCTIONS["INDEX"](self.GRID, 1), xlerrors.ValueExcelError)


class TestNorminv:
    def test_median_is_the_mean(self):
        assert float(FUNCTIONS["NORMINV"](0.5, 10, 2)) == pytest.approx(10.0)

    def test_matches_known_z_scores(self):
        assert float(FUNCTIONS["NORMINV"](0.975, 0, 1)) == pytest.approx(1.959964, abs=1e-5)
        assert float(FUNCTIONS["NORMINV"](0.025, 0, 1)) == pytest.approx(-1.959964, abs=1e-5)

    def test_scales_with_standard_deviation(self):
        assert float(FUNCTIONS["NORMINV"](0.975, 100, 15)) == pytest.approx(
            100 + 15 * 1.959964, abs=1e-4
        )

    @pytest.mark.parametrize("p", [0, 1, -0.1, 1.1])
    def test_probability_outside_open_interval_is_an_error(self, p):
        assert isinstance(FUNCTIONS["NORMINV"](p, 0, 1), xlerrors.NumExcelError)

    @pytest.mark.parametrize("sd", [0, -1])
    def test_non_positive_sd_is_an_error(self, sd):
        assert isinstance(FUNCTIONS["NORMINV"](0.5, 0, sd), xlerrors.NumExcelError)


class TestValue:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("123", 123.0),
            ("1,234.5", 1234.5),
            ("$1,000", 1000.0),
            ("  42  ", 42.0),
            ("15%", 0.15),
            ("(500)", -500.0),   # accounting notation for negative
            ("-7.5", -7.5),
        ],
    )
    def test_conversions(self, text, expected):
        assert float(FUNCTIONS["VALUE"](text)) == pytest.approx(expected)

    def test_numbers_pass_through(self):
        assert float(FUNCTIONS["VALUE"](42)) == 42.0

    @pytest.mark.parametrize("text", ["", "abc", "12ab"])
    def test_unconvertible_is_an_error(self, text):
        assert isinstance(FUNCTIONS["VALUE"](text), xlerrors.ValueExcelError)


class TestHlookup:
    TABLE = Array([["a", "b", "c"], [1, 2, 3], [10, 20, 30]])

    def test_finds_value_in_row_below(self):
        assert FUNCTIONS["HLOOKUP"]("b", self.TABLE, 2) == 2
        assert FUNCTIONS["HLOOKUP"]("c", self.TABLE, 3) == 30

    def test_missing_key_is_na(self):
        assert isinstance(FUNCTIONS["HLOOKUP"]("z", self.TABLE, 2), xlerrors.NaExcelError)

    def test_row_out_of_range_is_a_ref_error(self):
        assert isinstance(FUNCTIONS["HLOOKUP"]("a", self.TABLE, 9), xlerrors.RefExcelError)


def test_offset_and_indirect_stay_unimplemented():
    """These are refused by design, not by omission.

    They build references at runtime, so a workbook using them has no statically
    knowable dependency graph -- and every Plumbline analysis rests on that graph.
    If someone implements them later, this test should fail loudly and force a
    decision about what the dependency analysis then means.
    """
    for name in UNSUPPORTED_BY_DESIGN:
        assert name not in FUNCTIONS
