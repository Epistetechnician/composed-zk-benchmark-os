# Pure-Data Adversarial Harness - Phase 2 Spec

## Status And Claim Boundary

This is the implementation spec for Phase 2 of the managed-attestation track. It
does not integrate Phala, Azure, Intel Trust Authority, Apple, Darkbloom, zkTLS,
or any live network service. It is a pure Rust end-to-end adversarial harness over
the shipped HSAI crates.

The purpose is to verify that the local stack behaves correctly before the first
real attestation backend is added. A passing harness is not external evidence, not
a proof, and not a backend verification result. It is a local regression surface
for HSAI's claim-boundary and admission invariants.

## Build Target

Build exactly one new harness crate:

```text
crates/hsai-e2e-harness
```

The crate is test-oriented. It may expose small deterministic fixture helpers, but
it must not add protocol primitives. It path-depends on the shipped crates:

- `hsai-claim-envelope`
- `hsai-agent-case`
- `hsai-distinct-agent`
- `hsai-attestation`
- `hsai-economy`
- `hsai-membrane`
- `hsai-economy-sim` only for funding-rule invariant checks

No existing crate is modified.

## System Under Test

The harness composes the current local stack:

```text
AgentCase
  -> DistinctAgentLane
  -> AttestationLane<ManagedTokenVerifier>
  -> conjoin
  -> AcceptancePolicy(require_closed, min Attested)
  -> IdentityRegistry
  -> Economy
  -> Membrane
```

The attestation lane uses only `ManagedTokenVerifier`. This phase does not verify
managed-service signatures. It proves that once a verifier accepts or rejects
token fields, every downstream gate treats the result honestly.

## Fixture Model

Use one deterministic subject and one deterministic hardware anchor:

```text
subject = SubjectId("agent-e2e")
anchor  = Anchor::HardwareAttested { vendor: "harness", device: "dev-0" }
```

Use a single `AgentCase` with:

- `observed_at = 150`
- `expected = Verdict::Accept`
- `target_guarantees = { distinctness(subject) }`
- `excluded = {}`

Use a good token:

```text
anchor_id    = anchor.anchor_id()
nonce        = 7
measurements = [1, 2, 3, 4]
not_before   = 100
not_after    = 300
```

Use a work envelope that guarantees `PolicyCompliance(subject)` at `Local`, with
closed assumptions, matching the existing `hsai-economy` test pattern.

Use a demurrage economy for membrane/economy checks:

```text
FloorPlusDemandPeg { floor: 100, demand_multiplier: 0 }
DemurragePolicy { rate: 1 }
```

## Acceptance Policies

Distinctness admission policy:

```text
require        = { distinctness(subject) }
min_maturity   = Attested
forbid_roots   = {}
require_closed = true
at             = 150
```

Work admission policy:

```text
require        = { PolicyCompliance(subject) }
min_maturity   = Local
forbid_roots   = {}
require_closed = true
at             = 150
```

Forbidden-root policy for adversarial checks:

```text
require        = { distinctness(subject) }
min_maturity   = Attested
forbid_roots   = { HardwareVendor }
require_closed = true
at             = 150
```

## Unit Vectors

### EH-1 - Valid Attestation Closes Distinctness

Evaluate `DistinctAgentLane`, evaluate `AttestationLane<ManagedTokenVerifier>`
with the good token, conjoin them, and assert:

- assumptions are empty;
- guarantees include `Distinctness(subject)`;
- guarantees include `anchor.validity_assumption(subject)`;
- maturity is `Attested`;
- `admits(distinctness_policy, joined)` is `Ok`;
- `IdentityRegistry::register(subject, joined, policy)` is `Ok`.

### EH-2 - Nonce Mismatch Keeps Distinctness Inadmissible

Use `expected_nonce != token.nonce`. Assert:

- attestation envelope is `Stub`;
- conjoined envelope still has the anchor-validity assumption open;
- `admits(require_closed)` rejects with open assumption;
- registry registration fails.

### EH-3 - Measurement Mismatch Keeps Distinctness Inadmissible

Use wrong expected measurements. Assert the same rejection shape as EH-2.

### EH-4 - Expired Attestation Keeps Distinctness Inadmissible

Set `observed_at > token.not_after`. Assert the same rejection shape as EH-2.

### EH-5 - Anchor Reuse Is Rejected

Register the first subject with a valid closed envelope. Attempt to register a
second subject using the same hardware anchor trust root. Assert:

```text
Err(RegisterError::SybilAnchorReuse(root))
```

### EH-6 - Unregistered Worker Cannot Earn

Create an economy with an empty registry and attempt `earn` with a valid closed
work envelope. Assert:

```text
Err(EconomyError::Unregistered)
```

### EH-7 - Registered Worker Can Earn

Register the subject with EH-1's closed distinctness envelope. Call
`economy.earn` with the work envelope and policy. Assert:

- returned credits are positive;
- subject balance increases;
- total credits increases by the reward amount.

### EH-8 - Frozen Worker Cannot Cross Membrane

Register and fund/earn a positive balance. Freeze the subject in `Economy`. Call
`Membrane::convert_out` and `Membrane::convert_in`. Assert both fail and both
economy and membrane state remain unchanged.

### EH-9 - Forbidden Hardware Trust Root Is Rejected

Use the valid closed distinctness envelope but a policy forbidding
`TrustRootClass::HardwareVendor`. Assert `admits` rejects for forbidden root and
the registry does not admit the identity.

### EH-10 - Funding-Rule Invariants Still Hold

Run `hsai-economy-sim::sweep` over a tiny deterministic config with all three
funding rules. Assert every `terminal_gini <= 1000` and `run(config) ==
run_with_funding(config, FundingRule::Even)`.

## Property Tests

### EHP-1 - Single Fault Prevents Registration

Randomize one fault at a time:

- nonce mismatch;
- measurement mismatch;
- expired token;
- wrong anchor id.

For every fault, assert the final conjoined envelope is not admitted under the
closed distinctness policy.

### EHP-2 - Accepted Path Never Exceeds Attested

For randomized valid windows and measurements, assert every envelope in the
distinctness + attestation path has maturity `<= Attested`, and the conjoined
envelope has maturity `Attested` at most.

### EHP-3 - Registry Admits At Most One Identity Per Trust Root

For randomized hardware anchors and two subjects, assert the first valid
registration succeeds and the second registration with the same anchor root fails
with `SybilAnchorReuse`.

### EHP-4 - Freeze Is A Hard Membrane Gate

For randomized positive balances and membrane caps, once the subject is frozen,
`convert_out` and `convert_in` both fail without consuming cap or changing total
credits.

## Definition Of Done

- New crate `crates/hsai-e2e-harness` is added to workspace members.
- It modifies no existing crate.
- EH-1..EH-10 are unit tests.
- EHP-1..EHP-4 are proptests.
- Commands pass:

```sh
cargo test -p hsai-e2e-harness
cargo fmt --all --check
cargo clippy -p hsai-e2e-harness --all-targets -- -D warnings
```

## Out Of Scope

- No Phala integration.
- No Azure or Intel JWT verification.
- No Apple/Darkbloom provider-key verification.
- No network access.
- No external rails.
- No new claim-envelope algebra.
- No new economy rules.
- No new Proof of Agent governance model.

## Next Phase Input

If this harness is green, Phase 3 may implement the first real backend:

```text
crates/hsai-attestation-phala
```

The harness then becomes the local guardrail for the live backend's captured
fixtures and eventual end-to-end tests.
