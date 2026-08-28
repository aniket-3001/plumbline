"""Command-line interface.

    plumbline audit model.xlsx
    plumbline audit model.xlsx --report audit.md
    plumbline check model.xlsx        # can this workbook be audited at all?
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def _audit(path: Path, report_path: Path | None, as_json: bool, skip_checks: bool) -> int:
    from plumbline.audit import audit
    from plumbline.report import render_markdown, render_terminal

    if not path.exists():
        print(f"no such file: {path}", file=sys.stderr)
        return 2

    result = audit(path, check_determinism=not skip_checks)

    if as_json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print(render_terminal(result))

    if report_path:
        report_path.write_text(render_markdown(result, source=str(path)), encoding="utf-8")
        print(f"\nwrote {report_path}")

    # Exit 1 when something was proved, so CI can gate on it.
    return 1 if result.proved else 0


def _check(path: Path) -> int:
    """Report whether a workbook can be audited, and why not if it cannot."""
    from plumbline.determinism import check, find_volatile

    if not path.exists():
        print(f"no such file: {path}", file=sys.stderr)
        return 2

    print(f"Plumbline readiness — {path.name}\n")
    vol = find_volatile(path)
    print(f"  volatile functions   {vol.summary()}")
    if vol.is_volatile:
        print("\n  Cannot audit: this workbook recalculates to different numbers each")
        print("  time, so a proof by recomputation would not be reproducible.")
        return 1

    det = check(path)
    print(f"  determinism          {det.summary()}")
    if not det.stable:
        print("\n  Cannot audit: repeated evaluation disagrees with itself.")
        return 1
    print("\n  Ready to audit.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="plumbline",
        description="Audit a spreadsheet and prove every finding by recomputation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("audit", help="audit a workbook")
    a.add_argument("workbook", type=Path)
    a.add_argument("--report", type=Path, help="write a full Markdown report here")
    a.add_argument("--json", action="store_true", help="emit machine-readable output")
    a.add_argument(
        "--skip-checks",
        action="store_true",
        help="skip the volatility/determinism guard (not recommended)",
    )

    c = sub.add_parser("check", help="report whether a workbook can be audited")
    c.add_argument("workbook", type=Path)

    args = parser.parse_args(argv)
    if args.command == "audit":
        return _audit(args.workbook, args.report, args.json, args.skip_checks)
    return _check(args.workbook)


app = main  # entry point named in pyproject


if __name__ == "__main__":
    sys.exit(main())
