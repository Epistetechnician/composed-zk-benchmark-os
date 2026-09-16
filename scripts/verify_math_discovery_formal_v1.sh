#!/usr/bin/env bash
set -euo pipefail

# State slice: proof-carrying-symbolic-transfer-formal-v1
# This verifies the Lean M0 contract only. It does not execute a model,
# provider, corpus, candidate, or ZK prover.

formal_root="$(cd "$(dirname "$0")/../formal/math-discovery-v1" && pwd)"
expected_source_digest="a66dbae1b0c8eda1ceffbbd4991cd4f86728ecd3fa8d6791358f6078a29711ac"
source_digest="$(shasum -a 256 "$formal_root/MathDiscovery/TransferContract.lean" | awk '{print $1}')"
if [ "$source_digest" != "$expected_source_digest" ]; then
  printf '%s\n' 'formal_contract_check: FAIL_CLOSED' >&2
  printf '%s\n' 'reason: formal source digest mismatch' >&2
  exit 3
fi
if ! command -v lake >/dev/null 2>&1; then
  printf '%s\n' 'formal_contract_check: UNAVAILABLE' >&2
  printf '%s\n' 'reason: pinned Lean lake executable is not installed' >&2
  exit 2
fi
cd "$formal_root"
lake env lean MathDiscovery/TransferContract.lean
printf '%s\n' 'formal_contract_check: PASS'
printf 'formal_source_digest: %s\n' "$source_digest"
printf '%s\n' 'claim_ceiling: LocalMachineCheckedFormalContractOnly'
printf '%s\n' 'local_continuation: AUTHORIZED'
printf '%s\n' 'independent_review_for_escalation: REQUIRED'
