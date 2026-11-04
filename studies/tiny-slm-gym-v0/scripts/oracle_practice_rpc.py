"""Trusted Oracle CLI RPC: stdin request, controller-only snapshot/output args.
Invoke only after editor processes stop, under 4G/64-task/300s systemd cap.
Not exposed inside editor sandbox. No request-controlled paths or seeds.
"""
import json
from pathlib import Path
import sys

from oracle_practice_request import MAX_REQUEST, parse
from oracle_paired_practice import BASE, MODEL, practice_items, C, gpu, T
from validate_oracle_edits import validate


def main():
    snapshot, output = map(Path, sys.argv[1:])
    root = BASE / 'trusted-snapshots'
    if snapshot.is_symlink() or snapshot.resolve().parent != root.resolve():
        raise ValueError('controller snapshot required')
    for path in [snapshot, *snapshot.iterdir()]:
        st = path.lstat()
        if st.st_uid != 0 or st.st_mode & 0o222 or path.is_symlink():
            raise ValueError('immutable root-owned snapshot required')
    manifest = validate(MODEL, snapshot)
    raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
    if len(raw) > MAX_REQUEST:
        raise ValueError('request too large')
    fixture = [json.loads(x) for x in (BASE / 'practice/toolchoice_practice.jsonl').read_text().splitlines()]
    req = parse(raw.decode('utf-8'), {x['id'] for x in fixture if x['split'] == 'practice'})
    rows = practice_items(req['ids'])
    items = [{'id': r['id'], 'messages': [{'role': 'system', 'content': T.SYSTEM},
              {'role': 'user', 'content': r['user']}], 'tools': T.to_openai_tools(r['tools'])} for r in rows]
    output.mkdir(exist_ok=False)
    C.model_dir = lambda target: MODEL
    # Per-call fresh checkpoint cache prevents accepting an editor-writable cache hit.
    C.STATE = output / 'controller-state'
    meta = gpu.generate({'target': 'functiongemma-270m', 'items': items, 'n': 1,
                         'max_tokens': req['max_tokens'], 'seed': 1729,
                         'edit_dir': str(snapshot) if req['arm'] == 'staged_edit' else None}, output)
    result = {'request': req, 'meta': meta, 'validated_tensors': len(manifest['accepted']),
              'scope': 'practice RPC engineering check, not quality evaluation'}
    (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
