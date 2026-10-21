#!/bin/bash
# session s2: C5 (model only, on omp-base) + exploratory X1 (pi --offline) and X2 (hermes no-tool)
cd $HOME/.cache/harness-speed-v1
mkdir -p data/s2
A=omp-base,omp-base@claude-opus-5-5,pi-base,pi-base-offline,hermes-base,hermes-base-clarify
echo "start $(date -Is) $(uptime)" > data/s2/host.txt
python3 harness/bench.py latency --arms $A --blocks 32 --warmup-blocks 1 --seed 20261023 --out data/s2 --session s2 > data/s2/latency.log 2>&1
echo "latency done $(date -Is) $(uptime)" >> data/s2/host.txt
python3 harness/bench.py tasks --arms omp-base,omp-base@claude-opus-5-5 --reps 1 --seed 20261023 --out data/s2 --session s2 > data/s2/tasks.log 2>&1
echo "tasks done $(date -Is) $(uptime)" >> data/s2/host.txt
