W=/mnt/zer0models/z0-wt/salvage/z0evals-optchat-post
N=1730847
cd $W
for i in 1 2 3; do
  timeout 1500 codex exec --model gpt-6.1-sol -c model_reasoning_effort=high --sandbox workspace-write --skip-git-repo-check --cd $W --output-last-message $W/.review/logs/codex-r2corr-final-$N.txt - < $W/.review/logs/spec-r2corr-$N.txt > $W/.review/logs/codex-r2corr-$N.log 2>&1
  rc=$?
  if grep -qi "at capacity" $W/.review/logs/codex-r2corr-$N.log && [ $rc -ne 0 ]; then sleep 60; continue; fi
  break
done
echo "EXIT $rc attempt $i" >> $W/.review/logs/codex-r2corr-$N.log
