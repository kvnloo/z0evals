"""Independent stdlib-only checks of the frozen study (no GPU or model needed)."""
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'manifest.yaml').read_text())  # JSON is valid YAML.
assert manifest['schema_version'] == 'z0eval.study.v1'
assert manifest['status'] == 'draft'
for source in manifest['sources']:
    assert len(source['commit']) == 40
for artifact in manifest['artifacts']:
    p = root / artifact['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == artifact['sha256'], p

trials = json.loads((root / 'data/niah-trials.json').read_text())
summary = json.loads((root / 'data/summary.json').read_text())
segments = json.loads((root / 'data/scaling-segments.json').read_text())
assert len(trials) == 720
assert len(segments) == 2958
assert len({(r['length'], r['i'], r['router']) for r in trials}) == 720
for r in summary['niah']:
    group = [t for t in trials if t['router'] == r['router'] and (r['length'] == 'pooled' or t['length'] == r['length'])]
    assert len(group) == r['n']
    assert sum(t['correct'] for t in group) == r['correct']
    assert abs(statistics.mean(t['attended_frac'] for t in group) - r['attended_frac']) < 1e-12
    base = {(t['length'], t['i']): t['correct'] for t in trials if t['router'] == 'dense'}
    assert sum(base[t['length'], t['i']] and not t['correct'] for t in group) == r['dense_correct_router_wrong']
    assert sum(not base[t['length'], t['i']] and t['correct'] for t in group) == r['dense_wrong_router_correct']
for r in summary['scaling']:
    group = [t for t in segments if (t['model'], t['n'], t['router']) == (r['model'], r['n'], r['router'])]
    assert len(group) == r['segments'] == 6
    for field in ['attended_frac', 'attention_mass', 'idealized_selected_node_plus_key_ratio']:
        assert abs(statistics.mean(t[field] for t in group) - r[field]) < 1e-12
assert json.loads((root/'data/run-status.json').read_text())['qwen3.5-4b']['scaling_rows'] == 0
for p in [*root.glob('*.md'), *root.glob('*.html'), *root.glob('scripts/*.py'), *root.glob('data/*')]:
    text = p.read_text()
    for private in ['/home/kvn', '/mnt/zer0models', '100.117.', 'groot', 'mbp-host']:
        # This checker includes the denylist literals but must not carry personal paths.
        if p.name != 'check_study.py':
            assert private not in text, (p.name, private)
subprocess.run([sys.executable, str(root/'scripts/figures.py'), '--check'], check=True)
print(f'ok: {len(manifest["artifacts"])} artifact hashes, 720 paired outcomes, 2958 scaling aggregates, report drift, privacy sentinels')
