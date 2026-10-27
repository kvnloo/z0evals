// Browser-lane mechanics bench (study gui-scripting-speed).
// Isolation: chrome-headless-shell (no display, no window), private temp profile, owned
// file:// fixture, CDP over a pipe-free loopback port chosen by Chrome. Never touches the
// owner's desktop or browser profile.
//
//   node harness/browser_cdp_bench.mjs --reps 10 --out data/browser/cdp-r1.jsonl
//
// Arms isolate observation and settle costs with a scripted (oracle) policy, so no model
// decision is timed here. Model-decision costs come from the shadow eval and are combined
// only in analysis, labelled as a composed estimate.
import { spawn } from "node:child_process";
import { mkdtempSync, appendFileSync, rmSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURE = "file://" + resolve(HERE, "../tasks/browser-fixture/settings.html");
const CHROME = process.env.CHROME_HEADLESS_SHELL ||
  `${process.env.HOME}/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell`;
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith("--") ? a.push([v.slice(2), arr[i + 1]]) : 0, a), []));
const REPS = Number(args.reps || 10), OUT = args.out;

const TASKS = {
  "android-version": { path: ["About phone", "Software information"], read: "Android version", expect: "16" },
  "battery-level": { path: ["Battery"], read: "Battery level", expect: "57%" },
  "search-display": { search: "display", path: ["Display"], read: "Screen timeout", expect: "30 seconds" },
};
const ARMS = ["pixel+fixed", "axtree+fixed", "axtree+event", "compact+event", "compiled"];

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function launch() {
  const prof = mkdtempSync(join(process.env.TMPDIR || tmpdir(), "gss-cdp-"));
  const env = { ...process.env }; for (const k of ["DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "HYPRLAND_INSTANCE_SIGNATURE", "DBUS_SESSION_BUS_ADDRESS"]) delete env[k];
  const p = spawn(CHROME, ["--remote-debugging-port=0", `--user-data-dir=${prof}`, "--no-first-run", "--no-default-browser-check",
    "--disable-gpu", "--window-size=412,915", "about:blank"], { env, stdio: ["ignore", "ignore", "pipe"] });
  const wsUrl = await new Promise((res, rej) => {
    let buf = ""; const t = setTimeout(() => rej(new Error("no devtools url")), 15000);
    p.stderr.on("data", d => { buf += d; const m = buf.match(/DevTools listening on (ws:\S+)/); if (m) { clearTimeout(t); res(m[1]); } });
  });
  return { p, prof, wsUrl };
}

class CDP {
  constructor(url) { this.ws = new WebSocket(url); this.id = 0; this.pending = new Map(); this.bytes = 0;
    this.ws.onmessage = e => { this.bytes += e.data.length; const m = JSON.parse(e.data); if (m.id && this.pending.has(m.id)) { const { res, rej } = this.pending.get(m.id); this.pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); } }; }
  open() { return new Promise((r, j) => { this.ws.onopen = r; this.ws.onerror = j; }); }
  send(method, params = {}, sessionId) { const id = ++this.id; const msg = { id, method, params }; if (sessionId) msg.sessionId = sessionId;
    return new Promise((res, rej) => { this.pending.set(id, { res, rej }); this.ws.send(JSON.stringify(msg)); }); }
}

async function page(cdp) {
  const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
  const s = (m, p) => cdp.send(m, p, sessionId);
  await s("Page.enable"); await s("Runtime.enable");
  return { s, targetId };
}
const evalJS = async (s, expr, awaitPromise = false) => (await s("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise })).result.value;

const WAIT_PAGE = (name) => `new Promise(r=>{const ok=()=>document.body.dataset.page===${JSON.stringify(name)};if(ok())return r(true);
  const mo=new MutationObserver(()=>{if(ok()){mo.disconnect();r(true)}});mo.observe(document.body,{attributes:true,childList:true,subtree:true});
  setTimeout(()=>{mo.disconnect();r(false)},3000)})`;
const CENTER = (label) => `(()=>{const el=[...document.querySelectorAll('li,button,input')].find(e=>e.textContent.trim()===${JSON.stringify(label)});
  if(!el)return null;let b=el.getBoundingClientRect();let scrolled=false;
  if(b.bottom>innerHeight||b.top<0){el.scrollIntoView({block:'center'});b=el.getBoundingClientRect();scrolled=true}
  return [b.x+b.width/2,b.y+b.height/2,scrolled]})()`;
const CLICK = (label) => `(()=>{const el=[...document.querySelectorAll('li,button')].find(e=>e.textContent.trim()===${JSON.stringify(label)});if(!el)return false;el.click();return true})()`;
const COMPACT = `[...document.querySelectorAll('li,button,input')].map((e,i)=>({i,role:e.getAttribute('role')||e.tagName.toLowerCase(),name:(e.getAttribute('aria-label')||e.textContent).trim().slice(0,80)}))`;
const READ = (k) => `(()=>{const li=[...document.querySelectorAll('li')].find(l=>l.querySelector('.k')?.textContent===${JSON.stringify(k)});return li?li.querySelector('.val').textContent:null})()`;

async function observe(arm, s) {
  const t0 = performance.now(); let bytes = 0;
  if (arm.startsWith("pixel")) { const r = await s("Page.captureScreenshot", { format: "png" }); bytes = r.data.length; }
  else if (arm.startsWith("axtree")) { const r = await s("Accessibility.getFullAXTree", {}); bytes = JSON.stringify(r).length; }
  else { const r = await evalJS(s, COMPACT); bytes = JSON.stringify(r).length; }
  return { ms: performance.now() - t0, bytes };
}

async function settle(arm, s, target) {
  const t0 = performance.now();
  if (arm.endsWith("fixed")) { await sleep(500); await evalJS(s, WAIT_PAGE(target), true); }   // fixed wait, then guard
  else await evalJS(s, WAIT_PAGE(target), true);
  return performance.now() - t0;
}

async function runStepwise(arm, s, task) {
  const steps = []; let value = null;
  const targets = [...(task.search ? [] : []), ...task.path];
  if (task.search) {
    const o = await observe(arm, s);
    const t0 = performance.now();
    await evalJS(s, `document.getElementById('q').focus()`);
    await s("Input.insertText", { text: task.search });
    steps.push({ kind: "type", observe_ms: o.ms, obs_bytes: o.bytes, act_ms: performance.now() - t0, settle_ms: 0 });
  }
  for (const label of targets) {
    const o = await observe(arm, s);
    const t0 = performance.now();
    if (arm.startsWith("pixel")) {
      const c = await evalJS(s, CENTER(label));                 // stands in for a grounding model's coordinates
      if (!c) { steps.push({ kind: "click", error: "not_found" }); break; }
      if (c[2]) { const o2 = await observe(arm, s); steps.push({ kind: "scroll", observe_ms: o2.ms, obs_bytes: o2.bytes }); }  // a pixel agent must look again after scrolling
      for (const type of ["mousePressed", "mouseReleased"]) await s("Input.dispatchMouseEvent", { type, x: c[0], y: c[1], button: "left", clickCount: 1 });
    } else if (!(await evalJS(s, CLICK(label)))) { steps.push({ kind: "click", error: "not_found" }); break; }
    const act = performance.now() - t0;
    const st = await settle(arm, s, label);
    steps.push({ kind: "click", observe_ms: o.ms, obs_bytes: o.bytes, act_ms: act, settle_ms: st });
  }
  const o = await observe(arm, s);
  value = await evalJS(s, READ(task.read));
  steps.push({ kind: "read", observe_ms: o.ms, obs_bytes: o.bytes });
  return { steps, value };
}

async function runCompiled(s, task) {
  // One evaluate: the whole sub-task with event-driven settle and a guard after every hop.
  const script = `(async()=>{const wait=(n)=>${WAIT_PAGE("__N__").replace('"__N__"', "n")};
    const click=(l)=>{const el=[...document.querySelectorAll('li,button')].find(e=>e.textContent.trim()===l);if(!el)return false;el.click();return true};
    ${task.search ? `const q=document.getElementById('q');q.focus();q.value=${JSON.stringify(task.search)};q.dispatchEvent(new Event('input'));` : ""}
    for (const l of ${JSON.stringify(task.path)}) { if(!click(l)) return {error:'guard:not_found:'+l}; if(!(await wait(l))) return {error:'guard:no_settle:'+l}; }
    return {value:${READ(task.read)}};})()`;
  const t0 = performance.now();
  const r = await evalJS(s, script, true);
  return { steps: [{ kind: "compiled", act_ms: performance.now() - t0 }], value: r?.value ?? null, error: r?.error };
}

async function main() {
  const { p, prof, wsUrl } = await launch();
  const cdp = new CDP(wsUrl); await cdp.open();
  const version = await cdp.send("Browser.getVersion");
  appendFileSync(OUT, JSON.stringify({ schema: "z0evals.gui_scripting_speed.browser_run.v1.header", chrome: version.product, fixture: "tasks/browser-fixture/settings.html", reps: REPS, arms: ARMS, ts: Date.now() / 1000 }) + "\n");
  try {
    for (let rep = 1; rep <= REPS; rep++) {
      const order = rep % 2 ? ARMS : [...ARMS].reverse();           // ABAB / BABA blocks
      for (const tid of Object.keys(TASKS)) for (const arm of order) {
        const task = TASKS[tid];
        const { s, targetId } = await page(cdp);
        await s("Page.navigate", { url: FIXTURE });
        for (let i = 0; i < 300; i++) {                      // untimed: fixture loaded and home rendered
          const ok = await evalJS(s, `location.protocol==='file:' && document.body?.dataset.page==='home'`).catch(() => false);
          if (ok) break; await sleep(10);
        }
        const b0 = cdp.bytes, t0 = performance.now();
        let r, err = null;
        try { r = arm === "compiled" ? await runCompiled(s, task) : await runStepwise(arm, s, task); err = r.error || null; }
        catch (e) { r = { steps: [], value: null }; err = String(e).slice(0, 200); }
        const total = performance.now() - t0, wire = cdp.bytes - b0;
        const oracle = await evalJS(s, `window.__state.shown && window.__state.shown[${JSON.stringify(task.read)}]`);
        const row = { schema: "z0evals.gui_scripting_speed.browser_run.v1", rep, task: tid, arm, block_order: order.join(","),
          total_ms: +total.toFixed(2), wire_bytes: wire, value: r.value, oracle_value: oracle,
          verified: r.value === task.expect && oracle === task.expect, error: err,
          observe_ms_sum: +r.steps.reduce((a, x) => a + (x.observe_ms || 0), 0).toFixed(2),
          settle_ms_sum: +r.steps.reduce((a, x) => a + (x.settle_ms || 0), 0).toFixed(2),
          obs_bytes_sum: r.steps.reduce((a, x) => a + (x.obs_bytes || 0), 0),
          observations: r.steps.filter(x => x.observe_ms !== undefined).length, steps: r.steps.length,
          evidence_class: "executed_owned_fixture" };
        appendFileSync(OUT, JSON.stringify(row) + "\n");
        await cdp.send("Target.closeTarget", { targetId });
      }
      process.stdout.write(`rep ${rep} done\n`);
    }
  } finally {
    cdp.ws.close(); p.kill("SIGTERM"); await sleep(300); rmSync(prof, { recursive: true, force: true });
  }
}
main().catch(e => { console.error(e); process.exit(1); });
