#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 PYTEST_ADDOPTS= PYTEST_PLUGINS= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./scripts/python -B -m pytest -q \
  tools/proof_carrying_nano_host_activation_boundary_v1/tests

printf '%s\n' 'proof_carrying_nano_host_activation_boundary_v1_contract_check: PASS'
printf '%s\n' 'claim_ceiling: LocalCachedSmallTransformerActivationCaptureOnly'
printf '%s\n' 'causal_intervention_records: SEALED_UNTIL_INDEPENDENT_REVIEW'
printf '%s\n' 'dashboard: NOT IMPLEMENTED'
printf '%s\n' 'swarm_coordination: NOT IMPLEMENTED'
