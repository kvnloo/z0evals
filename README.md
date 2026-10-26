# z0evals

Reproducible evaluations and public research reports for the Zer0 ecosystem.

z0evals is the **frozen evidence/publication layer**. It does not run production routing, own runtime policy, or replace the experiment engines that produce candidate systems.

## Ownership

```text
frontier-kb      external evidence / literature
       │
Evolution Lab    experiment design + execution + training
       │
Tokenomics       neutral measurements / receipts / verified outcomes
       │
z0evals          frozen datasets + analysis + figures + public reports
       │
z0intelligence   promotion / shadow / canary decisions
       │
Kerdoios         resource placement among allowed candidates
```

A study enters z0evals only after its input revisions are pinned and its results can be reproduced or independently inspected.

## First study

`studies/slm-router-v0/` is reserved for the local SLM routing study produced from the September 2026 z0intelligence / Evolution Lab work.

The initial report will investigate:

- compiler-first legal-action filtering
- FunctionGemma, Hammer 2.1, Nemotron-Orchestrator and Qwen routing behavior
- latency / quality / GPU tradeoffs on an RTX 3080 Ti
- bounded tool choice versus authentic orchestration
- the basis for a continuously distilled Q-Route policy

## Setup

CI pins Python 3.12 and Node 22 (`.python-version`, `.nvmrc`). Python 3.10 or newer and Node 20.9 or newer also work, but CI does not test other versions.

Always use a virtual environment. Many hosts (Arch/CachyOS, Debian 12+, Ubuntu 24.04, Homebrew Python) mark the system Python as externally managed (PEP 668), and a bare `pip install` fails there. Do not pass `--break-system-packages`.

```bash
# with uv
uv venv .venv --python 3.12
uv pip install -p .venv -r requirements.txt

# or with the standard library only
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run every script with `.venv/bin/python`. The checks below follow the CI order (`.github/workflows/ci.yml`). `zer0.repo.yaml` (`setup:`) declares the same order for the z0 onboarder.

```bash
PY=.venv/bin/python

# Python tier (no network after pip)
$PY -m unittest discover -s tests -p test_pages_publication.py -v
$PY scripts/validate.py
$PY tests/expire_claims.py
$PY scripts/validate_optchat_publication.py
$PY -m unittest discover -s tests -p test_optchat_publication.py -v
$PY scripts/audit_web_source.py
$PY scripts/build_site.py && test -f site/index.html
$PY scripts/build_site_data.py   # must run before any npm typecheck/dev/build
$PY scripts/build_posts.py
$PY -m unittest discover -s tests -p test_build_posts.py -v

# Web tier (needs the npm registry and Google Fonts at build time)
cd web
npm ci --no-audit --no-fund      # npm only; keep optional deps (platform natives)
npm run typecheck
Z0_BASE_PATH=/z0evals npx next build && test -f out/index.html
cd ..
$PY scripts/audit_web_export.py --root web/out
```

Offline, run only the Python tier: `next/font/google` fetches fonts during `next build`.

The generators write gitignored outputs (`site/`, `web/data/posts/`, `web/data/research-focus.html`, `web/data/optchat-long-horizon-v0.json`). `build_site_data.py` also rewrites the committed `web/data/study.json`: without the local openjev corpus (`~/tmp/openjev`) only its `matrixOrigin` line changes; with the corpus it also rewrites `studies/slm-router-v0/data/phase1b-matrix.json`. Do not commit that drift by accident.

### Open questions for the maintainer

These are known and not resolved here:

- **B7, branching docs conflict.** `prompt.md` says the stable scheme (branch from `origin/main`). `.verified-oss-loop/rollout.yml`, `AGENTS.md` and `CONTRIBUTING.md` say the rolling scheme with base `nightly`. Until the maintainer decides, `python3 .verified-oss-loop/rollout.py show` is the authority.
- **B8, single-branch or shallow clones.** These see only `origin/main`, but the Pages build and the contributor flow need `main`, `dev`, `nightly` and `preview`. Run `git fetch origin main dev nightly preview`. Also, `web/data/research-log.json` links `studies/fsm-work-item-v0` at a SHA that is not on `main`, and `docs/verified-oss-loop.md` references `tests/fixtures/issues-tiny.json`, which does not exist.

## Layout

```text
studies/    frozen study manifests, analysis notes, public data and figures
posts/      publication-ready narratives derived from studies
schemas/    versioned contracts
scripts/    import, validation and site-generation helpers
site/       generated GitHub Pages output
```

## Importing a local DSH result

Do **not** push a whole local worktree or private trace directory.

Use an import spec that pins the source repository and commit, and explicitly allowlists each artifact to publish:

```bash
.venv/bin/python scripts/import_local.py imports/slm-router-v0.local.yaml
.venv/bin/python scripts/validate.py
```

Set up the venv first (see Setup).

See `imports/slm-router-v0.example.yaml`.

## Rules

1. Every claim in a post should resolve to a frozen study artifact.
2. Source-reported benchmark numbers and our reproduced measurements are different fields.
3. Raw secrets, credentials, personal traces and private prompts never enter this public repository.
4. Training/evaluation splits must preserve work-item lineage.
5. The system that generated a label cannot silently become its own verifier.
6. A study may report an incomplete or negative result. Do not hide failed hypotheses.

## Related repos

- https://github.com/kvnloo/z0
- https://github.com/kvnloo/z0intelligence
- https://github.com/kvnloo/evolution-lab
- https://github.com/kvnloo/tokenomics
- https://github.com/kvnloo/kerdoios
- https://github.com/kvnloo/frontier-kb
