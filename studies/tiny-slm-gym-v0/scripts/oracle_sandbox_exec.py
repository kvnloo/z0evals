"""Oracle-side code transport. Install with trusted harness; stdin is confined Python.

Usage: python3 oracle_sandbox_exec.py RUN_ID < code.py
Only the public pinned model and practice snapshot are visible to submitted code.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0, '/home/ubuntu/wsp/slm')
from sandbox import PRELUDE  # type: ignore[import-not-found]
from common import TARGETS  # type: ignore[import-not-found]


def main():
    run_id = sys.argv[1]
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', run_id):
        raise ValueError('invalid run id')
    code = sys.stdin.read(200001)
    if len(code) > 200000:
        raise ValueError('code too large')
    base = Path('/opt/wsp-isolation')
    model = base / 'model-79eaaa84125b897f5a0ad6638362b864fec813ad'
    practice = base / 'practice'
    assert (model / 'model.safetensors').is_file()
    assert (practice / 'toolchoice_practice.jsonl').is_file()
    work = base / ('session-' + run_id)
    work.mkdir(mode=0o777, exist_ok=True)
    work.chmod(0o777)
    config = work / '.sandbox.json'
    expected = json.dumps(TARGETS['functiongemma-270m'])
    if not config.exists():
        config.write_text(expected)
    assert config.read_text() == expected, 'config changed'
    cmd = ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--collect',
           '-p', 'MemoryMax=4G', '-p', 'TasksMax=64', '-p', 'RuntimeMaxSec=600',
           '-p', 'LimitFSIZE=67108864',
           '/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
           '--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/bin', '/bin',
           '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
           '--ro-bind', str(base / '.venv'), str(base / '.venv'),
           '--ro-bind', str(model), '/model', '--ro-bind', str(practice), '/practice',
           '--bind', str(work), '/work', '--chdir', '/work',
           '--uid', '65534', '--gid', '65534', '--cap-drop', 'ALL',
           '--setenv', 'HOME', '/tmp', '--setenv', 'OMP_NUM_THREADS', '2',
           str(base / '.venv/bin/python'), '-I', '-c', PRELUDE + '\n' + code]
    t0 = time.time()
    # Spool output to a worker-local file: do not buffer untrusted output in memory.
    log = work / ('transport-' + str(time.time_ns()) + '.log')
    with log.open('w+') as stream:
        try:
            p = subprocess.run(cmd, stdout=stream, stderr=stream, timeout=620)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = 124
        stream.seek(0)
        out = stream.read(10000)
    print(json.dumps({'returncode': rc, 'wall_s': round(time.time()-t0, 2),
                      'out': out, 'work': str(work), 'log': str(log)}))
    raise SystemExit(rc)


if __name__ == '__main__':
    main()
