#!/bin/bash
# session s3 tasks, restarted after the aborted first attempt (see protocol "s3 amendment"): same arms, seed,
# tasks and reps as run_s3.sh; latency and warm rows from run_s3.sh are kept.
cd $HOME/.cache/harness-speed-v1
T=pi-base,hermes-base,fx-base,fx-cli,hermes-speed,hermes-speed-guided
echo "tasks restart $(date -Is) $(uptime)" >> data/s3/host.txt
python3 harness/bench.py tasks --arms $T --reps 2 --tasks t01-paginate,t02-slugify,t03-csvsum,t04-cliflag,t05-lru,t06-duration,t07-rename,t08-merge --seed 20261024 --out data/s3 --session s3 > data/s3/tasks.log 2>&1
echo "tasks done $(date -Is) $(uptime)" >> data/s3/host.txt
python3 harness/bench.py tasks --arms $T --reps 2 --tasks h01-reserve,h02-config,h03-bus,h04-money,h05-calc,h06-wordstats --seed 20261024 --out data/s3 --session s3h > data/s3/tasks-hard.log 2>&1
echo "hard tasks done $(date -Is) $(uptime)" >> data/s3/host.txt
