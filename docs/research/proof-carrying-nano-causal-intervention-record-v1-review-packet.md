# Independent review packet: causal-intervention record V1

State slice: `proof-carrying-nano-causal-intervention-record-v1`  
Packet status: `PENDING_INDEPENDENT_REVIEW`  
Assessment authorization: `false`  
Claim ceiling: `LocalCausalInterventionRecordBindingOnly`

This packet requests an independent review of the closed record/proof
boundary. It does not request or authorize a causal assessment. The operator
who prepared this packet may not issue the acceptance receipt.

## Exact scope under review

The proposed record-only slice includes:

1. a parent activation action digest;
2. donor and target checkpoint digests, layer, site, and token position;
3. donor and target activation digests;
4. exact `replace_token_vector` syntax with coefficient `1`, interpolation
   `none`, and source/target activation digest bindings;
5. a finite canonical-decimal effect and nonempty uniquely identified control
   observations;
6. equal host parameter digests before and after the declared observation;
7. replay input digest, index, seed, runner identity, and replay digest;
8. `checked` or `failed` proof status with immutable Lean proof attempts.

The only exported status is `CausalInterventionRecordOnly`, and the assessment
status is `SEALED_UNTIL_INDEPENDENT_REVIEW`. The Lean theorem and validator
prove record identity and declared binding facts only. They do not prove a
causal effect, donor semantic validity, checkpoint faithfulness, or any
scientific, safety, alignment, benchmark, or production claim.

## Bound inputs and provenance

The parent activation evidence is the prior read-only boundary record:

- record: `docs/research/proof-carrying-nano-host-activation-boundary-v1.md`;
- activation state slice:
  `proof-carrying-nano-host-activation-boundary-v1`;
- checkpoint custody manifest:
  `/Users/shaanp/.codex/runs/proof-carrying-nano-host-activation-boundary-v1-custody/checkpoint-custody.json`;
- checkpoint digest:
  `sha256:be2686001169c6ca132bd2243a94dc70e12d6a0d59ec4cd5e0c383da638515cd`;
- activation qualification report:
  `/Users/shaanp/.codex/runs/proof-carrying-nano-host-activation-boundary-v1-qualification-v2/qualification-report.json`;
- activation qualification report digest:
  `sha256:73927a71a86aca120185c2876cd1eea586501dc13893910b1852b79039c75df0`;
- parent activation action digest:
  `sha256:d3e9f9773d4907ef6e36473a6b326be014149144b8bbd7ee2bba92c6bbf1bffe`;
- parent activation bundle digest:
  `sha256:b74e8b20d5000d7f6d5b9cc5dacd226132bd61a7068db18fac3645b96c58c7f2`;
- parent activation digest:
  `sha256:b0f0a6435621a47a7434d6906ed13f7a34675b5bda8f0d8e4545acc7078fdf72`.

These are provenance references for the future record boundary, not a causal
assessment dataset. This slice created no host intervention output, retained
no new raw activation trace, and made no provider call.

## Implementation manifest

The reviewer must hash the exact files in the current checkout and compare
them with this manifest before deciding. SHA-256 values below are the bytes at
packet preparation time.

| Path | SHA-256 |
| --- | --- |
| `tools/proof_carrying_nano_causal_intervention_record_v1/record.py` | `ae329a9476124d3213f8bcfde6af769abede15c7dadf619343b813ea94c05ace` |
| `tools/proof_carrying_nano_causal_intervention_record_v1/proof.py` | `cbce8ef2969798383d4eb6a3978574880a6fa3960458268246fbe0ab182f30f7` |
| `tools/proof_carrying_nano_causal_intervention_record_v1/store.py` | `4c725eded7c2213a2b201f2a031f611b24873775da3f7e282f0d644f123ee273` |
| `tools/proof_carrying_nano_causal_intervention_record_v1/__init__.py` | `4d0e03ec64ebb25a0009687b39408b5123f9c04a5aef2d9424c94df94bde6d7d` |
| `tools/proof_carrying_nano_causal_intervention_record_v1/tests/test_record.py` | `93f07156cbb3d08972d334f91d693befb4fd45b0f2ab33199bb5e951d40e5e32` |
| `tools/proof_carrying_nano_causal_intervention_record_v1/tests/test_contract.py` | `1da388f9773d6c782eb52eb8cf9ac512f056c632f69e92aa24755fbb05ba762b` |
| `tools/proof_carrying_nano_jevlike_independent_validation_v1/causal_intervention.py` | `6fc47f5ad75112c4503afc6100f14ec9903ce825f391274e897add05ccf8fdaa` |
| `tools/proof_carrying_nano_jevlike_independent_validation_v1/__init__.py` | `d5479e58f7a7b85e542763d5e417bc878a8e68b00af53c923668245aa46f6934` |
| `tools/proof_carrying_nano_causal_intervention_record_v1/README.md` | `d64659e0b2299a99d62d56f3f5b65914d6971a1c20d4689d73df1adceb24c5e7` |
| `formal/proof-carrying-nano-interp-v1/NanoInterp/CausalInterventionRecord.lean` | `12879fbe65643593b0bf82ba1e559c773609e0ecda485cce379ec60296f9986b` |
| `formal/proof-carrying-nano-interp-v1/lakefile.toml` | `1a441a7f37b06f1bead7738c471e8683278a161c641385e8d9159779a2100b11` |
| `formal/proof-carrying-nano-interp-v1/lean-toolchain` | `54727eec5cba149c18842e6deb5c41b369d66455c93ce135d7d5347c782b2325` |
| `formal/proof-carrying-nano-interp-v1/lake-manifest.json` | `d6b104063fcaa7bd6ca83206130bf07364efa37d3b8042f73156c876f2c543e9` |
| `scripts/verify_proof_carrying_nano_causal_intervention_record_v1.sh` | `8fb023da2254358b3307d5e1735600e9c58cc5f3065d2d23e207091b400d606e` |
| `docs/research/proof-carrying-nano-causal-intervention-record-v1.md` | `a4fadc4ef041b50944b5a98816355f9f89448bada8d2978b2d0858e60b481b26` |
| `package.json` | `2cd77a86b9c488771c41c718e358b62a77dc648df2f38c0a67fcbc4e95369097` |
| `AGENTS.md` | `221d6f9cc6578e8b2878106859a9fa7efdbeb0f9bb4e8e57f2e239a9732ecffc` |

The repository is intentionally dirty. The dirty checkout is not release-ready
and no clean-branch or release claim is made by this packet.

## Required independent checks

The reviewer should execute from the repository root:

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-causal-intervention-record-v1
cd formal/proof-carrying-nano-interp-v1 && lake build
```

The reviewer should also inspect that:

- the independent validator has no import of the record producer, proof engine,
  or store;
- generated checked proofs import the committed
  `NanoInterp.CausalInterventionRecord` module rather than redefining its
  predicate;
- checked proof metadata binds the exact `lean-toolchain` and
  `lake-manifest.json` bytes used by the checker;
- the validator recomputes nested operator, effect, control, replay, record,
  proof, and bundle digests;
- donor/source and target activation digests are checked against their
  endpoints;
- altered operators, missing controls, non-finite effects, replay changes,
  host parameter changes, and proof-status mismatches fail closed;
- the formal theorem contains only the declared record-level predicate;
- no code path in this slice calls a host model or applies an intervention;
- the package gate reports `CausalInterventionRecordOnly` and
  `SEALED_UNTIL_INDEPENDENT_REVIEW`.

## Decision and authorization

The reviewer must return exactly one packet-bound decision, `ACCEPT` or
`REJECT`, including the packet SHA-256, the `AGENTS.md` SHA-256, reviewer
identity, timestamp, executed commands, and any diagnostic details. An
`ACCEPT` must explicitly state that it authorizes only the next reviewed
configuration step; it does not authorize causal assessment automatically.

Until an independent `ACCEPT` for these exact packet bytes and configuration
exists:

```text
causal_assessment_authorized: false
accepted_evidence_mutation: false
dashboard: NOT_IMPLEMENTED
swarm_coordination: NOT_IMPLEMENTED
jevlike: HypothesisOnly; no integration changes in this slice
production_claims: false
```

No acceptance receipt is embedded here. The next admissible work after an
acceptance is a separately configured and reviewed causal-assessment packet;
that work is outside this slice and was not run.
