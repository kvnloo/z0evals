"""Trusted synthetic staging qualification; no private traces or held-out data."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from safetensors.numpy import save_file
from stage_oracle_edits import stage


def main():
    with tempfile.TemporaryDirectory(prefix='staging-test-', dir='/opt/wsp-isolation') as root:
        root = Path(root)
        root.chmod(0o755)
        model, edits = root / 'model', root / 'edits'
        model.mkdir(); edits.mkdir()
        name = 'model.layers.0.mlp.down_proj.weight'
        value = np.ones((2, 3), dtype=np.float32)
        save_file({name: value}, model / 'model.safetensors')
        np.save(edits / (name + '.npy'), value)
        receipt = stage(model, edits, root / 'trusted')
        snapshot = Path(receipt['snapshot'])
        # Mutating the source after publication must not affect inference bytes.
        np.save(edits / (name + '.npy'), value * 9)
        checks = {'snapshot_matches': bool(np.array_equal(np.load(snapshot / (name + '.npy')), value)),
                  'root_owned': snapshot.stat().st_uid == 0,
                  'dir_read_only': snapshot.stat().st_mode & 0o222 == 0,
                  'file_read_only': (snapshot / (name + '.npy')).stat().st_mode & 0o222 == 0}
        attempt = subprocess.run(['setpriv', '--reuid=65534', '--regid=65534', '--clear-groups',
                                  '/usr/bin/python3', '-c',
                                  'import sys; open(sys.argv[1], "wb").write(b"bad")',
                                  str(snapshot / (name + '.npy'))], capture_output=True)
        checks['editor_identity_write_denied'] = attempt.returncode != 0
        # Root can clean the owned fixture; no shared paths are removed.
        snapshot.chmod(0o755)
        for path in snapshot.iterdir(): path.chmod(0o644)
        result = {'n': len(checks), 'passed': sum(checks.values()), 'checks': checks,
                  'ci': None, 'scope': 'synthetic immutable staging, not inference or model improvement'}
        print(json.dumps(result, indent=2))
        assert all(checks.values()), result


if __name__ == '__main__': main()
