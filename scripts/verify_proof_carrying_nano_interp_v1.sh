#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root/formal/proof-carrying-nano-interp-v1"
lake env lean NanoInterp/FeatureClaim.lean
printf '%s\n' 'proof_carrying_nano_interp_v1_formal_check: PASS'
printf '%s\n' 'claim_ceiling: LocalSyntheticToyHostFeatureLookupHypothesisRankingAndToyInterventionOnly'
printf '%s\n' 'independent_review: REQUIRED'
