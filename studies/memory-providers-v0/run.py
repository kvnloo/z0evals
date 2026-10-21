#!/usr/bin/env python3
"""Synthetic-only native retrieval probes. No hosted upload implementation."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request


def stamp(value):
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('provider', choices=['hermes', 'ctx', 'tencent'])
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--hermes-source', type=Path)
    p.add_argument('--repeats', type=int, default=5)
    a = p.parse_args()
    a.state = a.state.resolve()
    db = None
    fixture = json.loads((Path(__file__).parent / 'data/synthetic.json').read_text())
    assert fixture['privacy'] == 'synthetic-public'
    a.state.mkdir(parents=True, exist_ok=True)
    docs = fixture['documents']
    start = time.perf_counter()
    if a.provider == 'hermes':
        sys.path.insert(0, str(a.hermes_source))
        from hermes_state import SessionDB
        from tools.session_search_tool import session_search
        db = SessionDB(a.state / 'state.db')
        for d in docs:
            db.create_session(d['id'], 'cli')
            db.append_message(d['id'], 'user', d['text'], timestamp=stamp(d['at']))

        def hermes_search(q):
            r = json.loads(session_search(q, limit=5, db=db))
            if r.get('success') is False:
                raise RuntimeError(r)
            return [x['session_id'] for x in r['results']]
        search = hermes_search
    elif a.provider == 'ctx':
        records = [{'record_type': 'manifest', 'schema_version': 'ctx-history-jsonl-v2'},
                   {'record_type': 'source', 'source_id': 'synthetic', 'provider_key': 'memoryeval',
                    'source_format': 'synthetic', 'trust': 'synthetic'}]
        for d in docs:
            records += [
                {'record_type': 'session', 'source_id': 'synthetic', 'provider_session_id': d['id'],
                 'started_at': d['at'], 'agent_scope': 'primary'},
                {'record_type': 'event', 'source_id': 'synthetic', 'provider_session_id': d['id'],
                 'event_index': 0, 'event_type': 'message', 'role': 'user',
                 'occurred_at': d['at'], 'payload': {'text': d['text']}}]
        history = a.state / 'history.jsonl'
        history.write_text(''.join(json.dumps(r) + '\n' for r in records))
        ctx_root = a.state / 'ctx-root'
        ctx_root.mkdir(exist_ok=True)
        config = ctx_root / 'config.toml'
        if not config.exists():
            config.write_text('[sources]\nautomatic = false\n[indexing]\nmode = "manual"\n'
                              '[analytics]\nenabled = false\n[upgrade]\nauto = "off"\n')
        env = dict(os.environ, CTX_DATA_ROOT=str(ctx_root), CTX_DAEMON_ENABLED='false',
                   CTX_ANALYTICS_ENABLED='false', CTX_UPGRADE_AUTO='off')
        r = subprocess.run(['ctx', 'import', '--input-format', 'ctx-history-jsonl-v2',
                            '--path', str(history), '--format', 'json'],
                           env=env, capture_output=True, text=True, timeout=90)
        (a.state / 'import.log').write_text(r.stdout + r.stderr)
        r.check_returncode()

        def ctx_search(q):
            r = subprocess.run(['ctx', 'search', q, '--provider-key', 'memoryeval',
                                '--source-id', 'synthetic', '--refresh', 'off', '--limit', '5',
                                '--format', 'json'], env=env, capture_output=True, text=True, timeout=30)
            r.check_returncode()
            return [x['provider_session_id'] for x in json.loads(r.stdout)['results']]
        search = ctx_search
    else:
        # Separate synthetic tenant. Never use the owner's live/default tenancy.
        def post(path, body):
            body = dict(body, team_id='memory-eval-public-20261021', agent_id='eval', user_id='synthetic')
            req = urllib.request.Request('http://127.0.0.1:8420/v3/' + path,
                data=json.dumps(body).encode(), headers={'Content-Type': 'application/json',
                'Authorization': 'Bearer local', 'x-tdai-service-id': 'default'}, method='POST')
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.load(res)
            if data.get('code') != 0:
                raise RuntimeError(data)
            return data['data']
        for d in docs:
            post('conversation/add', {'session_id': d['id'], 'messages': [
                {'role': 'user', 'content': d['text'], 'timestamp': d['at']}]})

        def tencent_search(q):
            r = post('conversation/search', {'query': q, 'limit': 5})
            ids = []
            for x in r['messages']:
                text = x.get('content', '')
                for d in docs:
                    if d['text'] == text and d['id'] not in ids:
                        ids.append(d['id'])
            return ids
        search = tencent_search
    ingest = time.perf_counter() - start
    rows = []
    for repeat in range(a.repeats):
        for q in fixture['queries']:
            started = time.perf_counter()
            ids = search(q['query'])
            rows.append({'query_id': q['id'], 'repeat': repeat, 'ids': ids,
                         'latency_ms': (time.perf_counter() - started) * 1000})
    result = {'provider': a.provider, 'corpus': 'synthetic-public', 'k': 5,
              'ingest_seconds': ingest, 'rows': rows,
              'scope': 'retrieval only; no answer-generation or temporal resolver'}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'provider': a.provider, 'rows': len(rows), 'output': str(a.output)}))
    if db is not None:
        db.close()


if __name__ == '__main__':
    main()
