#!/usr/bin/env bash
# fleet-build on the MBP host lane, retrying while the Kueue webhook restarts.
# usage: mbp.sh <timeout_s> <command string>
cd "$(dirname "$0")/../../.."
to=$1; shift
for i in 1 2 3 4 5 6 7 8; do
  out=$(timeout $((to + 240)) fleet-build --node mbp-host --light --wait 600 --timeout "$to" \
        --src-include studies/agent-vcs-v0 -- bash -lc "$*" 2>&1)
  if grep -q "no endpoints available for service \"kueue-webhook-service\"\|failed calling webhook" <<<"$out"; then
    sleep 40; continue
  fi
  grep -v -i "podsecurity\|^fleet: \(job\|Kueue\|terminal\)\|job.batch\|kubectl\|Failed to stop\|timed out waiting" <<<"$out"
  exit 0
done
echo "mbp.sh: gave up after retries" >&2; exit 75
