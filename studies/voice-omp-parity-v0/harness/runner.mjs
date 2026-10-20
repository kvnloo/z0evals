// Shared, environment-agnostic scenario timeline runner (Bun for OMP, Chromium page for z0live).
// It never inspects transcripts: every wait is driven by output-audio RMS windows and by the
// arm's own work-pending signal, so both arms are steered by identical acoustic rules.
//
// adapter contract:
//   now(): number                      monotonic ms (same clock as level timestamps)
//   play(clipId, mark): Promise<{start, end}>   inject a clip into the mic path; resolves when fully sent
//   playAsync(clipId, mark): void       same, without blocking the timeline
//   workPending(): boolean              arm-specific: delegated/background work still outstanding
//   log(record): void                   append a timeline record
// The adapter must call runner.level(rms, t) for every 50 ms output window.

export const LEVEL_THRESHOLD = 0.015; // RMS, ~ -36.5 dBFS; equals OMP's OUTPUT_ACTIVE_LEVEL
export const WINDOW_MS = 50;

export function createRunner(adapter) {
  let lastAudible = -Infinity;
  let audibleCount = 0;
  const waiters = new Set();
  const runner = {
    level(rms, t) {
      if (rms >= LEVEL_THRESHOLD) {
        lastAudible = t;
        audibleCount += 1;
      }
      for (const w of [...waiters]) w();
    },
    get lastAudible() {
      return lastAudible;
    },
    async run(scenario) {
      const marks = {};
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      const waitUntil = async (pred, timeoutMs) => {
        const deadline = adapter.now() + timeoutMs;
        while (adapter.now() < deadline) {
          if (pred()) return true;
          await sleep(20);
        }
        return pred();
      };
      for (const [index, step] of scenario.steps.entries()) {
        const t = adapter.now();
        adapter.log({ kind: "step", index, op: step.op, t, mark: step.mark ?? null });
        if (step.op === "idle") {
          if (step.mark) marks[step.mark] = { start: t };
          await sleep(step.ms);
          if (step.mark) marks[step.mark].end = adapter.now();
        } else if (step.op === "say") {
          const r = await adapter.play(step.utt, step.mark);
          marks[step.mark] = r;
        } else if (step.op === "noise") {
          adapter.playAsync(step.clip, step.mark);
        } else if (step.op === "await_audible") {
          const since = t;
          const ok = await waitUntil(() => lastAudible >= since, step.timeout_ms);
          adapter.log({ kind: "await", op: step.op, ok, t: adapter.now() });
        } else if (step.op === "await_reply_end" || step.op === "await_result") {
          const since = t;
          const needWork = step.op === "await_result";
          const ok = await waitUntil(
            () =>
              lastAudible >= since &&
              adapter.now() - lastAudible >= step.silence_ms &&
              (!needWork || !adapter.workPending()),
            step.timeout_ms,
          );
          adapter.log({ kind: "await", op: step.op, ok, t: adapter.now(), work_pending: adapter.workPending() });
        } else {
          throw new Error(`unknown step op ${step.op}`);
        }
      }
      return { marks, audible_windows: audibleCount };
    },
  };
  return runner;
}
