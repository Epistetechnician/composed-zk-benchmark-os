# V28R2 Acquisition-Qualification Validator Notes

State slice:
`astral-rgs-v28r2-acquisition-qualification-validator`.

Status: `ValidatorImplemented / HermeticContractTestsPassed /
RealR1FingerprintNotBuilt / R2PacketNotSupplied /
ModelBackedExecutionNotRun / UpdateArmsNotAuthorized /
Gate2Sealed / Gate3Sealed / AssessmentSealed`.

## Implemented boundary

The additive implementation under
`tools/astral-rgs-acquisition-v28r2/` contains:

- the frozen declarative protocol
  `astral.rgs_acquisition_v28r2.protocol.v1`;
- a standard-library clean-room validator core;
- a read-only operator CLI with exclusive report creation;
- a hash-only retired-V28R1 fingerprint builder;
- hermetic full-census and adversarial tests.

The V28R1 validator and producer remain unchanged. The retained R1 bundle was
inspected read-only to verify its artifact schema and frozen raw-versus-semantic
digests; the real fingerprint builder was not executed and no fingerprint was
created. No RGS file, cached model, tokenizer, repository-external V28R2
campaign path, scientific seed, corpus, score row, or model output was created
or executed by this implementation.

## Protocol and reconstruction

The validator freezes:

- 1,536 families in each of four fact kinds;
- 6,144 family clusters total;
- four paraphrase, four multi-hop, and four withheld-composition queries per
  family;
- 73,728 queries per baseline run;
- exactly one `pre_update` and one separately restarted `no_update` run;
- exactly 16 two-sided hypotheses, adjusted alpha `0.003125`, symmetric
  chance-normalized-lift margin `0.05`, and minimum critical value `5.0`;
- all 24 template-to-answer-position permutations once in every 24-family
  fact-kind/query-class block.

The exact canonical protocol identity is
`sha256:236d7a2f4d8f81fdd1990c746cdfff0d3de85c191781bb7c3fde9d84d5b1aaf2`.

From the revealed seed and protocol AST catalogs, the core independently
reconstructs every concept, source/support string, template, alias, wrapper,
option order, question, prompt, expected answer, dependency, mapping,
derivation identity, and canonical hash. Supplied corpus objects must match
exactly.

The generator-input allowlist excludes model/tokenizer scores, generated model
text, R1 observations, R1 item rows, and ambient inputs. The packet must bind
the exact allowlist.

## Baseline and score contract

Every run binds producer-declared preparation/evaluation process identities,
runtime and tokenizer inventories, source-removal receipts, checkpoint
identities, stage order, and zero update budget. The validator requires all
four process identities to be distinct and exact cross-arm score-row parity.
Every lifecycle artifact has an exact version, state slice, and closed key
schema. Run receipts bind back to the sealed checkpoint-state, runtime,
tokenizer, and scorer inventories; the seed commitment binds the checkpoint,
pre-generation receipt, and exclusive one-shot claim. These canonical receipt
chains remain producer attestations: they do not independently prove
operating-system history, filesystem durability, restart execution, source
byte removal, or tokenization correctness.

Each score row binds the canonical prompt hash, explicit input-token array and
hash, input-token count, A-D labels and token IDs, four finite non-boolean
scores, lowest-index tie rule, and independently recomputed argmax. Unknown,
missing, duplicate, reordered, swapped, rebound, malformed, or noncanonical
rows fail closed.

Family IDs are the only statistical clusters. Prompts and restart processes do
not increase sample size. Overall, each fact kind, and each evaluation class
must independently fit wholly inside `[-0.05, 0.05]`.

## Retired-R1 fingerprint boundary

The builder has no executable default path. Its CLI requires explicit absolute
packet, validation-report, artifact-manifest, and new output paths; rejects
symlinks and overwrite; and verifies the three frozen V28R1 digests before
emitting a canonical manifest of domain-separated fingerprints.

The builder deliberately excludes observation rows, choices, and raw scores.
The validator accepts only the pinned hash-only manifest and checks identifier,
content, AST, normalized-skeleton, line, structural eight-token n-gram, seed,
and future-assessment intersections.

The real retired-R1 fingerprint was not built. The committed protocol says
`not-built`, so any scientific packet fails closed until a later separately
authorized slice builds, reviews, commits, and pins the real fingerprint.

## Operator surface

The future read-only invocation shape is:

```text
python3 tools/astral-rgs-acquisition-v28r2/validate_packet.py \
  --protocol /pinned/protocol.json \
  --r1-fingerprint /pinned/retired-v28r1-fingerprint.json \
  --bundle-root /repository-external/v28r2-run \
  --packet /repository-external/v28r2-run/acquisition-packet.json \
  --output /new/repository-external/v28r2-validation.json
```

Exit `0` is restricted to
`NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun`; exit `2` is a valid
`CorpusNotNovel` negative; exit `1` covers `Invalid`, `NotRun`, input failure,
and output-path failure. The output is created exclusively and never
overwritten.

The fingerprint-builder invocation shape is:

```text
python3 \
  tools/astral-rgs-acquisition-v28r2/build_retired_v28r1_fingerprint.py \
  --packet /pinned/v28r1/acquisition-packet.json \
  --validation-report /pinned/v28r1/astral-validation-report.json \
  --artifact-manifest /pinned/v28r1/artifact-manifest.json \
  --output /new/review/fingerprint.json
```

That command is documented but not authorized against the real retained
bundle in this slice.

## Verification

Focused implementation and V28R1 regression:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider \
  tools/astral-rgs-acquisition-v28/tests/test_v28.py \
  tools/astral-rgs-acquisition-v28r2/tests/test_v28r2.py -q
```

Result: `127 passed`.

Static Python check:

```text
python3 -m ruff check tools/astral-rgs-acquisition-v28r2
```

Result: `All checks passed`.

The V28R2 suite contains `89` tests, including one exact public-entrypoint
full-census fixture over 6,144 families and 147,456 score rows plus focused
pure-function and adversarial coverage. Every reconstructed family receives
semantic validation; there is no representative-family reduction. The
separate V27 regression suite passes `17` tests. Synthetic test namespaces and
values are contract fixtures only; they cannot fill a scientific cell.

## Claim boundary

The implementation establishes only
`LocalAcquisitionQualificationValidatorV28R2`: a local engineering contract
and hermetic regression surface. It is not a real R1 fingerprint, V28R2
corpus, model-backed novelty result, acquisition, consolidation,
retention/recovery, continual learning, Astral selection, independent
replication, benchmark evidence, a breakthrough, self-improvement,
introspection, self-modeling, Stage 0C, Stage 1, or production evidence.

A separately committed RGS producer authorization may be drafted only after
this implementation is committed and its protocol, core, CLI, and fingerprint
builder source hashes are pinned.
