# fsm-integration-v0

Loop 3 of the z0 control plane: an integration owner for each repository.
Source: z0intelligence#188, stacked on worker-supervision#184 and work-item#183.
The Hapsland layer is in .files#34. See manifest.yaml for full pinned SHAs.

The change statechart is Branch → DraftPR → Queued → OnIntegrationBranch →
Deployed → OwnerAccepted → Merged, with explicit expiring Parked and Conflicted
side states. Its per-repository lease cannot be stolen while unexpired.
Independent review and owner acceptance are different facts. An agent using
the owner's GitHub login is not evidence of either one.

Verification reproduced in this run:

- Kernel receipt passes for I1–I5 safety/deadline-monitor claims, including an
  all-event merge-entry law. Scope: Bend's emitted book, not compiler/source
  equivalence (`source_semantics_attested=false`).
- 11/11 semantic mutants compile alone but fail the laws under --verdict.
- Python twin matches compiled Bend over all single-step constructor/flag
  combinations and seeded tapes: 625 tapes, 16,225 prefix comparisons, 20
  deadline cases and 300 lease cases. A test-only merge-bypass sabotage fails.
- 32 targeted tests pass on Python 3.13.13 with pytest 8.4.2 (Loop 3 plus Loop 2
  regressions). No full-machine-learning/repository suite claim is made.
- Hapsland producer: 17 tapes, 96 steps, 73 display edges; zero missing/extra
  Mermaid edges. All five new tapes complete in isolated headless Chromium at
  412×915, match the receipt-bound producer on every step, and produce no
  page/console errors or horizontal overflow.
- Full upstream Hapsland check:fast was attempted with fleet-build on the MBP;
  it could not start Vitest because that clean remote source shipment has no
  vitest installed. The bounded Vite build/browser proof passes; full upstream
  source qualification is not claimed.

The read-only checker observed 90 open drafts across eight repositories and
six service/build targets at 2026-10-21T07:44:00Z. Its 79 findings include both
violations and evidence gaps, which must not be added up as 79 proven failures:

- 21 drafts definitely not contained in their designated integration branch
  after 24 hours; 27 more cannot be checked because no canonical branch is
  designated in the registry.
- Five stale recorded child bases and six GitHub-CONFLICTING drafts.
- Eight repositories without a supplied integration-owner lease record.
- One NOOP source checkout behind/different from the fresh remote integration
  head. This does not establish the source revision of the installed S25 APK.
- All six runtime/build source revisions remain unattested. A checkout HEAD,
  an active systemd unit or an APK version is not exact deployed-SHA evidence.

This last point is intentional: diagnosing integration debt with stale checkout
metadata must not produce a false green deployment. Integration branch selection,
lease registration, conflict resolution and runtime telemetry are agent work.
The observed snapshot contains no eligible owner-acceptance item or explicit
parking request, so the immediate needs-Kevin batch is empty. No owner consent,
parking decision or merged result was manufactured to populate it.

Privacy: only explicitly allowlisted counts, public change ids, short SHAs,
finding codes and proof/parity/browser outcomes are imported. Private reports,
service paths, listeners, process ids, commands, personal traces and parking prose
are not published. Five new view tapes use real snapshot initial states; all
subsequent events are labelled WHAT-IF. They are not historical action logs.

Nothing was merged, deployed to a phone, or independently accepted by this
worker. The only published service artifact is the authorized Hapsland preview;
no owner service was restarted and no S25/S22 screen was touched.
