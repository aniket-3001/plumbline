# Data

Corpus files are NOT committed (see .gitignore). Download them with:

    python scripts/fetch_corpus.py

- `raw/` — downloaded archive as fetched
- `corpus/` — extracted, filtered to formula-bearing workbooks
- `seeded/` — workbooks with injected errors plus ground-truth manifests
