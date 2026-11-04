"""Adversarial synthetic fixtures, not model quality data. Run on public worker."""
import json
from pathlib import Path
import tempfile
import numpy as np
from safetensors.numpy import save_file
from validate_oracle_edits import validate


def main():
    checks = {}
    with tempfile.TemporaryDirectory(prefix='wsp-validator-') as tmp:
        root = Path(tmp)
        model = root / 'model'
        model.mkdir()
        name = 'model.layers.0.mlp.down_proj.weight'
        frozen = 'model.embed_tokens.weight'
        save_file({name: np.ones((2, 3), dtype=np.float32), frozen: np.ones((2, 3), dtype=np.float32)},
                  model / 'model.safetensors')
        for case in ['valid', 'empty', 'unknown', 'frozen', 'shape', 'nan', 'inf', 'integer', 'object', 'symlink', 'hardlink', 'directory']:
            edits = root / case
            edits.mkdir()
            file = edits / (name + '.npy')
            value = np.ones((2, 3), dtype=np.float32)
            if case == 'unknown': file = edits / 'model.unknown.npy'
            if case == 'frozen': file = edits / (frozen + '.npy')
            if case == 'shape': value = np.ones((3, 2), dtype=np.float32)
            if case == 'nan': value[0, 0] = np.nan
            if case == 'inf': value[0, 0] = np.inf
            if case == 'integer': value = value.astype(np.int32)
            if case == 'object': value = np.array([object()])
            if case not in ['empty', 'directory']:
                np.save(file, value)
            if case == 'directory': file.mkdir()
            if case in ['symlink', 'hardlink']:
                original = root / (case + '-target.npy')
                file.rename(original)
                if case == 'symlink': file.symlink_to(original)
                else:
                    import os
                    os.link(original, file)
            try:
                result = validate(model, edits)
                checks[case] = case == 'valid' and len(result['accepted']) == 1
            except (ValueError, OSError):
                checks[case] = case != 'valid'
    print(json.dumps({'fixture': 'synthetic tensor security checks, not accuracy', 'n': len(checks),
                      'checks': checks, 'passed': sum(checks.values()), 'ci': None}, indent=2))
    assert all(checks.values()), checks


if __name__ == '__main__':
    main()
