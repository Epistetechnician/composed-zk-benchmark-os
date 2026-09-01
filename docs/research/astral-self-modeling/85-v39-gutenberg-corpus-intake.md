# V39 Project Gutenberg corpus intake

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

This document defines the source-custody step for the fresh V39-derived Stage
0C protocol. It does not authorize assessment, Stage 0C promotion, Stage 1,
benchmark evidence, introspection claims, or production use.

## Source boundary

The intake uses explicit Project Gutenberg ebook IDs. It does not crawl for
books, choose a random sample, reuse V25/V28/V29 artifacts, or generate
concepts. Project Gutenberg documents canonical ebook landing pages and
machine-readable per-ebook RDF metadata; its landing pages expose a plain
UTF-8 download for each ebook:

- landing page: `https://www.gutenberg.org/ebooks/{id}`
- text: `https://www.gutenberg.org/ebooks/{id}.txt.utf-8`
- RDF metadata: `https://www.gutenberg.org/cache/epub/{id}/pg{id}.rdf`

The acquisition code accepts only HTTPS responses that remain on
`gutenberg.org` or `www.gutenberg.org`. It requires the RDF metadata to mark
the work as public domain and the text to contain its Project Gutenberg
identity and start/end boundaries. Rights must still be checked for the
operator's jurisdiction and for each selected ebook. See the [Project
Gutenberg license](https://gutenberg.org/policy/license.html), [permission
guidance](https://www.gutenberg.org/policy/permission), [bibliographic record
documentation](https://gutenberg.org/help/bibliographic_record.html), and
[offline catalog guidance](https://www.gutenberg.org/ebooks/offline_catalogs.html).

## Selection contract

The external selection manifest must contain:

- the V39 protocol and state-slice identifiers;
- exactly 12 unique Gutenberg IDs;
- exactly four documents assigned to each of `fit`, `tune`, and `assessment`.

The selection is copied byte-for-byte into the output bundle and bound by
SHA-256. The operator must separately verify that the selected documents and
the later 48 concept families are absent from V25 and V28–V29 manifests. The
download script does not make that scientific freshness determination.

## Acquisition

Run:

```text
python3 -B tools/astral-stage0c-qwen36-v39/fetch_gutenberg_corpus_v39.py \
  --selection-manifest /path/to/external/selection-v39.json \
  --output-root /Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-corpus-2026-08-26
```

The destination must be outside the repository and must not already exist.
The command stages the complete bundle and publishes it only after all twelve
documents pass validation. A failed or interrupted acquisition is cleaned up
and cannot leave a partial published root.

The published root contains:

- `documents/{gutenberg_id}/text.txt` — exact downloaded UTF-8 bytes;
- `documents/{gutenberg_id}/metadata.rdf` — exact downloaded RDF bytes;
- `selection-manifest.json` — exact input selection bytes;
- `corpus-manifest.json` — titles, authors, rights, source URLs, byte lengths,
  per-file SHA-256 digests, split assignments, and custody flags;
- `corpus-manifest.sha256` — digest sidecar for the corpus manifest.

Raw source documents remain outside the repository. No activations, logits,
prompts, predictions, or assessment effects are created by this step.

## Independent validation

Run the separate validator after acquisition:

```text
python3 -B tools/astral-stage0c-qwen36-v39/validate_gutenberg_corpus_v39.py \
  /Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-corpus-2026-08-26 \
  --write-receipt
```

The validator performs no network calls. It recomputes the root census,
selection digest, manifest sidecar, metadata identity and rights, UTF-8
content boundaries, per-file digests, duplicate-text check, split counts, and
the closed assessment flags. A valid result is classified only as
`ExternalCorpusCustodyValid` with ceiling
`LocalDevelopmentExternalCorpusCustodyOnly`.

## What remains closed

This intake does not create the 48 concept families. A later, separately
reviewed sealing step must bind a fresh concept registry, enforce document- and
concept-disjoint splits, and verify exclusion from V25 and V28–V29 before any
fit measurement. V39 qualification remains
`InstrumentQualificationPassed` only; assessment stays closed until the
configuration review and prediction lock exist.
