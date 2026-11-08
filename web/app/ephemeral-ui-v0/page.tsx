import type { Metadata } from "next";
import fs from "node:fs";
import path from "node:path";
import StoryShell, { type StoryBanner } from "@/components/StoryShell";
import type { TocItem } from "@/components/Toc";
import Callout from "@/components/Callout";
import { Tldr, ExpHead, Evidence, SetupFigure, KitEmbed, Citation } from "@/components/essay/Essay";

// Every number on this page is read from the vendored fixture the cards themselves render,
// web/public/embeds/ephemeral-ui/data/trace-fixture.json (see VENDORED.md next to it).
type Summary = { wallMs: number; modelMs: number; toolMs: number; idleMs: number; requests: number; toolCalls: number; subagents: number; totalTokens: number; costTotal: number };
type Trace = { title: string; summary: Summary; tracks: unknown[] };
type Fixture = { source: string; generatedAt: number; sessions: { file: string; harness: string }[]; traces: Record<string, Trace>; api: Record<string, unknown> };

const slug = "ephemeral-ui-v0";
const DIR = path.join(process.cwd(), "public", "embeds", "ephemeral-ui");
const F = JSON.parse(fs.readFileSync(path.join(DIR, "data", "trace-fixture.json"), "utf8")) as Fixture;
const vendored = fs.readFileSync(path.join(DIR, "VENDORED.md"), "utf8");
const pin = /commit `([0-9a-f]{40})`/.exec(vendored)?.[1];
if (!pin) throw new Error("ephemeral-ui post: VENDORED.md does not name the pinned commit");

const traces = Object.values(F.traces);
const sessions = F.sessions;
const harnesses = new Map<string, number>();
for (const s of sessions) harnesses.set(s.harness, (harnesses.get(s.harness) ?? 0) + 1);
const unpriced = traces.filter((t) => t.summary.totalTokens === 0);
const slowest = traces.reduce((a, b) => (b.summary.wallMs > a.summary.wallMs ? b : a));
const modelShare = slowest.summary.modelMs / slowest.summary.wallMs;
const endpoints = Object.keys(F.api).map((k) => k.split("?")[0]);
const uniqueEndpoints = [...new Set(endpoints)];
const idleMost = traces.reduce((a, b) => (b.summary.idleMs / b.summary.wallMs > a.summary.idleMs / a.summary.wallMs ? b : a));
if (traces.length !== sessions.length) throw new Error("ephemeral-ui post: fixture sessions and traces disagree");
if (unpriced.length !== 1) throw new Error("ephemeral-ui post: the text says exactly one session has no recorded usage");

const pct = (x: number) => `${Math.round(x * 100)}%`;
const hours = (ms: number) => `${(ms / 3_600_000).toFixed(1)} h`;
const words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
const word = (n: number) => words[n] ?? String(n);
const harnessList = [...harnesses].map(([h, n]) => `${word(n)} ${h === "omp" ? "omp" : "Hermes"}`).join(" and ");
const kitRepo = `https://github.com/kvnloo/launch-videos/tree/${pin}/pretotypes/ephemeral-ui`;

export const metadata: Metadata = {
  title: "an agent's session, as cards — z0evals",
  description:
    "ephemeral-ui cards for the omp /stats dashboard, live in the post: scrub a real (sanitized) session, open its spans, and ask it a question.",
};

const banner: StoryBanner = {
  tag: "prototype · sanitized fixture",
  text: `the cards below run the kit's own code on ${word(sessions.length)} real sessions, sanitized. nothing is wired to a live agent, and the question box is rule-based, not a model.`,
};

const toc: TocItem[] = [
  { id: "what", label: "what ephemeral ui is", depth: 0 },
  { id: "timeline", label: "1 · the session, scrubbable", depth: 0 },
  { id: "kinds", label: "2 · the dashboard, as cards", depth: 0 },
  { id: "ask", label: "3 · ask the trace", depth: 0 },
  { id: "limits", label: "what this does not show", depth: 0 },
  { id: "explore", label: "receipts", depth: 0 },
];

const story = (
  <>
    <Tldr>
      <p>
        ephemeral ui is a card kit: a card appears when an agent touches an app, takes the host&apos;s theme (T3 Code,
        Hermes desktop) and dissolves into a one-line receipt when the task is done. one family of those cards re-creates
        the <code>omp /stats</code> dashboard and takes its JSON unchanged.
      </p>
      <p>
        this post runs those cards live on {word(sessions.length)} sanitized sessions ({harnessList}). the slowest ran{" "}
        <b>{hours(slowest.summary.wallMs)}</b> of wall time, and its model spans add up to only <b>{pct(modelShare)}</b> of
        that. a timeline shows where the rest went in one glance; a table of totals does not.
      </p>
    </Tldr>

    <h2 id="what">what ephemeral ui is</h2>
    <p>
      an agent that touches gmail, a pull request or a calendar usually reports back in prose. ephemeral ui replaces the
      prose with the app&apos;s own surface, shrunk to a card: you can scrub it, open it, hold to approve, and when the job
      is done it folds into a receipt line. the kit is open and lives at{" "}
      <a href="https://ephemeralui.vercel.app">ephemeralui.vercel.app</a>, with every card kind, a theme engine read from
      the hosts&apos; own source, and a short reel.
    </p>
    <p>
      the cards here are the trace family. they look like results from the oh-my-pi <code>/stats</code> dashboard (
      <code>@oh-my-pi/omp-stats</code>, MIT), read the same{" "}
      {uniqueEndpoints.length} API shapes it serves, and sit in an iframe running the kit&apos;s unmodified modules, so
      what you touch below is the kit, not a screenshot of it.
    </p>

    <ExpHead n={1} id="timeline">the session, scrubbable</ExpHead>
    <p>
      <Evidence kind="source-reported">omp-stats export, sanitized</Evidence>
    </p>
    <SetupFigure
      setup={
        <>
          <p>
            {F.source}. tracks are the main agent and its subagents; lanes are input, model, tools, agents and background
            work. drag to pan, scrub the minimap, ⌘/ctrl-wheel to zoom, click a span for its drawer, click a track to
            collapse it.
          </p>
          <p>prompts, messages, tool output, paths, hosts and project names were removed before the file was published.</p>
        </>
      }
      caption={
        <>
          the default trace card picks the newest omp session that used subagents. in the slowest session,{" "}
          {slowest.title}, model spans cover {pct(modelShare)} of the wall time and tool spans{" "}
          {pct(slowest.summary.toolMs / slowest.summary.wallMs)}.
        </>
      }
    >
      <KitEmbed params="view=kind&kind=trace" title="trace timeline card" minHeight={520} />
    </SetupFigure>
    <p>
      the point of the timeline is the gaps. {idleMost.title} logged {pct(idleMost.summary.idleMs / idleMost.summary.wallMs)}{" "}
      of its wall time as idle, between turns rather than inside them. a wall-time total alone would call that a slow
      session; the timeline shows it was mostly waiting.
    </p>

    <ExpHead n={2} id="kinds">the dashboard, as cards</ExpHead>
    <p>
      the same data feeds the rest of the family. each card is one dashboard view: the session summary, tool latency and
      failure rate, grouped errors that jump to the failing span, and a side-by-side compare of any two sessions.
    </p>
    <div className="eu-pair es-wide">
      <KitEmbed params="view=kind&kind=trace-summary" title="trace summary card" minHeight={360} />
      <KitEmbed params="view=kind&kind=trace-tools" title="tool latency card" minHeight={360} />
      <KitEmbed params="view=kind&kind=trace-errors" title="errors card" minHeight={360} />
      <KitEmbed params="view=kind&kind=trace-compare" title="session compare card" minHeight={360} />
    </div>
    <Callout>
      {unpriced[0].title} shows usage as &ldquo;not recorded&rdquo; rather than 0 tokens and $0. the fixture has no token
      counts for it, and a card that printed zeros would have claimed it was free.
    </Callout>

    <ExpHead n={3} id="ask">ask the trace</ExpHead>
    <p>
      <Evidence kind="prediction">a plan format, not a model answer</Evidence>
    </p>
    <p>
      a question turns into a small typed query plan (<code>trace-query.v0</code>): which endpoints to call, which cards to
      show, which layers to switch on. an agent would emit that plan; here a short list of phrase rules stands in for it.
      pick a suggestion or type your own, then toggle layers to re-draw every card without refetching.
    </p>
    <div className="es-wide">
      <KitEmbed params={`view=ask&q=${encodeURIComponent("why was this session slow?")}`} title="ask the trace" minHeight={900} />
    </div>

    <h2 id="limits">what this does not show</h2>
    <ul>
      <li>no live integration. the cards read a frozen, sanitized fixture; a host would swap the fixture for its own omp-stats server and nothing else.</li>
      <li>
        the phrase-to-plan step is rules, not a model. questions that match no rule get a general overview of the newest
        session.
      </li>
      <li>
        {word(sessions.length)} sessions is a demo, not a sample. nothing here says how sessions usually spend their time.
      </li>
      <li>the cards are T3 Code dark here; the kit also renders them in Hermes desktop themes.</li>
    </ul>
  </>
);

const explore = (
  <div className="explore-block">
    <h2 id="receipts">receipts</h2>
    <ul>
      <li>
        kit: <a href={kitRepo}>kvnloo/launch-videos pretotypes/ephemeral-ui</a> at <code>{pin.slice(0, 7)}</code>,
        vendored unmodified under <code>web/public/embeds/ephemeral-ui</code>
      </li>
      <li>fixture: {F.source}</li>
      <li>
        dashboard: <a href="https://github.com/can1357/oh-my-pi">oh-my-pi</a> <code>omp stats</code> (MIT), whose API
        shapes the cards read
      </li>
      <li>card kit built on <a href="https://github.com/thesysdev/openui">OpenUI</a> by Thesys (MIT)</li>
    </ul>
    <h3>cite</h3>
    <Citation
      id="z0evals2026ephemeralui"
      title="an agent's session, as cards"
      year={2026}
      url={`https://kvnloo.github.io/z0evals/${slug}/`}
      note="prototype on a sanitized omp-stats fixture"
    />
  </div>
);

export default function Page() {
  return <StoryShell slug={slug} toc={toc} banner={banner} story={story} explore={explore} />;
}
