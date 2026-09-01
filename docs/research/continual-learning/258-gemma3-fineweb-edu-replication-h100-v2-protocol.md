# Gemma3 FineWeb-Edu H100 V2 corrected contract protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v2`.

This is a fresh protocol identity. V1 is terminally closed and no V1
protocol, review receipt, result, model, corpus, provider receipt, or launch
artifact is an input to V2.

V2 repairs the V1 implementation boundary only. It permits additive contract
source, hermetic tests, deterministic byte freezing, and independent review.
It does not authorize model loading, data acquisition, provider access, spend,
H100 execution, assessment, or publication of scientific results.

## Corrected byte binding

The implementation manifest contains the exact ordered list of non-manifest
review files and their SHA-256 digests. Its own `manifest_sha256` is computed
from canonical JSON after omitting only that field. The manifest is included
in the review packet's exact reviewed-file list and digest map, but not in its
own recursive file list.

The manifest is generated only after the protocol, review packet, V2 source,
V2 tests, and current `AGENTS.md` are frozen. Any later change to a reviewed
byte invalidates the freeze and requires a new V2 packet and review.

## Corrected provider receipt boundary

Any future launch must carry a provider-originated attestation over the exact
receipt payload. The validator requires the attestation envelope, exact
GiveMeANode identity, allocation and node IDs, launch-manifest binding,
allowed stop reason, ordered UTC start/stop times, and provider-reported
billing values. It rejects missing attestation verification, reversed or
overlong runtime, non-finite or negative billing, quote/ceiling drift, and
charges above both the sealed estimate and hard ceiling.

The code must receive an independent signature-verification result. A
self-digested JSON object is not provider evidence.

## Corrected publication boundary

The runner must write only to a unique staging root. The provider receipt must
be present before classification. A separate immutable validator must reject
symlinks, directories, extra files, and changed bytes. Only a validated,
unchanged staging root may be moved to a previously absent final root. A
pre-existing final root is always a hard failure.

V2's claim ceiling is
`LocalDevelopmentGemma3FineWebEduReplicationH100V2ContractOnly`. A passing
review does not authorize execution or establish replication, H100
performance, benchmark, production, or breakthrough evidence.

Every mutation in this phase names state slice
`continual-learning-gemma3-fineweb-edu-replication-h100-v2`.
