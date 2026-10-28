#!/usr/bin/env bash
set -euo pipefail
# State slice: neuron-gate-formal-v1. Checks harness decision-rule logic, selection/quota
# arithmetic, permutation-p rank uniformity, and the exact V61-local verdict certificate.
root="$(cd "$(dirname "$0")/../formal/neuron-gate-v1" && pwd)"
repo="$(cd "$root/../.." && pwd)"
python3 "$repo/scripts/gen_neuron_certificate_v61.py" >/dev/null
git -C "$repo" diff --exit-code -- formal/neuron-gate-v1/NeuronGate/CertV61.lean >/dev/null \
  || { echo 'certificate differs from committed (regenerated from logs)'; exit 1; }
cd "$root"
lake build
for f in Gate Pipeline CertV61; do printf 'sha256 %s: %s\n' "$f" "$(shasum -a 256 NeuronGate/$f.lean | awk '{print $1}')"; done
rm -rf .lake
echo 'neuron_gate_check: PASS'; echo 'claim_ceiling: LocalMachineCheckedFormalContractOnly'
