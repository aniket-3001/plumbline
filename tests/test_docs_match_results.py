"""The numbers in the README must be the numbers in results/.

Documentation drift is not cosmetic here. Every headline figure is a claim about
measured behaviour, and a judge or a reader has no way to tell a stale number from
a false one -- they look identical. This has already happened three times in this
project: the v5 detector change moved figures in the README, the trajectory docs and
the video script, and each was caught by hand rather than by anything automatic.

So the tables are parsed out of the Markdown and compared against the committed JSON
they summarise. If a run changes the numbers, this fails until the docs are updated,
which is the only way the two stay honest without someone remembering.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ARMS = ROOT / "results" / "arms.json"
BASELINE = ROOT / "results" / "baseline.json"

#: Reading a figure from prose is unreliable; reading it from a table row is not.
ROW = r"^\|\s*{label}\s*\|(.+)\|\s*$"


def _cells(label: str) -> list[str]:
    """The cells of the README table row whose first column is `label`."""
    text = README.read_text(encoding="utf-8")
    match = re.search(ROW.format(label=re.escape(label)), text, re.MULTILINE)
    assert match, f"README has no table row labelled {label!r}"
    return [c.strip().replace("*", "").replace(",", "") for c in match.group(1).split("|")]


def _num(cell: str) -> float:
    return float(cell)


@pytest.fixture(scope="module")
def arms():
    if not ARMS.exists():
        pytest.skip("results/arms.json absent; run scripts/run_arms.py")
    return json.loads(ARMS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def baseline():
    if not BASELINE.exists():
        pytest.skip("results/baseline.json absent; run scripts/run_baseline.py")
    return json.loads(BASELINE.read_text(encoding="utf-8"))["summary"]


class TestBaselineVsSolutionTable:
    """The four-arm comparison, which is the brief's mandatory deliverable."""

    ORDER = ("naive", "block", "screened", "full")

    @pytest.mark.parametrize(
        ("label", "key"),
        [
            ("**Precision**", "precision"),
            ("**Recall**", "recall"),
            ("**F1**", "f1"),
            ("True positives", "true_positives"),
            ("False positives", "false_positives"),
            ("Findings carrying a proof", "proved"),
        ],
    )
    def test_row_matches_the_run(self, arms, label, key):
        cells = _cells(label)
        assert len(cells) == 4, f"{label}: expected 4 arms, found {len(cells)}"
        for arm, cell in zip(self.ORDER, cells):
            expected = arms[arm]["summary"][key]
            assert _num(cell) == pytest.approx(expected, abs=0.001), (
                f"README says {label} for {arm} is {cell}; results/arms.json says {expected}"
            )

    def test_cells_reported_matches(self, arms):
        for arm, cell in zip(self.ORDER, _cells("Cells reported to the analyst")):
            assert _num(cell) == arms[arm]["summary"]["reported_total"]


class TestHeadlineLadder:
    """The v1..v5 table. Only the last column names the current state; the earlier
    columns describe runs that happened and are deliberately not re-derived."""

    @pytest.mark.parametrize(
        ("label", "key"),
        [
            ("**Precision**", "precision"),
            ("**Recall**", "recall"),
            ("**F1**", "f1"),
        ],
    )
    def test_final_column_is_the_current_baseline(self, baseline, label, key):
        # Two rows carry these labels; the ladder is the 5-cell one.
        text = README.read_text(encoding="utf-8")
        rows = re.findall(ROW.format(label=re.escape(label)), text, re.MULTILINE)
        ladder = [r for r in rows if len(r.split("|")) == 5]
        assert ladder, f"no 5-column ladder row for {label}"
        final = ladder[0].split("|")[-1].strip().replace("*", "")
        assert _num(final) == pytest.approx(baseline[key], abs=0.001), (
            f"README ladder ends at {final} for {label}; "
            f"results/baseline.json says {baseline[key]}"
        )

    def test_silent_recall_matches(self, baseline):
        text = README.read_text(encoding="utf-8")
        rows = re.findall(ROW.format(label=re.escape("Recall, *silent*")), text, re.MULTILINE)
        ladder = [r for r in rows if len(r.split("|")) == 5]
        assert ladder
        final = ladder[0].split("|")[-1].strip().replace("*", "")
        assert _num(final) == pytest.approx(
            baseline["recall_by_difficulty"]["silent"], abs=0.001
        )


class TestProseFigures:
    """Figures quoted in prose, which drift as easily as tables and are read more."""

    def test_the_excluded_population_is_stated_correctly(self, baseline):
        count = baseline["pre_existing_hits"]
        text = README.read_text(encoding="utf-8")
        assert f"{count} findings that were already in the original Enron files" in text, (
            f"README should say {count} pre-existing findings"
        )

    def test_the_test_count_is_current(self):
        """The README tells a reader what `pytest` should print."""
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--collect-only"],
            cwd=ROOT, capture_output=True, text=True,
        )
        tail = [line for line in proc.stdout.splitlines() if "test" in line and "collected" in line]
        if not tail:
            pytest.skip("could not determine collected test count")
        collected = int(re.search(r"(\d+)", tail[-1]).group(1))
        claimed = re.search(r"#\s*(\d+) passed", README.read_text(encoding="utf-8"))
        assert claimed, "README no longer states an expected pytest count"
        assert int(claimed.group(1)) == collected, (
            f"README claims {claimed.group(1)} passed; pytest collects {collected}"
        )
