# Verified OSS Loop (z0evals)

This repository already has its own `AGENTS.md`. The Verified OSS Loop kit lives under `.verified-oss-loop/` so onboard does not replace project instructions or dump kit skills over existing `source: local` skills.

The rollout ladder is `feature → preview → nightly → dev → main`. Preview/nightly are integration channels; `dev` and `main` remain maintainer-gated. This repository's maintainer may explicitly authorize origin writes and promotions.

## Kit paths

- Inventory / rollout: `.verified-oss-loop/`
- Kit skills (not copied into `skills/`): `.verified-oss-loop/skills/`
- Similar-issue clustering (local fixture only, cap 64): `.verified-oss-loop/scripts/cluster-similar-issues.py`

## Commands

| Layer | Command |
|---|---|
| Unit | `python scripts/validate.py` |
| Mutation | `n/a` |
| Runtime | `python scripts/build_site.py` |

```bash
python3 .verified-oss-loop/rollout.py show
python3 .verified-oss-loop/scripts/cluster-similar-issues.py tests/fixtures/issues-tiny.json
```

Repo: https://github.com/kvnloo/z0evals
