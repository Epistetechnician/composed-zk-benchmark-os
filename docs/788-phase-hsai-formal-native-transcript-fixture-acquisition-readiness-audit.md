# Phase 788 HSAI Formal Native Transcript Fixture Acquisition Readiness Audit

## Status

Stopped documentation-only before Phase 786 prerequisite `P02`.

State slice:
`phase-788-hsai-formal-native-transcript-fixture-acquisition-readiness-audit`.

Classification: `NativeTranscriptFixtureCaptureNotReady`.

Execution status: `StoppedDocumentationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Verdict

Phase 788 completes the documentation-first `P01` capture protocol and
readiness audit. It does not authorize Phase 789 capture.

The immutable command census, five semantic-shape classes, target source
rules, capture envelope, raw-byte policy, corpus schemas, deterministic
negative derivations, reviewer inputs, and failure conditions are exact.
Current readiness fails because the repository and prior retained state contain
none of the following required inputs:

1. a concrete accepted machine-policy instance for `CODESIGN_EXE`,
   `SPCTL_EXE`, and `OTOOL_EXE`;
2. accepted `hsai-formal-executable-identity-observation-v1` records for those
   three roles;
3. the packaged Aeneas target bytes admitted by their historical digests;
4. an accepted ordinal-073 build receipt and retained source-built Charon
   target bytes;
5. observed native stdout and stderr bytes; or
6. named, distinct capture, fixture-review, and grammar-review principals.

Historical packaged digests identify removed artifacts. Historical
source-built Charon digests are explicitly nonqualifying diagnostics. Ignored
local `target/` outputs are not source authority. No missing byte, identity,
receipt, reviewer, or transcript may be reconstructed from documentation.

Phase 780 lane `L05` remains open. Resolved lanes remain `L01-L04,L09`; open
lanes remain `L05-L08,L10-L11`. Historical Phase 779 JSONL remains unchanged
with 1,469 blockers, 102 blocked rows, and no source-ledger digest.

## Immutable Protocol Header

The capture protocol schema is
`hsai-formal-native-transcript-capture-protocol-v1` with these fixed values:

```text
protocol_id=phase788-darwin-native-n21-capture-v1
operation_order_sha256=490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
executable_registry_document_sha256=e198efaab08ee38e02b7dabf03d380ecb3c48a8e37e7431ec4741443667f6f67
selector_schema=darwin-native-v1
scope_id=N21
scope_ordinal_count=21
semantic_shape_count=5
capture_root=/private/tmp/hsai-native-transcript-capture-v1
cwd=/private/tmp/hsai-native-transcript-capture-v1
timeout_seconds=120
stdout_cap_bytes=1048576
stderr_cap_bytes=1048576
stdin=closed
```

`${CAPTURE_ROOT}` below is a contract token whose only admitted expansion is
the literal `capture_root` above. It is not an environment lookup or shell
expansion. The root must be absent before capture, created exclusively as mode
`0700`, owned by the capture principal, and free of symlink ancestors.

## Exact Selector Input

Every observed positive fixture must bind one accepted byte-identical
`darwin-native-v1` selector:

```text
role_id
acceptance_policy_id
machine_policy_id
machine_policy_sha256
observed_executable_sha256
platform_product_version
platform_build_version
platform_arch
```

The selector must come from an accepted Phase 787 identity observation for the
exact native role. Path-only, role-only, platform-only, signer-only, wildcard,
range, nearest-version, default, and unknown-version fallback are forbidden.
The three required selector values are absent at this phase.

## Exact N21 Semantic Census

No two shapes are treated as equivalent merely because they share a tool or
return code.

| Shape ID | Role | Exact command form | Rows | Outcome | Required semantic authority |
|---|---|---|---:|---|---|
| `codesign-verify-valid-v1` | `CODESIGN_EXE` | `codesign --verify --strict --verbose=4 TARGET` | 5 | `exit/0/null` | strict signature verification succeeds |
| `codesign-display-adhoc-v1` | `CODESIGN_EXE` | `codesign --display --verbose=4 TARGET` | 5 | `exit/0/null` | valid ad-hoc identity and no Team ID |
| `spctl-rejected-v1` | `SPCTL_EXE` | `spctl --assess --type execute --verbose=4 TARGET` | 3 | `exit/3/null` | stderr classifies the target as rejected |
| `otool-libraries-v1` | `OTOOL_EXE` | `otool -L TARGET` | 6 | `exit/0/null` | ordered dependency records support exact path policy |
| `otool-load-commands-v1` | `OTOOL_EXE` | `otool -l TARGET` | 2 | `exit/0/null` | ordered load commands support exact `LC_RPATH` policy |

The row partition is exactly `5 + 5 + 3 + 6 + 2 = 21`.

## Target Slots And Identity Rules

Future capture may materialize only these six non-secret target slots. Target
bytes must be copied without mutation into an absent regular-file slot, then
read back and SHA-256 checked before and after every consumer.

| Target ID | Exact capture slot | Source authority | Required identity |
|---|---|---|---|
| `packaged-aeneas` | `${CAPTURE_ROOT}/targets/packaged/aeneas` | Phase 667 Aeneas release archive | SHA-256 `9b9acc9b8c0820de5650fa72b8f66c6caf5e85bce616f8b6cb91c3b5f30d877a` |
| `packaged-charon` | `${CAPTURE_ROOT}/targets/packaged/charon` | Phase 667 Aeneas release archive | SHA-256 `a71675cd16831f8dbba6936c8d9f85b2a2e171259d5c1cd2746bba99781be90a` |
| `packaged-charon-driver` | `${CAPTURE_ROOT}/targets/packaged/charon-driver` | Phase 667 Aeneas release archive | SHA-256 `dde11d6bfedd3bd6b3c8b56c54b96992245c68e784c8d112aaada1d6618bed86` |
| `packaged-libgmp` | `${CAPTURE_ROOT}/targets/packaged/libgmp.10.dylib` | Phase 667 Aeneas release archive | SHA-256 `1b0ae61990da7a4661f2c8c601f55f6c9950279bbfef12453dd5bb0c01e4b0df` |
| `built-charon` | `${CAPTURE_ROOT}/targets/built/charon` | accepted ordinal-073 build receipt | exact receipt SHA-256; currently absent |
| `built-charon-driver` | `${CAPTURE_ROOT}/targets/built/charon-driver` | accepted ordinal-073 build receipt | exact receipt SHA-256; currently absent |

The packaged source is exactly:

```text
url=https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz
byte_length=123234656
sha256=fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45
```

The built source authority is exact Charon commit
`909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` under the Phase 778 ordinal-073
build contract. Its output identities are attempt-specific receipt values, not
the diagnostic Phase 671 digests and not universal expected digests.

The packaged archive bytes were removed after prior attempts. The later
diagnostic source-built digests from Phase 671 cannot populate either built
slot because they followed an earlier stop condition. A future input-preparation
slice must prove source authority and materialize all six targets without
executing them. Phase 788 performs neither action.

## Exact Capture Commands

Every argv array below is submitted directly without a shell. Rows 076-082 use
the Phase 776 sandbox prefix and byte-exact profile SHA-256
`5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08`.

| Ordinal | Operation ID | Exact argv |
|---:|---|---|
| 043 | `codesign-verify-packaged-aeneas` | `/usr/bin/codesign --verify --strict --verbose=4 ${CAPTURE_ROOT}/targets/packaged/aeneas` |
| 044 | `codesign-verify-packaged-charon` | `/usr/bin/codesign --verify --strict --verbose=4 ${CAPTURE_ROOT}/targets/packaged/charon` |
| 045 | `codesign-verify-packaged-charon-driver` | `/usr/bin/codesign --verify --strict --verbose=4 ${CAPTURE_ROOT}/targets/packaged/charon-driver` |
| 046 | `codesign-display-packaged-aeneas` | `/usr/bin/codesign --display --verbose=4 ${CAPTURE_ROOT}/targets/packaged/aeneas` |
| 047 | `codesign-display-packaged-charon` | `/usr/bin/codesign --display --verbose=4 ${CAPTURE_ROOT}/targets/packaged/charon` |
| 048 | `codesign-display-packaged-charon-driver` | `/usr/bin/codesign --display --verbose=4 ${CAPTURE_ROOT}/targets/packaged/charon-driver` |
| 049 | `spctl-packaged-aeneas` | `/usr/sbin/spctl --assess --type execute --verbose=4 ${CAPTURE_ROOT}/targets/packaged/aeneas` |
| 050 | `spctl-packaged-charon` | `/usr/sbin/spctl --assess --type execute --verbose=4 ${CAPTURE_ROOT}/targets/packaged/charon` |
| 051 | `spctl-packaged-charon-driver` | `/usr/sbin/spctl --assess --type execute --verbose=4 ${CAPTURE_ROOT}/targets/packaged/charon-driver` |
| 052 | `otool-libraries-packaged-aeneas` | `/usr/bin/otool -L ${CAPTURE_ROOT}/targets/packaged/aeneas` |
| 053 | `otool-libraries-packaged-charon` | `/usr/bin/otool -L ${CAPTURE_ROOT}/targets/packaged/charon` |
| 054 | `otool-libraries-packaged-charon-driver` | `/usr/bin/otool -L ${CAPTURE_ROOT}/targets/packaged/charon-driver` |
| 055 | `otool-libraries-packaged-libgmp` | `/usr/bin/otool -L ${CAPTURE_ROOT}/targets/packaged/libgmp.10.dylib` |
| 056 | `otool-load-commands-packaged-charon-driver` | `/usr/bin/otool -l ${CAPTURE_ROOT}/targets/packaged/charon-driver` |
| 076 | `codesign-verify-built-charon` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/codesign --verify --strict --verbose=4 ${CAPTURE_ROOT}/targets/built/charon` |
| 077 | `codesign-verify-built-charon-driver` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/codesign --verify --strict --verbose=4 ${CAPTURE_ROOT}/targets/built/charon-driver` |
| 078 | `codesign-display-built-charon` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/codesign --display --verbose=4 ${CAPTURE_ROOT}/targets/built/charon` |
| 079 | `codesign-display-built-charon-driver` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/codesign --display --verbose=4 ${CAPTURE_ROOT}/targets/built/charon-driver` |
| 080 | `otool-libraries-built-charon` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/otool -L ${CAPTURE_ROOT}/targets/built/charon` |
| 081 | `otool-libraries-built-charon-driver` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/otool -L ${CAPTURE_ROOT}/targets/built/charon-driver` |
| 082 | `otool-load-commands-built-charon-driver` | `/usr/bin/sandbox-exec -f ${CAPTURE_ROOT}/sandbox.sb /usr/bin/otool -l ${CAPTURE_ROOT}/targets/built/charon-driver` |

The exact replacement environment for every row is:

```text
HOME=${CAPTURE_ROOT}/home
LANG=C
LC_ALL=C
TZ=UTC
TMPDIR=${CAPTURE_ROOT}/tmp
TERM=dumb
NO_COLOR=1
PATH=/usr/bin:/bin:/usr/sbin:/sbin
```

No parent environment entry is inherited. Proxy, credential, token, askpass,
SSH, resolver override, dynamic-loader override, and user configuration values
are absent. File descriptors other than standard input/output/error and the
private close-on-exec status channel are closed.

## Positive Corpus Contract

Each row writes exclusively beneath:

```text
${CAPTURE_ROOT}/corpus/${SELECTOR_SHA256}/${ORDINAL_3}-${OPERATION_ID}/status.json
${CAPTURE_ROOT}/corpus/${SELECTOR_SHA256}/${ORDINAL_3}-${OPERATION_ID}/stdout.bin
${CAPTURE_ROOT}/corpus/${SELECTOR_SHA256}/${ORDINAL_3}-${OPERATION_ID}/stderr.bin
${CAPTURE_ROOT}/corpus/${SELECTOR_SHA256}/${ORDINAL_3}-${OPERATION_ID}/provenance.json
```

Directories are mode `0700`; files are mode `0600`. All paths must be absent,
canonical, owner-contained, regular, non-symlink, and unique. Both streams are
captured independently even when empty. Status is written last after stream
flush and complete process-group reap.

`provenance.json` has exactly these fields:

```text
schema
fixture_id
fixture_class=observed-positive
capture_protocol_sha256
operation_order_sha256
ordinal
operation_id
semantic_shape_id
darwin_native_selector
executable_identity_observation_sha256
target_id
target_source_authority
target_observation_sha256
argv
cwd
replacement_environment
timeout_seconds
stdout_cap_bytes
stderr_cap_bytes
reason
return_code
signal
stdout_length
stdout_sha256
stderr_length
stderr_sha256
platform_product_version
platform_build_version
platform_arch
captured_at_utc
capture_operator_id
```

The status and provenance objects, raw stream bytes, target observation, and
selector are read back through no-follow descriptors and digest-checked before
review. Missing, extra, duplicate, traversing, replaced, oversized, truncated,
or digest-mismatched content rejects the complete corpus.

## Raw-Byte And Publication Policy

Raw observed bytes are grammar authority and may not be normalized, rewritten,
decoded and re-encoded, merged, reconstructed, or redacted in place.

The initial corpus remains outside git under `${CAPTURE_ROOT}`. A publication
candidate may use only this portable path shape:

```text
formal/hsai-native-transcript-fixtures/v1/${SELECTOR_SHA256}/${FIXTURE_ID}/status.json
formal/hsai-native-transcript-fixtures/v1/${SELECTOR_SHA256}/${FIXTURE_ID}/stdout.bin
formal/hsai-native-transcript-fixtures/v1/${SELECTOR_SHA256}/${FIXTURE_ID}/stderr.bin
formal/hsai-native-transcript-fixtures/v1/${SELECTOR_SHA256}/${FIXTURE_ID}/provenance.json
```

Publication requires byte-identical raw stream digests, a deterministic scan
showing no credential, token, username, home path, hostname, network address,
hardware identifier, or uncontrolled temporary path, and independent fixture
review. The fixed public capture-root spelling is permitted. If any forbidden
value occurs, the fixture is rejected and deleted; it is not sanitized and is
not replaced with reconstructed bytes. Phase 788 creates no publication path.

## Deterministic Synthetic Negatives

Every synthetic negative derives from one admitted positive parent and records:

```text
fixture_class=synthetic-negative
parent_fixture_id
parent_stream
parent_stream_sha256
mutation_class
start_offset
end_offset
inserted_bytes_hex
expected_rejection_code
result_length
result_sha256
```

The only mutation operations are:

| Mutation class | Exact byte transformation |
|---|---|
| `missing` | delete `[start_offset,end_offset)` |
| `duplicate` | insert the parent slice `[start_offset,end_offset)` at `end_offset` |
| `reordered` | swap two declared adjacent non-overlapping parent ranges |
| `ambiguous` | insert one declared conflicting parent-derived record at `end_offset` |
| `malformed` | replace `[start_offset,end_offset)` with `inserted_bytes_hex` |
| `truncated` | retain exactly parent bytes `[0,start_offset)` |
| `extra` | insert `inserted_bytes_hex` at `start_offset` |

Offsets are unsigned byte offsets into the parent stream. Ranges must be
in-bounds and transformations are applied once. UTF-8 indexing, regex
replacement, line-ending normalization, parser-dependent editing, random
mutation, and mutation chaining are forbidden. The derivation is independently
recomputed from the positive parent before use. Synthetic negatives are never
described as observed native output.

## Corpus Manifest And Review

The complete manifest schema is
`hsai-formal-native-transcript-corpus-manifest-v1`:

```text
schema
protocol_sha256
operation_order_sha256
registry_document_sha256
ordered_positive_fixture_ids
ordered_synthetic_negative_fixture_ids
semantic_shape_coverage
selector_coverage
target_coverage
file_inventory
fixture_reviewer_id
grammar_reviewer_id
fixture_reviewed_at_utc
grammar_reviewed_at_utc
fixture_review_decision
grammar_input_decision
nonclaim_acknowledgement
```

The capture operator, fixture reviewer, and grammar reviewer must be three
distinct named principals. Reviewers receive the protocol bytes, selector and
identity observations, target observations, exact argv/envelope, raw streams,
status/provenance objects, mutation manifests, file inventory, all digests,
and deterministic scan result. Both decisions must be `accepted`; abstention,
missing identity, self-review, partial-shape review, warning-only review, or
digest drift fails the entire corpus.

Review confirms only that the corpus is suitable input to a later grammar
phase. It does not accept a grammar or close `L05`.

## Readiness Audit

| P01 requirement | Contract state | Current input state | Result |
|---|---|---|---|
| exact native selectors | exact schema | three accepted observations absent | blocked |
| exact target sources and identities | exact rules | six target files and ordinal-073 receipt absent | blocked |
| argv, cwd, environment, timeout, caps | exact | no run requested | ready as contract |
| expected process outcomes | exact for 21 rows | no observations | ready as contract |
| raw-byte ownership and publication | exact | no raw bytes or scan result | blocked |
| corpus manifest and path schema | exact | no corpus manifest | blocked |
| deterministic negative derivation | exact | no admitted positive parents | blocked |
| independent reviewer inputs | exact | named distinct principals absent | blocked |
| local-regression nonclaim | exact | acknowledged in this phase | ready as contract |

The readiness decision is `not-ready`. Phase 789 `P02` is not authorized.

## Required Route Before Capture

A later explicit documentation-first route correction must separate and order:

1. operator-reviewed machine-policy input;
2. non-executing identity observation for the three native tools;
3. lawful target acquisition or source-build production with accepted receipts;
4. six-slot target materialization and read-back validation;
5. assignment of three distinct review principals; and only then
6. bounded native transcript capture under this protocol.

That route may not combine target production with native transcript capture or
silently admit ignored local build outputs. Phase 789 remains conditional and
cannot begin from current repository state.

## State Preserved

```text
Phase 778 ordinary operation count     102
Phase 778 operation-order digest       490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
historical Phase 779 blocker count     1469
historical Phase 779 blocked rows      102
historical Phase 779 source digest     absent
resolved Phase 780 lanes               L01-L04,L09
open Phase 780 lanes                   L05-L08,L10-L11
P01 readiness decision                 not-ready
P02 capture authorization              absent
```

No native tool, helper, test, producer, network client, Rustup, Cargo, Charon,
Aeneas, Lean, Lake, sandbox, SMT, Z3, COBALT, or kernel command ran. No attempt
root, machine policy, identity observation, target, transcript, fixture,
manifest, grammar, parser output, acceptance operation ID, or evidence record
was created.

## Source Correspondence

| Contract fact | Controlling source |
|---|---|
| Exact N21 census and L05 gate | Phase 780 resolution matrix |
| Exact outcomes and missing corpus authority | Phase 785 provenance stop |
| P01 fields, positive authority, and negative distinction | Phase 786 dependency route correction |
| Role paths and selector schema | Phase 787 executable registry |
| Native argv, bounds, environment, and sandbox prefix | Phases 774 and 776 |
| Separate streams and no reconstruction | Phase 728 identity transcript closure |
| Exact fixture identity and digest precedent | Phase 732 fixture closure |
| Packaged target digests and cleanup | Phases 667 and 669 |
| Nonqualifying built digests and cleanup | Phase 671 observation |

## Claim Boundary

Phase 788 is a capture protocol and readiness stop. It is not capture
authorization, a machine-policy instance, machine observation, executable
digest, target receipt, native-tool run, transcript, fixture corpus, grammar,
parser, acceptance operation ID, executable plan, executor binding, backend
result, generated Lean, retained kernel result, proof artifact, checker
transcript, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
action authority.

## Phase 789 Forward Result

Phase 789 subsequently replaces the unauthorized capture step with the
preparation route in
`docs/789-phase-hsai-formal-native-transcript-capture-prerequisite-route-correction.md`.
It corrects the omitted built-row wrapper observation and capture-root
prepopulation conflict, separates input materialization, capture, and grammar
authority, and moves the earliest plan-v2 boundary to Phase 801. Phase 789 runs
nothing, closes no lane, and preserves this phase's `not-ready` result and all
claim limits.
