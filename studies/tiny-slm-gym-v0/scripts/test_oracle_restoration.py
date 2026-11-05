"""Trusted cross-process original/edit/original practice RPC qualification."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BASE = Path('/opt/wsp-isolation')
MODEL = BASE / 'model-79eaaa84125b897f5a0ad6638362b864fec813ad'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    out = Path(sys.argv[1])
    out.mkdir(exist_ok=False)
    before = sha(MODEL / 'model.safetensors')
    item = json.loads((BASE / 'practice/toolchoice_practice.jsonl').open().readline())
    results = []
    for index, arm in enumerate(['unedited', 'staged_edit', 'unedited']):
        dest = out / str(index)
        req = json.dumps({'ids': [item['id']], 'max_tokens': 8, 'arm': arm})
        cmd = [sys.executable, '/home/ubuntu/wsp/oracle_practice_rpc.py',
               str(BASE / 'trusted-snapshots/snapshot-lse4ll64'), str(dest)]
        p = subprocess.run(cmd, input=req, capture_output=True, text=True, timeout=90)
        (out / f'{index}.log').write_text(p.stdout + '\n' + p.stderr)
        assert p.returncode == 0, (index, p.returncode, p.stderr[-1000:])
        receipt = json.loads((dest / 'receipt.json').read_text())
        results.append({'arm': arm, 'meta': receipt['meta'], 'generation_sha256': sha(dest / 'gen.jsonl')})
    checks = {
        'original_after_edit_identical': results[0]['generation_sha256'] == results[2]['generation_sha256'],
        'base_weights_unchanged': before == sha(MODEL / 'model.safetensors'),
        'original_uses_base': all(results[i]['meta']['checkpoint'] == str(MODEL) for i in (0, 2)),
        'edited_uses_controller_cache': results[1]['meta']['checkpoint'].startswith(str(out / '1/controller-state/')),
        'three_fresh_processes_completed': len(results) == 3,
    }
    result = {'n': 3, 'checks': checks, 'passed': sum(checks.values()), 'results': results,
              'base_sha256': before, 'ci': None,
              'scope': 'restoration/isolation engineering smoke; no accuracy or edit-effect claim',
              'limitations': ['session.forward not integrated', 'trusted fixture edit only',
                              '8-token truncation cannot establish quality']}
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    assert all(checks.values())


if __name__ == '__main__':
    main()
