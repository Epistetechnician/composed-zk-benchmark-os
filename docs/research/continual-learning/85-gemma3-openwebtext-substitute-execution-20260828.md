# Gemma3 OpenWebText Substitute Execution R1

State slice: `continual-learning-gemma3-paper-recirculation-openwebtext-substitute-v1`.

## Disposition

The bounded local substitute pilot completed its locked offline execution and
passed independent validation. It selected the preregistered paper target
pair `(source=11, destination=4)` from the fixed candidate panel. This is a
mechanics result on pinned OpenWebText data; it is not exact TFDS
`c4/webtextlike`, a full paper replication, proof of general recirculation, or
benchmark evidence.

## Custody

- Source: `Skylion007/openwebtext`, revision
  `79d93d786212f7344586290adb811d4ae6a1762c`, config `plain_text`, split
  `train`.
- Raw custody: 80 Parquet shards, 8,013,769 rows, and 24,193,092,408 bytes;
  source manifest SHA-256
  `9ba40c0d5d05b4117c6792d63b8e71c8da3b8e42c92b8ccdf2cf5688c0b72cac`.
- Corpus manifest SHA-256:
  `d508c5296e0c4969a3a2b8d589f2aecd94efe4012cc9fa98d154ae3f8cffddc5`.
- GiveMeANode bucket: `gemma3-openwebtext-substitute-v1`; remote inventory:
  80 raw objects plus 10 source/corpus/result receipt objects, with the raw
  object byte sum matching the source manifest.
- Local raw, source, corpus, and result roots remain outside the repository on
  PrimaryED.

## Locked execution

The run used 16 fit and 16 assessment windows of exactly 1024 tokens, fixed
candidate pairs `(7,2)`, `(9,3)`, `(11,4)`, `(12,5)`, fit alpha `0.10`,
evaluation alpha `0.15`, evaluation beta `0.85`, source-to-destination norm
adjustment, and temperature control `1.2`. Weights remained frozen; training,
network access, and Evidence Ledger mutation were false.

## Observed result

- Assessment baseline mean NLL: `2.893553733`.
- Assessment selected mean NLL: `2.821577781`.
- Selected-minus-baseline assessment mean NLL delta: `-0.071975952`.
- Paper expected pair recovered: `true`.
- Native/MLX parity: passed; maximum absolute logit delta `0.0` across 32
  sequences.
- Zero-alpha parity: passed.
- Deterministic repeat: passed; maximum metric delta `0.0`.

## Receipts

- Config SHA-256: `d268e0781858a462500f7011a7b83018d846317b8e42593ebb19fee841e17455`.
- Results SHA-256: `c48f6e35d6f1761a143232955128e4167aa4484ad9681f53ef13599b63bb2773`.
- Receipt SHA-256: `582e28722113ffc12d2f37b0100c911b2df85f90fb2b8b5bd8e2b7425194b58e`.
- Model manifest SHA-256:
  `69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`.
- Independent validator: `valid: true`.

The claim ceiling remains
`LocalDevelopmentGemma3OpenWebTextSubstitutePilot`.
