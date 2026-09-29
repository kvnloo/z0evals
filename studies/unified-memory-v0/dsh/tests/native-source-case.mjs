// Appended to runtime.mjs; Bun -e from the pinned DSH source root.
// Offline UNIT only: source Agent + DeepSeekAdapter with native loopback transport.
// No real credentials, provider traffic, product boot, or cohort answers.
const assert = (await import('node:assert/strict')).default;
const { Context: UnitContext } = await import('@deepseek-ai/cordis');
const ULlm = await import('@deepseek-ai/dsh-llm');
const USession = await import('@deepseek-ai/dsh-session');
const UProjection = await import('@deepseek-ai/dsh-session-projection');
const UPrompt = await import('@deepseek-ai/dsh-system-prompt');
const UTools = await import('@deepseek-ai/dsh-tools');
const UAgents = await import('@deepseek-ai/dsh-agent');
const ULoop = await import('@deepseek-ai/dsh-agent-loop');
const URetry = await import('@deepseek-ai/dsh-llm-retry');
const UDeep = await import('@deepseek-ai/dsh-llm-deepseek');
const UProjectionClass = await import('./packages/core/agent-loop/src/runtime-context.ts');
const unitCtx = new UnitContext();
const originalFetch = globalThis.fetch;
const denyFetch = () => { throw Error('UNIT unexpected network'); };
globalThis.fetch = denyFetch;
const mode = process.env.DSH_UNIT_CAPTURE_MODE;
const delay = Number(process.env.DSH_UNIT_EOF_DELAY);
const answer = 'UNIT transport fixture, NOT a cohort answer';
const frame = e => `event: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`;
const events = [
  { type: 'message_start', message: { id: 'UNIT-message', model: 'deepseek-flash', usage: { input_tokens: 1, output_tokens: 1 } } },
  { type: 'content_block_start', index: 0, content_block: { type: 'text', text: '' } },
  { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: answer } },
  { type: 'content_block_stop', index: 0 },
  { type: 'message_delta', delta: { stop_reason: 'end_turn' }, usage: { output_tokens: 1 } },
  { type: 'message_stop' },
];
if (mode === 'max-tokens') events[4].delta.stop_reason = 'max_tokens';
if (mode === 'empty-answer') events[2].delta.text = '';
let fixture = events.map(frame).join('');
if (mode === 'truncated-frame') fixture = fixture.slice(0, -1); // No blank-line delimiter.
if (mode === 'incomplete') fixture = events.slice(0, -1).map(frame).join('');
if (mode === 'fake-terminal') fixture = events.slice(0, -1).map(frame).join('') + frame({ type: 'ping', note: 'message_stop' });
if (mode === 'malformed-terminal') fixture = events.slice(0, -1).map(frame).join('') + 'event: message_stop\ndata: {"type":"ping"}\n\n';
if (mode === 'invalid-json') fixture = events.slice(0, -1).map(frame).join('') + 'event: message_stop\ndata: {"type":"message_stop"\n\n';
if (mode === 'unsettled-block') fixture = events.filter(e => e.type !== 'content_block_stop').map(frame).join('');
if (mode === 'orphan-terminal') fixture = frame({ type: 'message_stop' });
if (mode === 'sse-error') fixture = events.slice(0, 3).map(frame).join('') + frame({ type: 'error', error: { type: 'invalid_request_error', message: 'UNIT error' } });
if (mode === 'http-error') fixture = '{"error":{"type":"invalid_request_error","message":"UNIT HTTP error"}}';
if (mode === 'cancel') fixture = events.slice(0, 3).map(frame).join('');
const success = ['complete', 'fragmented', 'late-tail'].includes(mode);
const protocolComplete = success || ['max-tokens', 'empty-answer', 'cancel-terminal', 'agent-error-terminal', 'clone-read-error'].includes(mode);
let fixtureCalls = 0;
let requestBody;
let timer;
let signal;
let nativeResponse;
let responseReturned;
let adapterInput;
let adapterInit;
let fragmentTimer;
const server = Bun.serve({ hostname: '127.0.0.1', port: 0, async fetch(request) {
  fixtureCalls++;
  requestBody = await request.text();
  assert.equal(request.headers.get('x-api-key'), 'UNIT-not-a-credential');
  return new Response(new ReadableStream({ start(controller) {
    function finish() {
      if (!delay) { controller.close(); return; }
      timer = setTimeout(() => { try {
        if (mode === 'late-tail') controller.enqueue(new TextEncoder().encode(': UNIT trailing body not observed\n\n'));
        controller.close();
      } catch {} }, delay);
    }
    if (mode === 'fragmented') {
      // Split the terminal event name and its final blank-line delimiter.
      const pieces = [fixture.slice(0, -35), fixture.slice(-35, -1), fixture.slice(-1)];
      function send() {
        controller.enqueue(new TextEncoder().encode(pieces.shift()));
        if (pieces.length) fragmentTimer = setTimeout(send, 3); else finish();
      }
      send();
    } else { controller.enqueue(new TextEncoder().encode(fixture)); finish(); }
  } }), { status: mode === 'http-error' ? 400 : 200,
    headers: { 'content-type': 'text/event-stream', 'x-unit-secret': 'UNIT-private-response-header' } });
} });
try {
  for (const plugin of [ULlm.LlmRuntime, USession.SessionStore, UProjection.SessionProjectionRegistry, UPrompt.SystemPrompt, UTools.ToolRuntime, UAgents.AgentRegistry]) await unitCtx.plugin(plugin);
  await unitCtx.plugin(ULoop.default, { agents: [] });
  await unitCtx.plugin(URetry, {});
  if (mode === 'cancel') unitCtx.on('agent/assistant-stream', ({ agent, frame }) => {
    if (frame.type === 'chunk' && frame.chunk.type === 'text-delta') agent.cancel({ kind: 'user' });
  });
  if (mode === 'cancel-terminal') unitCtx.on('agent/turn-stopping', ({ agent }) => { agent.cancel({ kind: 'user' }); });
  if (mode === 'agent-error-terminal') unitCtx.on('agent/turn-stopping', () => { throw Error('UNIT settlement failure'); });
  unitCtx.systemPrompt.section({ name: 'UNIT-base', order: 1, text: 'UNIT source native capture' });
  const connection = UDeep.resolveAdapterOptions({});
  unitCtx.llm.registerAdapter(['deepseek-official'], new UDeep.DeepSeekAdapter({
    options: () => connection,
    resolveAuth: async () => ({ headers: { 'x-api-key': 'UNIT-not-a-credential' } }),
    resolveUserId: () => 'UNIT-user',
    prepareExtensions: async () => ({ fields: {}, accept: async () => {} }),
  }));
  const fixtureFetch = async (input, init) => {
    assert.equal(input, 'https://api.deepseek.com/anthropic/v1/messages');
    assert.equal(input, adapterInput);
    assert.equal(init, adapterInit, 'exact original fetch init object, including headers and signal');
    assert.equal(init.signal.aborted, false);
    signal = init.signal;
    // Only the UNIT transport substitutes the URL; the runner passes init unchanged.
    nativeResponse = await originalFetch(server.url.href, init);
    // Supplemental UNIT fault injection ONLY on the capture branch. The real
    // native response still delivers a complete answer to the source adapter.
    if (mode === 'clone-truncated') nativeResponse.clone = () => new Response(fixture.slice(0, -1));
    if (mode === 'clone-read-error') nativeResponse.clone = () => new Response(new ReadableStream({ start(controller) {
      controller.enqueue(new TextEncoder().encode(fixture));
      init.signal.addEventListener('abort', () => controller.error(Error('UNIT non-abort clone failure')), { once: true });
    } }));
    return nativeResponse;
  };
  // Observe both sides of the tee without changing the adapter's request/Response.
  unitCtx.on('llm/stream', (options, next) => {
    const capturedFetch = globalThis.fetch;
    globalThis.fetch = async (...args) => {
      [adapterInput, adapterInit] = args;
      responseReturned = await capturedFetch(...args);
      assert.equal(args[1], adapterInit);
      assert.equal(adapterInit.signal, signal);
      assert.equal(responseReturned, nativeResponse);
      return responseReturned;
    };
    return next();
  });
  const counters = { native_fetch_calls: 0, neutral_requests: 0 };
  const testCase = { question_id: 'exact-identifier', variant: 'canonical', prompt_id: 'UNIT-native-prompt',
    prompt: 'UNIT native loopback diagnostic', evidence: [], intentional_missing_slots: [] };
  let caught;
  const result = await runCase({ ctx: unitCtx, api: { ...ULlm, ...USession, ...UPrompt, ...UAgents, ...UProjectionClass },
    testCase, dir: process.env.DSH_UNIT_OUT, taskCwd: process.cwd(),
    selection: { provider: 'deepseek-official', model: 'deepseek-flash', reasoningEffort: 'high' },
    allowModel: true, assertRuntime: () => {}, nativeFetch: fixtureFetch, counters, identity: { test_only: true } }).catch(error => { caught = error; });
  const read = name => JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, name), 'utf8'));
  const wire = read('wire-0001.json');
  const committed = read('committed-answer.json');
  const stage = read('case-stage.json');
  const turn = read('turn-end.json');
  const captured = readFileSync(join(process.env.DSH_UNIT_OUT, 'wire-0001-response.body'));
  assert.equal(globalThis.fetch, denyFetch, 'fetch must be restored even when blocked');
  assert.equal(fixtureCalls, 1);
  assert.equal(counters.native_fetch_calls, 1);
  assert.equal(counters.neutral_requests, 1);
  assert.equal(readFileSync(join(process.env.DSH_UNIT_OUT, 'wire-0001-request.body'), 'utf8'), requestBody);
  assert.equal(wire.request_sha256, hash(requestBody));
  assert.equal(wire.status, mode === 'http-error' ? 400 : 200);
  assert.equal(captured.toString(), mode === 'clone-truncated' ? fixture.slice(0, -1) : fixture,
    'capture hashes must describe only the bytes actually received by the tee');
  assert.equal(wire.response_capture_sha256, hash(captured));
  assert.equal(wire.response_bytes, captured.byteLength);
  assert.equal(wire.protocol_complete, mode === 'http-error' ? null : protocolComplete);
  assert.equal(wire.response_sha256, wire.http_eof_observed ? hash(captured) : null);
  assert.equal(wire.trailing_http_body, wire.http_eof_observed ? 'none' : 'unknown');
  assert.equal(wire.response_capture_kind, wire.http_eof_observed ? 'http-body-complete'
    : protocolComplete ? 'terminal-complete-prefix' : 'incomplete-prefix');
  assert.equal(signal.aborted, true, 'actual source adapter cleanup abort must be exercised');
  if (success) {
    assert.equal(hash(captured), '7a2d6270456429bccf7bb2d9af01ca300839b8c2daea6dcbf6f90a9dfff32169');
    assert.equal(committed.length, 1);
    assert.equal(committed[0].text, answer);
    assert.equal(committed[0].interrupted, false);
    assert.equal(turn.at(-1).reason.kind, 'completed');
    assert.equal(caught?.studyCode, undefined, `complete source protocol blocked: ${caught?.studyCode}`);
    assert.equal(stage.status, 'captured-unscored');
    assert.equal(result.committed_answer_sha256, hash(stable(committed)));
    assert.equal(result.replay.additional_model_calls, 0);
    assert.equal(result.replay.additional_session_events, 0);
    assert.equal(wire.response_stream_error, delay > 0);
    assert.equal(wire.response_stream_aborted, delay > 0);
    assert.equal(wire.http_eof_observed, delay === 0);
    assert.equal(wire.protocol_finish_kind, 'stop');
  } else {
    assert.equal(caught?.studyCode, mode.startsWith('clone-') ? 'RESPONSE_CAPTURE_FAILED'
      : mode === 'http-error' || protocolComplete ? 'CASE_NOT_COMPLETED' : 'RESPONSE_CAPTURE_FAILED');
    assert.equal(stage.status, 'blocked');
    const expectedTurn = mode === 'max-tokens' ? 'max-tokens' : mode.startsWith('cancel') ? 'aborted'
      : mode === 'empty-answer' || mode.startsWith('clone-') ? 'completed' : 'error';
    assert.equal(turn.at(-1).reason.kind, expectedTurn);
    if (mode.startsWith('clone-')) {
      assert.equal(committed[0].text, answer);
      assert.equal(committed[0].interrupted, false);
      assert.equal(stage.committed_answer_sha256, hash(stable(committed)));
      assert.equal(wire.response_stream_aborted, false);
      assert.equal(wire.response_stream_error, mode === 'clone-read-error');
    } else if (protocolComplete) {
      assert.equal(committed[0].text, mode === 'empty-answer' ? '' : answer);
      assert.equal(stage.committed_answer_sha256, hash(stable(committed)));
      assert.equal(wire.protocol_finish_kind, mode === 'max-tokens' ? 'max-tokens' : 'stop');
    } else {
      assert(!committed.some(e => !e.interrupted && e.text), 'no authoritative noninterrupted answer on early failure');
      assert.equal(wire.protocol_finish_kind, null);
    }
  }
  console.log(JSON.stringify({ test_only: true, fixture_calls: fixtureCalls, provider_network_calls: 0,
    mode, delay_ms: delay, captured_sha256: hash(captured), wire, stage_status: stage.status,
    committed_messages: committed.length, committed_answer_sha256: stage.committed_answer_sha256,
    turn_end_kind: turn.at(-1).reason.kind }));
} finally {
  clearTimeout(timer);
  clearTimeout(fragmentTimer);
  server.stop(true);
  await unitCtx.fiber.dispose();
  globalThis.fetch = originalFetch;
}
