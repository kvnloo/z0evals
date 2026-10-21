#!/bin/bash
# session s3 (declared in protocol.md before it ran): new arms fx-cli, hermes-speed, hermes-speed-guided,
# hermes-default-ft, interleaved with anchors pi-base, hermes-base, fx-base, omp-base; warm Hermes over ACP;
# tasks t01-t08 (session s3) and the six harder tasks h01-h06 (session s3h).
cd $HOME/.cache/harness-speed-v1
mkdir -p data/s3
L=pi-base,hermes-base,fx-base,omp-base,fx-cli,hermes-speed,hermes-speed-guided,hermes-default-ft
W=hermes-speed,fx-base,pi-base,omp-base
T=pi-base,hermes-base,fx-base,fx-cli,hermes-speed,hermes-speed-guided
echo "start $(date -Is) $(uptime)" > data/s3/host.txt
python3 harness/bench.py latency --arms $L --blocks 32 --warmup-blocks 1 --seed 20261024 --out data/s3 --session s3 > data/s3/latency.log 2>&1
echo "latency done $(date -Is) $(uptime)" >> data/s3/host.txt
python3 harness/warm.py --arms $W --rounds 30 --warmup 1 --seed 20261025 --out data/s3 --session s3 > data/s3/warm.log 2>&1
echo "warm done $(date -Is) $(uptime)" >> data/s3/host.txt
python3 harness/bench.py tasks --arms $T --reps 2 --tasks t01-paginate,t02-slugify,t03-csvsum,t04-cliflag,t05-lru,t06-duration,t07-rename,t08-merge --seed 20261024 --out data/s3 --session s3 > data/s3/tasks.log 2>&1
echo "tasks done $(date -Is) $(uptime)" >> data/s3/host.txt
python3 harness/bench.py tasks --arms $T --reps 2 --tasks h01-reserve,h02-config,h03-bus,h04-money,h05-calc,h06-wordstats --seed 20261024 --out data/s3 --session s3h > data/s3/tasks-hard.log 2>&1
echo "hard tasks done $(date -Is) $(uptime)" >> data/s3/host.txt
