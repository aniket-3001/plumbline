"""Characterise every remaining miss: what was seeded, and what the row looks like now."""
import json, sys, glob, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts')
from openpyxl import load_workbook
from plumbline.audit import audit

for t in sys.argv[1:]:
    man = glob.glob(f'data/seeded/*{t}*.truth.json')[0]
    m = json.load(open(man, encoding='utf-8'))
    wb = os.path.join('data/seeded', m['seeded'])
    found = {(f.sheet, f.cell) for f in audit(wb, check_determinism=False, max_proofs=1).findings}
    book = load_workbook(wb)
    print(f"\n=== {m['workbook']} ===")
    for s in m['seeds']:
        if (s['sheet'], s['cell']) in found:
            continue
        row = int(''.join(c for c in s['cell'] if c.isdigit()))
        cells = [(c.coordinate, c.value) for c in book[s['sheet']][row] if c.value is not None]
        print(f"  MISS {s['sheet']}!{s['cell']}  {s['panko_class']}/{s['difficulty']}")
        print(f"       was {s['original_formula']!r} -> {s['seeded_formula']!r}")
        print(f"       row {row}: {cells[:10]}")
