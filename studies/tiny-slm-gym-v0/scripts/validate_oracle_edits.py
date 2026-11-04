"""Trusted pre-inference gate; run capped on the worker, never inside editor Python.

Validates artifacts only, not the scientific justification or no-training rule.
Usage: python validate_oracle_edits.py MODEL_DIR EDIT_DIR
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

import numpy as np
from safetensors import safe_open

FROZEN = re.compile(r'(^|\.)(norm\.weight|embed_tokens\.weight)$|^lm_head\.weight$')
MAX_BYTES = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024


def validate(model, edits):
    model, edits = Path(model), Path(edits)
    if edits.is_symlink() or not edits.is_dir():
        raise ValueError('edit directory must be a real directory')
    files = list(edits.iterdir())
    if not files or len(files) > 256:
        raise ValueError('empty or excessive edit set')
    shapes = {}
    for shard in model.glob('*.safetensors'):
        with safe_open(str(shard), framework='np') as source:
            shapes.update({name: tuple(source.get_slice(name).get_shape()) for name in source.keys()})
    total, accepted = 0, []
    for path in sorted(files):
        name = path.stem
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        fd = os.open(path, flags)
        with os.fdopen(fd, 'rb') as stream:
            meta = os.fstat(stream.fileno())
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise ValueError('not a single-link regular file')
            total += meta.st_size
            if meta.st_size > MAX_BYTES or total > MAX_TOTAL:
                raise ValueError('edit storage cap exceeded')
            if path.suffix != '.npy' or name not in shapes or not name.startswith('model.') or FROZEN.search(name):
                raise ValueError('unknown or frozen tensor: ' + name)
            value = np.load(stream, allow_pickle=False, max_header_size=16384)
            if value.shape != shapes[name] or value.dtype.kind != 'f' or value.dtype.itemsize > 4:
                raise ValueError('shape or dtype mismatch: ' + name)
            if not np.isfinite(value).all():
                raise ValueError('nonfinite values: ' + name)
            stream.seek(0)
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            accepted.append({'tensor': name, 'shape': list(value.shape), 'dtype': str(value.dtype),
                             'bytes': meta.st_size, 'sha256': digest})
    return {'accepted': accepted, 'total_bytes': total,
            'note': 'Copy validated files into a controller-owned immutable staging directory before inference; '
                    'this manifest alone does not prevent later mutation. Scientific edit-scope audit is separate.'}


if __name__ == '__main__':
    print(json.dumps(validate(*sys.argv[1:]), indent=2))
