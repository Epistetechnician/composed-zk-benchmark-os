#!/usr/bin/env bash
set -euo pipefail

# State slice: proof-carrying-nano-causal-intervention-record-v1.
# This gate validates record/proof contracts only and never runs assessment.
repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 PYTEST_ADDOPTS= PYTEST_PLUGINS= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./scripts/python -B -m pytest -q \
  tools/proof_carrying_nano_causal_intervention_record_v1/tests

printf '%s\n' 'proof_carrying_nano_causal_intervention_record_v1_contract_check: PASS'
printf '%s\n' 'claim_ceiling: LocalCausalInterventionRecordBindingOnly'
printf '%s\n' 'status: CausalInterventionRecordOnly'
printf '%s\n' 'causal_assessment: SEALED_UNTIL_INDEPENDENT_REVIEW'
printf '%s\n' 'independent_review: REQUIRED'
printf '%s\n' 'dashboard: NOT IMPLEMENTED'
printf '%s\n' 'swarm_coordination: NOT IMPLEMENTED'
printf '%s\n' 'jevlike: HypothesisOnly and unchanged'
