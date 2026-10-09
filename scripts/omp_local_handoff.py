#!/usr/bin/env python3
"""Pinned local OMP preflight/capture. Never runs inference or reads provider secrets."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import stat
import sys
import omp_capture as capture

HANDOFF = 'a81a94ff590d627473eacbefd5c9438b86c9b63fdc3afdab084f54998f89f62f'
SOURCE = '532a444ffaaa8de3623d4c97d77eaff8b5e34313'
REGISTRY = '172e06830af7a3cea88e7390264433506fad0c77'
DEPENDENCIES = {
    'run-native.py': '4a51c6de5719e10f8007f8d98e080c259e38d741e2d9d1c50405db350992d77d',
    'qualify-r13.py': '41b51d6b41c0cb5374b343b0db298d81cb2ca40f5d43706cb937f6a84ddaf2be',
    'qualify-base.py': '5fefe126c00c551770dcb8510a9bb4002a26878bb3ca7b9e635dfcdee11c2ac1',
    'omp_qualification_paths.py': 'd372708a153dc6e3ac8ebbeb838774c0921d62349354b06f91a1dcfe92830323',
    'omp-launcher-paths.patch': '7f416cf1c3e49e528647dce968dc0df8dac94d6d71aead5e01785e8d3d2b2893',
    'omp-launcher-paths.provenance.json': '2808f53bccc890622126a81e968329920ae862c96affc18b212b3de549525010',
    'test_omp_reuse_oracle.py': 'f053f708a297b05c50fb779d8d332de74dfc0e5ca52f7982016bb50210b2293b',
}
ROLE_FILES = {'launcher': 'qualify-r13.py', 'launcher_base': 'qualify-base.py',
              'path_helper': 'omp_qualification_paths.py', 'task_oracle': 'test_omp_reuse_oracle.py'}


def provider_present(raw):
    # Metadata only: do not open, hash, parse, copy, or export provider configuration.
    path = Path(raw).absolute()
    capture.require(not any(p.is_symlink() for p in (path, *path.parents)), 'provider symlink')
    info = path.stat()
    capture.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                    and info.st_mode & 0o077 == 0, 'provider file must be private and locally owned')


def preflight(release, spec_path, provider_config):
    release = Path(release)
    provider_present(provider_config)
    provider = Path(provider_config)
    # Reject aliases/hardlinks before any evidence bytes are read.
    for path in [Path(spec_path), *(release / n for n in ('handoff.json', *DEPENDENCIES))]:
        capture.require(not path.exists() or not path.samefile(provider), 'provider cannot be an evidence input')
    for name, digest in {'handoff.json': HANDOFF, **DEPENDENCIES}.items():
        path = capture.plain_file(str(release / name))
        capture.require(capture.sha256(path) == digest, 'canonical bundle mismatch')
    spec = capture.read_json(spec_path)
    capture.require(spec.get('evidence_kind') != 'synthetic_fixture', 'fixtures are not original evidence')
    for row in spec.get('files', {}).values():
        path = Path(row['path'])
        capture.require(not path.exists() or not path.samefile(provider), 'provider cannot be an evidence input')
    private, _ = capture.validate(spec)
    pins = {row['commit'] for row in private['sources']}
    capture.require({SOURCE, REGISTRY} <= pins, 'canonical source and registry checkouts required')
    capture.require(any(row['repo'] == 'kvnloo/z0intelligence' and row['commit'] == SOURCE
                        for row in private['sources']), 'canonical source binding required')
    for role, name in ROLE_FILES.items():
        capture.require(private['files'][role]['sha256'] == DEPENDENCIES[name], 'role is not canonical bundle dependency')
    # A hash verifies bytes, not event semantics, approvals, helper reuse or run truth.
    return spec


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'capture'))
    parser.add_argument('--release-dir', required=True)
    parser.add_argument('--spec', required=True)
    parser.add_argument('--provider-config', required=True, help='existing local file; metadata checked only')
    parser.add_argument('--manifest')
    parser.add_argument('--export')
    args = parser.parse_args(argv)
    try:
        capture.require(args.mode != 'capture' or (args.manifest and args.export), 'capture outputs required')
        capture.require(args.mode != 'preflight' or not (args.manifest or args.export), 'preflight writes nothing')
        spec = preflight(args.release_dir, args.spec, args.provider_config)
        if args.mode == 'capture':
            capture.capture(spec, args.manifest, args.export)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        print('BLOCKED: canonical bundle, source/registry pins, evidence spec, or private provider-file metadata failed. No OMP execution performed.', file=sys.stderr)
        return 2
    print('Local integrity checks passed. Provider usability, free route, EventLog 534 semantics, helper reuse, approvals and outcome remain unverified. No OMP execution performed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
