# V39 Project Gutenberg corpus acquisition record

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

## Result

The explicit 12-item selection supplied for V39 was acquired from Project
Gutenberg on 2026-08-26 and independently validated without a second network
call.

- external custody root:
  `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-corpus-2026-08-26`
- classification: `ExternalCorpusCustodyValid`
- claim ceiling: `LocalDevelopmentExternalCorpusCustodyOnly`
- corpus manifest SHA-256:
  `04fba6da83b28e468fbb0a4688e2382d83b4608e143b4a16d2f001015d6b9154`
- selection manifest SHA-256:
  `0a7d36364ccb210ded39945e3a0f80d387fa3b5bf341ff806c6fdd9566fb2dd6`
- retrieval timestamp: `2026-08-26T23:13:45.361674Z`
- validator: `valid=true`, `errors=[]`

The source bundle contains exact downloaded UTF-8 text and per-ebook RDF
metadata for all twelve IDs. The validator recomputed the source-file
digests, metadata identity, public-domain rights marker, English language,
Project Gutenberg text boundaries, duplicate-text condition, split census,
manifest sidecar, and external-root boundary.

## Frozen split assignment

The supplied order was assigned deterministically because no split assignment
was supplied:

- fit: `1342`, `2701`, `2554`, `84`;
- tune: `1661`, `16328`, `11`, `1727`;
- assessment: `43`, `1513`, `100`, `345`.

The complete titles and per-file digests remain in the external
`corpus-manifest.json`. Raw text is not copied into the repository.

## Review item before concept sealing

Gutenberg `100`, *The Complete Works of William Shakespeare*, contains the
work represented by Gutenberg `1513`, *Romeo and Juliet*. Both are assigned to
assessment, so this is not a cross-split document leak. The validator's exact
text-digest check correctly treats the downloaded files as distinct but does
not detect contained works. The concept-registry reviewer must prevent shared
passages or duplicated semantic families from being used as separate evidence.

## Boundary

This record establishes external source custody only. It does not establish
concept freshness, the 48-family concept registry, concept-disjointness,
prediction locking, independent scientific review, held-out intervention
utility, causal-target validity, Stage 0C, Stage 1, benchmark evidence, or
production readiness. `concept_registry_sha256` remains unset and
`assessment_ready` remains false.
