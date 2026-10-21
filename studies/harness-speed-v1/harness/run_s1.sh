#!/bin/bash
# session s1: all eight arms
cd $HOME/.cache/harness-speed-v1
A=hermes-base,hermes-default,fx-base,omp-base,omp-default,pi-base,pi-solpi,pi-rlm
echo "start $(date -Is) $(uptime)" > data/s1/host.txt
python3 harness/bench.py latency --arms $A --blocks 32 --warmup-blocks 1 --out data/s1 --session s1 > data/s1/latency.log 2>&1
echo "latency done $(date -Is) $(uptime)" >> data/s1/host.txt
python3 harness/warm.py --arms fx-base,omp-base,omp-default,pi-base,pi-solpi,pi-rlm --rounds 30 --warmup 1 --out data/s1 --session s1 > data/s1/warm.log 2>&1
echo "warm done $(date -Is) $(uptime)" >> data/s1/host.txt
python3 harness/bench.py tasks --arms $A --reps 2 --out data/s1 --session s1 > data/s1/tasks.log 2>&1
echo "tasks done $(date -Is) $(uptime)" >> data/s1/host.txt
