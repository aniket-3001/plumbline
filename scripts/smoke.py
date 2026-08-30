"""Run every command the documentation tells a reader to type, and check it works.

    python scripts/smoke.py            # everything runnable with what is present
    python scripts/smoke.py --quick    # skip anything needing the seeded corpus

The unit tests cover behaviour on fixtures. They do **not** cover the thing a judge,
a reader, or a camera actually does: type the commands out of the README, the
reproduction guide and the video script, and see what happens.

That gap has bitten twice. `pip install -e .` had never once been run here -- the
tests only pass because pytest sets `pythonpath = ["src"]` -- so `plumbline audit`,
the command both documents tell you to type, did not exist. And after the v5 detector
change three documented figures silently went stale, including a trace the video
script puts on screen.

So each check below names where the command is documented, runs it for real, and
asserts something specific about the output rather than just the exit code. A command
that runs but prints the wrong thing is the failure mode that matters here.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

CLEAN = "tests/fixtures/quarterly_pl.xlsx"
HARD = "tests/fixtures/quarterly_pl_hardcoded.xlsx"
DEMO = "data/seeded/chris_germany__1938__Mar2002_EstateGas.xlsx"


class Check:
    def __init__(self, name, where, argv, *, expect_exit=0, must_contain=(), must_not=()):
        self.name, self.where, self.argv = name, where, argv
        self.expect_exit = expect_exit
        self.must_contain = must_contain
        self.must_not = must_not

    def run(self) -> tuple[bool, str, float]:
        t0 = time.time()
        try:
            p = subprocess.run(
                [str(PY), *self.argv], cwd=ROOT, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=600,
            )
        except subprocess.TimeoutExpired:
            return False, "timed out after 600s", time.time() - t0

        out = (p.stdout or "") + (p.stderr or "")
        elapsed = time.time() - t0
        if p.returncode != self.expect_exit:
            return False, f"exit {p.returncode}, expected {self.expect_exit}", elapsed
        for needle in self.must_contain:
            if needle not in out:
                return False, f"output missing {needle!r}", elapsed
        for needle in self.must_not:
            if needle in out:
                return False, f"output should not contain {needle!r}", elapsed
        return True, "", elapsed


def checks(quick: bool) -> list[Check]:
    cli = ["-m", "plumbline.cli"]
    out = [
        Check(
            "plumbline audit (clean fixture)", "README Reproduction",
            [*cli, "audit", CLEAN],
            # Exit 1 is correct and load-bearing: it is how CI gates on a finding.
            expect_exit=1,
            must_contain=["PROVED", "P&L!C11", "=SUM(C8:C10)", "27000 -> 30000"],
        ),
        Check(
            "plumbline check", "README Reproduction",
            [*cli, "check", CLEAN],
            must_contain=["Ready to audit", "no volatile functions found"],
        ),
        Check(
            "plumbline audit --json", "cli.py docstring",
            [*cli, "audit", CLEAN, "--json"],
            expect_exit=1,
            must_contain=['"proof_deferred"', '"proved": 1'],
        ),
        Check(
            "scripts/poc.py", "REPRODUCTION.md 6",
            ["scripts/poc.py", CLEAN],
            must_contain=["[PROVED ]", "P&L!C11", "delta +3000"],
        ),
        Check(
            "scripts/sensitivity_probe.py", "REPRODUCTION.md 6",
            ["scripts/sensitivity_probe.py", HARD],
            must_contain=["PROVED DEAD", "no response", "responds"],
        ),
        Check(
            "scripts/agent_trajectories.py replay", "AGENT_TRAJECTORIES.md B",
            ["scripts/agent_trajectories.py", "replay"],
            must_contain=["accepted", "rejected by guard 1", "AJ40"],
        ),
        # `make_fixture.py --help` once silently rewrote both committed fixtures,
        # so the no-argument path is checked rather than assumed.
        Check(
            "make_fixture.py refuses without --write", "scripts/make_fixture.py",
            ["scripts/make_fixture.py"],
            expect_exit=2,
            must_contain=["refusing to overwrite"],
        ),
        Check(
            "make_fixture_hard.py refuses without --write", "scripts/make_fixture_hard.py",
            ["scripts/make_fixture_hard.py"],
            expect_exit=2,
            must_contain=["refusing to overwrite"],
        ),
    ]
    if quick:
        return out

    out += [
        Check(
            "plumbline audit (the video's demo shot)", "VIDEO_SCRIPT.md 0:35",
            [*cli, "audit", DEMO],
            expect_exit=1,
            # The exact lines the script puts on screen. If the detector changes
            # what this workbook reports, the video script is wrong and this fails.
            must_contain=[
                "Sheet1!AI74", "=+AH73", "=+AH74", "+50002",
                "Sheet1!AG55", "=+AF55", "no response", "responds",
                "1,395 formula cells checked",
            ],
        ),
        Check(
            "plumbline audit --report", "VIDEO_SCRIPT.md 1:25",
            [*cli, "audit", DEMO, "--report", "results/smoke_report.md"],
            expect_exit=1,
            must_contain=["wrote results"],
        ),
        Check(
            "scripts/trace_pipeline.py", "AGENT_TRAJECTORIES.md A",
            ["scripts/trace_pipeline.py", DEMO, "--out", "results/smoke_trace.json"],
            must_contain=["0 readiness", "2 screen", "5 triage", "Human checkpoint"],
        ),
    ]
    return out


def error_checks() -> list[Check]:
    """Bad input must be explained, never dumped as a traceback.

    Every entry point here used to end in an openpyxl stack trace, which tells the
    reader the tool is broken when in fact their input is. `check` was worse: it
    printed its readiness banner first, so the crash looked like it happened during
    the audit rather than before it began.
    """
    cli = ["-m", "plumbline.cli"]
    return [
        Check("audit rejects a non-spreadsheet", "cli._unreadable",
              [*cli, "audit", "README.md"], expect_exit=2,
              must_contain=["is not a spreadsheet"], must_not=["Traceback"]),
        Check("check rejects a non-spreadsheet", "cli._unreadable",
              [*cli, "check", "README.md"], expect_exit=2,
              must_contain=["is not a spreadsheet"],
              must_not=["Traceback", "Plumbline readiness"]),
        Check("audit rejects a missing file", "cli._unreadable",
              [*cli, "audit", "definitely_absent.xlsx"], expect_exit=2,
              must_contain=["no such file"], must_not=["Traceback"]),
        Check("poc.py rejects a missing file", "scripts/poc.py",
              ["scripts/poc.py", "definitely_absent.xlsx"], expect_exit=2,
              must_contain=["no such file"], must_not=["Traceback"]),
        Check("sensitivity_probe.py explains a bad file type", "scripts/sensitivity_probe.py",
              ["scripts/sensitivity_probe.py", "README.md"], expect_exit=2,
              must_contain=["could not read"], must_not=["Traceback"]),
        Check("trace_pipeline.py rejects a non-spreadsheet", "scripts/trace_pipeline.py",
              ["scripts/trace_pipeline.py", "README.md"], expect_exit=2,
              must_contain=["is not a spreadsheet"], must_not=["Traceback"]),
        Check("agent_trajectories dump does not call a missing file clean",
              "scripts/agent_trajectories.py",
              ["scripts/agent_trajectories.py", "dump", "definitely_absent.xlsx"],
              expect_exit=2,
              must_contain=["no such file"], must_not=["nothing proved"]),
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quick", action="store_true",
                    help="skip checks that need data/seeded (no corpus download)")
    args = ap.parse_args(argv)

    if not args.quick and not (ROOT / DEMO).exists():
        print(f"note: {DEMO} not present, running --quick set only\n")
        args.quick = True

    todo = checks(args.quick) + error_checks()
    print(f"running {len(todo)} documented commands with {PY.name}\n")

    failures = []
    for check in todo:
        ok, why, elapsed = check.run()
        mark = "ok  " if ok else "FAIL"
        print(f"  [{mark}] {check.name:44} {elapsed:5.1f}s   ({check.where})")
        if not ok:
            print(f"         {why}")
            failures.append((check.name, why))

    print()
    if failures:
        print(f"{len(failures)} of {len(todo)} documented commands are broken:")
        for name, why in failures:
            print(f"  - {name}: {why}")
        return 1
    print(f"all {len(todo)} documented commands work.")

    # Report checks separately: a report is what the reader actually receives, and
    # its blind-spots section is a promise the project makes in writing.
    report = ROOT / "results" / "smoke_report.md"
    if report.exists():
        body = report.read_text(encoding="utf-8")
        for needed in ("What this audit did not check",
                       "qualified reviewer",
                       "same block"):
            if needed not in body:
                print(f"report is missing its {needed!r} section")
                return 1
        print("the generated report states its blind spots and asks for a reviewer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
