import type { Metadata } from "next";
import fs from "node:fs";
import path from "node:path";
import LogExplorer, { STATUS, type LogEntry } from "@/components/LogExplorer";

export const metadata: Metadata = {
  title: "the research log — z0evals",
  description: "every eval, experiment, goal and idea in one place, and where our attention is going and why.",
};

type LogDoc = { updated: string; entries: LogEntry[] };

function load(): { doc: LogDoc; focusHtml: string } {
  const dir = path.join(process.cwd(), "data");
  const doc = JSON.parse(fs.readFileSync(path.join(dir, "research-log.json"), "utf8")) as LogDoc;
  // prerendered from research-focus.md by scripts/build_posts.py
  const focusPath = path.join(dir, "research-focus.html");
  const focusHtml = fs.existsSync(focusPath) ? fs.readFileSync(focusPath, "utf8") : "";
  return { doc, focusHtml };
}

export default function ResearchLog() {
  const { doc, focusHtml } = load();
  const byStatus = Object.keys(STATUS)
    .map((k) => [k, doc.entries.filter((e) => e.status === k).length] as const)
    .filter(([, n]) => n > 0);
  const posts = doc.entries.filter((e) => e.post).length;
  return (
    <div className="shell log-shell">
      <header className="blog-page-header">
        <div>
          <nav className="site-nav" aria-label="research pages">
            <a className="brand" href="../">z0evals</a>
            <div className="links">
              <a href="../log/" aria-current="page">log</a>
              <a href="../">phase 1b</a>
              <a href="../z0intelligence-function-routing/">routing</a>
              <a href="../researching-the-frontier/">research</a>
              <a href="../unified-memory-v0/">memory</a>
              <a href="../optchat-long-horizon-v0/">optchat</a>
              <a href="https://github.com/kvnloo/z0evals">github</a>
            </div>
          </nav>
        </div>
      </header>
      <main className="log-main">
        <header className="log-hero">
          <div className="log-kicker">the research log · updated {doc.updated}</div>
          <h1 className="article-title">everything we&apos;re testing, <em>and why.</em></h1>
          <p className="story-lede">
            one page for every eval, experiment, goal and idea. what we measured, what it does not prove, and where
            our attention is going because a result, a paper or an idea pulled it there. negative and incomplete
            results stay on the page.
          </p>
          <div className="log-strip" aria-label="entries by status">
            <div className="log-stat"><b>{doc.entries.length}</b><span>entries</span></div>
            <div className="log-stat"><b>{posts}</b><span>with a post</span></div>
            {byStatus.map(([k, n]) => (
              <div className="log-stat" key={k}><b>{n}</b><span><span className={`dot ${STATUS[k][0]}`} /> {STATUS[k][1]}</span></div>
            ))}
          </div>
        </header>
        {focusHtml ? (
          <section className="log-focus prose" aria-labelledby="focus">
            <div dangerouslySetInnerHTML={{ __html: focusHtml }} />
          </section>
        ) : null}
        <section aria-labelledby="all-entries">
          <h2 id="all-entries" className="log-h2">every entry</h2>
          <LogExplorer entries={doc.entries} />
        </section>
        <footer className="log-foot">
          <p>
            statuses follow the z0evals evidence rules: <i>published</i> and <i>frozen</i> mean pinned, reproducible
            evidence; <i>draft study PR</i> means the evidence is not reviewed yet; <i>proposal</i> and <i>idea</i>{" "}
            mean nothing has been measured. a finding is only as strong as its linked source.
          </p>
        </footer>
      </main>
    </div>
  );
}
