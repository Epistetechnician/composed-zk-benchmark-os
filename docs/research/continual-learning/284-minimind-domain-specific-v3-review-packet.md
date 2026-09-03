# MiniMind domain-specific continual-learning V3 review packet

State slice: `continual-learning-minimind-domain-specific-v3`.

Review status: `PENDING_INDEPENDENT_REVIEW`.

This packet is a read-only review boundary. It is not an execution receipt and
does not authorize model loading, training, inference, provider activity, or
assessment.

## Frozen input set

The reviewer must recompute the SHA-256 of exactly these seven files after
freeze. Any byte change makes the review stale and requires a new V3 packet.

1. `docs/research/continual-learning/283-minimind-domain-specific-v3-protocol.md`
2. `docs/research/continual-learning/284-minimind-domain-specific-v3-review-packet.md`
3. `experiments/continual_learning/minimind_domain_specific_v3.py`
4. `experiments/continual_learning/validate_minimind_domain_specific_v3.py`
5. `experiments/continual_learning/tests/test_minimind_domain_specific_v3.py`
6. `docs/research/continual-learning/285-minimind-domain-specific-v3-implementation-manifest.json`
7. `AGENTS.md`

## Required independent checks

- V2 remains terminal `REJECT`; V3 imports no V1/V2 scientific artifact.
- MiniMind source is the exact clean external checkout, commit, remote,
  license, required-file roster, byte lengths, and digests.
- The synthetic runner and independent validator reproduce the exact 108
  aggregate trial identities and arithmetic values.
- Tune selection is completed before any assessment trial is computed; the
  phase order and lock are explicit and fail closed.
- Synthetic validator independently enforces external custody, owner-only
  `0700`, exact three-file output set, no symlinks, aggregate-only schema, and
  all result/contract digests.
- Fresh corpus identity, external `0700` custody, exact nine-file roster,
  document and author disjointness, record schema, file bytes, and V1/V2
  prior-root exclusion are recomputed from current bytes.
- Model-contract validation requires an exact top-level schema, exact typed
  aggregate rows, exact non-empty Boolean hard-guard sets, receipt file digest,
  source/corpus bindings, exact phase roster, and a tune-only lock.
- The external trust bundle fingerprint is fixed; the registry snapshot is
  signed by its pinned review root; the reviewer certificate is root-signed;
  the receipt signer key is resolved from the certificate; reviewer and
  operator principals/keys are distinct.
- The operator binding is signed by the separate execution root and binds the
  exact packet, V3 protocol, runner audience, and one-time nonce.
- Receipt validation is exact JSON schema, packet-bound, complete frozen-file
  digest-bound, source/corpus-bound, Ed25519-verified, and performed before
  MiniMind import.
- Model output retains only aggregate `contract.json`; no raw records, tokens,
  checkpoints, weights, gradients, or logs are allowed below the result root.
- No provider, network, benchmark, production, publication, or Evidence Ledger
  action is implied by this packet.

## External bindings

The independent receipt must additionally bind the exact current SHA-256 of the
fresh V3 source manifest, fresh V3 corpus manifest, fixed external trust bundle,
and fixed external reviewer registry. The corpus manifest is:

`/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-corpus-20260902/corpus-manifest.json`

The trust bundle is:

`/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-trust-bundle-20260902.json`

The reviewer registry path is fixed in the V3 implementation and cannot be
selected by the receipt. The receipt must set disposition exactly to
`ACCEPTED_FOR_MODEL_EXECUTION`; no prose, silence, or synthetic candidate
status substitutes for it.

## Claim ceiling

Before a valid receipt, the only allowed claim is
`LocalDevelopmentMiniMindDomainSequenceSyntheticOnly`. After a valid receipt,
the maximum model claim is
`LocalDevelopmentMiniMindDomainSequenceQualificationV3`, subject to the
independent final contract validator. This packet does not establish general
continual-learning superiority, benchmark evidence, production readiness, or
provider evidence.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v3`.
