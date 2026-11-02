#!/bin/bash
BIN=/home/shaanp/loops/composed-zk-benchmark-os/target/release/examples/operator_soak_campaign
OUT=/tmp/opencode/rsi/sweep.jsonl
: > "$OUT"
export ZKBENCH_SOAK_ACK="I acknowledge this soak campaign produces local Level0DesignNote telemetry only."
export ZKBENCH_SOAK_APPROVED_BY=rsi-agent
export ZKBENCH_SOAK_APPROVAL_STATEMENT="local RSI soak measurement"
export ZKBENCH_SOAK_PROFILE=smoke
for fam in baseline_fsm branching_fsm bounded_counter_loop nested_loop guard_heavy_machine recursive_envelope memory_heavy_state_machine public_private_boundary_stress zkml_control_flow_mixed; do
  for start in $(seq 0 8 4088); do
    end=$((start+8))
    id="rsi-${fam}-${start}"
    root=/tmp/opencode/rsi/art/$id
    res=$(ZKBENCH_SOAK_CAMPAIGN_ID=$id ZKBENCH_SOAK_ARTIFACT_ROOT=$root \
      ZKBENCH_SOAK_FAMILIES=$fam ZKBENCH_SOAK_SEED_START=$start ZKBENCH_SOAK_SEED_END=$end \
      ZKBENCH_SOAK_SHARD_COUNT=8 timeout 60 $BIN 2>/tmp/opencode/rsi/err.txt)
    rc=$?
    rm -rf "$root"
    if [ $rc -ne 0 ]; then
      echo "{\"family\":\"$fam\",\"start\":$start,\"rc\":$rc,\"err\":\"$(tr -d '\n"' < /tmp/opencode/rsi/err.txt | head -c 300)\"}" >> "$OUT"
    else
      echo "$res" | tr -d '\n' | sed "s/^/{\"family\":\"$fam\",\"start\":$start,\"rc\":0,\"summary\":/; s/\$/}/" >> "$OUT"
      echo >> "$OUT"
    fi
  done
done
echo DONE >> /tmp/opencode/rsi/sweep.status
