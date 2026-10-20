# Owner attestation for the V49 campaign (NOT an independent review)

Manifest sha256: `accf60050bc7b1c9b45af0cf4a251620ebcf3fdaf7d598bbd9e973285b53fec1`.

On 2026-10-20 the owner instructed, in chat, that the independent signed decision be bypassed to demonstrate the pipeline end to end. This file records that instruction. It is an owner waiver and attestation only.

- It is not an independent review: the owner and the operator are not independent of the work, and no Ed25519 signature or reviewer identity exists.
- It does not change the claim ceiling: `LocalDevelopmentUnreviewed`.
- It does not create accepted evidence, Level2+, independent verification, proof, SOTA, benchmark, production, or introspection claims, and does not mutate any Evidence Ledger.
- `review-decision-template.json` stays unsigned. Any independent decision must come from a genuinely independent reviewer.

## Update 2026-10-20: self-attestation ceiling
AGENTS.md slice `v49-owner-self-attestation-v1` now permits recording this campaign at claim ceiling `OwnerSelfAttestedLocalDevelopment`. The label is mandatory and means: the owner reviewed the packet and accepts it for their own use. It is not independent review, not accepted evidence, and carries no signature. Cite it only with the packet caveats.
