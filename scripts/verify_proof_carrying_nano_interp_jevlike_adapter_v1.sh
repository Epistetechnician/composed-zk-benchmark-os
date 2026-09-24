#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 PYTEST_ADDOPTS= PYTEST_PLUGINS= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./scripts/python -B -m pytest -q tools/proof_carrying_nano_interp_jevlike_adapter_v1/tests

printf '%s\n' 'proof_carrying_nano_interp_jevlike_adapter_v1_contract_check: PASS'
printf '%s\n' 'claim_ceiling: LocalExternalJevlikeQuantizedHypothesisRankingOnly'
printf '%s\n' 'external_model_execution: NOT RUN'
printf '%s\n' 'independent_review: REQUIRED'
