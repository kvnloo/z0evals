#!/usr/bin/env python3
"""Allowlisted OMP evidence capture, integrity replay, and public-safe export.

Never executes a launcher, reads credentials, or promotes metadata to verified
success. Raw sources remain at explicitly supplied local paths. The private
manifest is not a portable witness bundle; replay requires the same source bytes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

# Reuse the repository's existing artifact hashing primitive.
from import_local import sha256

ROLES = ('launcher', 'launcher_base', 'path_helper', 'eventlog', 'witness',
         'task_oracle', 'owning_tests', 'run_metadata')
STATES = {'passed', 'failed', 'unknown'}
KINDS = {'synthetic_fixture', 'archival_run', 'fresh_run'}
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024
HEX40 = re.compile(r'[0-9a-f]{40}')
HEX64 = re.compile(r'[0-9a-f]{64}')
REPO = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')


def git(root, *args):
    # The import helper's git() inherits stderr, which can disclose local paths.
    # Keep that transport quiet here; expected pins are validated below.
    try:
        return subprocess.check_output(['git', '-C', str(root), *args],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError as error:
        raise ValueError('source repository unavailable') from error


def require(condition, message):
    if not condition:
        raise ValueError(message)


def plain_file(raw):
    require(isinstance(raw, str) and raw, 'input path is required')
    path = Path(raw).absolute()
    # Reject symlinks in every component, and reserved credential/session areas.
    for component in (path, *path.parents):
        require(not component.is_symlink(), 'symlink input is not allowed')
        require(component.name not in {'.aws', '.ssh', '.codex', '.env'},
                'credential/session area is not an evidence input')
    require(path.is_file(), 'required input file is missing')
    require(stat.S_ISREG(path.stat().st_mode), 'input must be a regular file')
    require(path.stat().st_size <= MAX_FILE_BYTES, 'input exceeds 64 MiB bound')
    return path.resolve()


def read_json(path):
    path = plain_file(str(path))
    require(path.stat().st_size <= MAX_METADATA_BYTES, 'JSON control input exceeds 1 MiB bound')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def number(value, *, integer=False):
    require(value is None or (
        type(value) in ({int} if integer else {int, float})
        and math.isfinite(value) and value >= 0), 'measurement must be nonnegative or null')
    return value


def metrics(data):
    require(isinstance(data, dict), 'run metadata must be an object')
    require(all(k in data for k in ('correctness', 'first_turn', 'owning_tests_passed', 'latency_ms', 'tokens')),
            'missing run metadata dimensions; use explicit null/unknown when unmeasured')
    for key in ('correctness', 'first_turn'):
        require(isinstance(data[key], str) and data[key] in STATES, 'invalid outcome state')
    tokens = data['tokens']
    require(isinstance(tokens, dict) and all(k in tokens for k in ('input', 'output', 'cache_read', 'reasoning')),
            'missing token dimensions; use explicit null when unmeasured')
    # Exact typed projection, not a blacklist: unknown fields and arbitrary text
    # never enter the public document, including private prompts and credentials.
    return {'correctness': data['correctness'], 'first_turn': data['first_turn'],
            'owning_tests_passed': number(data['owning_tests_passed'], integer=True),
            'latency_ms': number(data['latency_ms']),
            'tokens': {key: number(tokens[key], integer=True)
                       for key in ('input', 'output', 'cache_read', 'reasoning')}}


def validate(spec):
    require(isinstance(spec, dict) and type(spec.get('version')) is int and spec['version'] == 1, 'unsupported capture specification')
    require(isinstance(spec.get('evidence_kind'), str) and spec['evidence_kind'] in KINDS, 'explicit evidence_kind is required')
    files = spec.get('files')
    require(isinstance(files, dict) and set(files) == set(ROLES),
            'exact required roles: ' + ', '.join(ROLES))
    records = {}
    for role in ROLES:
        row = files[role]
        require(isinstance(row, dict) and set(row) == {'path', 'sha256'}, 'invalid file binding')
        require(isinstance(row['sha256'], str) and HEX64.fullmatch(row['sha256']), 'expected SHA-256 required')
        path = plain_file(row['path'])
        require(sha256(path) == row['sha256'], 'input hash mismatch: ' + role)
        records[role] = {'path': str(path), 'sha256': row['sha256']}
    sources = spec.get('sources')
    require(isinstance(sources, list) and sources, 'pinned source repositories are required')
    source_rows = []
    for row in sources:
        require(isinstance(row, dict) and set(row) in (
            {'repo', 'root', 'commit'},
            {'repo', 'root', 'commit', 'observed_head', 'worktree_dirty'}), 'invalid source binding')
        require(isinstance(row['repo'], str) and REPO.fullmatch(row['repo']), 'invalid repository identity')
        require(isinstance(row['commit'], str) and HEX40.fullmatch(row['commit']), 'full source commit required')
        require(isinstance(row['root'], str), 'source root required')
        root = Path(row['root']).resolve(strict=True)
        resolved = git(root, 'rev-parse', '--verify', '--quiet', row['commit'] + '^{commit}')
        require(resolved == row['commit'], 'source commit unavailable')
        head = git(root, 'rev-parse', 'HEAD')
        dirty = bool(git(root, 'status', '--porcelain', '--untracked-files=normal'))
        if spec['evidence_kind'] == 'fresh_run':
            require(head == row['commit'] and not dirty, 'fresh-run source must be clean at declared commit')
        if 'observed_head' in row:
            require(row['observed_head'] == head and type(row['worktree_dirty']) is bool
                    and row['worktree_dirty'] == dirty, 'source checkout state changed since capture')
        source_rows.append({'repo': row['repo'], 'root': str(root), 'commit': row['commit'],
                            'observed_head': head, 'worktree_dirty': dirty})
    projection = metrics(read_json(records['run_metadata']['path']))
    # Recheck bytes after projection, never hash one metadata version and export another.
    for row in records.values():
        require(sha256(Path(row['path'])) == row['sha256'], 'input changed during capture')
    private = {'version': 1, 'evidence_kind': spec['evidence_kind'], 'sources': source_rows, 'files': records}
    public = {'version': 1, 'evidence_kind': spec['evidence_kind'],
              'actual_omp_run': 'not_executed_by_exporter',
              'measurement_status': 'source_reported_unverified',
              'replay_scope': 'source_integrity_and_export_only',
              'repository_identity': 'operator_asserted_not_verified',
              'source_binding': 'declared_commit_and_observed_checkout_not_execution_attestation',
              'sources': [{k: row[k] for k in ('repo', 'commit', 'observed_head', 'worktree_dirty')}
                          for row in source_rows],
              'artifacts': {role: {'sha256': records[role]['sha256']} for role in ROLES},
              'metrics': projection,
              'privacy': 'raw_sources_paths_prompts_and_unknown_fields_omitted',
              'credits': 'Existing Claude/human OMP implementation and owning verifiers unchanged.'}
    return private, public


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def output_path(path):
    path = Path(path).absolute()
    require(not path.exists() and not path.is_symlink(), 'output already exists; choose a new path')
    require(path.parent.is_dir(), 'output parent must already exist')
    require(not any(p.is_symlink() for p in path.parents), 'symlink output parent is not allowed')
    return path


def write_exclusive(path, data):
    # Exclusive creation prevents overwriting a source, another run, or symlink.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)


def capture(spec, manifest, export):
    manifest, export = output_path(manifest), output_path(export)
    require(manifest != export, 'private manifest and public export must differ')
    private, public = validate(spec)
    write_exclusive(manifest, encode(private))
    try:
        write_exclusive(export, encode(public))
    except Exception:
        manifest.unlink()  # Only the manifest created by this invocation.
        raise
    return public


def replay(manifest, export):
    export = output_path(export)
    _, public = validate(read_json(manifest))
    write_exclusive(export, encode(public))
    return public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    capture_parser = sub.add_parser('capture', help='hash explicit local inputs and emit a private manifest plus public summary')
    capture_parser.add_argument('--spec', type=Path, required=True)
    capture_parser.add_argument('--manifest', type=Path, required=True)
    capture_parser.add_argument('--export', type=Path, required=True)
    replay_parser = sub.add_parser('replay', help='revalidate original sources and reproduce the public summary; never execute OMP')
    replay_parser.add_argument('--manifest', type=Path, required=True)
    replay_parser.add_argument('--export', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode == 'capture':
            capture(read_json(args.spec), args.manifest, args.export)
        else:
            replay(args.manifest, args.export)
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Do not echo paths, file contents, JSON fragments or provider details.
        print('capture/export blocked: invalid, missing, changed, or unsafe input (' + type(error).__name__ + ')', file=sys.stderr)
        return 2
    print('Integrity/export complete. OMP execution and independent qualification were not performed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
