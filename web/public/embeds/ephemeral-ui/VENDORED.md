# Vendored: ephemeral-ui trace cards

Copied unmodified from kvnloo/launch-videos `pretotypes/ephemeral-ui/src` at commit `95b9ada56cafbbff8dca1517d8a130b8e604572d`
(`git show <commit>:pretotypes/ephemeral-ui/src/<file>`):

- `js/motion.js`, `js/shell.js`, `js/themes.js`, `js/trace-data.js`, `js/kinds-t.js`, `js/ask.js`
- `styles.css`, `trace.css`
- `data/trace-fixture.json` (omp-stats 18.9.2 API responses, sanitized by the kit's `tools/sanitize-trace.mjs`
  and leak-checked by `tools/leak-check.mjs`; the same file is served at https://ephemeralui.vercel.app)
- `data/themes.json`, `schema/trace-query.v0.json`

`embed.html` is ours: it mounts one trace card (`?view=kind&kind=<kind>`) or the "Ask the trace"
section (`?view=ask&q=<question>`) and posts its height to the parent (`web/components/essay/KitEmbed.tsx`).

To refresh, copy the same files from a newer commit and update the hash above; the post reads it.
