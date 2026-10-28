#!/usr/bin/env bash
set -euo pipefail
# State slice: neuron-gate-formal-v1. Checks harness decision-rule logic only.
root="$(cd "$(dirname "$0")/../formal/neuron-gate-v1" && pwd)"
cd "$root"
lake env lean NeuronGate/Gate.lean
printf 'sha256: %s\n' "$(shasum -a 256 NeuronGate/Gate.lean | awk '{print $1}')"
echo 'neuron_gate_check: PASS'; echo 'claim_ceiling: LocalMachineCheckedFormalContractOnly'
