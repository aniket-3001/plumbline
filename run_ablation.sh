set -e
PY=.venv/Scripts/python.exe
# Each arm's exclusion list must be computed at that arm's own threshold, or a more
# sensitive audit is charged for the extra pre-existing cells it correctly finds.
$PY -u scripts/seed_corpus.py --refresh-pre-existing --min-peers 3 > results/ablate_refresh3.log 2>&1
$PY -u scripts/run_baseline.py --max-proofs 25 --min-peers 3 --out baseline_peers3.json > results/ablate_peers3.log 2>&1
$PY -u scripts/seed_corpus.py --refresh-pre-existing --min-peers 2 > results/ablate_refresh2.log 2>&1
$PY -u scripts/run_baseline.py --max-proofs 25 --min-peers 2 --out baseline_peers2.json > results/ablate_peers2.log 2>&1
echo ABLATION_DONE
