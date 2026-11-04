"""Oracle-only trusted smoke of the actual editing prelude and public practice mount."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0, '/home/ubuntu/wsp/slm')
from sandbox import PRELUDE  # type: ignore[import-not-found]
from common import TARGETS  # type: ignore[import-not-found]

BASE = Path('/opt/wsp-isolation')
REV = '79eaaa84125b897f5a0ad6638362b864fec813ad'
MODEL = BASE / ('model-' + REV)
PRACTICE = BASE / 'practice'
RUN = BASE / ('model-smoke-' + str(time.time_ns()))
SNAP = Path('/home/ubuntu/hf/hub/models--unsloth--functiongemma-270m-it/snapshots') / REV
MODEL.mkdir(exist_ok=True)
for src in SNAP.iterdir():
    if src.is_file() and not (MODEL / src.name).exists():
        shutil.copyfile(src.resolve(), MODEL / src.name)
PRACTICE.mkdir(exist_ok=True)
rows = [json.loads(line) for line in Path('/home/ubuntu/toolchoice/items.jsonl').read_text().splitlines()]
rows = [r for r in rows if r['split'] == 'practice']
assert len(rows) == 1213
practice = PRACTICE / 'toolchoice_practice.jsonl'
practice.write_text(''.join(json.dumps(r) + '\n' for r in rows))
RUN.mkdir(mode=0o777)
RUN.chmod(0o777)
(RUN / '.sandbox.json').write_text(json.dumps(TARGETS['functiongemma-270m']))
code = r'''
import hashlib
assert len(practice('toolchoice_practice.jsonl')) == 1213
name = next(n for n in NAMES if not _FROZEN.search(n) and len(SHAPES[n]) == 2)
a = load_original(name)
b = a.clone()
b.view(-1)[0] += 0.125
message = save_edit(name, b)
assert torch.equal(load(name), b)
assert torch.equal(load_original(name), a)
assert len(edited()) == 1
frozen = next(n for n in NAMES if _FROZEN.search(n))
try:
    save_edit(frozen, load_original(frozen))
    raise RuntimeError('frozen edit accepted')
except AssertionError:
    pass
try:
    open('/model/probe-write', 'w')
    raise RuntimeError('model write accepted')
except OSError:
    pass
print(json.dumps({'tensor': name, 'shape': list(a.shape), 'tensor_count': len(NAMES),
                  'edited_entries': int((a != b).sum()), 'roundtrip_equal': True,
                  'original_unchanged': True, 'frozen_rejected': True,
                  'practice_items': 1213, 'uid': os.getuid(), 'message': message}))
'''
cmd = ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--collect',
       '-p', 'MemoryMax=4G', '-p', 'TasksMax=64', '-p', 'RuntimeMaxSec=60',
       '/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
       '--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/bin', '/bin',
       '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
       '--ro-bind', str(BASE / '.venv'), str(BASE / '.venv'),
       '--ro-bind', str(MODEL), '/model', '--ro-bind', str(PRACTICE), '/practice',
       '--bind', str(RUN), '/work', '--chdir', '/work',
       '--uid', '65534', '--gid', '65534', '--cap-drop', 'ALL',
       '--setenv', 'HOME', '/tmp', '--setenv', 'OMP_NUM_THREADS', '2',
       str(BASE / '.venv/bin/python'), '-I', '-c', PRELUDE + '\n' + code]
t0 = time.time()
p = subprocess.run(cmd, capture_output=True, text=True, timeout=80)
print(json.dumps({'returncode': p.returncode, 'wall_s': round(time.time() - t0, 2),
                  'stdout': p.stdout, 'stderr': p.stderr, 'model_revision': REV,
                  'practice_sha256': hashlib.sha256(practice.read_bytes()).hexdigest(),
                  'work': str(RUN), 'scope': 'trusted one-entry smoke edit only, not an editor improvement',
                  'limits': {'memory_bytes': 4 << 30, 'tasks': 64, 'runtime_seconds': 60}}, indent=2))
raise SystemExit(p.returncode)
