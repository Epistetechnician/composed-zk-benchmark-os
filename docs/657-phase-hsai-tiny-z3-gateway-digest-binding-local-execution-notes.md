# Phase 657 HSAI Tiny-Z3 Gateway Digest-Binding Local Execution Notes

State slice: `phase-657-hsai-tiny-z3-gateway-digest-binding-local-execution`.

Phase 657 consumes the Phase 656 preflight and runs exactly one local tiny-Z3
obligation for `gateway_proposal_digest_binding_determinism_v1` over one
concrete non-secret `GatewayActionProposal` fixture.

This is the first post-architecture execution in the Phase 647+ acceleration
lane. It remains `Level1LocalReplayOrLower` local execution observation.

## Implemented

- Typed concrete fixture with baseline, repeated, target-mutation, and
  value-mutation proposals.
- Fixture validation requiring that the repeated proposal is identical and each
  mutation changes only its selected field.
- Canonical QF_BV SMT-LIB2 generation from the actual Rust-produced 256-bit
  proposal digest witnesses.
- Exact Phase 650, Phase 653, and Phase 656 source/preflight revalidation.
- Fixed local Z3 invocation through `-in -smt2`, empty inherited environment,
  SHA-256 executable identity verification, and a 5000 ms timeout.
- Exact output grammar requiring one `unsat` line and empty stderr.
- Bounded stdout/stderr summary digests, output classification, redaction,
  quarantine, replay, and nonpromotion digests.
- Result validation and negative tests for fixture drift, preflight drift,
  executable mismatch, output promotion, and input promotion.
- A claim-boundary source-scan exception restricted to the exact Phase 657
  runner function, exact process-construction line, and Phase 657 claim-boundary
  needle, with tests rejecting arbitrary functions and missing boundaries.

No raw solver transcript, proof artifact, checker transcript, or solver
certificate is retained.

## Executed Run

Execution date: 2026-07-09.

```text
run_id: phase657-local-run-run
z3_path: /opt/homebrew/bin/z3
z3_version: 4.15.0
property_id: gateway_proposal_digest_binding_determinism_v1
solver_verdict: solver_unsat_without_certificate
process_spawned: true
backend_executed: true
level_mapping: Level1LocalReplayOrLower
```

Bounded run digests:

| Binding | SHA-256 / record digest |
|---|---|
| execution input | `e4c965828d1f3d616bfc8de19cb5d18cee62f956bea06f353ff19a5bfec7337d` |
| Phase 656 preflight | `ed832693d0ae4c7d44e82210293158ed9275cc9ba10048824988a660b9697bd3` |
| Phase 650 packet | `67cc70caa930276b9a5ae7ea081b67504030eb4086bc66d8b2747fc2616d1a21` |
| Phase 653 observation | `b5f3da21b8d383b7de9a945d94810ab640e535d6f42ab9e19e0db94cf2583dbb` |
| fixture | `6abb9264de0940b3984403172f15428832ae1fe137722590c1b161d612d7cac0` |
| baseline and repeated proposal | `c4b3f5c6a3abe0d3fb9aad0a3722b50d843380cbbe1509fa247eb4512a542184` |
| target mutation proposal | `dc146ef899232262dda6f219422582ed55b7eab612a5857702b89613ed8b1243` |
| value mutation proposal | `033a014d2fb3efcf5432fccb4d2883ae908d06b34f7a9f7ff17ce17124880ca3` |
| SMT-LIB2 obligation | `48d0476793a737ece1a823f1a6624b9e7a1b0d1fed65aa8fcfb7b6c74cffe0e6` |
| Z3 executable | `5d83379fd1979ed2d308658ffb4564f2af46edc4b3e3556f098b9ea89c3d3878` |
| process output metadata | `a6679e3dd58977e0762abef10b2443871a016b4eeb335a0ca5a4efa0366f02a8` |
| stdout summary | `5fb5fd8881b2a3b4c994770330397bc1526fa398db81feb764f434b5148b724c` |
| stderr summary | `9a43ebe774f71694087a952bdfbc3385ab14cf9edf073ad079e3f0641481a170` |
| output classification | `9729820ccd7e6b38daa67688bede05e1b4ab8d3b3dcf29d5c316ee82e4a2bad9` |
| redaction report | `8e358ccf63702f3d61aa33b9ddf93ad66f0125a465280c4c9ffbde40666544c9` |
| quarantine report | `8dbd00a6f0c9fe44027d3e3d1dbdd6dd78c300c5e460251127d2d01e882d71e3` |
| replay instruction | `ca437759e6de44f81782a47c487b731224e2ce1db39545d7c7d659e756c07a84` |
| nonpromotion | `10c8c3e99630ef0be416f39b17385a89a1779150a7326e789cd222c34f8fd53d` |

The execution-input, Phase 650, Phase 653, and Phase 656 digests above bind
this exact run instance. A separately constructed local test source tree may
use different temporary-root metadata and therefore produce different source
instance digests. Replay equivalence must compare the stable fixture,
proposal-witness, obligation, executable, argv/environment, solver-verdict,
bounded output-summary, output-classification, redaction, and quarantine
bindings rather than assert equality of newly constructed temporary-root
source records.

The run was exercised by:

```bash
cargo test -p hsai-agent-admission --lib phase657_hsai_tiny_z3_gateway_digest_binding_local_execution -- --nocapture
```

Observed result: 5 passed, 0 failed. One test performed the successful Z3
execution. The remaining tests performed validation-only rejection checks.

## Exact Meaning

The obligation asks Z3 whether any of these concrete witness violations hold:

- the baseline and repeated Rust proposal digests differ;
- the baseline and target-mutation proposal digests are equal;
- the baseline and value-mutation proposal digests are equal.

Z3 returned `unsat`. For this exact fixture and these exact Rust-produced
digest witnesses, none of those violations is satisfiable.

This does not prove the SHA-256 implementation, serialization correctness,
general collision resistance, general source correspondence, arbitrary
proposal sensitivity, gateway semantic correctness, or whole-system security.

## Evidence Ceiling

The ceiling after Phase 657 is:

```text
Level1LocalReplayOrLower local execution observation for one concrete fixture.
```

Phase 657 creates no accepted evidence, accepted formal evidence, Level2+
evidence, score-axis evidence, benchmark evidence, proof artifact, checker
transcript, solver certificate, external-audit evidence, semantic-correctness
claim, production-readiness claim, SOTA claim, breakthrough claim,
full-security claim, human-review acceptance, or action authority.

## Next Responsible Phase

The next phase should replay this exact obligation under the same executable,
argv, environment, timeout, and concrete fixture; verify a fresh preflight
against its own exact source instance; compare the stable semantic/output
digest subset identified above; classify any nondeterminism or source-instance
drift; and issue a post-run residual ceiling report. It must remain local and
nonpromoting.

Lean, COBALT, Rust-to-Lean extraction, repository-scale benchmarks, accepted
evidence, Level2+, and score axes remain separate later boundaries.

## Defensible Claim

```text
HSAI executed one preflight-bound local Z3 obligation for a concrete gateway
proposal digest-binding fixture and recorded an unsat result with bounded,
replay-oriented, nonpromoting metadata.
```

It does not justify:

```text
HSAI proved SHA-256 or gateway semantics.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI is semantically correct.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```
