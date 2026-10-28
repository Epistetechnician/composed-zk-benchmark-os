#!/bin/zsh
# Sequential arms; each writes out_<arm>.json. No retries.
C=/Users/shaanp/hsi-custody/v62
R=/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os
mkdir -p $C/results
for arm in mps_f32 mps_bf16 mps_fp16 cpu_f32; do
  /usr/bin/caffeinate -i ~/.pyenv/shims/python3 $R/tools/astral-neuron-level-causal-lane-v62/run_v62.py $arm \
    --v50-packet $R/docs/research/astral-self-modeling/v50-run/packet.json --model-dir $C/model \
    --corpus $C/corpus.json --out $C/results/out_$arm.json \
    --expected-corpus-digest 59c514f0c5a89a1cf046f94a64e4abbe1254158bf3e992f37fbcf5e754a33221 \
    --code-commit $(git -C $R rev-parse --short HEAD) \
    --v54-out $R/docs/research/astral-self-modeling/v54-run/results/out_v54.json > $C/results/log_$arm.txt 2>&1
  echo "$arm exit $?" >> $C/results/status.txt
done
