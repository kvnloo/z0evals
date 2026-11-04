"""Compare collected real Oracle outputs to frozen lexical control; public dev only."""
import hashlib
import json
import random
import sys
from pathlib import Path

HARNESS = Path('/mnt/zer0models/z0-wt/z0int-weight-space/benchmarks/weight_space/slm')
sys.path.insert(0, str(HARNESS))
import toolchoice as T
import toolchoice_controls as C

ROOT = Path(__file__).resolve().parents[1]
SRC = Path.home() / '.z0int/state/weight-space/slm/tc-base-oracle/toolchoice-dev-unedited'
items = T.load('dev')
by = {r['id']: r for r in items}
gens = [json.loads(s) for s in (SRC / 'gen.jsonl').read_text().splitlines()]
assert len(gens) == len(items) == 604
assert len({g['id'] for g in gens}) == 604
control_meta = json.loads((ROOT / 'data/toolchoice-controls-dev.json').read_text())
weights = C.idf(T.load('practice'))
control = {i['id']: r['pred'] for i, r in zip(items, C.run(items, weights, control_meta['abstain_threshold']))}
rows, delta = [], []
for g in gens:
    it = by[g['id']]
    p = T.predicted(g['text'], [t['name'] for t in it['tools']])
    ok, cok = p == it['gold'], control[it['id']] == it['gold']
    rows.append({'kind': it['kind'], 'gold': it['gold'], 'pred': p})
    delta.append(int(ok) - int(cok))
rng = random.Random(20261104)
boot = sorted(100 * sum(rng.choices(delta, k=len(delta))) / len(delta) for _ in range(4000))
res = {
    'run_id': 'tc-base-oracle', 'split': 'public dev', 'n': len(rows),
    'model': T.score(rows),
    'control': control_meta['arms']['lexical+abstain'],
    'difference_model_minus_control_pp': 100 * sum(delta) / len(delta),
    'paired_item_bootstrap_95ci_pp': [boot[100], boot[3899]],
    'ci_caveat': 'IID item bootstrap; BFCL related items may be correlated; dev only, not transfer evidence.',
    'model_only_correct': delta.count(1), 'control_only_correct': delta.count(-1),
    'gen_sha256': hashlib.sha256((SRC / 'gen.jsonl').read_bytes()).hexdigest(),
    'inference_wall_s': json.loads((SRC / 'score.json').read_text())['gen']['wall_s'],
    'weights_edited': False
}
(ROOT / 'data/toolchoice-oracle-baseline-dev.json').write_text(json.dumps(res, indent=2) + '\n')
print(json.dumps(res, indent=2))
