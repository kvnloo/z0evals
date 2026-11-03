import type { Metadata } from "next";
import StoryShell, { type StoryMeta, type StoryBanner } from "@/components/StoryShell";
import { studyMeta } from "@/lib/catalog";
import type { TocItem } from "@/components/Toc";
import Callout from "@/components/Callout";
import { Tldr, ExpHead, Evidence, Teaser, GrowBars, SetupFigure, TracePages, Citation, type TraceItem } from "@/components/essay/Essay";
import "./fframes.css";
// Every number below is read from the frozen study through ./data, which throws at build
// time if the per-frame series, the source summary, and the upload sizes disagree.
import {
  allWin,
  bestPlatform,
  byId,
  clipLosses,
  commit,
  contents,
  doc,
  fmt,
  FRAMES,
  gradientPlatforms,
  gradientRow,
  platforms,
  ratioMax,
  ratioMin,
  short,
  signed,
  sourceUrl,
  totalFrames,
} from "./data";
import { FrameExplorer, GainChart, GradientMini, GradientPanel } from "./figures";

if (!allWin) {
  throw new Error("fframes post: the text says ours wins pooled mean and p5 everywhere; the data no longer agrees");
}

const slug = "fframes-delivery-v0";
const x = byId("x");
const gp = gradientPlatforms[0];
const gN = gradientRow(gp, "naive").vmaf;
const gO = gradientRow(gp, "fast").vmaf;
const n = platforms.length;
const perArm = FRAMES * contents.length;
const secs = x.clips[0].duration_s;
const zFloor = Math.floor(x.summary.naive.vmaf.p5 / 10) * 10;
const study = `https://github.com/kvnloo/z0evals/tree/main/studies/${slug}`;
const underOne = platforms.filter((p) => p.gain.vmaf.mean < 1).length;
const yt = gradientRow(gp, "fast").cambi.mean < gradientRow(gp, "naive").cambi.mean;
const other = gradientPlatforms[1];
// The prose states these directions; fail the build if the frozen data stops supporting them.
const checks: [boolean, string][] = [
  [platforms.every((p) => contents.every((c) => {
    const mean = (k: string) => doc.series[p.id][k].naive.vmaf.reduce((a, b) => a + b, 0);
    return c === "gradient" || mean("gradient") < mean(c);
  })), "gradient is the lowest-scoring naive clip in every simulator"],
  [platforms.filter((p) => p.ours_profile.prefilter !== "none").map((p) => p.id).join() === "x", "x is the only sharpened profile"],
  [x.gain.vmaf_neg.mean < x.gain.vmaf.mean, "x NEG gain is smaller than VMAF gain"],
  [gradientPlatforms.every((g) => gradientRow(g, "hevc10").vmaf.mean < gradientRow(g, "naive").vmaf.mean), "hevc10 also loses mean VMAF on the ramp"],
  [yt && !!other && gradientRow(other, "fast").cambi.mean > gradientRow(other, "naive").cambi.mean, "CAMBI direction differs between ramp simulators"],
];
for (const [ok, what] of checks) if (!ok) throw new Error(`fframes post: prose check failed: ${what}`);
const lossText = clipLosses.map((l) => `${l.platform} ${l.content} ${l.stat} (${fmt(l.naive)} to ${fmt(l.ours)})`).join(", ");

export const metadata: Metadata = {
  title: "a bigger upload scores higher in a simulator · z0evals",
  description:
    "fframestudio's platform export recipes beat a naive x264 upload in five playback simulators. the uploads are 3 to 4 times larger, the clips were also the tuning set, and a synthetic gradient goes the other way.",
};

const meta: StoryMeta = studyMeta("fframes-delivery-v0");

const banner: StoryBanner = {
  tag: "simulator only · source-reported",
  text: `no video was uploaded to any platform. the recipes were picked on the same ${contents.length} clips they are scored on. uploads are ${fmt(ratioMin)}x to ${fmt(ratioMax)}x larger than naive, so this is not an equal-bitrate test.`,
};

const toc: TocItem[] = [
  { id: "what", label: "what was compared", depth: 0 },
  { id: "exp-pooled", label: "1. five simulators", depth: 0 },
  { id: "exp-frames", label: "2. ninety frames at a time", depth: 0 },
  { id: "exp-gradient", label: "3. the blue ramp", depth: 0 },
  { id: "exp-gates", label: "4. what checked the code", depth: 0 },
  { id: "limits", label: "what this does not show", depth: 0 },
  { id: "explore", label: "source and provenance", depth: 0 },
];

function profileLine(p: (typeof platforms)[number], which: "naive_profile" | "ours_profile") {
  const q = p[which];
  const rate = q.maxrate_kbps ? `, maxrate ${q.maxrate_kbps / 1000} Mbps` : "";
  const buf = q.bufsize_kbits ? `, buffer ${q.bufsize_kbits / 1000} Mbit` : "";
  const quality = q.encoder === "libx264" ? `CRF${q.quality}` : `CQ${q.quality}`;
  return `${q.width}x${q.height}, ${q.encoder} ${quality}, ${q.scale} scale${q.prefilter !== "none" ? `, ${q.prefilter}` : ""}, GOP ${q.gop_seconds} s${rate}${buf}`;
}

const setupCommon = (
  <ul>
    <li>clips: {contents.join(", ")}. {FRAMES} frames each at 30 fps, from one lossless FFV1 reference per aspect ratio.</li>
    <li>metrics: VMAF {doc.metric_versions.vmaf} and VMAF NEG {doc.metric_versions.vmaf_neg} through FFmpeg libvmaf, every aligned frame, no last-frame padding.</li>
    <li>pooled p5: 5th percentile of all {perArm} frames per arm, linear interpolation, not an average of clip p5 values.</li>
    <li>both arms go through the same simulator. naive and ours differ only in the upload recipe.</li>
  </ul>
);

const setupPlatforms = (
  <ul>
    {platforms.map((p) => (
      <li key={p.id}>
        <strong>{p.id}</strong>. naive: {profileLine(p, "naive_profile")}. ours: {profileLine(p, "ours_profile")}. simulator:{" "}
        {p.simulator.width}x{p.simulator.height} {p.simulator.codec} CRF{p.simulator.crf}, nominal {p.simulator.bitrate_kbps / 1000} Mbps, GOP{" "}
        {p.simulator.gop_seconds} s.
      </li>
    ))}
  </ul>
);

const gateAsk: Record<string, string> = {
  "ruff check": "does the delivery code pass the linter?",
  "ruff format": "is the delivery code already formatted?",
  "python -m compileall": "does every delivery module compile?",
  "git diff --cached": "does the staged diff have whitespace errors?",
};
const gateItems: TraceItem[] = [
  ...doc.gates.gates.map((g): TraceItem => {
    const key = Object.keys(gateAsk).find((k) => g.command.startsWith(k)) ?? g.command;
    return {
      label: key,
      group: "gates.json",
      ask: gateAsk[key] ?? g.command,
      given: <code>{g.command}</code>,
      answer: g.output ? <code>{g.output}</code> : <span>no output</span>,
      verdict: { text: `exit ${g.returncode}`, tone: g.returncode === 0 ? "pass" : "fail" },
      steps: [<>ran <code>{g.command}</code> in the source repo</>, <>recorded return code {g.returncode}</>],
      foot: <>source: <code>delivery/evidence/gates.json</code> at {short}</>,
    };
  }),
  {
    label: "review",
    group: "gates.json",
    ask: "did someone other than the author review this run?",
    answer: doc.gates.review,
    verdict: { text: "self-review only", tone: "hold" },
    steps: [
      <>static scan findings recorded: {doc.gates.static_scan_findings.length}</>,
      <>these are hygiene checks. none of them checks a VMAF number.</>,
    ],
    foot: <>source: <code>delivery/evidence/gates.json</code> at {short}</>,
  },
];

const story = (
  <>
    <Tldr>
      <p>
        the selected export recipes score higher than a naive x264 CRF{x.naive_profile.quality} upload on pooled mean and p5 VMAF in all{" "}
        {n} of fframestudio&apos;s playback simulators. the largest move is {bestPlatform.id}: p5 goes from{" "}
        {fmt(bestPlatform.summary.naive.vmaf.p5)} to {fmt(bestPlatform.summary.fast.vmaf.p5)}.
      </p>
      <p>
        that gain is paid for. our uploads are {fmt(ratioMin)}x to {fmt(ratioMax)}x larger. the recipes were tuned on the same{" "}
        {contents.length} clips of {secs} seconds, and on a synthetic 10-bit blue ramp the selected H.264 recipe loses. nothing was uploaded to
        a real platform.
      </p>
    </Tldr>

    <Teaser
      label="the result in three panels"
      panels={[
        {
          step: "encode",
          task: <>export the same clips two ways for the {x.id} simulator.</>,
          visual: (
            <GrowBars from={1} to={x.upload_ratio} max={Math.ceil(ratioMax)} labels={["naive", "ours"]} digits={2} suffix="x" />
          ),
          by: <>upload bytes, ours / naive, {contents.length} clips summed</>,
          big: <>{fmt(x.upload_ratio)}x</>,
          note: <>the upload is bigger. keep that in mind for the next panel.</>,
        },
        {
          step: "score",
          task: <>re-encode both uploads with the {x.id} simulator, then score every frame.</>,
          visual: (
            <GrowBars
              from={x.summary.naive.vmaf.p5 - zFloor}
              to={x.summary.fast.vmaf.p5 - zFloor}
              max={100 - zFloor}
              labels={["naive", "ours"]}
              digits={1} offset={zFloor}
            />
          ),
          by: <>pooled VMAF p5, {perArm} frames per arm. bars start at {zFloor}.</>,
          big: <>{signed(x.gain.vmaf.p5, 1)}</>,
          note: <>p5 VMAF. the low tail moves up.</>,
        },
        {
          step: "counterexample",
          task: <>same recipe, a procedural 10-bit blue ramp, {gp} simulator.</>,
          visual: <GradientMini platform={gp} />,
          by: <>filled dot mean, hollow dot p5. axis zoomed.</>,
          big: <>{signed(gO.mean - gN.mean)}</>,
          note: <>mean VMAF. naive wins here.</>,
        },
      ]}
    />

    <h2 id="what">what was compared</h2>
    <p>
      fframes and fframestudio make the videos. the delivery step decides how a finished master is encoded before it goes to youtube,
      shorts, tiktok, reels, or x. a platform then re-encodes what it gets, so a good-looking upload is not the end of the story.
    </p>
    <p>
      fframestudio could not measure a real platform without uploading, so it built a stand-in for each one: a fixed codec, quality, and
      bitrate request that approximates playback. both arms go through the same stand-in. <em>naive</em> is x264 medium at CRF{x.naive_profile.quality}{" "}
      with {x.naive_profile.scale} scaling. <em>ours</em> is NVENC H.264 at CQ{x.ours_profile.quality} with {x.ours_profile.scale} scaling,
      and mild CAS sharpening for x. the scores are{" "}
      <Evidence kind="source-reported">fframestudio ran the encodes and libvmaf</Evidence>. we re-derived every pooled mean and p5 from the{" "}
      {totalFrames.toLocaleString("en-US")} per-frame rows and they match the source summary{" "}
      <Evidence kind="reproduced">aggregation only, no video re-scored</Evidence>.
    </p>

    <ExpHead n={1} id="exp-pooled">five simulators, one pooled score each</ExpHead>
    <p>
      each bar pair is ours minus naive for one simulator, pooled over {perArm} frames. the red bar beside it is what that cost in upload
      bytes. switch to VMAF NEG, the variant that is meant to discount gains from sharpening and contrast boosts.
    </p>
    <SetupFigure
      setup={
        <>
          {setupCommon}
          {setupPlatforms}
        </>
      }
      caption={
        <>
          gain is source-reported pooled VMAF or VMAF NEG, ours minus naive. upload size is the sum of the four clip uploads. sizes differ by{" "}
          {fmt(ratioMin)}x to {fmt(ratioMax)}x, so a quality gain at equal bitrate is not tested here.
        </>
      }
    >
      <GainChart />
    </SetupFigure>
    <p>
      every simulator moves in the same direction, but {underOne} of {n} move less than one VMAF point on the mean. x stands out at{" "}
      {signed(x.gain.vmaf.mean)} mean and {signed(x.gain.vmaf.p5)} p5. x is also the only profile with a sharpening filter, and its VMAF NEG
      gain is smaller: {signed(x.gain.vmaf_neg.mean)} mean. part of the x gain is the kind of sharpening VMAF is known to reward.
    </p>

    <ExpHead n={2} id="exp-frames">ninety frames at a time</ExpHead>
    <p>
      a pooled number hides where it comes from. pick a simulator and a clip, then drag across the chart or use the arrow keys (shift for
      ten frames) to read each frame. the table under it prints the clip and pooled mean and p5 for the metric you picked.
    </p>
    <SetupFigure setup={setupCommon} caption={<>per-frame scores from <code>frames.csv</code>, rounded to three decimals for the page.</>}>
      <FrameExplorer />
    </SetupFigure>
    <p>
      the gradient clip has the lowest naive mean in every simulator. the aggregate also hides some
      clip-level losses. on VMAF alone, ours is below naive for: {lossText || "none"}. the source report lists more on other metrics, such
      as CAMBI banding on reels gradient.
    </p>

    <ExpHead n={3} id="exp-gradient">the blue ramp, where we lose</ExpHead>
    <p>
      fframestudio also exported a procedural 10-bit blue ramp. it is a stress test for banding, not real sky footage. here the selected
      H.264 recipe scores lower than naive on mean and p5 VMAF in both simulators that ran it. an HEVC Main10 upload does not fix it
      either: playback is still 8-bit 4:2:0 after the simulator.
    </p>
    <SetupFigure
      setup={
        <ul>
          <li>source: {gradientRow(gp, "naive").source}.</li>
          <li>
            arms:{" "}
            {["naive", "fast", "hevc10"].map((v) => {
              const r = gradientRow(gp, v);
              return `${v === "fast" ? "ours" : v} ${r.encoder} q${r.quality}`;
            }).join(", ")}.
          </li>
          <li>simulators: {gradientPlatforms.join(", ")}. {gradientRow(gp, "naive").frames} frames each.</li>
          <li>the HEVC arm changes codec and bit depth together, so it is not a bit-depth-only test.</li>
        </ul>
      }
      caption={<>VMAF mean and p5, or CAMBI mean, from <code>gradient10.json</code>. CAMBI is a banding score; lower is less banding.</>}
    >
      <GradientPanel />
    </SetupFigure>
    <p>
      the VMAF gaps are small in absolute terms, all scores sit near 100. the point is the direction. a recipe that wins the four-clip
      aggregate can still lose on a gradient, which is the content where banding shows. CAMBI tells a mixed story: our H.264 arm bands less
      on the {gp} simulator by that score, and not on {other}.
    </p>

    <ExpHead n={4} id="exp-gates">what checked the code</ExpHead>
    <p>
      the source run recorded its hygiene gates. they are worth reading for what they are: lint, format, compile, and whitespace checks
      that passed. none of them verifies a quality number, and the review was the author&apos;s own.
    </p>
    <TracePages items={gateItems} label="source quality gates" />

    <h2 id="limits">what this does not show</h2>
    <Callout kind="warning" title="simulator, not platform">
      <p>
        no video was uploaded to youtube, shorts, tiktok, reels, or x. each simulator is a guess at playback encoding, built from public
        upload guidance. the real services use their own ladders and codecs.
      </p>
    </Callout>
    <ul>
      <li>
        the recipes were chosen on these {contents.length} clips and scored on the same clips. there is no held-out corpus, so some of the
        gain may be fit to these clips.
      </li>
      <li>
        {contents.length} clips of {FRAMES} frames ({secs} seconds) each. frames within a clip are correlated. we make no significance claim.
      </li>
      <li>
        uploads are {fmt(ratioMin)}x to {fmt(ratioMax)}x larger. a fair next test holds upload bitrate fixed.
      </li>
      <li>VMAF is not calibrated for small UI text or portrait phone viewing. no human viewing test was run.</li>
      <li>the encoded videos are not frozen here, only the scores, sizes, and gates the source recorded.</li>
    </ul>
    <p>
      what would change our mind, in either direction: real uploads and downloads across accounts, a held-out set of native portrait
      clips, natural skies and fast motion, and the same comparison at equal upload size.
    </p>

    <Citation
      id="zer0-fframes-delivery-v0"
      title="a bigger upload scores higher in a simulator"
      year={2026}
      url={`https://kvnloo.github.io/z0evals/${slug}/`}
      note={`fframestudio ${commit}`}
    />
  </>
);

const explore = (
  <>
    <h2>source and provenance</h2>
    <p>
      the source is <code>kvnloo/fframestudio</code> at <code>{commit}</code>, the commit that scrubbed machine paths from the delivery
      evidence. the evidence files are unchanged at the later main branch head. the study manifest records each file&apos;s sha256.
    </p>
    <ul>
      <li>
        <a href={sourceUrl("delivery/REPORT.md")}>delivery/REPORT.md</a>, the full source report, including low-resolution and temporal
        experiments this post does not chart.
      </li>
      <li>
        <a href={sourceUrl("delivery/RESEARCH.md")}>delivery/RESEARCH.md</a>, the platform guidance behind each simulator.
      </li>
      <li>
        <a href={sourceUrl("delivery/evidence/frames.csv")}>frames.csv</a> ({totalFrames.toLocaleString("en-US")} rows) and{" "}
        <a href={sourceUrl("delivery/evidence/summary.json")}>summary.json</a>.
      </li>
      <li>
        <a href={`${study}/manifest.yaml`}>study manifest</a>. <code>results.json</code> and <code>gradient10.json</code> are frozen as
        cleaned copies with their path fields removed; the numbers are unchanged.
      </li>
    </ul>
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>pooled VMAF and VMAF NEG, mean / p5, {perArm} frames per arm. source-reported.</caption>
        <thead>
          <tr>
            <th scope="col">simulator</th>
            <th scope="col">naive VMAF</th>
            <th scope="col">ours VMAF</th>
            <th scope="col">VMAF gain</th>
            <th scope="col">NEG gain</th>
            <th scope="col">upload</th>
          </tr>
        </thead>
        <tbody>
          {platforms.map((p) => (
            <tr key={p.id}>
              <th scope="row">{p.id}</th>
              <td>{fmt(p.summary.naive.vmaf.mean, 3)} / {fmt(p.summary.naive.vmaf.p5, 3)}</td>
              <td>{fmt(p.summary.fast.vmaf.mean, 3)} / {fmt(p.summary.fast.vmaf.p5, 3)}</td>
              <td>{signed(p.gain.vmaf.mean, 3)} / {signed(p.gain.vmaf.p5, 3)}</td>
              <td>{signed(p.gain.vmaf_neg.mean, 3)} / {signed(p.gain.vmaf_neg.p5, 3)}</td>
              <td>{fmt(p.upload_ratio)}x</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <p>
      the page data is built by <code>scripts/build_fframes_delivery.py</code> from the frozen files. it recomputes every pooled mean and
      p5 from the per-frame rows with the source&apos;s percentile rule and fails if any differs from the summary.
    </p>
  </>
);

export default function Page() {
  return <StoryShell meta={meta} toc={toc} banner={banner} story={story} explore={explore} />;
}
