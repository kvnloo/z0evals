"""Trusted root-only snapshot gate. Never run editor code in this process.

Copy bounded regular files with no-follow opens into a root-owned staging root,
validate the COPIED bytes, and publish read-only. Source mutation cannot alter
published bytes. Run only after all editor processes for the session have exited.
Usage: sudo python stage_oracle_edits.py MODEL EDITS STAGING_ROOT
"""
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

from validate_oracle_edits import MAX_BYTES, MAX_TOTAL, validate


def stage(model, source, destination):
    if os.geteuid() != 0:
        raise PermissionError('trusted root launcher required')
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError('linked staging root')
    destination.mkdir(mode=0o755, parents=True, exist_ok=True)
    info = destination.stat()
    if info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError('staging root must be root-owned and not group/world writable')
    # Directory FD pins the source, and relative no-follow opens reject links.
    directory = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    temp = Path(tempfile.mkdtemp(prefix='.pending-', dir=destination))
    try:
        names = os.listdir(directory)
        if not names or len(names) > 256:
            raise ValueError('empty or excessive edit set')
        total = 0
        for name in names:
            if not name.endswith('.npy'):
                raise ValueError('unexpected artifact')
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(fd, 'rb') as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise ValueError('not a single-link regular file')
                if before.st_size > MAX_BYTES:
                    raise ValueError('file cap exceeded')
                with (temp / name).open('xb') as output:
                    count = 0
                    while True:
                        chunk = stream.read(min(1024 * 1024, MAX_BYTES + 1 - count))
                        if not chunk:
                            break
                        count += len(chunk)
                        total += len(chunk)
                        if count > MAX_BYTES or total > MAX_TOTAL:
                            raise ValueError('copy cap exceeded')
                        output.write(chunk)
                after = os.fstat(stream.fileno())
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise ValueError('source mutated during copy')
        manifest = validate(model, temp)
        for path in temp.iterdir():
            path.chmod(0o444)
        temp.chmod(0o555)
        final = destination / temp.name.replace('.pending-', 'snapshot-', 1)
        temp.rename(final)
        return {'snapshot': str(final), 'manifest': manifest,
                'authority': 'artifact validation only, not scientific edit approval'}
    except BaseException:
        temp.chmod(0o700)
        shutil.rmtree(temp)
        raise
    finally:
        os.close(directory)


if __name__ == '__main__':
    print(json.dumps(stage(*sys.argv[1:]), indent=2))
