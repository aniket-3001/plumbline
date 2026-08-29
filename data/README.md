# Data

Corpus files are NOT committed (see .gitignore). Download them with:

    python scripts/fetch_corpus.py

- `raw/` — downloaded archive as fetched
- `corpus/` — extracted, filtered to formula-bearing workbooks
- `seeded/` — workbooks with injected errors plus ground-truth manifests

## What is committed, and why

The corpus is not: it is 1.9 GB and freely downloadable. The seeded workbooks are
not: they are regenerable from the corpus with `--seed 42`.

The **ground-truth manifests are** — `data/seeded/*.truth.json`, 88 KB. They are the
answer key for every number in the README: each records the seeds injected into one
workbook, their Panko class, their difficulty, and the findings that were already in
the original file and are therefore excluded from scoring. Committing them lets a
reader check our scoring against the exact seeds we scored, without first spending
forty minutes rebuilding a corpus.

## Attribution

The [Enron Spreadsheet Corpus](https://figshare.com/articles/dataset/Enron_Spreadsheets_and_Emails/1221767)
(Hermans & Murphy-Hill, ICSE 2015), DOI `10.6084/m9.figshare.1221767`, is released
under **CC BY 4.0** and is used here under that licence with attribution. Only the
spreadsheets are used; the ~9 GB of email archives that ship with the corpus are not
downloaded and not used.

The formula engine is [xlcalculator](https://github.com/bradbase/xlcalculator) (MIT).
