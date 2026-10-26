import type { Metadata } from "next";
import SiteLink from "@/components/site/SiteLink";
import StatusDot from "@/components/site/StatusDot";
import { POST_STATUS, STATUS } from "@/lib/status";
import { site } from "@/lib/catalog";

export const metadata: Metadata = {
  title: "about — z0evals",
  description: "what zer0 evals is, how a study becomes a post, and what each evidence status means.",
};

export default function About() {
  const conf = site();
  return (
    <div className="site-container page-narrow about prose">
      <header className="page-head">
        <h1 className="page-title">about</h1>
        <p className="page-lede">{conf.positioning}</p>
      </header>

      <h2 id="what">what this is</h2>
      <p>
        zer0 evals is the public, reproducible evaluation layer of the zer0 agent stack. other repositories run the
        experiments and own the production behaviour; this one freezes the evidence and publishes what it does and
        does not show.
      </p>

      <h2 id="method">how a study becomes a post</h2>
      <ol>
        <li>an experiment runs somewhere else and is committed there.</li>
        <li>an import spec pins that source by commit sha and allowlists the files that may be published.</li>
        <li>the frozen data is validated, analysed and turned into figures.</li>
        <li>the post says what was measured, what it does not prove, and links every receipt.</li>
      </ol>
      <p>
        no claims without receipts. negative and incomplete results stay on the site: a miss against a
        pre-registered bar is still evidence. the <SiteLink href="/log/">research log</SiteLink> lists every eval,
        experiment and idea, including the ones that never became a post.
      </p>

      <h2 id="status">evidence status</h2>
      <p>every post and study carries one of these. status is always a dot and a word, never colour alone.</p>
      <dl className="status-legend">
        {Object.entries(POST_STATUS).map(([raw, [tone, label]]) => (
          <div key={raw}>
            <dt><StatusDot tone={tone} label={label} /></dt>
            <dd><code>{raw}</code></dd>
          </div>
        ))}
      </dl>
      <p>research-log entries use their own lifecycle:</p>
      <dl className="status-legend">
        {Object.entries(STATUS).map(([raw, [tone, label]]) => (
          <div key={raw}>
            <dt><StatusDot tone={tone} label={label} /></dt>
            <dd><code>{raw}</code></dd>
          </div>
        ))}
      </dl>

      <h2 id="source">source</h2>
      <p>
        everything here is built from <a href={conf.repo}>the z0evals repository</a>: the posts, the frozen studies,
        their manifests and the scripts that render this site.
      </p>
    </div>
  );
}
