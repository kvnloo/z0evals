/* UNIT-only native HTTP capture checks. No provider and no model. */
import { test, expect } from 'bun:test';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import * as runner from '../runtime.mjs';

test('native fetch capture preserves request and original streaming response without headers', async () => {
  expect(typeof runner.captureFetch).toBe('function');
  const dir = mkdtempSync(join(process.env.TMPDIR, 'dsh-wire-unit-'));
  let received;
  const server = Bun.serve({ hostname: '127.0.0.1', port: 0, async fetch(request) {
    received = { body: await request.text(), secret: request.headers.get('x-unit-secret') };
    return new Response(new ReadableStream({ start(c) {
      c.enqueue(new TextEncoder().encode('UNIT native bytes one\n'));
      setTimeout(() => { c.enqueue(new TextEncoder().encode('UNIT native bytes two\n')); c.close(); }, 5);
    } }), { status: 201, headers: { 'x-secret-response': 'NEVER_LOG_RESPONSE_HEADER' } });
  } });
  try {
    let nativeResponse;
    const original = globalThis.fetch;
    const native = async (...args) => { nativeResponse = await original(...args); return nativeResponse; };
    const counters = { native_fetch_calls: 0 };
    const capture = runner.captureFetch({ nativeFetch: native, dir, counters,
      authorize: () => ({ case_id: 'UNIT', neutral_sha256: 'UNIT', packet_sha256: 'UNIT' }) });
    const body = JSON.stringify({ model: 'UNIT-not-a-model', messages: [] });
    const response = await capture.fetch(server.url.href, { method: 'POST', body, headers: { 'x-unit-secret': 'NEVER_LOG_REQUEST_HEADER' } });
    expect(response).toBe(nativeResponse);
    expect(await response.text()).toBe('UNIT native bytes one\nUNIT native bytes two\n');
    await capture.drain();
    expect(received).toEqual({ body, secret: 'NEVER_LOG_REQUEST_HEADER' });
    expect(readFileSync(join(dir, 'wire-0001-request.body'), 'utf8')).toBe(body);
    expect(readFileSync(join(dir, 'wire-0001-response.body'), 'utf8')).toBe('UNIT native bytes one\nUNIT native bytes two\n');
    const metadata = readFileSync(join(dir, 'wire-0001.json'), 'utf8');
    expect(metadata).not.toContain('NEVER_LOG');
    expect(JSON.parse(metadata).status).toBe(201);
    expect(counters.native_fetch_calls).toBe(1);
  } finally { server.stop(true); rmSync(dir, { recursive: true }); }
});
