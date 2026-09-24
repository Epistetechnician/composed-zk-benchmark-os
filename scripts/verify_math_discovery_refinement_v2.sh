#!/usr/bin/env bash
set -euo pipefail

# State slice: proof-carrying-symbolic-transfer-refinement-v2
# Local-only: no model, provider, corpus, network, or spend.

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
fixture="$repo_root/tools/proof_carrying_symbolic_transfer_refinement_v2/fixtures.json"
output_dir="$(mktemp -d "${TMPDIR:-/tmp}/math-discovery-refinement-v2.XXXXXX")"
trap 'rm -rf "$output_dir"' EXIT

if ! command -v lake >/dev/null 2>&1; then
  printf '%s\n' 'refinement_protocol: UNAVAILABLE' >&2
  printf '%s\n' 'reason: pinned Lean lake executable is not installed' >&2
  exit 2
fi

PYTHONPATH="$repo_root" python3 -m tools.proof_carrying_symbolic_transfer_refinement_v2.evaluator \
  "$fixture" "$output_dir"
