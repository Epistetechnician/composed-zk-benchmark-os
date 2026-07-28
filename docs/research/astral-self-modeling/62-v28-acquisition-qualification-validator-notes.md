# V28 Acquisition-Qualification Validator Notes

State slice: `astral-rgs-v28-acquisition-qualification-validator`.

Protocol slice:
`astral-rgs-novel-knowledge-acquisition-recoverable-consolidation-v28`.

Status: `LocalValidatorImplemented / HermeticContractTestsPassed /
ModelBackedPacketNotSupplied / RetentionRecoveryNotRun /
AstralSelectionNotAuthorized / AssessmentSealedNotAuthorized`.

## Implemented boundary

The additive validator under `tools/astral-rgs-acquisition-v28/` consumes one
caller-supplied repository-external acquisition packet. It does not generate a
corpus, load a model, train, update parameters, invoke RGS, execute recovery, or
open assessment.

It independently checks and recomputes:

- canonical packet, corpus-manifest, and observation hashes;
- exact source commit/tree and checkpoint, tokenizer, runtime, generator,
  configuration, split, and future-assessment commitment shapes;
- strict checkpoint-hash → seed-commitment → corpus-generation →
  configuration-lock → baseline-outcome → optional update-outcome ordering;
- explicit nonreuse of V27 data and no model-output-guided corpus generation;
- at least 24 unique qualification families for each of `nonce_fact`,
  `entity_relation`, `changed_rule`, and `opaque_mapping`;
- exactly four paraphrase, four multi-hop, and four withheld-composition
  queries per family, including disjoint training/evaluation template
  identities, committed source dependencies, and derivation manifests;
- query-specific answer-option mappings that rotate one semantic answer
  through all four positions exactly once within every family/query-kind cell;
- exact rejection of same-item and cross-item training-form prompt hashes;
- complete raw-row coverage and independently recomputed accuracy;
- symmetric near-chance pre-update and separately restarted no-update
  performance overall, by fact kind, and in every seed/order cell; two-sided
  Bonferroni equivalence intervals independently within every seed/order cell;
  and exact row-level pre-update/no-update parity within each cell;
- explicit context-only and retrieval access roles, with exact source and
  retrieval payload censuses and committed manifests;
- source-context and retrieval absence for persistent-state arms;
- distinct update/evaluation process identifiers and exact post-update state
  reload binding;
- an exact three-seed by three-task-order cell census, distinct implementation,
  configuration, artifact, and persistent-state/output identities, and equal
  persistent update budgets;
- Gate 1 overall, query-kind, and fact-kind accuracy floors in every seed/order
  cell; gain over no update; retrieval deltas; and deterministic absolute and
  paired per-seed/order family-cluster intervals with a frozen minimum Student-t
  critical value of `5.0`, with Bonferroni correction across every supplied
  persistent arm, Gate 1 dimension, and seed/order cell;
- hard absence of retention/recovery, selection, and assessment material;
- mandatory false claims.

## Fail-closed states

- An absent packet is `NotRun`.
- A malformed, contaminated, overclaiming, partially populated, or out-of-order
  packet is `Invalid`.
- A valid high-baseline packet is `CorpusNotNovel`; update arms must be absent.
- A structurally valid low-baseline packet without update arms is
  `NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun` and retains the
  artifact-byte verification gate.
- A complete comparison with fewer than two packet-threshold-passing persistent
  arms is `AcquisitionPacketNoCandidateUnverified`.
- Two or more packet-qualified persistent arms produce only
  `AcquisitionPacketCandidateUnverified`. Referenced model, state, and artifact
  bytes are not rehashed by this slice, so retention/recovery remains
  unauthorized and selection stays sealed.

Input runs are explicitly marked `producer_declared_native_unverified`.
Digest shapes, equality relations, and packet rows are checked, but those
producer-declared digests do not establish the existence or contents of model
or update-state bytes. The validator never emits model-backed acquisition,
retention/recovery, selection, continual-learning, replication, benchmark, or
production evidence. Its maximum claim is
`LocalAcquisitionQualificationValidatorV28`.

The frozen `5.0` critical value is deliberately above the Student-t critical
value required at 23 degrees of freedom for the protocol maxima of 324
one-sided or 144 two-sided Bonferroni comparisons. Larger family censuses only
increase degrees of freedom. No inference is taken across three seed clusters
or three task-order clusters; every preregistered cell must clear its own
family-cluster interval and hard floors.

## Test boundary

Hermetic fixtures exercise positive and adversarial packet paths. They are
constructed contract examples, not model outputs and not scientific cells.
The focused gate is:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider \
  tools/astral-rgs-acquisition-v28/tests/test_v28.py -q
```

The read-only operator entrypoint is:

```text
PYTHONDONTWRITEBYTECODE=1 python3 \
  tools/astral-rgs-acquisition-v28/validate_packet.py \
  --packet /repository-external/acquisition-packet.json \
  --output /new/repository-external/astral-validation.json
```

The CLI creates its output exclusively. Exit `0` is restricted to a positive
unverified packet candidate, exit `2` denotes a structurally valid scientific
negative, and exit `1` denotes `Invalid`, `NotRun`, or another noncandidate
state. Operators must also inspect the exact report status.

V27 remains a regression guard:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider \
  tools/astral-rgs-continual-v27/tests/test_v27.py \
  tools/astral-rgs-continual-v27/tests/test_release_v2.py -q
```

No V28 model-backed packet has been supplied or validated. Gate 2 process
recovery and Gate 3 prospective selection require separately authorized source
slices after a genuine Gate 1 packet exists.
