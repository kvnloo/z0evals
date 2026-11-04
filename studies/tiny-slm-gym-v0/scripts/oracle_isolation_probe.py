"""Run on Oracle only: trusted adversarial probes, never editor-generated code."""
import json
import pathlib
import subprocess
import tempfile

BASE = pathlib.Path('/opt/wsp-isolation')
CODE = r'''
import json, os, pathlib, socket
checks = {}
checks['unprivileged_uid'] = os.getuid() == 65534
checks['no_capabilities'] = next(x.split()[1] for x in open('/proc/self/status') if x.startswith('CapEff:')) == '0000000000000000'
checks['host_home_hidden'] = not pathlib.Path('/home/ubuntu/.ssh').exists()
checks['host_etc_hidden'] = not pathlib.Path('/etc/shadow').exists()
checks['clean_environment'] = 'PROBE_HOST_SECRET' not in os.environ
for name, path in [('model_readonly', '/model/probe'), ('practice_readonly', '/practice/probe'), ('root_readonly', '/usr/probe')]:
    try:
        pathlib.Path(path).write_text('bad')
        checks[name] = False
    except OSError:
        checks[name] = True
pathlib.Path('/work/output').write_text('ok')
checks['work_writable'] = pathlib.Path('/work/output').read_text() == 'ok'
checks['practice_readable'] = pathlib.Path('/practice/probe').read_text() == 'public practice fixture'
s = socket.socket()
s.settimeout(2)
try:
    s.connect(('1.1.1.1', 443))
    checks['network_blocked'] = False
except OSError:
    checks['network_blocked'] = True
checks['only_loopback_interface'] = set(os.listdir('/sys/class/net')) <= {'lo'} if pathlib.Path('/sys/class/net').exists() else True
import torch, numpy, safetensors
checks['torch_usable'] = float(torch.ones(2).sum()) == 2
print(json.dumps({'checks': checks, 'torch': torch.__version__, 'uid': os.getuid()}))
assert all(checks.values()), checks
'''

def main():
    with tempfile.TemporaryDirectory(dir=BASE, prefix='isolation-probe-') as tmp:
        root = pathlib.Path(tmp)
        root.chmod(0o755)
        for name in ('model', 'practice', 'work'):
            (root / name).mkdir(mode=0o777)
            (root / name).chmod(0o777)
        (root / 'practice/probe').write_text('public practice fixture')
        cmd = ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--collect',
               '-p', 'MemoryMax=2G', '-p', 'TasksMax=64', '-p', 'RuntimeMaxSec=60',
               '/usr/bin/bwrap', '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
               '--ro-bind', '/usr', '/usr', '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/bin', '/bin',
               '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
               '--ro-bind', str(BASE / '.venv'), str(BASE / '.venv'),
               '--ro-bind', str(root / 'model'), '/model',
               '--ro-bind', str(root / 'practice'), '/practice',
               '--bind', str(root / 'work'), '/work', '--chdir', '/work',
               '--uid', '65534', '--gid', '65534', '--cap-drop', 'ALL',
               '--setenv', 'HOME', '/tmp', '--setenv', 'OMP_NUM_THREADS', '2',
               str(BASE / '.venv/bin/python'), '-I', '-c', CODE]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=80,
                           env={**__import__('os').environ, 'PROBE_HOST_SECRET': 'synthetic-canary'})
        result = {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr,
                  'limits': {'memory_bytes': 2147483648, 'tasks': 64, 'runtime_seconds': 60},
                  'scope': 'trusted fixture probe only; not yet an editor backend or actual model smoke'}
        print(json.dumps(result, indent=2))
        raise SystemExit(p.returncode)

if __name__ == '__main__':
    main()
