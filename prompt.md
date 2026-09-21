# Autodevelop — z0evals

Paste this file as the first message to a coding agent donating one contribution pass.

Repository: https://github.com/kvnloo/z0evals  
Protocol: https://github.com/kvnloo/verified-oss-loop

You are a contributor, not a maintainer. Never merge `main`.

1. Open the repository and read `AGENTS.md`, `CONTRIBUTING.md`, and `docs/verified-oss-loop.md`.
2. Run `python3 .verified-oss-loop/rollout.py show`. z0evals uses `stable`, so branch from `origin/main` and target `main`.
3. Search open issues and PRs. Take exactly one `claimable` issue with a bounded lease. Do not self-promote an issue to `claimable`.
4. Orient before editing using `.verified-oss-loop/skills/orient/SKILL.md`.
5. For executable changes, fail then pass using `.verified-oss-loop/skills/tdd/SKILL.md`. Unit proof: `python scripts/validate.py`. Site proof: `python scripts/build_site.py`. Mutation: `n/a`.
6. Keep the smallest complete change using `.verified-oss-loop/skills/anti-slop/SKILL.md`.
7. Open a PR with `.github/PULL_REQUEST_TEMPLATE.md` fully filled. Bind `head_revision` to the actual PR head.
8. Stop. Independent review and maintainer merge come next.

z0evals-specific hard rule: never publish secrets, private prompts, personal traces, or mutable local runtime directories. Frozen study claims must resolve to pinned public evidence.
