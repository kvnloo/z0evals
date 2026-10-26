#!/usr/bin/env python3
"""Cold-agent recall arm for unified-memory-v0 (cohort v1).

A fresh Claude Code agent (no CLAUDE.md, no auto memory, no settings, no built-in tools,
no session persistence) answers each question using ONLY the memory MCP named in
$COLD_MCP_CONFIG. Scoring is deterministic: every `must` group needs one alternative
as a case-insensitive substring of the answer. No judge model.

usage: COLD_MCP_CONFIG=mcp.json PAR=3 run_cold.py <questions.json> <results.json> [ids]
Questions and results carry private transcript facts: keep them OUT of this repo.
"""
import json, subprocess, sys, os, time, concurrent.futures as cf
here = os.path.dirname(os.path.abspath(__file__))
Q = json.load(open(sys.argv[1])); out = sys.argv[2]; only = set(sys.argv[3].split(',')) if len(sys.argv) > 3 and sys.argv[3] else None
PROMPT = ("You are a fresh agent with no prior context. Answer this question about the owner's past work, which happened in "
          "some earlier agent session (possibly a different harness or machine). Use the memory tools if you have any. "
          "Do not guess: if you cannot find evidence, say UNKNOWN.\n\nQuestion: {q}\n\n"
          "End with exactly two lines:\nANSWER: <short answer or UNKNOWN>\nHANDLE: <the memory handle/session id that holds the evidence, or none>")
env = dict(os.environ, CLAUDE_CODE_DISABLE_CLAUDE_MDS='1', CLAUDE_CODE_DISABLE_AUTO_MEMORY='1')
def run(q):
    cmd = ['claude', '-p', PROMPT.format(q=q['q']), '--model', 'sonnet', '--strict-mcp-config', '--mcp-config', os.environ["COLD_MCP_CONFIG"],
           '--tools', '', '--allowedTools', 'mcp__z0int-memory', '--setting-sources', '', '--no-session-persistence', '--output-format', 'json']
    cwd = os.environ.get('COLD_CWD', os.path.join(here, 'empty')); os.makedirs(cwd, exist_ok=True)
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=300)
        r = json.loads(p.stdout) if p.stdout.strip().startswith('{') else {'result': p.stdout[-2000:], 'err': p.stderr[-1000:]}
    except subprocess.TimeoutExpired:
        r = {'result': 'TIMEOUT'}
    ans = r.get('result') or ''
    low = ans.lower()
    ok = all(any(a.lower() in low for a in g) for g in q['must'])
    unk = 'unknown' in low.split('answer:')[-1] if 'answer:' in low else 'unknown' in low
    return {'id': q['id'], 'source_harness': q['source_harness'], 'source_host': q['source_host'], 'gold_handle': q['handle'],
            'correct': ok, 'said_unknown': unk, 'false_confident': (not ok) and (not unk), 'cites_gold': q['handle'].split(':',1)[1][:12] in ans,
            'secs': round(time.time() - t0, 1), 'num_turns': r.get('num_turns'), 'cost_usd': r.get('total_cost_usd'), 'answer': ans[-600:]}
qs = [q for q in Q if not only or q['id'] in only]
with cf.ThreadPoolExecutor(int(os.environ.get('PAR', '2'))) as ex:
    res = list(ex.map(run, qs))
json.dump(res, open(out, 'w'), indent=1)
for r in res: print(r['id'], r['source_host'], r['source_harness'], 'OK' if r['correct'] else ('UNK' if r['said_unknown'] else 'WRONG'), r['secs'], 's', r['num_turns'], 'turns')
n = len(res); c = sum(r['correct'] for r in res)
print(f"SCORE {c}/{n} = {c/n:.0%}  false_confident={sum(r['false_confident'] for r in res)}  cites_gold={sum(r['cites_gold'] for r in res)}")
