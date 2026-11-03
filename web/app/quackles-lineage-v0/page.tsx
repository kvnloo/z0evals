import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import { studyMeta } from "@/lib/catalog";
import type { TocItem } from "@/components/Toc";
import { Tldr, ExpHead, Evidence, Teaser, SetupFigure, TracePages, Citation, type TraceItem } from "@/components/essay/Essay";
import LineageSwimlane from "@/components/quackles/LineageSwimlane";
import ReviewGate from "@/components/quackles/ReviewGate";
import CompareSwipe from "@/components/quackles/CompareSwipe";
import ZoomLadder from "@/components/quackles/ZoomLadder";
import DensityChart from "@/components/quackles/DensityChart";
import { SpriteWall, DecisionGrid } from "@/components/quackles/TeaserVisuals";
import { THEME_LABEL, type QuacklesData } from "@/components/quackles/types";
import { asset } from "@/lib/asset";
import raw from "@/data/quackles-lineage-v0.json";
import "./quackles.css";

// Every number below is read from web/data/quackles-lineage-v0.json, which
// scripts/build_quackles_data.py derives from studies/quackles-lineage-v0/data.
const D = raw as unknown as QuacklesData;
const N = D.entries.length;
const sumCounts = Object.values(D.counts).reduce((a, b) => a + b, 0);
if (sumCounts !== N) throw new Error("quackles: per-scene counts do not add up to the version total");
const promoted = D.trialCounts.promoted ?? 0;
const Z = D.zoom;
const nightHead = Z.density.find((d) => d.theme === "night" && d.source.startsWith("head print"))!;
const below1gp = Z.density.filter((d) => d.d1gp < Z.thresholds.minimum).length;
const below201 = Z.density.filter((d) => d.d201 < Z.thresholds.minimum).length;
const stone = Z.coupons.find((c) => c.id === "stone-face")!;
const fmtInt = (n: number) => n.toLocaleString("en-US");
const nightHeadCrop = D.zoomRegions.find((r) => r.theme === "night" && r.scale === "1gp" && r.feature === "head-print")!;
const days = Math.round((D.entries[N - 1][1] - D.entries[0][1]) / 86400000);
const repo = "https://github.com/kvnloo/z0evals";

export const metadata: Metadata = {
  title: "quackles, in 665 renders — z0evals",
  description:
    "an agent render loop, read from its own archive: how often the two-reviewer gate said no, and why a 1 gp export of the current scenes is not 1 gp of detail.",
};

const meta: StoryMeta = studyMeta("quackles-lineage-v0");

const banner: StoryBanner = {
  tag: "source-reported · no owner approval",
  text: "every number here comes from the quackles archive, operator logs and audit reports. nothing was re-rendered or re-reviewed for this post. every scene pick is an agent pick that the owner has not approved.",
};

const toc: TocItem[] = [
  { id: "what", label: "what quackles is", depth: 0 },
  { id: "archive", label: "1 · the archive", depth: 0 },
  { id: "gate", label: "2 · one night of the gate", depth: 0 },
  { id: "picks", label: "3 · the picks against their references", depth: 0 },
  { id: "zoom", label: "4 · a gigapixel that is not one", depth: 0 },
  { id: "scores", label: "5 · sharpness scores disagree", depth: 0 },
  { id: "timeline", label: "the timeline as software", depth: 0 },
  { id: "limits", label: "what this does not show", depth: 0 },
  { id: "next", label: "what comes next", depth: 0 },
  { id: "explore", label: "receipts", depth: 0 },
];

const sentences = (s: string) =>
  s
    .replace(/Evidence: \[artifact store\]/g, "")
    .split(/(?<=[.;])\s+(?=[A-Z])/)
    .map((x) => x.trim())
    .filter((x) => x && !x.startsWith("Backup:") && !x.startsWith("Previous:"));

const pickTraces: TraceItem[] = D.themes.map((t) => {
  const p = (D.picks as Record<string, { round: string; notes: string }>)[t];
  const steps = sentences(p.notes);
  return {
    label: THEME_LABEL[t],
    ask: <>is this candidate better than the current {THEME_LABEL[t]} scene, judged against the locked reference?</>,
    given: <>two fresh reviewers, sides swapped, a LOOK pair and a CLEAR pair</>,
    answer: <code>{p.round}</code>,
    verdict: { text: "agent pick · owner pending", tone: "hold" },
    steps: steps.map((s, i) => <span key={i}>{s}</span>),
    foot: <>review-picks.json · CURRENT.json as of 2026-10-16 18:11 CDT</>,
  };
});

function Story() {
  return (
    <>
      <Tldr>
        <p>
          quackles is a product page for a small robot, rendered as five Blender scenes by an agent loop. over {days} days
          the loop kept <b>{fmtInt(N)} versions</b>. in one overnight run, two blind reviewers looked at{" "}
          <b>{D.trialTotal} candidates</b> and the gate promoted <b>{promoted}</b>. by evening the small changes were tying,
          and the loop stopped to wait for the owner.
        </p>
        <p>
          the scenes also export at 1 GP, and every tile of every pyramid is there. that does not make them gigapixel
          images: at 1 GP, {below1gp} of the {Z.density.length} measured texture sources have less than one texel per
          final pixel. Night&apos;s head print has {nightHead.d1gp.toFixed(3)}.
        </p>
      </Tldr>

      <Teaser
        label="the three results"
        panels={[
          {
            step: "archive",
            task: <>keep every render the loop made, rejected ones included.</>,
            visual: <SpriteWall rows={D.entries} pages={D.atlasPages} />,
            by: <>five scenes, {days} days, nothing deleted</>,
            big: fmtInt(N),
            note: <>versions; {D.statusCounts.rejected} marked rejected</>,
          },
          {
            step: "review",
            task: <>two blind reviewers, sides swapped. both must prefer the candidate.</>,
            visual: <DecisionGrid trials={D.trials} />,
            by: <>one overnight run, 2026-10-16</>,
            big: `${promoted} / ${D.trialTotal}`,
            note: <>promoted; the rest held, tied, split or lost</>,
          },
          {
            step: "zoom",
            task: <>render the same spot at 1 GP. is the detail there?</>,
            visual: (
              // eslint-disable-next-line @next/next/no-img-element
              <img className="qk-pixelated" src={asset(nightHeadCrop.src)} alt="Night head print at 1 GP, native crop" />
            ),
            by: <>Night it12, head print, native 1 GP crop</>,
            big: nightHead.d1gp.toFixed(3),
            note: <>texels per pixel. the floor is {Z.thresholds.minimum}.</>,
          },
        ]}
      />

      <h2 id="what">what quackles is</h2>
      <p>
        quackles is a mobile product page for Pollen Robotics&apos; Microduck. the robot sits in five studio scenes: Day,
        White, Blue, Dark and Night. each has a locked reference poster that sets the look. scrolling moves the camera,
        and the frames are authored Blender Cycles renders, not a live 3D scene.
      </p>
      <p>
        agents did most of the rendering. a dream loop proposes a change to a copy of the scene, renders it, and a review
        step decides whether it replaces the current pick. this post reads that loop from the outside, through what it
        left behind: the archive, the operator log of one night, and an audit of what the scenes hold at maximum zoom.
      </p>
      <figure className="es-fig es-wide">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="qk-wide-img" src={asset("/media/quackles-lineage-v0/process/references.webp")} alt="Five reference posters: Day, White, Blue, Dark and Night." />
        <figcaption className="fig-caption">
          the five reference stills. they are image-led targets, not renders of the finished scene.
        </figcaption>
      </figure>

      <ExpHead n={1} id="archive">how much did the loop make, and what happened to it?</ExpHead>
      <p>
        the lineage archive keeps every render that survived on disk, deduplicated by image hash. it has {fmtInt(N)}{" "}
        versions: {D.themes.map((t, i) => (
          <span key={t}>
            {i ? (i === D.themes.length - 1 ? " and " : ", ") : ""}
            {THEME_LABEL[t]} {D.counts[t]}
          </span>
        ))}
        . Day has half of them: it went first, and the method was worked out on it.
      </p>
      <p>
        press play. the cards show each scene&apos;s newest render at the playhead; hold one to swap in its reference.
        switch the axis to <i>by date</i> and the bursts show up: most versions arrive in a few overnight runs, not
        steadily.
      </p>
      <SetupFigure
        caption={<>each tick is one preserved render. colour is the archive status; click a status to isolate it. drag the lane or the slider to scrub.</>}
        setup={
          <ul>
            <li>dataset: history-v1, sha256 {D.datasetSha256.slice(0, 12)}…, snapshot {D.snapshot.slice(0, 10)}</li>
            <li>{fmtInt(N)} versions, deduplicated by encoded image hash; rejected renders are kept</li>
            <li>dates: {D.mtimeDated} of {N} come from file mtimes, not creation receipts; the rest from git or a ledger</li>
            <li>statuses come from the archive, not from this study; &quot;unknown&quot; means nothing recorded a verdict</li>
            <li>thumbnails: the original /lineage sprite atlas, {D.atlasPages.length} pages of 2048²</li>
            <li>milestones mark the first artifact of a phase or the current pick; they are not decision timestamps</li>
          </ul>
        }
      >
        <LineageSwimlane data={D} />
      </SetupFigure>
      <p>
        the status split is the first honest number here. of {fmtInt(N)} versions, {D.statusCounts.candidate} are plain
        candidates, {D.statusCounts.unknown} have no recorded verdict at all, {D.statusCounts.rejected} were rejected and{" "}
        {D.statusCounts.kept} kept. {D.statusCounts.current} are current, one per scene. an archive that only kept winners
        would make the loop look far more decisive than it was.
      </p>

      <ExpHead n={2} id="gate">what does the review gate do over one night?</ExpHead>
      <p>
        the gate is simple. {D.protocol}
      </p>
      <p>
        we transcribed every decision in the operator log for the night of October 16: {D.trialTotal} in all, counting a
        batch of six held trials as six. {promoted} were promoted. the rest is the interesting part.
      </p>
      <SetupFigure
        caption={<>every decision in log order. pick one to see what was tried and why it landed where it did.</>}
        setup={
          <ul>
            <li>source: the operator log OVERNIGHT-2026-10-16.md, transcribed row by row</li>
            <li>reviewers are model subagents shown LOOK and CLEAR pairs with sides swapped</li>
            <li>&quot;held&quot; covers both-prefer cases stopped by a measured regression or a parent override</li>
            <li>&quot;stopped&quot; means a lane hit its two-failure rule and went to the owner as two directions</li>
            <li>no review was re-run for this post</li>
          </ul>
        }
      >
        <ReviewGate trials={D.trials} counts={D.trialCounts} total={D.trialTotal} />
      </SetupFigure>
      <p>three things in that log are worth more than the win rate.</p>
      <p>
        <b>both reviewers preferring a candidate was not enough.</b> the it22 stone trial won both votes and was held
        because the count of front glints fell from 34 to 15. it25 won both votes and was held because its long pale
        streaks contradicted the owner&apos;s ask for dot-shaped glints. the gate is a vote plus measurements plus a stated
        direction, and the vote can lose.
      </p>
      <p>
        <b>the loop was wrong about its own target, and a measurement caught it.</b> the plinth polish lanes chased
        &quot;a broad wet sheen&quot; on the stone front. after two failed rounds the log measured the target: the reference
        front is darker than ours (low-pass luminance median 4.86 against 6.61), and the added coat had pushed it to 26.7.
        the rule written down that evening was &quot;measure before hypothesising&quot;.
      </p>
      <p>
        <b>ties are a stopping signal.</b> by 20:10 small Night changes kept tying. the loop paused its Night lanes and
        put three questions on the owner&apos;s page instead of rendering more. that is the right call, and it is also the
        limit of this kind of eval: a pair of model reviewers can rank close candidates, but they cannot settle taste.
      </p>

      <ExpHead n={3} id="picks">where did each scene end up?</ExpHead>
      <p>
        the archive snapshot is from October 15. drag the handle to compare each scene&apos;s pick at that point with its
        locked reference. the October 16 picks, with the reviewers&apos; notes, are in the tabs below.
      </p>
      <SetupFigure
        caption={<>reference left of the handle, pick right. medium plates from the lineage assets, 683×1024.</>}
        setup={
          <ul>
            <li>picks: the five current cards of the 2026-10-15 lineage snapshot</li>
            <li>references are art direction, not renders of the finished scene</li>
            <li>agent picks are working review selections, not release approval</li>
          </ul>
        }
      >
        <CompareSwipe themes={D.themes} references={D.references} current={D.current} />
      </SetupFigure>
      <TracePages items={pickTraces} label="the current pick per scene, 2026-10-16" />

      <ExpHead n={4} id="zoom">is a 1 GP export a gigapixel image?</ExpHead>
      <p>
        the scenes were meant to be explored with deep zoom, so each one has a tile pyramid. at {fmtInt(Z.scales["1gp"].width)} ×{" "}
        {fmtInt(Z.scales["1gp"].height)} that is {fmtInt(Z.scales["1gp"].pixels)} pixels, and the pyramids are complete:{" "}
        {Z.pyramids.map((p, i) => (
          <span key={i}>
            {i ? "; " : ""}
            {p.family}, {fmtInt(p.tiles)} of {fmtInt(p.expected)} tiles
          </span>
        ))}
        . <Evidence kind="source-reported">fidelity audit, 2026-10-15</Evidence>
      </p>
      <p>
        a complete pyramid only proves the pixels exist. the audit asked a different question: at each final pixel, how
        many texels of real source image land there? it traced neighbouring rays one 1 GP pixel apart through the actual
        UV and mapping chain of Night it12 and Day r115. below one texel per pixel, the renderer is interpolating.
      </p>
      <SetupFigure
        caption={<>texels per final pixel, log scale. switch between the two output sizes.</>}
        setup={
          <ul>
            <li>fixtures: {Z.fixtures.night} and {Z.fixtures.day}, source files hash-verified unchanged</li>
            <li>160×240 camera grid; per hit, neighbours one 1 GP pixel apart; smallest singular value of the texel Jacobian</li>
            <li>values are representative medians per source, not whole-material quality scores</li>
            <li>thresholds: {Z.thresholds.minimum} minimum, {Z.thresholds.preferred} preferred</li>
            <li>{Z.coverage.note}: Night {Z.coverage.night.below1_201}% at 201 MP and {Z.coverage.night.below1_1gp}% at 1 GP</li>
          </ul>
        }
      >
        <DensityChart rows={Z.density} minimum={Z.thresholds.minimum} preferred={Z.thresholds.preferred} />
      </SetupFigure>
      <p>
        at 201 MP, {below201} of {Z.density.length} sources are already under the floor. at 1 GP it is {below1gp}. the
        lettering on the robot is the worst case: about {Math.round(1 / nightHead.d1gp)} final pixels per source texel on
        Night&apos;s head. rendering more pixels does not add detail the textures never had.
      </p>
      <p>you can see it. pick a region on the plate and compare the same spot at each scale.</p>
      <SetupFigure
        caption={<>left: the plate with every audited region. right: the web plate scaled up, then the native 201 MP and 1 GP render crops.</>}
        setup={
          <ul>
            <li>crops: Cycles / OptiX, 32 samples, seed 17, denoised, compositor off</li>
            <li>surface diagnostics, not the final graded look</li>
            <li>Blender border rounding gave some crops 1023 or 1025 px; nothing was resized to hide it</li>
            <li>render seconds include crop setup on a shared GPU</li>
          </ul>
        }
      >
        <ZoomLadder regions={D.zoomRegions} plates={D.current} density={Z.density} />
      </SetupFigure>
      <p>
        production policy already reflects this. {Z.policy} nothing in the audit says the other scenes should join Blue
        yet.
      </p>

      <ExpHead n={5} id="scores">can a sharpness score stand in for the eye?</ExpHead>
      <p>
        the audit tried three fixes on copies of the scene and measured each with simple sharpness scores. the stone-face
        coupon is the warning: on the same crop, blur-1 gradient energy fell to {stone.blur1_gradient_energy_ratio}× while
        Laplacian variance rose to {stone.laplacian_variance_ratio}×. one score says much softer, the other says sharper.
      </p>
      <div className="qk-coupons">
        {Z.coupons.map((c) => (
          <div key={c.id} className="qk-coupon">
            <div className="qk-coupon-id">{c.id.replace("-", " ")}</div>
            <div className="qk-coupon-what">{c.what}</div>
            <div className="qk-coupon-bars">
              <Ratio label="blur-1 gradient energy" v={c.blur1_gradient_energy_ratio} />
              {"laplacian_variance_ratio" in c && c.laplacian_variance_ratio ? (
                <Ratio label="Laplacian variance" v={c.laplacian_variance_ratio as number} />
              ) : null}
            </div>
            <div className="qk-coupon-note">
              <span className="es-chip" data-tone="hold">
                {c.outcome}
              </span>{" "}
              {c.note}
            </div>
          </div>
        ))}
      </div>
      <p>
        all three were held. the head-ink trace is the most tempting one: edge energy rose 1.887×, and the traced letters
        came out sharply wrong. a score that rewards edge energy would have promoted it.
      </p>
      <figure className="es-fig">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="qk-wide-img" src={asset("/media/quackles-lineage-v0/zoom/coupons-before-after.webp")} alt="Before and after crops for the head-ink, banner-ink and stone-face coupons." loading="lazy" />
        <figcaption className="fig-caption">before and after for the three coupons. technique proofs, not scene approvals.</figcaption>
      </figure>

      <h2 id="timeline">the timeline as software</h2>
      <p>
        the swimlane in experiment 1 is a smaller rebuild of the quackles /lineage page. that page had its own checks, and
        its log reports: <Evidence kind="source-reported" /> Lighthouse{" "}
        {D.ui.lineage_page.lighthouse}; {D.ui.lineage_page.timeline_passes}; {D.ui.lineage_page.unit_tests}.
      </p>
      <p>
        two things did not happen. {D.ui.lineage_page.not_run} were never run, so there is no claim here that it holds 120
        Hz on a phone. and one failure turned out to be the sensor: {D.ui.home_sensor.finding}
      </p>

      <h2 id="limits">what this does not show</h2>
      <ul>
        <li>no render, review or audit was re-run. this is a reading of logs and reports, labelled source-reported.</li>
        <li>no scene is owner-approved. &quot;current&quot; means the agent&apos;s pick.</li>
        <li>the reviewers are model subagents. agreement between two of them is not a human preference study.</li>
        <li>one overnight log is one night. we make no claim about the gate&apos;s long-run promote rate.</li>
        <li>{D.mtimeDated} of {N} archive dates are file mtimes.</li>
        <li>texel densities are sampled medians; the heatmap coverage numbers are warnings, not proof of blur.</li>
      </ul>

      <h2 id="next">what comes next</h2>
      <p>
        three Night decisions are waiting on the owner: the banner face (keep the portrait image or sculpt it), the robot
        finish (clean printed shell or one painted exemplar), and which of two Night briefs is the real one. the
        region-colour metric rewards the darker brief, which is exactly why a metric cannot pick it.
      </p>
      <p>
        for gigapixel, the audit names the work: clean vector artwork for the lettering, owner-approved microdetail, and
        exports from the right scene lineage, each checked with a max-zoom gate before anyone calls a scene gigapixel-ready.
        when that happens, it gets its own frozen study.
      </p>
    </>
  );
}

function Ratio({ label, v }: { label: string; v: number }) {
  const w = Math.min(100, (v / 2) * 100);
  return (
    <div className="qk-ratio">
      <span className="qk-ratio-l">{label}</span>
      <span className="qk-ratio-track">
        <span className="qk-ratio-one" />
        <span className="qk-ratio-bar" data-up={v >= 1} style={{ width: `${w}%` }} />
      </span>
      <span className="qk-ratio-v">{v}×</span>
    </div>
  );
}

function Explore() {
  return (
    <div className="explore-block">
      <h2 id="receipts">receipts</h2>
      <p>
        the frozen study is <a href={`${repo}/tree/main/studies/quackles-lineage-v0`}>studies/quackles-lineage-v0</a>. its
        manifest pins the quackles commits, hashes every data file and image, and lists the limitations above.
      </p>
      <ul>
        <li>
          lineage dataset, timeline and atlas: kvnloo/quackles <code>fff480b</code> (local branch perf/motion-decode-eval,
          not pushed), bound by dataset sha256 <code>{D.datasetSha256.slice(0, 16)}…</code>
        </li>
        <li>
          plates: kvnloo/quackles-assets <code>7c2e7da</code> (local branch), content-addressed filenames
        </li>
        <li>
          process images: <a href="https://github.com/kvnloo/quackles/tree/cb1196dcbfb05e4061b1eb30a1b6891a79372107/public/process/images">kvnloo/quackles cb1196d</a>, unchanged
        </li>
        <li>overnight trials, picks, fidelity numbers: transcribed from the operator log, CURRENT.json and the fidelity REPORT.md; artifact-store paths removed</li>
        <li>web data: <code>python3 scripts/build_quackles_data.py</code>, which fails if the frozen files disagree</li>
      </ul>
      <h3>cite</h3>
      <Citation
        id="z0evals2026quackles"
        title="quackles, in 665 renders"
        year={2026}
        url="https://kvnloo.github.io/z0evals/quackles-lineage-v0/"
        note="source-reported study quackles-lineage-v0"
      />
    </div>
  );
}

export default function QuacklesLineagePage() {
  return <StoryShell meta={meta} banner={banner} toc={toc} story={<Story />} explore={<Explore />} />;
}
