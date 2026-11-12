#!/usr/bin/env python3
"""Render the committed privacy-allowlisted canonical sustained-chat snapshot for Pages."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'studies/android-sustained-chat-100-v0/data/progress.json'
OUTPUT = ROOT / 'web/data/generated/sustained-chat-100.md'


def value(number):
    return 'Not measured' if number is None else f'{number:,.3f}'


def render(snapshot):
    if snapshot['schema_version'] != 'z0eval.sustained-chat-progress.v2':
        raise ValueError('unsupported native progress schema')
    lanes = {(lane['app'], lane['device']): lane for lane in snapshot['lanes']}
    ordered = [lanes[('chatgpt', 's25')], lanes[('deepseek', 's22')]]
    if snapshot['requested'] != 100 or any(sum(lane['states'].values()) != lane['requested'] for lane in ordered):
        raise ValueError('inconsistent study counts')
    names = {'chatgpt': 'ChatGPT / S25 Ultra', 'deepseek': 'DeepSeek / S22+'}
    lines = [f"Snapshot: **{snapshot['observed_at']}**. Run status: **{snapshot['status'].replace('_', ' ')}**.", '',
             '| App / phone | Planned | Queued | Claimed, no receipt | Sent | Unconfirmed | Failed | Rate-limited | Owner busy |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for lane in ordered:
        states = lane['states']
        cells = [names[lane['app']], str(lane['requested'])]
        cells += [str(states.get(key, 0)) for key in ('queued', 'claimed_without_receipt', 'sent', 'unconfirmed', 'failed', 'rate_limited', 'owner_busy')]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines.extend(['', '| App / phone | Identity-verified results | Matching draft PRs | Quality verifiers run | Quality passes |',
                  '|---|---:|---:|---:|---:|'])
    for lane in ordered:
        passes = lane['verified_quality_passes']
        lines.append(f"| {names[lane['app']]} | {lane['replies_captured']} | {lane['draft_prs_observed']} | "
                     f"{lane['verified_quality_evaluated']} | {passes if passes is not None else 'Not graded'} |")
    lines.extend(['', '**Unconfirmed dispatch is not the same as a failed answer.** A full, identity-verified reply can be captured '
                  'later without rewriting the original dispatch receipt. A captured reply is not independently verified answer quality.', '',
                  '| Lane / control path / result channel | Tasks with receipts | Measurement | n | p50 (ms) | p95 (ms) |',
                  '|---|---:|---|---:|---:|---:|'])
    labels = {'dispatch_wall_ms': 'Canonical dispatch wall time', 'transport_ms': 'Transport-reported time',
              'reply_observed_after_dispatch_ms': 'Dispatch end → reply observed'}
    for lane in ordered:
        for cohort in lane['cohorts']:
            label = 'fx canary' if cohort['harness'] == 'fx' else 'deterministic uiautomator2'
            channel = cohort['result_channel']
            channel_label = {
                'github_tracking_issue_comment_and_optional_draft_pr': 'GitHub connector',
                'deepseek_clipboard': 'DeepSeek Copy',
                'legacy_app_reply': 'legacy app reply',
                'unknown_result_channel': 'unknown dispatch revision',
            }[channel]
            label += ' / ' + channel_label
            for metric, title in labels.items():
                values = cohort['metrics'][metric]
                lines.append(f"| {names[lane['app']]} / {label} | {cohort['tasks']} | {title} | {values['n']} | "
                             f"{value(values['p50'])} | {value(values['p95'])} |")
    if not any(lane['cohorts'] for lane in ordered):
        lines.append('| Neither lane has a dispatch receipt yet | 0 | No timing observations | 0 | Not measured | Not measured |')
    lines.extend(['', 'The single fx canary is a separate control-path cohort. Native dispatch does not use an LLM to type prompts. '
                  'Reply-observed time includes harvest scheduling and is not model inference latency. Missing observations stay null, not zero.', ''])
    telemetry = snapshot.get('phone_telemetry', {})
    if telemetry.get('available'):
        lines.extend(['### sampled phone telemetry', '',
                      '| Phone | Samples | AP peak (°C) | Skin peak (°C) | Battery first → last (%) | Highest sampled thermal status | Min available RAM (MB) |',
                      '|---|---:|---:|---:|---|---:|---:|'])
        for dev, name in (('s25', 'S25 Ultra'), ('s22', 'S22+')):
            sample = telemetry['devices'][dev]
            numeric = sample['numeric']
            statuses = [int(key) for key in sample['thermal_status_counts']]
            highest = max(statuses) if statuses else None
            battery = f"{sample['battery_first']} → {sample['battery_last']}" if sample['battery_first'] is not None else 'Not measured'
            lines.append(f"| {name} | {sample['samples']} | {value(numeric['ap_c']['max'])} | {value(numeric['skin_c']['max'])} | "
                         f"{battery} | {highest if highest is not None else 'Not measured'} | {value(numeric['mem_avail_mb']['min'])} |")
        lines.extend(['', 'These are the existing phone-worker samples, roughly five minutes apart, plus the last available pre-run baseline. '
                      'A sampled status of 0 does not prove that no throttling happened between samples. The collector does not drive the phones to obtain telemetry.', ''])
    return '\n'.join(lines)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(json.loads(SOURCE.read_text())))
    print(f'ok: rendered canonical sustained-chat status from {SOURCE.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
