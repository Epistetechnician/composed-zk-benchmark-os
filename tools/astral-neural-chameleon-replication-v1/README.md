# Neural Chameleon replication V1

State slice: `astral-neural-chameleon-replication-v1-preflight`.

This additive slice implements the custody boundary for an eventual offline
replication of the released Neural Chameleon and activation-oracle studies. It
does not download, train, load, or execute a model. Its only runtime action is
to validate an operator-supplied external `artifact-manifest.json` and emit an
aggregate preflight result.

The tooling requires Python 3.9 or newer. Manifest paths use canonical
POSIX-relative syntax, checkpoint roles are deterministic file sets so sharded
weights are representable, every role is bound by a role-level SHA-256, and the
schema version is a strict JSON integer (not a boolean).
Pass the artifact root as its canonical resolved path. Symlinked roots and
symlinked ancestors are rejected even when they resolve to an otherwise valid
external directory.

Run the hermetic tests:

```text
python3 -B -m unittest discover -s tools/astral-neural-chameleon-replication-v1/tests -p 'test_*.py'
```

Run a custody preflight:

```text
python3 -B tools/astral-neural-chameleon-replication-v1/preflight_v1.py \
  --artifact-root /path/to/external/neural-chameleon-v1
```

The independent validator must receive the same trusted external root; a
result JSON alone is not a custody gate:

```text
python3 -B tools/astral-neural-chameleon-replication-v1/validator_v1.py \
  /path/to/preflight-result.json \
  --artifact-root /path/to/external/neural-chameleon-v1
```

The independent validator rechecks the manifest semantics, artifact census,
file digests, role digests, cardinality, and uniqueness before accepting a
ready result.

The manifest must contain exactly these repository-external roles:

- `chameleon_checkpoint`
- `precursor_checkpoint`
- `activation_oracle_checkpoint`
- `linear_monitor_bundle`
- `oracle_corpus_bundle`
- `mechanistic_corpus_bundle`
- `runtime_manifest`

The manifest also requires structurally separate oracle and mechanistic arm
bindings, typed model/tokenizer/monitor/corpus/runtime provenance, explicit
freshness exclusions for V22/V23/V24/V25/V26/V38, measurable endpoint and
sample-count declarations, prediction locking before assessment, and an
aggregate-only retention policy. The preflight is ready only for instrument
qualification. It never authorizes assessment opening, training, network
access, accepted evidence, or claims beyond
`LocalDevelopmentNeuralChameleonReplicationPreflightOnly`.
