# V28R2 Retired-R1 Fingerprint Construction Authorization

State slice:
`astral-rgs-v28r2-retired-r1-fingerprint-construction`.

Status: `ControllerImplemented / ConstructionAuthorized /
ConstructionNotRun / FingerprintNotBuilt / ProtocolPinUnchanged /
R2ExecutionNotAuthorized`.

## Authorization

This slice adds and authorizes exactly one future invocation of:

```text
tools/astral-rgs-acquisition-v28r2/construct_retired_v28r1_fingerprint.py
```

Its pinned file SHA-256 is:

```text
sha256:105a11041bc9fa7a116c02de9ec40ba4e8a7098a87b196e119c52906c3210e87
```

The controller accepts no arguments. Eight hermetic tests in
`tests/test_construction_controller.py` cover fixed configuration, exact
builder argv, terminal types, symlink components, output absence, relative
path rejection, hashing, no-argument enforcement, and forbidden dynamic or
network path surfaces.

The controller performs the preflight in
`67-v28r2-retired-r1-fingerprint-construction-boundary.md` and, only if it
passes, invokes the committed hash-only builder once.

The controller must use the clean implementation checkout:

```text
/Users/shaanp/.codex/worktrees/composed-zk-benchmark-os-astral-v28r2-validator
```

That checkout must remain at:

```text
8cf75d745c20afa885286fecfbd8d67c253b8707
```

with an empty Git status. The exact implementation and retained-input hashes
remain those pinned in document 67.

## Exact path preflight

The controller must hard-code and byte-for-byte compare these values:

```text
input root:
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1

packet:
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/acquisition-packet.json

validation report:
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/astral-validation-report.json

artifact manifest:
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/artifact-manifest.json

output:
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r1-retired-fingerprint-8cf75d7-r1.json
```

Before invoking the builder, the controller must use no-follow metadata checks
over every existing component of the implementation path, input root, three
input paths, output parent, and output path. It must reject any symlink,
non-directory ancestor, non-regular input, changed input/root relationship,
existing output, changed checkout commit/status, or pinned hash mismatch.

The only authorized controller invocation is:

```text
PYTHONDONTWRITEBYTECODE=1 python3 \
  /Users/shaanp/.codex/worktrees/composed-zk-benchmark-os-astral-v28r2-r1-fingerprint-construction/tools/astral-rgs-acquisition-v28r2/construct_retired_v28r1_fingerprint.py
```

Before that invocation, the controller file hash above and clean construction
checkout must be independently rechecked. The pinned controller then invokes
exactly:

```text
PYTHONDONTWRITEBYTECODE=1 python3 \
  /Users/shaanp/.codex/worktrees/composed-zk-benchmark-os-astral-v28r2-validator/tools/astral-rgs-acquisition-v28r2/build_retired_v28r1_fingerprint.py \
  --packet /Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/acquisition-packet.json \
  --validation-report /Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/astral-validation-report.json \
  --artifact-manifest /Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/artifact-manifest.json \
  --output /Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r1-retired-fingerprint-8cf75d7-r1.json
```

The controller and builder invocation counts are zero before this
authorization and may each become exactly one. Any controller, preflight, or
builder failure consumes the construction identity. No retry, alternate input,
copied bundle, alternate output, repair, or overwrite is authorized.

## Authorized post-construction inspection

If the builder succeeds, this slice permits read-only inspection of the new
output, calculation of its raw-file SHA-256 and canonical
`manifest_sha256`, verification of its closed schema and fingerprint-set
census, scans for prohibited raw R1 material, and independent repository,
validation, and research-scope audits.

This slice also permits one Markdown execution record and status-only updates
under `docs/research/astral-self-modeling/`, `README.md`, and `AGENTS.md`.
Those records may report construction facts only. They may not commit the
fingerprint or modify the protocol.

## Mandatory stop

After construction and audit, stop. The output remains repository-external.
The committed protocol remains `not-built`. A later, distinct reviewed slice
must explicitly authorize committing the accepted hash-only fingerprint and
repinning the protocol.

No V28R2 seed, corpus, tokenizer, model, baseline, update arm, recovery,
selector, assessment, or evidence-promotion operation is authorized.

## Claim boundary

This slice can establish at most
`LocalRetiredR1FingerprintConstructedUnpinnedV28R2`. Even a valid constructed
output is not yet a committed fingerprint or protocol pin and cannot make a
V28R2 packet eligible. It is not novelty, acquisition, consolidation,
retention/recovery, continual learning, Astral selection, independent
replication, benchmark evidence, breakthrough, self-improvement,
introspection, self-modeling, Stage 0C, Stage 1, or production evidence.
