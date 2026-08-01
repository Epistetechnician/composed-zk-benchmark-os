# Phase 796-A3L4 HSAI P01B Portable Authorization Receipt Boundary

## Status

Complete as a documentation-only boundary for one non-executing command and
receipt contract implementation. No Docker command, container, network,
archive, backend, or evidence mutation is authorized.

State slice:
`phase-796a3l4-hsai-p01b-portable-evidence-carrying-authorization-receipt-boundary`.

Decision: `authorize_local_container_command_receipt_contract_only`.

Execution status: `DocumentationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Optimization Contract

The commercial hypothesis is a portable evidence-carrying authorization
conformance receipt: a future buyer-shaped action may be admitted only when the
handoff is digest-bound to the exact action, policy, evidence, execution
contract, and observed receipt. The transferable format should compose with
existing OCI identities and established provenance envelopes rather than claim
a proprietary provenance standard. Relevant public specifications include the
[OCI image specification](https://github.com/opencontainers/image-spec), the
[in-toto Statement](https://in-toto.io/Statement/v1), and
[SLSA provenance](https://slsa.dev/spec/v1.2/provenance).

This phase does not establish that commercial moat. It freezes only the first
local implementation seam needed to make future execution receipts typed and
independently inspectable.

Mechanical metric:

```text
metric = closed_container_correspondence_classes
baseline = 2/10 (C01,C08)
result after the authorized implementation = 2/10 (unchanged)
direction = higher
```

No documentation-only or pure-data change moves the correspondence metric.
Phase 796-A3L4I instead has one separate binary readiness metric:

```text
c10_local_contract_implemented = false -> true
```

C10 remains open until a separately authorized retained execution produces
receipts and an independent audit accepts their correspondence. C02-C07 and
C09 remain open.

## Bound Predecessors

```text
predecessor commit = 2011e1289109665ebabc9de067f374c3c3e87264
predecessor tree = da3d6b0a887b808b8dbecc49717f29ec0ac4e0a5
Phase 796-A3L boundary = 87fb100d4454e9cc05c1b19baf47749230324fbc9ccf32f6a150a67e2f4b0ea7
Phase 796-A3L1 stop = 458d1d7c0688f45920d5308fa6670ef5f0ec2e6a4a30da6cd52af31424c3bb12
Phase 796-A3L2 boundary = a9e43d8d354759f7a55f45b9ef650e3e36c108dc3d30f09844b1cd3688c29f8a
Phase 796-A3L3 implementation commit = 0d67de690625fb47b26c3b47f7cc195ec2adfc7c
Phase 796-A3L3 implementation tree = 3c81b177f66ade993862810df8d1174f05927c18
Phase 796-A3L3 audit record = 553198b652366919d42fcaa80409f21f14bec2755c18a305c8d0b8576d7adabf
Phase 796-A3L3 phase-note sha256 = 0b75ec56c570752fb461e20095b874c927563b9915b542b499bf8b29e739d398
preserved dirty admission sha256 = 41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de
```

The admission edit is user-owned and outside this state slice. A3L4I must not
read it as authority, format it, edit it, stage it, or include it in a commit.

## Documentation State Slice

This boundary changes only:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l4-phase-hsai-p01b-portable-authorization-receipt-boundary.md
docs/90-whole-codebase-validation-report.md
```

It changes no Python, Rust, Cargo, corpus, profile, fixture, package, CI,
generated artifact, or accepted-evidence file.

## Authorized A3L4I State Slice

The implementation commit may add exactly:

```text
tools/hsai-formal-preflight/p01b_container_contract.py
tools/hsai-formal-preflight/tests/p01b_container_contract_tests.py
```

The following audit/documentation commit may change exactly:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l4i-phase-hsai-p01b-container-command-receipt-contract-implementation.md
docs/90-whole-codebase-validation-report.md
```

The implementation test filename intentionally does not match `test_*.py`.
The frozen Phase 796-A3L3 future-workload corpus remains 151 tests and normal
formal-preflight discovery remains 172 tests. A3L4I runs its tests explicitly.

## Allowed Python Surface

`p01b_container_contract.py` is a pure-data contract module. It may use only
standard-library data, hashing, strict JSON, regular-expression, and typing
facilities. Its public surface is limited to:

```text
ContainerContractError
AuthorizationRoot
PlaceholderBindings
ContainerCommand
ContainerCommandPlan
CommandReceipt
AttemptState
canonical_json_bytes
domain_sha256
validate_authorization_root
validate_placeholder_bindings
build_container_command_plan
validate_container_command_plan
next_container_command
parse_command_receipt
validate_command_receipt
validate_receipt_chain
advance_attempt_state
```

The module may define immutable supporting enums, constants, and private
helpers needed by those functions. It may not expose a CLI, runner, transport,
Docker client, filesystem writer, environment loader, dynamic import, or
network surface.

## Authorization Root

The caller-supplied immutable `AuthorizationRoot` contains exactly:

```text
schema = hsai-p01b-portable-authorization-root-v1
authorization_id
action_sha256
policy_sha256
evidence_bundle_sha256
admission_decision_sha256
```

Every digest is 64 lowercase hexadecimal characters. The command plan binds
the canonical authorization-root digest, and every receipt binds both that
authorization-root digest and the command-plan digest. These are caller-
supplied identities only. A3L4I does not load or evaluate the dirty admission
source, does not decide admission, and does not grant authority.

## Exact Command Roles And Argv

The normal plan is ordered exactly:

```text
create
inspect-prestart
start-attach
wait
inspect-terminal
remove
```

Only a timeout, stdout-cap, or stderr-cap breach during `start-attach`, after
successful creation, stable container-id capture, and successful pre-start
inspection, requires `kill` before wait, terminal inspection, and removal.
Start is invalid before successful creation and pre-start inspection. Removal
is mandatory after a stable container id exists. A removal failure is a
terminal nonacceptance, not successful cleanup.

The only endpoint mechanism is the explicitly bound `--host` URI below.
`--config` names one caller-owned absolute empty Docker-config root so ambient
Docker configuration cannot add authority. `HOME` is not used for endpoint or
configuration discovery.

The prefix is exactly:

```text
${DOCKER_EXE}
--config
${EMPTY_DOCKER_CONFIG_ABS}
--host
${DOCKER_HOST_URI}
--log-level
error
```

`create` appends exactly this ordered array:

```text
container
create
--pull=never
--platform=linux/arm64/v8
--name=hsai-p01b-${ATTEMPT_ID}
--hostname=hsai-p01b
--runtime=runc
--network=none
--ipc=none
--cgroupns=private
--user=65532:65532
--read-only
--privileged=false
--cap-drop=ALL
--security-opt=no-new-privileges:true
--security-opt=seccomp=${SECCOMP_PROFILE_ABS}
--memory=536870912
--memory-swap=536870912
--memory-swappiness=0
--oom-kill-disable=false
--pids-limit=16
--cpu-period=100000
--cpu-quota=100000
--ulimit=cpu=900:900
--ulimit=fsize=67108864:67108864
--ulimit=nofile=32:32
--ulimit=core=0:0
--tmpfs=/work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700
--shm-size=1048576
--log-driver=none
--restart=no
--no-healthcheck
--mount=type=bind,src=${CLEAN_CORPUS_ROOT_ABS},dst=/input,readonly,bind-propagation=rprivate
--workdir=/input
--entrypoint=/usr/bin/env
${PINNED_PLATFORM_MANIFEST_REFERENCE}
-i
HOME=/nonexistent
LANG=C.UTF-8
LC_ALL=C.UTF-8
PATH=/usr/local/bin:/usr/bin:/bin
PYTHONHASHSEED=0
PYTHONDONTWRITEBYTECODE=1
PYTHONNOUSERSITE=1
TMPDIR=/work
TZ=UTC
${FROZEN_WORKLOAD_ARGV}
```

`FROZEN_WORKLOAD_ARGV` is exactly either the `focused.argv` or `full.argv`
array from the Phase 796-A3L3 canonical corpus; arbitrary workload argv is not
accepted.

The remaining role templates append exactly:

```text
inspect-prestart = container inspect --format={{json .}} ${CREATED_CONTAINER_ID}
start-attach = container start --attach ${CREATED_CONTAINER_ID}
kill = container kill --signal=KILL ${CREATED_CONTAINER_ID}
wait = container wait ${CREATED_CONTAINER_ID}
inspect-terminal = container inspect --format={{json .}} ${CREATED_CONTAINER_ID}
remove = container rm ${CREATED_CONTAINER_ID}
```

`${CREATED_CONTAINER_ID}` is the sole runtime placeholder. It must be absent
before a successful create receipt, must equal the one captured stable id
after creation, and must be resolved by `next_container_command` before a
command becomes executable. A returned command may contain no placeholder.

The plan uses direct argv arrays only. It binds:

- one absolute Docker executable and its SHA-256;
- one explicit Docker context/config endpoint identity;
- the pinned platform-manifest reference and image config digest;
- the Phase 796-A3L3 seccomp, corpus, source-manifest, and test-id digests;
- caller-supplied typed absolute roots and host URI;
- the exact A3L1 create controls and ordering;
- the frozen container environment from A3L3; and
- a closed host environment allowlist.

Shells, empty arguments, NUL bytes, relative paths, path aliases, inherited
environment keys, and any placeholder in a command returned for execution
reject.

## Host And Container Environment

The host client environment is exactly:

```text
HOME=/nonexistent
LANG=C
LC_ALL=C
PATH=/usr/bin:/bin
TMPDIR=<typed attempt-owned absolute path>
TZ=UTC
```

The container environment remains the A3L3 corpus value. A3L4I may not derive
either environment from the running process.

## Receipt Contract

Each receipt is canonical ASCII JSON with sorted keys and no unknown,
duplicate, missing, or noncanonical fields. Booleans do not satisfy integer
fields. A receipt binds:

- schema, ordinal, role, exact argv, exact environment, and cwd identity;
- Docker executable path and digest;
- monotonic start, end, and exact duration;
- mutually exclusive exit-code and signal outcomes;
- complete stdout/stderr lengths, SHA-256 values, caps, and truncation flags;
- one stable container id after creation;
- predecessor-receipt digest; and
- explicit nonexecution and authority booleans.

`not_run` carries no observation. A create failure has no stable container id;
all later roles are `not_run`, removal is forbidden, and the typed terminal
state is `cleanup_not_applicable_no_container_created`. A pre-start inspection
failure forbids start, kill, wait, and terminal inspection but requires remove
because a stable container id exists. A successful `start-attach` path forbids
kill. A bounded `start-attach` breach requires kill, then wait, terminal
inspection, and removal. Wait or terminal-inspection failure is terminal
nonacceptance with best-effort removal and does not invent a kill. No transition
is legal after successful or failed cleanup.

## Required Failure Taxonomy

A3L4I must reject at least:

```text
MalformedCanonicalJson
UnknownOrMissingField
InvalidPlaceholderBinding
UnresolvedPlaceholder
CommandOrderDrift
ArgvDrift
EnvironmentDrift
IdentityDigestDrift
ReceiptRoleOrOrdinalDrift
ReceiptChainDrift
ContainerIdentityDrift
TimestampOrDurationDrift
ExitSignalConflict
StreamDigestOrCapDrift
MissingRequiredKill
UnexpectedKill
KillWithoutStartedContainer
MissingCleanup
TransitionAfterCleanup
FabricatedNotRunObservation
AuthorityEscalationAttempt
```

## Verification And Keep Rule

The focused implementation gate is:

```text
/usr/bin/python3 -B -m unittest \
  tools/hsai-formal-preflight/tests/p01b_container_contract_tests.py -v
```

The guard set is:

```text
/usr/bin/python3 -B -m unittest \
  tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py -v
/usr/bin/python3 -B -m unittest discover \
  -s tools/hsai-formal-preflight/tests -p 'test_*.py'
ruff check \
  tools/hsai-formal-preflight/p01b_container_contract.py \
  tools/hsai-formal-preflight/tests/p01b_container_contract_tests.py
cargo fmt --all -- --check
cargo test --workspace --all-features \
  --exclude hsai-agent-admission --exclude hsai-e2e-harness --quiet
cargo clippy --workspace --all-targets --all-features \
  --exclude hsai-agent-admission --exclude hsai-e2e-harness \
  -- -D warnings
git diff --check
```

Keep only if focused tests have zero failures, errors, and skips; normal
discovery remains exactly 172 tests; two independent reviewers accept the
immutable implementation commit with zero findings; exact changed paths hold;
and the dirty admission SHA-256 is unchanged. Otherwise rework or revert the
implementation candidate.

## Stop Rules

A3L4I stops before:

- importing or calling `subprocess`, `socket`, Docker SDKs, or network APIs;
- reading process environment as authority;
- filesystem writes or materialized receipts;
- Docker inspection, socket access, image action, or container action;
- archive access, backend execution, or proof generation;
- changes to C02-C09 semantics or status;
- A3L5 run authorization; or
- accepted evidence, Level2+, score axes, stronger claims, or action authority.

## Residual Gate

Even a green A3L4I changes only
`c10_local_contract_implemented=false` to `true`; correspondence class C10
remains open. The remaining runtime-coupled classes require a later docs-first
driver, probe, effective-receipt, provenance, and certificate boundary. A
retained normal and OOM run requires another explicit decision after those
controls are implemented and independently audited.

## Claim Boundary

This boundary is not a receipt observation, container run, containment result,
runtime-provenance result, filesystem certificate, archive acquisition,
backend run, proof artifact, accepted evidence, Level2+ evidence, score-axis
result, independent reproduction, commercial moat, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
action authority.
