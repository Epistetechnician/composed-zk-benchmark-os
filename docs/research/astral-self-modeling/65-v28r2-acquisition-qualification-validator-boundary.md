# V28R2 Acquisition-Qualification Validator Boundary

State slice:
`astral-rgs-v28r2-acquisition-qualification-validator`.

Status: `ImplementationComplete / HermeticContractTestsPassed /
RealR1FingerprintNotBuilt / R2PacketNotSupplied /
ModelBackedExecutionNotRun / UpdateArmsNotAuthorized /
Gate2SealedNotAuthorized / Gate3SealedNotAuthorized /
AssessmentSealedNotAuthorized`.

## Decision

V28R2 requires an additive clean-room validator before any producer
implementation or scientific campaign exists. The validator must implement the
powered, two-baseline protocol in
`64-v28r2-powered-acquisition-novelty-preregistration.md` without importing or
trusting either V28R1 or V28R2 generator logic.

This boundary authorizes validator implementation and hermetic contract tests
only. It does not authorize building the real retired-V28R1 fingerprint,
mutating RGS, creating a scientific seed or corpus, loading a tokenizer or
model, executing a baseline, validating model-backed R2 data, or opening any
later gate.

## Cross-repository commit order

The order is mandatory:

1. commit this docs-first composed-repository authorization from a clean
   worktree;
2. implement, test, and commit the additive composed validator from a clean
   worktree;
3. record that exact composed commit and the SHA-256 identities of
   `protocol.json`, `v28r2.py`, `validate_packet.py`, and
   `build_retired_v28r1_fingerprint.py`;
4. only then create and commit a separate RGS docs-first producer
   authorization that pins all five identities;
5. only after that RGS authorization commit may additive RGS producer
   implementation begin.

RGS V28R2 authorization or implementation before the composed validator commit
exists is prohibited.

## Additive implementation surface

Exactly these new source paths are authorized:

```text
tools/astral-rgs-acquisition-v28r2/protocol.json
tools/astral-rgs-acquisition-v28r2/v28r2.py
tools/astral-rgs-acquisition-v28r2/validate_packet.py
tools/astral-rgs-acquisition-v28r2/build_retired_v28r1_fingerprint.py
tools/astral-rgs-acquisition-v28r2/tests/test_v28r2.py
```

Implementation notes may be added at:

```text
docs/research/astral-self-modeling/66-v28r2-acquisition-qualification-validator-notes.md
```

Status-only updates are allowed in this boundary, V28 notes 61, 62, and 64,
the Astral claim ledger, roadmap, navigation, and `AGENTS.md`.

The existing `tools/astral-rgs-acquisition-v28/` directory and every V28R1
protocol, validator, test, packet, corpus, ledger, and retained artifact are
immutable and read-only.

## Frozen protocol identity

The implementation freezes:

```text
protocol version:
  astral.rgs_acquisition_v28r2.protocol.v1
packet version:
  mesh.astral_v28r2_acquisition_packet.v1
packet state slice:
  astral-rgs-v28r2-powered-acquisition-novelty
claim ceiling:
  LocalAcquisitionQualificationValidatorV28R2
```

The exact power profile is:

- four fact kinds;
- 1,536 families per fact kind;
- 6,144 complete family clusters;
- four queries in each of three evaluation classes per family;
- 73,728 canonical queries per run;
- exactly one `pre_update` and one separately restarted `no_update` run;
- 16 two-sided baseline hypotheses;
- familywise alpha `0.05`;
- Bonferroni-adjusted alpha `0.003125`;
- symmetric chance-normalized-lift margin `0.05`;
- minimum Student-t critical value `5.0`;
- family ID as the only statistical cluster.

Within every fact-kind/query-class block of 24 families, the four template
ordinals against four answer positions use all 24 lexicographic permutations
exactly once.

## Declarative reconstruction contract

`protocol.json` must embed declarative concept ASTs, training and evaluation
template ASTs, prompt-shell AST, derivation grammar, normalization profile,
domain tags, ordering rules, power profile, permutation contract, baseline
process contract, nonreuse contract, required false claims, and an exact
generator-input allowlist. The allowlist must exclude model or tokenizer
scores, generated text, V28R1 observations, V28R1 item rows, and every ambient
path or input not sealed before the seed. The packet binds the allowlist digest
and the validator rejects any undeclared producer input.

The validator independently interprets those declarations. Supplied corpus
text, IDs, expected answers, mappings, dependencies, prompt text, hashes,
scores, observations, summaries, or manifests are never authoritative.

For every family and query, the validator reconstructs:

- typed concept semantics;
- source and support text;
- training and evaluation template identity and AST;
- aliases, wrappers, values, options, and option order;
- question and prompt bytes;
- expected choice and template-to-position permutation;
- family, item, query, dependency, mapping, and derivation identities;
- canonical hashes and exact object shape.

A packet is `Invalid` on any difference, even when generator-supplied hashes
are internally consistent.

## Clean-room boundary

The validator core may contain only standard-library canonical JSON and
SHA-256 helpers, strict type/key checks, protocol loading, artifact-tree
validation, a protocol-owned AST interpreter and derivation implementation,
corpus reconstruction, retired-fingerprint membership checks, score and argmax
reconstruction, process/state validation, family-cluster statistics, and
report construction.

It may not import or call:

- V28R1 or V28R2 producer/generator modules;
- RGS source;
- MLX or model/tokenizer libraries;
- network libraries;
- subprocess execution.

The builder and validator are separate. The validator consumes only a pinned
canonical retired-R1 fingerprint manifest and may not read R1 generator
objects, corpus objects, item rows, observations, or model outcomes.

## Retired-V28R1 fingerprint builder

The builder source may be implemented and tested with synthetic fixtures. It
must refuse input until the fixed R1 packet, validation-report, and
artifact-manifest digests match:

- packet
  `sha256:2fd74b389907d3167518a0d91d9d63f18fda7c1231a51764657e791286ee2ad0`;
- report
  `sha256:3e24804dc84744a300bb11bc246fdfd40256459f97a68da0df7993d676b9ea3d`;
- manifest
  `sha256:5b01a32e1ba9d7d9ce84c8b301f29e0145962ac8c0eac0ec59b07cd5cfca846e`.

The output contains domain-separated hashes only, with no raw R1 text or model
outcome. Required sets cover seeds and commitments; namespaces; family, item,
query, concept, anchor, value, alias, and wrapper identities; source, support,
question, prompt, option, dependency, and mapping hashes; template and concept
AST hashes; typed normalized skeleton and line hashes; typed structural
eight-token n-grams; and future-assessment family identities.

Running the builder on the real retained R1 bundle requires a later
construction authorization. Committing an accepted output and pinning it into
the protocol require a later, distinct reviewed authorization after
construction audit.

## Artifact and packet validation

The operator CLI accepts explicit protocol, retired-fingerprint manifest,
bundle root, packet, and new output paths. It is read-only except for exclusive
creation of the report. The bundle must contain only the closed protocol-owned
path inventory, use canonical relative member paths, contain no symlinks, and
match its no-self-entry manifest.

Every baseline score row binds:

- canonical query ID and prompt-byte hash;
- canonical token-ID-array hash and input-token count;
- exact A-D labels and token IDs;
- four finite, non-boolean label log-probability scores;
- lowest-index tie rule and independently recomputed argmax.

The validator rejects unknown, missing, duplicate, reordered, swapped,
counterfeit, rebound, or noncanonical rows. It requires all four process
identities to be distinct and retains exact runtime inventories and ordered
process receipts. `pre_update` must carry a receipt chain declaring a fresh
checkpoint load before any update-data processing. `no_update` must use a
distinct zero-budget no-op preparation process, carry a canonical
source-removal receipt declaring removal of source-context and retrieval
material, then start a distinct evaluator that declares a fresh load of the
exact checkpoint. The clean-room validator binds these producer records and
their hashes; it does not independently observe the operating-system processes
or execute the tokenizer. Lifecycle records are closed-schema,
content-addressed producer attestations only. They are not independently
reconstructed process, filesystem-durability, restart, or byte-removal proof.
The validator requires zero update budgets, no declared context or retrieval,
and exact cross-arm prompt, score, argmax, and observation parity.

The validator also reconstructs the complete producer-declared one-shot receipt
chain. The fixed
power profile, catalogs, grammar, generator-input allowlist, future-assessment
identity commitment, and all inventories precede an exclusive ledger claim.
The receipt chain must declare that the ledger and parent directory were durably
synced before exactly one seed draw. Exactly one corpus may follow. Any second
seed or corpus, discarded
candidate, adaptive family expansion, post-seed power change, alternate output
root, reused R1 ledger or seed, or recovery after a post-claim failure is
`Invalid`. A future producer must record concurrent ledger claims with exactly
one winner, and any failure after the winning claim permanently retires the
campaign. These are fail-closed artifact semantics, not independent proof of
filesystem durability or process history.

With the same sealed inputs and seed, independent reconstruction must yield a
byte-identical corpus and manifest. Any nondeterministic field or ordering
difference is `Invalid`.

The only passing baseline disposition is
`NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun`. A valid interval
failure is `CorpusNotNovel` with only
`acquisition.v28r2_permanently_retired_corpus_not_novel`; it does not request
or authorize another V28R2 corpus. Malformed or contaminated material is
`Invalid`; absent material is `NotRun`.

## Hermetic test boundary

Tests use reduced construction-known synthetic fixtures and explicit test-only
namespaces. They may exercise the full 1,536-per-kind census only through
in-memory deterministic construction that does not touch a model, scientific
seed, production ledger, or repository-external campaign path.

Adversarial coverage must include:

- exact protocol, power, family, query, process, and comparison censuses;
- missing or duplicate 24-permutation members;
- generator-consistent but independently invalid semantics;
- validator import-graph separation and generator-input allowlist denial;
- R1 fingerprint and normalization drift;
- reused or renamed R1 IDs, content, ASTs, skeletons, lines, and eight-grams;
- training/evaluation template overlap;
- exclusive-create ledger races with exactly one winner, durable ledger and
  parent-directory sync before seed, lock/ledger/seed ordering violations,
  second seeds or corpora, discarded candidates, adaptive expansion,
  post-seed power changes, alternate output roots, R1 ledger/seed reuse, and
  permanent retirement after every post-claim failure;
- byte-identical deterministic generation and manifest reconstruction from the
  same sealed inputs/seed, with nondeterministic fields or ordering rejected;
- repeated preparation or evaluator IDs, evaluator reuse, incorrect process
  order, runtime drift, missing source-removal receipt, and retained source or
  retrieval material;
- every score-row binding and failure class;
- cross-arm parity failures;
- near-chance points with intervals crossing either margin;
- overall passes masking fact-kind or evaluation-class failures;
- any update, recovery, selection, assessment, or true claim-boundary field.

Synthetic fixtures are contract coverage only. They cannot fill a scientific
cell or support model-backed evidence.

## Stop and claim boundary

Implementation stops after source, tests, notes, and status mirrors are
committed from a clean worktree. It may reach only:

```text
ValidatorImplemented /
HermeticContractTestsPassed /
RealR1FingerprintNotBuilt /
R2PacketNotSupplied /
ModelBackedExecutionNotRun /
UpdateArmsNotAuthorized /
Gate2Sealed /
Gate3Sealed /
AssessmentSealed
```

No producer source, RGS mutation, fingerprint construction from the real
bundle, corpus generation, checkpoint access, model execution, artifact
promotion, accepted evidence, independent replication, benchmark evidence,
continual-learning or breakthrough claim, self-improvement, introspection,
self-modeling, Stage 0C, Stage 1, or production claim is authorized. The
maximum claim is `LocalAcquisitionQualificationValidatorV28R2`.
