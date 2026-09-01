# Gemma3 OpenWebText substitute pilot V1

State slice: `continual-learning-gemma3-paper-recirculation-openwebtext-substitute-v1`.

This slice provides a bounded local substitute for the blocked TFDS
`c4/webtextlike` input. It uses the pinned `Skylion007/openwebtext` Parquet
release at revision
`79d93d786212f7344586290adb811d4ae6a1762c`, keeps the raw shards and
normalized source outside the repository on PrimaryED, and mirrors the raw
shards to the dedicated GiveMeANode object-storage bucket.

The acquisition boundary is
`experiments/continual_learning/acquire_gemma3_openwebtext_substitute_v1.py`.
It records the upstream revision, all 80 raw-shard checksums, the pinned
aggregate row and byte counts, and two document-disjoint global row ranges:
rows `0..255` for fit and `1,000,000..1,000,255` for assessment. The
independent source validator is
`experiments/continual_learning/validate_gemma3_openwebtext_substitute_v1.py`.

The runtime boundary is
`experiments/continual_learning/stage_and_run_gemma3_openwebtext_substitute_v1.py`.
It selects the first sixteen full 1024-token windows from each range, checks
Gemma3 tokenizer round trips, uses the fixed candidate pairs `(7,2)`, `(9,3)`,
`(11,4)`, and `(12,5)`, locks evaluation at `alpha=0.15` and `beta=0.85`,
checks zero-alpha parity and a deterministic repeat, and keeps the cached
Gemma3 1B BF16 MLX weights frozen with network access disabled.

The exact external roots are:

```text
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-openwebtext-substitute-raw-v1/
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-openwebtext-substitute-source-v1/
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-openwebtext-substitute-corpus-v1/
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-openwebtext-substitute-recirculation-v1/
```

The result ceiling is
`LocalDevelopmentGemma3OpenWebTextSubstitutePilot`. This slice does not
establish exact `c4/webtextlike` identity, full-paper replication, general
recirculation, benchmark superiority, production readiness, or accepted
scientific evidence.
