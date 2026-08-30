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


def _cells(label: str, width: int | None = None) -> list[str]:
    """The cells of the README table row whose first column is `label`.

    Matched by **shape**, not by document order. The same label legitimately appears
    in more than one table -- "Precision" is a row of the four-arm comparison and
    also a row of the proposed rubric -- so taking the first match silently reads
    whichever table happens to come first, and adding a section above rearranges
    what the test is checking. Requiring the expected column count pins it.
    """
    text = README.read_text(encoding="utf-8")
    rows = re.findall(ROW.format(label=re.escape(label)), text, re.MULTILINE)
    assert rows, f"README has no table row labelled {label!r}"
    for row in rows:
        cells = [c.strip().replace("*", "").replace(",", "") for c in row.split("|")]
        if width is None or len(cells) == width:
            return cells
    raise AssertionError(
        f"no {width}-column table row labelled {label!r}; "
        f"found widths {[len(r.split('|')) for r in rows]}"
    )


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
        cells = _cells(label, width=4)
        for arm, cell in zip(self.ORDER, cells):
            expected = arms[arm]["summary"][key]
            assert _num(cell) == pytest.approx(expected, abs=0.001), (
                f"README says {label} for {arm} is {cell}; results/arms.json says {expected}"
            )

    def test_cells_reported_matches(self, arms):
        for arm, cell in zip(self.ORDER, _cells("Cells reported to the analyst", width=4)):
            assert _num(cell) == arms[arm]["summary"]["reported_total"]


class TestHeadlineLadder:
    """The v1..v5 ladder is history and ends at v5 on purpose.

    v6 detects along columns, and measuring that needs a corpus containing column
    errors -- so it re-seeds, which makes it a different benchmark rather than the
    next rung. Quoting v6's recall against v5's would compare two question papers.
    The ladder's last column is therefore checked against the **v5** results file,
    not against the current one.
    """

    V5 = ROOT / "results" / "baseline_v5_contiguity.json"

    @pytest.fixture(scope="class")
    @classmethod
    def v5(cls):
        if not cls.V5.exists():
            pytest.skip("v5 snapshot absent")
        return json.loads(cls.V5.read_text(encoding="utf-8"))["summary"]

    def _ladder_final(self, label: str) -> float:
        text = README.read_text(encoding="utf-8")
        rows = re.findall(ROW.format(label=re.escape(label)), text, re.MULTILINE)
        ladder = [r for r in rows if len(r.split("|")) == 5]
        assert ladder, f"no 5-column ladder row for {label}"
        return _num(ladder[0].split("|")[-1].strip().replace("*", ""))

    @pytest.mark.parametrize(
        ("label", "key"),
        [("**Precision**", "precision"), ("**Recall**", "recall"), ("**F1**", "f1")],
    )
    def test_ladder_ends_at_the_v5_snapshot(self, v5, label, key):
        assert self._ladder_final(label) == pytest.approx(v5[key], abs=0.001)

    def test_ladder_silent_recall_matches_v5(self, v5):
        assert self._ladder_final("Recall, *silent*") == pytest.approx(
            v5["recall_by_difficulty"]["silent"], abs=0.001
        )


class TestCurrentBaselineTable:
    """The row-only vs row+column table is the current state, and must track it."""

    def _two_col(self, label: str) -> tuple[float, float]:
        text = README.read_text(encoding="utf-8")
        rows = re.findall(ROW.format(label=re.escape(label)), text, re.MULTILINE)
        pair = [r for r in rows if len(r.split("|")) == 2]
        assert pair, f"no 2-column row for {label}"
        a, b = (c.strip().replace("*", "").replace(",", "") for c in pair[0].split("|"))
        return _num(a), _num(b)

    @pytest.mark.parametrize(
        ("label", "key"),
        [("Precision", "precision"), ("Recall", "recall"), ("F1", "f1")],
    )
    def test_both_arms_match_their_runs(self, label, key):
        row_only = ROOT / "results" / "baseline_v6_rowonly.json"
        both = ROOT / "results" / "baseline_v6_bothaxes.json"
        if not (row_only.exists() and both.exists()):
            pytest.skip("v6 arms absent")
        r = json.loads(row_only.read_text(encoding="utf-8"))["summary"]
        b = json.loads(both.read_text(encoding="utf-8"))["summary"]
        stated_row, stated_both = self._two_col(label)
        assert stated_row == pytest.approx(r[key], abs=0.001)
        assert stated_both == pytest.approx(b[key], abs=0.001)


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
