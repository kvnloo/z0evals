// Appended to runtime.mjs and evaluated from DSH root. UNIT fixtures only.
// The real source adapter and Agent run; the transport is a test-owned Response,
// never the network and never a cohort answer. No real credentials are mounted.
const assert = (await import('node:assert/strict')).default;
assert.equal(typeof runCase, 'function', 'real Agent case executor missing');
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
const forbiddenNative = globalThis.fetch;
globalThis.fetch = () => { throw Error('UNIT unexpected network'); };
let fixtureCalls = 0;
try {
  for (const plugin of [ULlm.LlmRuntime, USession.SessionStore, UProjection.SessionProjectionRegistry, UPrompt.SystemPrompt, UTools.ToolRuntime, UAgents.AgentRegistry]) await unitCtx.plugin(plugin);
  await unitCtx.plugin(ULoop.default, { agents: [] });
  await unitCtx.plugin(URetry, {});
  unitCtx.systemPrompt.section({ name: 'UNIT-base', order: 1, text: 'base {{unit_value}}' });
  unitCtx.systemPrompt.variable('unit_value', () => 'UNIT-expanded');
  unitCtx.systemPrompt.context({ name: 'UNIT-context', order: 1, text: 'UNIT-context-retained' });
  unitCtx.systemPrompt.tools(() => ({ schemas: [{ name: 'UNIT_tool', description: 'UNIT no execution', parameters: { type: 'object' } }] }));
  unitCtx.on('system-prompt/assemble', async (_a, _c, next) => ({ ...await next(), unit_extension: { retained: true } }));
  assert.equal((await unitCtx.systemPrompt.assemble()).sections.filter(s => s.name.startsWith('study:')).length, 0);
  const connection = UDeep.resolveAdapterOptions({});
  unitCtx.llm.registerAdapter(['deepseek-official'], new UDeep.DeepSeekAdapter({
    options: () => connection,
    resolveAuth: async () => ({ headers: { 'x-api-key': 'UNIT-not-a-credential' } }),
    resolveUserId: () => 'UNIT-user',
    prepareExtensions: async () => ({ fields: {}, accept: async () => {} }),
  }));
  const events = [
    { type: 'message_start', message: { id: 'UNIT-message', model: 'deepseek-flash', usage: { input_tokens: 1, output_tokens: 1 } } },
    { type: 'content_block_start', index: 0, content_block: { type: 'text', text: '' } },
    { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text: 'UNIT transport fixture, NOT a cohort answer' } },
    { type: 'content_block_stop', index: 0 },
    { type: 'message_delta', delta: { stop_reason: 'end_turn' }, usage: { output_tokens: 1 } },
    { type: 'message_stop' },
  ];
  const fixtureFetch = async (_input, _init) => {
    fixtureCalls++;
    if (process.env.DSH_UNIT_ERROR) return new Response('{"error":{"type":"invalid_request_error","message":"UNIT failure"}}', { status: 400 });
    return new Response(events.map(e => `event: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`).join(''), { headers: { 'content-type': 'text/event-stream' } });
  };
  const counters = { native_fetch_calls: 0, neutral_requests: 0 };
  const testCase = { question_id: 'exact-identifier', variant: 'canonical', prompt_id: 'UNIT-prompt', prompt: 'UNIT diagnostic request',
    evidence: [{ slot: 'identifier', source_id: 'UNIT-source', source_version: 'sha256:' + '1'.repeat(64), trust_class: 'UNIT', locator: 'UNIT-message:1', origin_harness: 'UNIT', origin_session_id: 'UNIT-session', key: 'UNIT-key', text: 'UNIT literal {{do_not_expand}}' }], intentional_missing_slots: [] };
  let caught;
  const result = await runCase({ ctx: unitCtx, api: { ...ULlm, ...USession, ...UPrompt, ...UAgents, ...UProjectionClass },
    testCase, dir: process.env.DSH_UNIT_OUT, taskCwd: process.cwd(), selection: { provider: 'deepseek-official', model: 'deepseek-flash', reasoningEffort: 'high' },
    allowModel: true, assertRuntime: () => {}, nativeFetch: fixtureFetch, counters, identity: { test_only: true } }).catch(error => { caught = error; });
  if (process.env.DSH_UNIT_ERROR) {
    assert.equal(caught?.studyCode, 'CASE_NOT_COMPLETED');
    assert.equal(JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, 'turn-end.json'), 'utf8'))[0].reason.kind, 'error');
    assert.equal(JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, 'committed-answer.json'), 'utf8')).length, 0);
    assert.equal(JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, 'wire-0001.json'), 'utf8')).status, 400);
    console.log(JSON.stringify({ test_only: true, fixture_calls: fixtureCalls, provider_network_calls: 0, error_capture_verified: true }));
  } else {
  if (caught) throw caught;
  assert.equal(fixtureCalls, 1);
  assert.equal(counters.neutral_requests, 1);
  assert.equal(result.turn_end_kind, 'completed');
  assert.equal(result.system_admissions, 1);
  assert.equal(result.replay.additional_model_calls, 0);
  assert.equal(result.replay.additional_session_events, 0);
  assert.equal(result.replay.section_count, 1);
  assert.equal(result.replay.projection_updates, 0);
  assert.equal(result.replay.proof, 'retained-agent-reoffer+real-assembly+real-projection-no-commit');
  const committed = JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, 'committed-answer.json'), 'utf8'));
  assert.equal(committed[0].text, 'UNIT transport fixture, NOT a cohort answer');
  assert.equal(result.committed_answer_sha256, hash(stable(committed)));
  const wire = JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, 'wire-0001-request.body'), 'utf8'));
  assert(wire.system.includes('{{do_not_expand}}'));
  assert(!JSON.stringify(wire).includes('UNIT transport fixture'));
  const assembly = JSON.parse(readFileSync(join(process.env.DSH_UNIT_OUT, 'assembly.json'), 'utf8')).assemblies[0].assembly;
  assert.equal(assembly.sections.find(s => s.name === 'UNIT-base').text, 'base {{unit_value}}');
  assert.equal(assembly.tools[0].name, 'UNIT_tool');
  assert.equal(assembly.contexts[0].name, 'UNIT-context');
  assert.equal(assembly.variables.unit_value, 'UNIT-expanded');
  assert.deepEqual(assembly.unit_extension, { retained: true });
  console.log(JSON.stringify({ test_only: true, fixture_calls: fixtureCalls, provider_network_calls: 0, result }));
  }
} finally { await unitCtx.fiber.dispose(); globalThis.fetch = forbiddenNative; }
