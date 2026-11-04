"""Trusted Oracle smoke: immutable edits -> existing inference; practice only.
Not an editor, scientific evaluation or general RPC endpoint. Run under capped systemd.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, '/home/ubuntu/wsp/slm')
sys.path.insert(0, '/home/ubuntu/wsp')
import common as C  # type: ignore[import-not-found]
import gpu  # type: ignore[import-not-found]
import toolchoice as T  # type: ignore[import-not-found]
from stage_oracle_edits import stage

BASE = Path('/opt/wsp-isolation')
MODEL = BASE / 'model-79eaaa84125b897f5a0ad6638362b864fec813ad'


def practice_items(ids):
    # Deliberately never opens mixed/dev/sealed files.
    rows = [json.loads(x) for x in (BASE / 'practice/toolchoice_practice.jsonl').read_text().splitlines()]
    assert len(rows) == 1213 and all(x['split'] == 'practice' for x in rows)
    by_id = {x['id']: x for x in rows}
    if len(ids) != len(set(ids)) or any(i not in by_id for i in ids):
        raise ValueError('practice ids only; unique ids required')
    return [by_id[i] for i in ids]


def main():
    source, output = map(Path, sys.argv[1:])
    output.mkdir(exist_ok=False)
    start = time.monotonic()
    staged = stage(MODEL, source, BASE / 'trusted-snapshots')
    snapshot = Path(staged['snapshot'])
    fixture = [json.loads(x) for x in (BASE / 'practice/toolchoice_practice.jsonl').read_text().splitlines()]
    ids = [next(x['id'] for x in fixture if x['kind'] == kind) for kind in ('choose', 'abstain')]
    rows = practice_items(ids)
    try:
        practice_items(['not-a-practice-id'])
        raise AssertionError('unknown id accepted')
    except ValueError:
        pass
    items = [{'id': r['id'], 'messages': [{'role': 'system', 'content': T.SYSTEM},
              {'role': 'user', 'content': r['user']}], 'tools': T.to_openai_tools(r['tools'])} for r in rows]
    C.model_dir = lambda target: MODEL
    arms = {}
    for arm, edits in [('unedited', None), ('staged_edit', str(snapshot))]:
        out = output / arm
        out.mkdir()
        req = {'target': 'functiongemma-270m', 'edit_dir': edits, 'items': items,
               'max_tokens': 16, 'n': 1, 'seed': 1729}
        meta = gpu.generate(req, out)
        gen = [json.loads(x) for x in (out / 'gen.jsonl').read_text().splitlines()]
        assert [x['id'] for x in gen] == ids
        arms[arm] = {'meta': meta, 'n': len(gen), 'tokens': sum(x['tokens'] for x in gen),
                     'cut': sum(x['cut'] for x in gen),
                     'generation_sha256': hashlib.sha256((out / 'gen.jsonl').read_bytes()).hexdigest()}
    report = {'scope': 'trusted one-entry edit, paired practice generation transport smoke only',
              'n_per_arm': 2, 'max_tokens': 16, 'arms': arms, 'staging': staged,
              'unknown_id_rejected': True, 'split': 'practice', 'ci': None,
              'ci_reason': 'deterministic engineering smoke, not accuracy estimate',
              'wall_s': round(time.monotonic() - start, 2),
              'limitations': ['truncated generations not quality scores', 'no AI editor run',
                              'not session RPC integrated', 'editor must be stopped before staging']}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
