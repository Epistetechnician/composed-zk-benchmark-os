# Phase 210 HSAI Gateway Adversarial Corpus Notes

Status: complete for local hermetic implementation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/210-hsai-gateway-adversarial-corpus-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Purpose

Implement the first local adversarial-corpus validation surface for the HSAI
Agent Approval Gateway. The corpus contract verifies that typed gateway cases
cover required threat labels, preserve an accepted benign control, reject unsafe
expected-accepted adversarial cases, use unique action ids, and reference a
registered model lane before local replay or report generation.

This phase does not generate corpus files. It validates in-memory typed corpus
metadata only.

## Implemented

Phase 210 adds:

- `GatewayAdversarialCorpus`
- `GatewayAdversarialCorpusIssue`
- `gateway_required_adversarial_threat_labels`
- `validate_gateway_adversarial_corpus`

The required threat-label set covers:

- prompt-injected payment requests;
- wrong-counterparty payments;
- amount-limit bypass attempts;
- source digest drift;
- stale approval replay;
- duplicate JSON key payloads;
- policy downgrade attempts;
- direct-authority requests;
- forged accepted decisions;
- missing nonclaim labels;
- missing source artifact digests;
- stale journal tips;
- signer/tool requests before accepted admission.

The validator rejects invalid corpus ids, empty corpora, duplicate case ids,
missing required threat labels, missing accepted benign controls, adversarial
cases that expect acceptance, unknown model-lane provenance, and invalid
model-lane registries.

## Tests

Focused tests cover:

- accepting a corpus with benign control plus full required threat coverage;
- rejecting invalid empty corpora without accepted benign controls;
- rejecting duplicate action ids;
- rejecting missing required threat labels;
- rejecting unsafe expected acceptance for adversarial cases;
- rejecting unknown model lanes and invalid registries.

## Claim Boundary

This is local typed metadata validation only. It is not corpus generation, not
model execution, not model download, not prompt storage, not provider
verification, not hosted-model calls, not external replay, not benchmark
evidence, not Level2+ evidence, not accepted Evidence Ledger mutation, not
score-axis population, not production readiness, not semantic correctness, not
signer/tool integration, not custody, not fully secure, and not a claim above
`Attested`.

## Validation

Run from repository root:

```sh
cargo fmt --all --check
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```
