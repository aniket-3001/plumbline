"""Tests for the product surface: the CLI and the audit report."""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

import plumbline  # noqa: F401
from plumbline.audit import audit
from plumbline.cli import main
from plumbline.report import render_markdown, render_terminal

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "tests" / "fixtures" / "quarterly_pl.xlsx"
HARD = ROOT / "tests" / "fixtures" / "quarterly_pl_hardcoded.xlsx"


@pytest.fixture(scope="module")
def clean_report():
    return audit(CLEAN, check_determinism=False)


@pytest.fixture
def volatile_wb(tmp_path) -> Path:
    path = tmp_path / "vol.xlsx"
    wb = Workbook()
    wb.active["A1"] = 1
    wb.active["B1"] = "=RAND()"
    wb.save(path)
    return path


class TestMarkdownReport:
    def test_names_the_cell_and_the_money(self, clean_report):
        md = render_markdown(clean_report)
        assert "C11" in md
        assert "27,000" in md and "30,000" in md
        assert "+3,000" in md

    def test_shows_current_and_expected_formula(self, clean_report):
        md = render_markdown(clean_report)
        assert "=SUM(C8:C9)" in md
        assert "=SUM(C8:C10)" in md

    def test_always_states_its_blind_spots(self, clean_report):
        """An audit that hides what it did not check manufactures false confidence."""
        md = render_markdown(clean_report)
        assert "did not check" in md
        assert "OFFSET" in md and "INDIRECT" in md

    def test_requires_a_human_reviewer(self, clean_report):
        """Ground rule 5: a qualified reviewer stays in the loop."""
        md = render_markdown(clean_report)
        assert "qualified reviewer" in md
        assert "does not edit workbooks" in md

    def test_explains_a_refusal_in_plain_english(self, volatile_wb):
        md = render_markdown(audit(volatile_wb))
        assert "could not be audited" in md
        assert "RAND" in md
        assert "different numbers each time" in md

    def test_hard_case_report_omits_a_meaningless_delta(self):
        """A dead cell is correct today, so a 'value if corrected' column would lie."""
        md = render_markdown(audit(HARD, check_determinism=False))
        assert "typed-in value where a formula belongs" in md
        assert "Value if corrected" not in md


class TestTerminalReport:
    def test_is_ascii_only(self, clean_report):
        """Windows consoles and pipes mangle non-ASCII; the report must survive them."""
        render_terminal(clean_report).encode("ascii")

    def test_is_ascii_even_when_values_are_missing_or_truncated(self):
        """The clean fixture never reaches the em dash placeholder or the ellipsis,
        so passing on it proves nothing. This exercises both."""
        from plumbline.audit import AuditReport, Finding

        report = AuditReport(workbook="x.xlsx", formula_cells=9)
        report.findings = [
            Finding(
                sheet="S", cell="C11", detector="pattern_break", panko_class="mechanical",
                actual="=SUM(" + "C8:C9," * 30 + "C10)", expected="=SUM(C8:C10)",
                reason="r", proved=True, proof="p",
                baseline_value=None, repaired_value=None, delta=None,
            ),
            Finding(
                sheet="S", cell="D11", detector="pattern_break", panko_class="mechanical",
                actual="=1", expected="=2", reason="r",
            ),
        ]
        render_terminal(report).encode("ascii")

    def test_the_cli_itself_prints_ascii(self, capsys):
        """`check` lives outside report.py and had its own em dash, mojibaked into a
        byte that was not even valid UTF-8."""
        main(["check", str(CLEAN)])
        out = capsys.readouterr().out
        out.encode("ascii")
        assert "Plumbline readiness" in out

    def test_mentions_the_proof(self, clean_report):
        assert "PROVED" in render_terminal(clean_report)


class TestCli:
    def test_audit_exits_1_when_something_is_proved(self, capsys):
        """Non-zero exit lets CI gate on a finding."""
        assert main(["audit", str(CLEAN), "--skip-checks"]) == 1

    def test_audit_writes_a_report_file(self, tmp_path, capsys):
        out = tmp_path / "audit.md"
        main(["audit", str(CLEAN), "--skip-checks", "--report", str(out)])
        assert out.exists()
        assert "C11" in out.read_text(encoding="utf-8")

    def test_json_output_is_valid(self, capsys):
        import json

        main(["audit", str(CLEAN), "--skip-checks", "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["counts"]["proved"] == 1

    def test_check_passes_a_clean_workbook(self, capsys):
        assert main(["check", str(CLEAN)]) == 0
        assert "Ready to audit" in capsys.readouterr().out

    def test_check_refuses_a_volatile_workbook(self, volatile_wb, capsys):
        assert main(["check", str(volatile_wb)]) == 1
        assert "Cannot audit" in capsys.readouterr().out

    def test_missing_file_exits_2(self, capsys):
        assert main(["audit", "does_not_exist.xlsx"]) == 2


class TestBadInputIsExplainedNotDumped:
    """A traceback tells the reader the tool is broken. It usually isn't.

    Every one of these produced a raw `InvalidFileException` stack dump before,
    and `check` printed its readiness banner first -- so the failure looked like it
    happened *during* the audit rather than before it started.
    """

    def test_a_non_spreadsheet_is_refused_by_name(self, tmp_path, capsys):
        path = tmp_path / "notes.md"
        path.write_text("# not a workbook", encoding="utf-8")
        for command in ("audit", "check"):
            assert main([command, str(path)]) == 2
            err = capsys.readouterr().err
            assert "notes.md is not a spreadsheet" in err
            assert "Traceback" not in err

    def test_a_legacy_xls_says_how_to_fix_it(self, tmp_path, capsys):
        """The Enron corpus ships 58 of these, so a reader will hit it."""
        path = tmp_path / "old.xls"
        path.write_bytes(b"\xd0\xcf\x11\xe0")      # OLE2 magic, a real .xls header
        assert main(["audit", str(path)]) == 2
        err = capsys.readouterr().err
        assert "legacy .xls" in err
        assert "save as .xlsx" in err

    def test_a_corrupt_xlsx_is_reported_in_one_line(self, tmp_path, capsys):
        path = tmp_path / "broken.xlsx"
        path.write_bytes(b"this is not a zip archive")
        assert main(["audit", str(path)]) == 2
        err = capsys.readouterr().err
        assert "could not open broken.xlsx" in err
        assert len(err.strip().splitlines()) == 1, "one line, not a traceback"

    def test_check_says_nothing_before_it_knows_it_can_read_the_file(self, tmp_path, capsys):
        path = tmp_path / "notes.md"
        path.write_text("x", encoding="utf-8")
        main(["check", str(path)])
        assert "Plumbline readiness" not in capsys.readouterr().out

    def test_a_missing_file_still_exits_2(self, tmp_path, capsys):
        assert main(["audit", str(tmp_path / "absent.xlsx")]) == 2
        assert "no such file" in capsys.readouterr().err


class TestConsoleOutputIsAsciiEverywhere:
    """Not just the report -- every script that prints progress to a terminal.

    `report.py` and `cli.py` were guarded, and four scripts in the documented
    pipeline still printed a literal ellipsis. On a legacy Windows code page that
    is either mojibake or a UnicodeEncodeError mid-run, and these are commands the
    reproduction guide tells a reader to type.
    """

    def test_no_script_emits_non_ascii_source_literals(self):
        import re
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        offenders = []
        for path in sorted((root / "scripts").glob("*.py")):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"[^\x00-\x7F]", line) and "print" in line:
                    offenders.append(f"{path.name}:{n}: {line.strip()[:70]}")
        assert not offenders, "non-ASCII in console output:\n" + "\n".join(offenders)

    def test_src_console_paths_are_ascii(self):
        """`report.render_markdown` may use typography -- it writes to a file with a
        declared encoding. Anything printed to a terminal may not."""
        import re
        from pathlib import Path

        cli = (Path(__file__).resolve().parents[1] / "src" / "plumbline" / "cli.py")
        offenders = [
            f"cli.py:{n}"
            for n, line in enumerate(cli.read_text(encoding="utf-8").splitlines(), 1)
            if re.search(r"[^\x00-\x7F]", line)
        ]
        assert not offenders, f"non-ASCII in cli.py: {offenders}"
