# OMP local capture and privacy-safe export

Status: **capture/export implemented; actual OMP execution remains blocked on
original inputs and an authorized free route.** Fixture tests below establish
export correctness only. Neither capture nor integrity replay executes a model,
runs the behavioral oracle, validates approval receipts, or proves helper reuse.

## Ownership and source handoff

- Coordination: [z0intelligence #137](https://github.com/kvnloo/z0intelligence/issues/137#issuecomment-6090259589).
- Original EventLog 534 witness reference: [Claude lane report](https://github.com/kvnloo/z0intelligence/issues/137#issuecomment-6088711509).
- Historical corrected-state handoff reviewed on 2026-10-09 before 22:51 UTC: [comment 6090204305](https://github.com/kvnloo/z0intelligence/issues/137#issuecomment-6090204305), source `686db4db2551f59806e27e2f964b74647bc3861e`, compact presentation, EXTEND, shared workstream scope, neutral start directory. The older `4ac01fc18f80be6a741be6fd583906e68160be28` is historical, not fresh corrected-state acceptance.
- New-run handoff published later on 2026-10-09: [comment 6090611759](https://github.com/kvnloo/z0intelligence/issues/137#issuecomment-6090611759) explicitly supersedes v2 **for NEW runs only**. It pins source `532a444ffaaa8de3623d4c97d77eaff8b5e34313`, registry `172e06830af7a3cea88e7390264433506fad0c77`, and evaluation PR #94 head `081dce921fc074af2dcbed1072df0d46bc80aa5a`. The immutable handoff SHA-256 is `870e89c9bb71895e0d350ae410bea369a2d674f1aabd471a8306ef3d535163a9`; use its exact dependency hashes and supported owning invocation on the authorized original host, not a derived wrapper. This is an explicitly repo-scoped attempt, not proof of unscoped owner discovery.
- The latest handoff reports 117-test archival full/compact replays but preserves unresolved approval/model-delivery qualification and explicitly leaves **fresh shared OMP acceptance open**. Those are source-reported results, not measurements reproduced by this exporter. This documentation update grants no native execution, private-handoff access, credential access, or route authorization.
- This tool reuses `scripts/import_local.py`'s SHA-256 helper and pinned-source convention. The existing `omp_qualification_paths.py`, patch, provenance, independent task oracle, and owning tests retain their owners. No Claude implementation or verification semantics are rewritten.
- z0evals freezes/export evidence; the original owning launcher remains responsible for execution and adjudication. Preserve Claude and human credits.

## Exact input gate

The original host/operator must supply these explicit **files**, not directories:

1. Existing launcher (the exact reviewed wrapper, not reconstructed from a patch).
2. Its frozen launcher base/dependency.
3. The registered path helper.
4. The selected EventLog export, including event 534 and relevant linked evidence. This tool does not search databases or infer missing events.
5. The exact native OMP witness/transcript.
6. The sealed task oracle.
7. Owning-test result receipt.
8. Run metadata in the typed projection below.

Every file needs an expected SHA-256 from the original capture/handoff. Each
source repository needs a full immutable commit and an accessible local checkout.
The public patch/provenance alone cannot replace missing `qualify.py`,
`qualify_r13.py`, frozen dependencies, witness, or oracle. No files are downloaded
implicitly. No credential/provider configuration is captured or exported.

Correctness still requires independent proof of selected repository → existing
helper → owning tests → actual OMP task. First-turn behavior, latency and tokens
remain separate measurements. Exporting a metadata value `passed` means only
**source reported passed**, never independently verified success. `fresh_run` is
an operator label, not proof a live run occurred. For that label, source checkouts
must be clean and at the declared commit; archival/fixture captures expose HEAD
and dirty state. Repository names are explicitly operator-asserted, not authenticated.

## Prepare local specification

Keep the spec and private manifest outside the repository, in an operator-owned
private directory. Install the existing repository requirements if needed. Use
Python 3.10+ and Git. This workflow adds no dependencies.

Historical archival example `capture-spec.json` (the `686db4d` pin below is not a new-run recommendation; replace every path and hash; placeholder hashes are
intentionally invalid, so this example cannot manufacture a passing capture):

```json
{
  "version": 1,
  "evidence_kind": "archival_run",
  "sources": [
    {
      "repo": "kvnloo/z0intelligence",
      "root": "/explicit/local/pinned-source",
      "commit": "686db4db2551f59806e27e2f964b74647bc3861e"
    }
  ],
  "files": {
    "launcher": {"path": "/explicit/qualify_r13.py", "sha256": "EXPECTED_SHA256"},
    "launcher_base": {"path": "/explicit/qualify-base.py", "sha256": "EXPECTED_SHA256"},
    "path_helper": {"path": "/explicit/omp_qualification_paths.py", "sha256": "EXPECTED_SHA256"},
    "eventlog": {"path": "/explicit/selected-eventlog.json", "sha256": "EXPECTED_SHA256"},
    "witness": {"path": "/explicit/native-witness.jsonl", "sha256": "EXPECTED_SHA256"},
    "task_oracle": {"path": "/explicit/sealed-oracle.py", "sha256": "EXPECTED_SHA256"},
    "owning_tests": {"path": "/explicit/owning-test-receipt.json", "sha256": "EXPECTED_SHA256"},
    "run_metadata": {"path": "/explicit/run-metadata.json", "sha256": "EXPECTED_SHA256"}
  }
}
```

Add the registry, OMP, and other actual source checkouts to `sources` when they
participated. Pin the historical run's real source, not a newer source merely
because it is now available. Hashing locally discovers a digest; it does not
independently authenticate provenance. Manifest contents and expected digests
must come from a trusted handoff. A modified manifest is not tamper-proof.

`run-metadata.json` requires every dimension; missing measurements stay explicit:

```json
{
  "correctness": "unknown",
  "first_turn": "unknown",
  "owning_tests_passed": null,
  "latency_ms": null,
  "tokens": {"input": null, "output": null, "cache_read": null, "reasoning": null}
}
```

Outcome states are `passed`, `failed`, or `unknown`. Counts are nonnegative
integers or null; latency is a finite nonnegative number or null. Preserve the
owning producer's metrics and conventions. Do not turn missing data into zero.
No token totals or composite winner scores are derived. Unknown fields, including
all arbitrary text, prompts, headers and credential-like fields, are omitted
from public output rather than relying on a fragile secret blacklist.

## One-command capture/export

From this checkout, with the output parent directory already present:

```bash
python3 scripts/omp_capture.py capture --spec /private/capture-spec.json --manifest /private/capture-manifest.json --export /private/public-summary.json
```

The private manifest holds exact local paths and hashes; raw files are **not
copied**. Both outputs are exclusively created with mode 0600. The public summary
contains only declared/observed revisions, hashes, fixed status/credit text and
typed metrics. It contains no local paths or raw witness/task/oracle contents.
Review it before any separately authorized publication. Neither command uploads
or commits anything.

## One-command local integrity replay/export

```bash
python3 scripts/omp_capture.py replay --manifest /private/capture-manifest.json --export /private/public-summary-replayed.json
```

This revalidates all original source bytes, accessible commits and observed
checkout state, then reproduces the same public summary. It is **integrity
replay**, not OMP/adjudicator replay. It requires the original files to remain
available; the public summary is not a portable execution bundle. Changes to a
captured file, missing input, invalid metadata, symlink input/output, existing
output or missing commit fail closed with exit 2. Select new output names for
each invocation. Files are bounded to 64 MiB each; control JSON to 1 MiB.

### Actual owning replay before capture

Do not guess the absent launcher's CLI or replace it with a synthetic runner.
On the original host, retain the already reviewed owning replay invocation in a
Bash array `OWNING_REPLAY` (executable plus its original arguments), then the
single compound command is:

```bash
test "${#OWNING_REPLAY[@]}" -gt 0 && "${OWNING_REPLAY[@]}" && python3 scripts/omp_capture.py capture --spec /private/capture-spec.json --manifest /private/capture-manifest.json --export /private/public-summary.json
```

The array and valid capture spec are required inputs, not supplied by this repo.
An exit-zero launcher alone still does not establish task correctness: retain
its original oracle, witness, approval and owning-test evidence. Capture only a
quiescent run; it is not a database snapshotter. This tool never runs that array
itself. For a fresh live run, the original per-run native approval and authorized
free provider route remain separate gates; never export the route handoff or
credentials. No paid inference, model download or live-user installation is
part of this workflow.

## Verification

```bash
python3 -m unittest discover -s tests -p test_omp_capture.py
python3 scripts/validate.py
PYTHONPATH=/explicit/pinned-z0intelligence/src python3 -m unittest discover -s studies/unified-memory-v0 -p test_omp_qualification_paths.py
```

The first suite uses synthetic local files strictly to test capture/export,
redaction-by-allowlist, missing inputs, digest drift, checkout drift, duplicate
JSON keys, malformed CLI input, and path/output safety. The last suite exercises
the existing production path helper; it does not run OMP. None substitutes for
the absent original real witness or a successful fresh corrected-state task.

### Recorded exporter verification provenance

The export implementation at `92b12cf1d023350e411740fdf084e0f8781a5ad3`
was checked with 38 repository tests (including 20 capture/export tests), and the
existing qualification-path suite passed 7 tests against source
`686db4db2551f59806e27e2f964b74647bc3861e`. Those seven tests remain attributed
to that historical source; they have **not** been silently repinned or rerun
against the later `532a444f` handoff. The later handoff notice changes only this
guide, not exported evidence, launcher bytes, or execution status.
