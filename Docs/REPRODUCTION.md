# Reproduction Guide

Written for someone starting from a clean machine with nothing installed.

Every command below is copy-pasteable. Where a step takes real time or disk, that
is stated up front rather than discovered halfway through.

---

## 0. What you will need

| | |
|---|---|
| **Python** | 3.11 or newer (developed on 3.11.0) |
| **Disk** | ~3.5 GB — 1 GB archive + 1.9 GB extracted corpus + working files |
| **Network** | One ~993 MB download from figshare. Everything after that runs offline |
| **Time** | ~15 min download, ~5 min extract, ~20 min full evaluation |
| **Cost** | **$0.** The deterministic arm uses no model API at all |
| **OS** | Developed on Windows 11. No OS-specific code; Linux and macOS should work |

There are no credentials, API keys, or accounts involved in the baseline arm.
Nothing in this repository needs configuring before it runs.

---

## 1. Set up

```bash
git clone https://github.com/aniket-3001/plumbline.git
cd plumbline

python -m venv .venv
# Windows
.venv/Scripts/python.exe -m pip install -e ".[dev]"
# Linux / macOS
# .venv/bin/python -m pip install -e ".[dev]"
```

Throughout this guide `PY` means the interpreter inside the venv —
`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere.

**Verify the install before going further** (takes ~5 seconds, needs no data):

```bash
PY -m pytest tests/ -q
```

Expected: `143 passed`. If this fails, stop — nothing downstream will be meaningful.

---

## 2. Get the data

The data is the [Enron Spreadsheet Corpus](https://figshare.com/articles/dataset/Enron_Spreadsheets_and_Emails/1221767)
(Hermans & Murphy-Hill, ICSE 2015), DOI `10.6084/m9.figshare.1221767`, released
**CC BY 4.0**. It is 15,871 real `.xlsx` workbooks recovered from a real company —
not synthetic, not toy.

```bash
PY scripts/fetch_corpus.py
```

Downloads `spreadsheets.7z` (993 MB) and extracts to `data/corpus/`. The download
is **resumable** — if it is interrupted, run the same command again and it
continues rather than restarting.

Only the spreadsheets are fetched. The corpus also ships ~9 GB of email archives,
which this project does not use.

Expected output ends with:

```
corpus: 15929 files, 1.88 GB
  .xlsx        15871
  .xls            58
```

---

## 3. Build the evaluation corpus

Most of the corpus cannot be audited, for reasons that are counted and reported
rather than quietly filtered away.

```bash
PY scripts/build_eval_corpus.py --scan 900 --target 40
```

Seven gates, cheapest first: opens, has formulas, has enough of them, no
`OFFSET`/`INDIRECT`, not volatile, compiles under xlcalculator, has repeated
formula patterns, and finally an empirical determinism check.

Writes accepted workbooks to `data/eval_corpus/` **as it goes** (so an interrupted
run keeps its progress) and the full funnel to `results/eval_corpus.json`.

**Runtime: 20–60 minutes.** The determinism check parses each workbook twice and
some Enron sheets carry 10,000+ formulas. Roughly a quarter of workbooks pass.

Typical rejection profile:

```
no_formulas              44%   (about half the corpus is pure data)
volatile                  9%   (contains RAND; see §7)
too_few_formulas          9%
compile_failed            5%
runtime_references        2%   (OFFSET / INDIRECT)
```

---

## 4. Seed errors into it

```bash
PY scripts/seed_corpus.py --seeds-per-workbook 4 --seed 42
```

Injects errors drawn from **Panko's taxonomy** — mechanical, logic, omission,
hardcoding — into the real workbooks, and writes a ground-truth manifest beside
each one. The RNG seed is fixed, so the same seed produces the same errors and the
evaluation is reproducible.

Runtime: ~2 minutes. Output goes to `data/seeded/` and `results/seeding.json`.

Expected shape (exact numbers depend on which workbooks your corpus scan accepted):

```
seeded 21 workbooks, 53 errors, skipped 3

by Panko class:          by difficulty:
  hardcoding   30 (57%)    silent      30 (57%)
  mechanical   17 (32%)    realistic   22 (41%)
  logic         6 (11%)    obvious      1 ( 2%)
```

Difficulty is assigned by what the error looks like *after* injection:

- **obvious** — the cell now reads 0, blank, or an Excel error. A human scanning
  the sheet would likely spot it.
- **realistic** — the cell still holds a plausible number. Nothing looks wrong.
- **silent** — the value is unchanged today and only diverges once an input moves.
  The hardest class, and the one a human auditor cannot catch by reading numbers.

---

## 5. Run the baseline

```bash
PY scripts/run_baseline.py
```

This is the deterministic arm: structural detection plus proof-by-recomputation,
**no model in the loop**. It is both a working product and the floor that any
model-assisted arm has to beat.

Runtime: 10–30 minutes. Results are written to `results/baseline.json`.

Add `--strict` to run the strict contract, where an unproved finding does not
count as a finding at all:

```bash
PY scripts/run_baseline.py --strict
```

Expected output shape:

```
  workbooks           21
  seeded errors       54
  found               NN
  false positives     NN
  pre-existing hits   NN  (excluded from scoring)

  precision           0.NNN
  recall              0.NNN
  F1                  0.NNN
  proof rate          0.NNN

  recall by difficulty:
    obvious    N.NNN
    realistic  N.NNN
    silent     N.NNN
```

Recall is reported per difficulty class deliberately. A single blended figure lets
a detector that only catches loud breakage look identical to one that catches
silent corruption, and only the second is worth having.

---

## 6. Run it on a single workbook

To see the product rather than the benchmark:

```bash
PY scripts/poc.py tests/fixtures/quarterly_pl.xlsx
PY scripts/sensitivity_probe.py tests/fixtures/quarterly_pl_hardcoded.xlsx
```

The first finds an off-by-one `SUM` range and proves it:

```
[PROVED ] P&L!C11
    is        =SUM(C8:C9)
    expected  =SUM(C8:C10)
    proof     C11: 27000 -> 30000 (delta +3000)
              C13: 45000 -> 42000 (delta -3000)
```

The second handles the hard case — a subtotal that is **correct today** and dead
tomorrow. It cannot be proved by repair (repairing it changes nothing), so it is
proved by perturbing an input and showing the cell fails to respond while a
control arm does.

You can point either script at any `.xlsx` file of your own.

---

## 7. Things that will surprise you

**About half the Enron corpus contains no formulas.** They are data dumps. This is
consistent with the published figure of ~24% formula-bearing; a screened sample
runs higher because screening removes the smallest files first.

**`RAND` appears in 2.67% of formula cells and it breaks proofs.** Plumbline proves
findings by comparing two evaluations. With `RAND` anywhere in the dependency cone,
the two runs differ for reasons that have nothing to do with the finding, so the
"proof" is noise. Those workbooks are refused, not audited. See `Docs/DESIGN.md` §6c.

**Function coverage is ~98.9%, not 100%.** xlcalculator implements 97 Excel
functions; we add `INDEX`, `NORMINV`, `VALUE` and `HLOOKUP` on top, which closes
most of the measured gap on this corpus. `OFFSET` and `INDIRECT` are refused **by
design** — they build references at runtime, so no static dependency graph exists,
and every Plumbline analysis rests on that graph.

**Timings vary enormously between workbooks.** A 39-formula sheet audits in 0.2s;
a 10,000-formula sheet can take minutes, because proving each finding requires
recomputing the workbook.

---

## 8. Versions this was developed against

```
Python           3.11.0
xlcalculator     0.5.0
openpyxl         3.1.5
numpy            1.26.4
scipy            1.17.1
pandas           3.0.5
py7zr            1.1.3
networkx         3.6.1
```

Exact pins are in `pyproject.toml`. `pip install -e ".[dev]"` reproduces this set.

---

## 9. If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `no .xlsx files found under data/corpus` | §2 did not complete. Re-run `fetch_corpus.py`; it resumes |
| Download stalls | Interrupt and re-run. Resumable via HTTP Range |
| `no seeded workbooks` | §3 produced nothing. Increase `--scan` |
| `ValueError: Invalid column index` | Should be fixed; please report with the workbook name |
| Audit reports `volatile:` and skips | Correct behaviour — that workbook cannot be proved. See §7 |
| Tests fail on a fresh clone | Check the Python version is ≥3.11 |

Warnings like `Defined name X refers to empty cell` come from openpyxl reading
twenty-five-year-old workbooks. They are noise and are suppressed in the scripts.
