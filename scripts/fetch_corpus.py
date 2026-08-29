"""Fetch and extract the Enron Spreadsheet Corpus.

Source: Hermans & Murphy-Hill, "Enron's Spreadsheets and Related Emails: A Dataset
and Analysis" (ICSE 2015). Published on figshare under CC BY 4.0.
DOI: 10.6084/m9.figshare.1221767

Only `spreadsheets.7z` (~993 MB) is fetched. The email archives (~9 GB) are not
used by this project.

Usage:
    python scripts/fetch_corpus.py            # download + extract
    python scripts/fetch_corpus.py --stats    # just report on what is present

The download is resumable: re-running after an interruption continues from where
it stopped rather than starting over.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CORPUS = ROOT / "data" / "corpus"

ARTICLE_ID = 1221767
ARCHIVE_NAME = "spreadsheets.7z"
EXPECTED_BYTES = 992_567_296  # figshare-reported size; used only as a sanity check
CHUNK = 1 << 20  # 1 MiB


def resolve_url() -> tuple[str, int]:
    """Ask the figshare API for the current download URL and size."""
    import json

    api = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}"
    with urllib.request.urlopen(api, timeout=60) as r:
        meta = json.load(r)
    for f in meta.get("files", []):
        if f["name"] == ARCHIVE_NAME:
            return f["download_url"], f["size"]
    raise SystemExit(f"{ARCHIVE_NAME} not found in figshare article {ARTICLE_ID}")


def download(url: str, dest: Path, total: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    have = dest.stat().st_size if dest.exists() else 0

    if have == total:
        print(f"  archive already complete ({have / 1e6:.0f} MB), skipping download")
        return
    if have > total:
        print(f"  local file larger than expected; re-downloading from scratch")
        dest.unlink()
        have = 0

    req = urllib.request.Request(url)
    if have:
        req.add_header("Range", f"bytes={have}-")
        print(f"  resuming at {have / 1e6:.0f} MB of {total / 1e6:.0f} MB")

    mode = "ab" if have else "wb"
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, mode) as out:
        got = have
        last_pct = -1
        while chunk := r.read(CHUNK):
            out.write(chunk)
            got += len(chunk)
            pct = int(got * 100 / total)
            if pct != last_pct:
                print(f"\r  downloading ... {pct:3d}%  ({got / 1e6:.0f}/{total / 1e6:.0f} MB)",
                      end="", flush=True)
                last_pct = pct
    print()


def extract(archive: Path, dest: Path) -> None:
    import py7zr

    dest.mkdir(parents=True, exist_ok=True)
    print(f"  extracting to {dest.relative_to(ROOT)} ... (this takes a few minutes)")
    with py7zr.SevenZipFile(archive, mode="r") as z:
        z.extractall(path=dest)


def stats() -> None:
    if not CORPUS.exists():
        print("corpus not extracted yet")
        return
    by_ext: dict[str, int] = {}
    total_bytes = 0
    for p in CORPUS.rglob("*"):
        if p.is_file():
            by_ext[p.suffix.lower()] = by_ext.get(p.suffix.lower(), 0) + 1
            total_bytes += p.stat().st_size
    print(f"corpus: {sum(by_ext.values())} files, {total_bytes / 1e9:.2f} GB")
    for ext, n in sorted(by_ext.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {ext or '(none)':10} {n:7d}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="report on the extracted corpus only")
    args = ap.parse_args()

    if args.stats:
        stats()
        return 0

    print("Enron Spreadsheet Corpus  (CC BY 4.0, DOI 10.6084/m9.figshare.1221767)")
    url, size = resolve_url()
    archive = RAW / ARCHIVE_NAME
    download(url, archive, size)

    if not any(CORPUS.iterdir()) if CORPUS.exists() else True:
        extract(archive, CORPUS)
    else:
        print("  corpus directory not empty, skipping extraction")

    stats()
    return 0


if __name__ == "__main__":
    sys.exit(main())
