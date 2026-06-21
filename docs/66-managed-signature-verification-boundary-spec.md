# Managed Signature Verification Boundary Spec

## Status And Claim Boundary

This was the docs-first boundary for the next managed-attestation phase after
the pure-data harness and Phase 4 anchor registry. The original docs-first slice
authorized no Rust implementation. It defined the conditions a later
implementation had to satisfy before this repository left pure-data and verified
managed-service signatures, JWKS/JWT material, or local quote evidence.

Follow-up status: `docs/77-managed-jwt-signature-verification-notes.md`
implements the first bounded subset of this boundary: offline ES256 managed-JWT
signature verification against caller-provided local public keys. That follow-up
does not authorize JWKS fetching, live managed-service calls, local DCAP quote
verification, PCCS or collateral handling, TLS channel binding, backend
execution, benchmark outputs, or claims above `Attested`.

The strongest possible output remains `Attested`, never `Proven`. Signature or
quote verification can strengthen the provenance of an anchor-validity envelope,
but it does not prove global software-agent uniqueness, competence, safety,
semantic correctness, benchmark performance, or official benchmark evidence.

## Source Attribution

This spec cites upstream work as source material. It does not copy source code,
vendor repositories, execute external tools, or treat upstream benchmark numbers
as local evidence.

- [zkCollective/zk-Harness](https://github.com/zkCollective/zk-Harness) remains
  the relevant benchmark-harness source for future ZK backend comparison. The
  current repo still uses only inert dry-run mapping; no live zk-Harness
  execution is authorized here.
- [Consensys/gnark](https://github.com/Consensys/gnark) and its
  [std/recursion package](https://pkg.go.dev/github.com/consensys/gnark/std/recursion)
  remain the relevant recursion-envelope source. Recursion proof remains
  separate from semantic proof.
- [zkonduit/zkml-framework-benchmarks](https://github.com/zkonduit/zkml-framework-benchmarks)
  remains the relevant narrow zkML workload-metrics source. zkML workload
  benchmarks must not become a broad benchmark scope or a semantic oracle.
- [Verified-zkEVM/clean](https://github.com/Verified-zkEVM/clean),
  [GaloisInc/zk-lean](https://github.com/GaloisInc/zk-lean), and
  [formal-land/garden](https://github.com/formal-land/garden) remain formal-lane
  references only. Machine-checked proof for a scoped property is not proof of
  the full benchmark OS.
- [Dstack-TEE/dstack](https://github.com/Dstack-TEE/dstack),
  [Phala-Network/dstack-cloud](https://github.com/Phala-Network/dstack-cloud),
  and [Phala-Network/trust-center](https://github.com/Phala-Network/trust-center)
  remain the relevant Phala/dstack managed-verifier and captured-artifact source
  family. The current repository records managed-verifier local regression
  evidence only.
- [Microsoft Azure Attestation](https://learn.microsoft.com/en-us/azure/attestation/basic-concepts)
  is the relevant Azure managed-JWT verifier reference.
- [Intel Trust Authority attestation tokens](https://docs.trustauthority.intel.com/main/articles/articles/ita/concept-attestation-tokens.html)
  and the [Intel Trust Authority EAT profile](https://portal.trustauthority.intel.com/eat_profile.html)
  are the relevant Intel managed-JWT verifier references.
- [flashbots/attested-tls](https://github.com/flashbots/attested-tls) is a
  relevant transport-bound attestation reference. It is reference-only here; no
  TLS, DCAP, PCCS, or transport-channel implementation is authorized.

## Purpose

Turn the deliberately deferred "managed service signed this token honestly"
assumption into a future explicit backend boundary behind the existing
`AttestationVerifier` trait.

The future implementation must verify a provider token or quote before applying
the existing local field checks:

1. signature or quote authenticity;
2. issuer, algorithm, key id, and trust-root constraints;
3. freshness and replay constraints;
4. nonce and report-data binding to `agent_pubkey`, `nonce`, and `case_hash`;
5. expected runtime/container/TEE measurement claims;
6. explicit trust-root disclosure in the emitted `ClaimEnvelope`;
7. output maturity capped at `Attested`.

## Candidate Backend Shapes

### Managed JWT Backend

Azure Attestation and Intel Trust Authority both fit this shape. A future backend
may add a verifier that accepts a signed attestation JWT, validates the signature
against an approved key source, maps claims into the local `Token` /
`VerifiedAttestation` shape, then runs the existing nonce, report-data,
measurement, anchor-id, and freshness checks.

Required negative tests:

- invalid signature;
- unsupported algorithm;
- unknown key id;
- wrong issuer;
- stale `nbf` / `exp`;
- missing nonce or report-data claim;
- wrong measurement claim;
- accepted token mapped to the wrong anchor id.

### Local Quote Or Captured Evidence Backend

Phala/dstack and lower-level TDX/DCAP references fit this shape. A future backend
may verify quote evidence, event logs, compose/runtime measurements, and report
data locally only if a later spec explicitly authorizes quote verification,
collateral handling, and any required external trust-root material.

Required negative tests:

- malformed quote or evidence bundle;
- invalid report-data binding;
- mismatched compose/runtime measurement;
- stale evidence;
- missing Docker image digest or runtime identity;
- trust-root disclosure missing a relied-on managed verifier or hardware root.

### Transport-Bound Attestation Backend

The flashbots attested-TLS family is relevant to a later transport-binding
question: whether the channel carrying an `AgentCase` can be cryptographically
bound to the attestation evidence. That is not required for the first
managed-signature backend. If used later, it must be specified as a separate
transport trust boundary, not folded into token verification by implication.

## State Slice For A Future Implementation

A future implementation phase must name one backend and no more than one
verification mode. The minimal Rust state slice would be a new backend crate or
an additive backend module behind `hsai-attestation`, focused tests, fixtures,
and phase notes. It must not modify `zkbench-core`, the accepted Evidence Ledger,
benchmark packs, live external runner policy, or Phase 4 registry semantics.

## Forbidden In This Docs-First Phase

- Rust implementation code.
- Network access in tests or examples.
- JWKS fetch code.
- JWT signature verification code.
- Intel DCAP quote verification code.
- PCCS or collateral fetch/caching code.
- TLS channel or attested-TLS implementation.
- External repo clones or vendored source.
- Secrets, API keys, cookies, bearer tokens, or private keys.
- Backend execution.
- Benchmark outputs.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For The Future Code Phase

- The future spec names the exact provider and verification mode.
- Source repo/document URLs are cited before implementation.
- Fixture inputs are non-secret and committed only when license/provenance allows.
- All relied-on trust roots are visible in output envelopes.
- Rejections leave no Phase 4 registry state mutation.
- The verifier never emits `Maturity::Proven`.
- Tests include adversarial token, quote, mapping, freshness, and trust-root
  disclosure failures.
- Documentation states that managed-signature verification is still not proof,
  not benchmark evidence, not global software-agent uniqueness, and not local
  semantic correctness.
