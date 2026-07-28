# V28R2 Retired-R1 Fingerprint Construction R2 Authorization

State slice:
`astral-rgs-v28r2-retired-r1-fingerprint-construction-r2`.

Status: `R1PreflightFailureRecorded / R1IdentityRetired /
R2ControllerImplemented / R2ConstructionAuthorized /
R2ConstructionNotRun / FingerprintNotBuilt / ProtocolPinUnchanged`.

## R1 failure record

The R1 execution shell stopped before controller invocation. Its first commit
comparison used an unverified incorrect full commit string instead of the
actual committed identity. The shell exited `1`; controller and builder
invocation counts remained zero; and

```text
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r1-retired-fingerprint-8cf75d7-r1.json
```

remained absent. The no-retry policy permanently retires that path and
construction identity. It may not be reused.

The actual R1 authorization commit, read directly from Git after the stop, is:

```text
e1085dd19b8313cd80dffd7ad72b7b0fff08d295
```

This record does not reinterpret the failed precheck as a successful run.

## R2 controller

R2 changes only the fixed external output identity in the pinned controller:

```text
/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r1-retired-fingerprint-8cf75d7-r2.json
```

All implementation-checkout, input-root, input-file, no-follow, clean-HEAD,
content-hash, canonical-protocol, builder-argv, one-invocation, failure-stop,
hash-only output, inspection, and later pinning rules from documents 67 and 68
remain unchanged.

The R2 controller accepts no arguments. Its exact file SHA-256 is:

```text
sha256:92bdb88cff100ccbc6f212605b7117fccda5f141679e9f30b73e46656878244e
```

## Exact invocation

After the R2 controller and this authorization are committed, independently
audited, and the fixed R2 output is confirmed absent, the only permitted
invocation is:

```text
PYTHONDONTWRITEBYTECODE=1 python3 \
  /Users/shaanp/.codex/worktrees/composed-zk-benchmark-os-astral-v28r2-r1-fingerprint-construction-r2/tools/astral-rgs-acquisition-v28r2/construct_retired_v28r1_fingerprint.py
```

The pre-execution shell may verify and display the controller SHA-256, clean
status, and fixed-output absence, but it must not compare against a manually
invented or abbreviated commit identity. The controller itself verifies the
only execution-relevant source commit:
`8cf75d745c20afa885286fecfbd8d67c253b8707`.

The R2 controller and builder invocation counts may each become exactly one.
Any R2 controller, preflight, or builder failure consumes R2. No retry,
alternate path, repair, overwrite, or fallback identity is authorized in this
slice.

## Mandatory stop and claim boundary

After successful construction and read-only independent audit, stop with the
output repository-external and the protocol at `not-built`. Fingerprint commit
and protocol repinning remain a separate reviewed gate.

This slice can establish at most
`LocalRetiredR1FingerprintConstructedUnpinnedV28R2`. It cannot establish
V28R2 eligibility, novelty, acquisition, consolidation, retention/recovery,
continual learning, Astral selection, independent replication, benchmark
evidence, breakthrough, self-improvement, introspection, self-modeling,
Stage 0C, Stage 1, or production evidence.
