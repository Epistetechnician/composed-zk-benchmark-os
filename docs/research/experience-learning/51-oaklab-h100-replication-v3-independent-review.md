# Oak Lab H100 replication V3 independent review

State slice: `oaklab-experience-learning-h100-replication-v3`.

Review decision: `REJECT`.

Reviewer: `codex-independent-reviewer-oaklab-h100-replication-v3`.

Reviewed at UTC: `2026-08-31T20:03:17Z`.

## Scope and byte freeze

This was a static review of exactly the eight files named by the frozen
review packet. No protocol, compiler, model, provider, dataset, H100, or
effects execution was performed. The sole permitted test command was:

`pnpm exec pytest experiments/experience_learning/tests/test_oaklab_h100_v3_protocol.py`

Result: 5 passed. The test suite does not cover cryptographic Ed25519
verification, tune-lock receipt validation, full result-file content
validation, joule computation or resource margins, or execution-order
enforcement.

The reviewed file SHA-256 values are recorded in the canonical JSON receipt
alongside the protocol, packet, and compiled-artifact hashes. The compiled
artifact's internal self-digest is `6af9517451e3b0e2f90ed7fc10ec9ed7e9e5fb1ff10bd72478a708520fa61c87`;
its byte hash is `f18b2921a7a6860fa05f9782ff4119455e7b22409026c8adf1ff9dc0f09a2f92`.
The receipt self-digest is
`75998664d1b6e91ce155196efe179c3f5e34007a08efc5572190bbe1578434e8`.

## Findings

1. `paired_estimand_and_carryover_controls`: `true`. The protocol fixes the
   episode pair, initial checkpoint, identical ordered stream, arm-order
   randomization, washout, post-washout formula, episode reset, and
   previous-block-only controller inputs. The compiled artifact carries the
   paired estimand and the validator checks its exact structure. This is the
   only finding accepted here; no runtime implementation was executed.

2. `canonical_campaign_manifest`: `false`. The protocol and compiled metadata
   state canonical UTF-8 JSON and a self-digest, and the validator checks the
   parsed dictionary's fields and digest. It never validates the original
   manifest bytes, canonical key ordering, compact separators, UTF-8 encoding,
   or trailing newline. A noncanonical byte representation can therefore pass
   `validate_campaign_manifest`.

3. `signed_provider_cost_stop_receipts`: `false`. The validator checks only
   Ed25519 key/signature string lengths and a SHA-256 self-digest; it never
   verifies the Ed25519 signature. It also has no validators for the separate
   `provider/allocation.json`, `provider/cost.json`, and `provider/stop.json`
   allowlisted files. Random signature bytes and malformed provider records can
   pass the implemented checks.

4. `closed_world_digest_content_result_root`: `false`. The result-root
   validator enforces the path set, symlink rejection, file presence, a hash of
   current file bytes, and the campaign manifest. It does not parse or validate
   the allowlisted compiled, lock, provider, joule, aggregate, or independent
   validation files, nor compare their contents to the manifest's individual
   bindings. Malformed JSON and digest-consistent substitutions therefore
   remain fail-open despite the protocol's content contract.

5. `fit_tune_prediction_lock_receipts`: `false`. The compiled artifact declares
   required lock fields and an independent receipt, but the validator defines
   no tune-lock or lock-receipt validator and `validate_result_root` never
   loads either file. Missing fields, altered predictions, and unvalidated
   locks can pass the available result-root checks.

6. `resource_energy_formulas_and_margins`: `false`. The compiler stores the
   resource metrics, 5% margin, sampling conditions, formula, and denominator
   as metadata. The executable validator only checks that the raw CSV has at
   least two finite nonnegative samples with strictly increasing timestamps;
   it neither integrates joules, validates successfully learned-event counts,
   checks operation/update/storage/latency metrics, nor applies any
   non-inferiority margin. The formula string is not an executable gate.

7. `execution_boundary_and_lane_isolation`: `false`. The protocol and compiled
   artifact declare effects and ordering booleans, but validation checks only
   `effects_run == false` in the compiled artifact. It does not enforce
   implementation-before-review, synthetic-candidate-before-real execution,
   preflight-before-provider, independent lock acceptance, offline/model lane
   separation, or the one-bounded-job rule. These are declarative controls with
   fail-open paths.

## Closure

Because six of seven findings are false, this receipt is `REJECT`. It authorizes
no implementation, custody, provider access, spend, H100 job, data/effects
execution, tune lock, assessment, or publication. V3 remains closed until a
new frozen packet fixes the validator enforcement gaps and receives a fresh
independent review.

`effects_run`: `false`.
