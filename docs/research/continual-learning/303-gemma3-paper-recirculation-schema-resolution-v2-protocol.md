# Gemma 3 paper-shaped recirculation optimization corpus V2

State slice: `gemma3-paper-recirculation-schema-resolution-v2`

Governance parent: `aligned-holistic-continual-learning-interpretability-monorepo-v1`

Status: `ProtocolDraft / AcquisitionClosed / ReviewRequired`

## Canonical identities

- Protocol: `gemma3-paper-recirculation-schema-resolution-v2`
- Corpus schema: `gemma3-paper-recirculation-corpus-v2`
- Acquisition manifest: `gemma3-paper-recirculation-acquisition-manifest-v2`
- Source record schema: `gemma3-paper-recirculation-source-record-v2`
- Weco lane: `weco-gemma-recirculation-v2`

Every consumer must use these identities. V1 runners, manifests, source roots,
and scientific outputs are historical inputs only and are not imported.

## Scope

This packet prepares a fresh acquisition contract for a bounded, paper-shaped
Gemma 3 1B recirculation optimization corpus. It is not the full paper corpus
and cannot support a full-paper replication claim. It does not authorize
downloading, model execution, Weco execution, spending, training, assessment,
Evidence Ledger mutation, or any scientific claim.

The external corpus must contain 16 fit windows and 16 assessment windows, each
exactly 1,024 Gemma-token IDs after the frozen normalization policy. Fit window
quotas are `arxiv=6`, `c4=5`, and `pg19=5`. Assessment quotas are `arxiv=2`,
`big_patent=2`, `billsum=2`, `booksum/book=2`, `c4/webtextlike=2`,
`gov_report=2`, `lambada=1`, `newsroom=1`, `pg19=1`, and `pubmed=1`.

## Acquisition boundary

Acquisition remains closed until a genuinely independent reviewer accepts the
exact packet bytes with a packet-bound Ed25519 `ACCEPT`. That receipt must name
the reviewer registry reference, reviewer-controlled key fingerprint,
independence attestation, operator, packet digest, allowed acquisition command,
external custody root, and explicit exclusions including no model execution,
no Weco, no spending, no assessment, no publication, and no Evidence Ledger
mutation. Newsroom form acceptance is evidence of restricted access only; it
is not acquisition authorization or a general IP license.

The raw and normalized source roots must remain outside the repository below the
named owner-only `0700` input roots in the manifest. The named acquisition
entrypoint is `experiments/continual_learning/acquire_gemma3_paper_recirculation_schema_v2.py`.
It must require those input roots to exist, refuse symlinks and repository
paths, refuse an existing output root, and reject partial staging.
Raw data may be retained for no more than 72 hours after independent validation
and must then be deleted.

## Deterministic selection

The acquisition packet freezes an executable source-specific enumeration and
selection algorithm in the machine-readable manifest. Each source has a pinned
loader revision, artifact/member order, malformed-row behavior, duplicate
policy, row identity, tokenizer policy, and exact window quota. The algorithm
fails on malformed or duplicate input; it never skips a row, searches a held-
out split adaptively, or carries text across documents. Selected row IDs,
source-field digests, normalized text digests, and window digests are empty in
this pre-acquisition packet and can be populated only by the authorized
acquisition process.

## License boundary

The manifest records rights as source-specific terms, not as a blanket “public
dataset” claim. `arxiv` and `pubmed` remain `rights-review-required` under the
Scientific Papers 1.1.1 archive. BookSum underlying text and summaries remain
`rights-review-required`; a BSD code license is not treated as a data license.
C4 retains ODC-BY and Common Crawl terms. NEWSROOM is limited to the accepted
Cornell agreement and non-commercial research/education, with no redistribution
right recorded.

## Gate ordering

1. Verify packet digest, independent authorization, and operator identity.
2. Verify external source roots and source artifacts without loading model
   weights.
3. Materialize an atomic external source root and validate its manifest,
   census, permissions, row identities, split disjointness, and digests.
4. Tokenize and publish the external corpus root with exact 16/16 quotas.
5. Run semantic oracle against the frozen model/runtime and corpus manifest.
6. Only after gates 1–5 pass may the separate Weco lane start.

Any failure returns `Blocked` or `NoCorpus`; it must not fall through to Weco.

This lane's maximum claim ceiling is
`LocalDevelopmentGemma3PaperShapedRecirculationOptimizationV2`. It cannot be
reported as a reproduction of the paper's full 484/488/500 fit-window corpus
or complete assessment panel.
