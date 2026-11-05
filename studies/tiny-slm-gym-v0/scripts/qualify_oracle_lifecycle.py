"""Reproduce missing guard, then check the patch. Synthetic, not Oracle qualification.

Usage: python3 qualify_oracle_lifecycle.py BASELINE_TRANSPORT.py NEW_OUTPUT_DIR
The baseline is oracle_sandbox_exec.py from z0evals commit 39af35a.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASELINE_SHA256 = '169bb8c590ba815b74eec22803edd1251098a3c1ba6442febbd3dbcf3f4313be'


def main():
    baseline, output = map(Path, sys.argv[1:])
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != BASELINE_SHA256:
        raise ValueError('baseline is not the pinned pre-change transport')
    output.mkdir(exist_ok=False)
    test = Path(__file__).with_name('test_oracle_sandbox_lifecycle.py')
    results = {}
    for arm, path in [('before', baseline.resolve()),
                      ('after', test.with_name('oracle_sandbox_exec.py').resolve())]:
        command = [sys.executable, str(test)]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=60,
                              env={**os.environ, 'ORACLE_TRANSPORT_UNDER_TEST': str(path)})
        log = proc.stdout + proc.stderr
        (output / (arm + '.log')).write_text(log)
        results[arm] = {'command': command, 'transport': str(path), 'exit_code': proc.returncode,
                       'transport_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        results[arm]['expected_result'] = (
            proc.returncode != 0 and 'timeout must stop the worker, not just systemd-run' in log if arm == 'before'
            else proc.returncode == 0 and 'Ran 17 tests' in log and log.rstrip().endswith('OK'))
        print(f'{arm}: rc={proc.returncode}, expected_result={results[arm]["expected_result"]}')
    receipt = {'scope': 'synthetic lifecycle regression plus real child processes; not real systemd or Oracle',
               'results': results, 'passed': all(r['expected_result'] for r in results.values())}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if not receipt['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
