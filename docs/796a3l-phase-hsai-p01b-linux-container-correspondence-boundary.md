# Phase 796-A3L HSAI P01B Linux-Container Correspondence Boundary

## Status

Complete as a documentation-first blocked alternate-substrate assessment.
Independent review found ten unresolved correspondence and containment
classes. No image is accepted, no container is created or run, and no archive
acquisition is authorized.

State slice: `phase-796a3l-hsai-p01b-linux-container-correspondence-boundary`.

Classification: `P01BLinuxContainerCorrespondenceBoundaryBlocked`.

Execution status: `HostMetadataObservationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Reason for a Separate Boundary

Phase 796-A2S establishes that the selected native macOS path cannot enforce
the frozen `max_resident_bytes=536870912` contract with an accepted
hard resident-memory primitive. Docker's Linux cgroup controller can provide a
hard container memory bound, but it changes the kernel, Python runtime,
filesystem, process namespace, descriptor identities, and execution authority.

Phase 796-A3L therefore does not amend or satisfy native Phase 796-A3. Linux
`memory.max` constrains aggregate cgroup-charged memory, not the
original per-process RSS quantity. That can be a stricter containment policy,
but it is not semantically identical and is not accepted here. This assessment
records the remaining work before a separately authorized synthetic
compatibility attempt can even be requested.

## Bound Predecessors

```text
predecessor commit = a15e91bfe6c4b0ba6c7fc44c6e96f4266f910801
Phase 796-A1 parser source = ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f
Phase 796-A2 audit = 5301f672b057396791e85af8c16194617accaf40df087f9a967e4ef148d15dfb
Phase 796-A2S stop = b67e4e734deb959328ebd795320e777def9b886f6d3c141f4344a94f64071fa6
```

These identities remain local repository evidence. They do not transfer
native Python 3.9.6 behavior to another runtime.

## Observed Docker Control Plane

Read-only metadata inspection observed:

```text
client path = /Applications/Docker.app/Contents/Resources/bin/docker
client sha256 = 73206884cd100a165e20fbab2b1f9e09e0ae8fc959ec9b02fed46152a99c5e79
client version = 29.5.3
client git commit = d1c06ef
app identifier = com.docker.docker
app team identifier = 9BNSXJN65R
app cdhash = 2a2e8e550e5b9960aff328df6ae6682c8251e02c
Docker Desktop = 4.77.0 (228796)
context = desktop-linux
context socket = unix:///Users/shaanp/.docker/run/docker.sock
server version = 29.5.3
server git commit = 285b471
server API = 1.54
engine = linux/arm64
kernel = 6.12.76-linuxkit
containerd = v2.2.4
runc = 1.3.5
cgroup = v2 / cgroupfs
memory limit support = true
swap limit support = true
pids limit support = true
running containers = 0
```

These are observed candidate identities, not an accepted execution authority.
The Docker socket controls a privileged external daemon and remains outside
the parser's trust boundary.

## Local Image Candidate

No Python 3.9.6 image is present locally. Read-only image inspection found:

```text
tag = python:3.11-slim-bookworm
repo digest = python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438
config digest = sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4
platform = linux/arm64/v8
size = 155411979
PYTHON_VERSION = 3.11.15
PYTHON_SHA256 = 272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625
candidate accepted = false
```

The mutable tag is never execution authority. Any future request must use and
recheck both the repo digest and config digest. Python 3.11.15 is not the
audited native Python 3.9.6 runtime. The image may become a synthetic
compatibility candidate only after a separate phase explicitly authorizes the
run and a later independent audit accepts the results.

Docker's
[Python Official Image documentation](https://hub.docker.com/_/python/)
describes the slim image family. The
[Official Images lifecycle policy](https://github.com/docker-library/official-images)
states that removed historical tags can remain downloadable without continued
maintenance. Availability is therefore not security or maintenance evidence.

## Required Synthetic Controls

A future blocker-closure phase must freeze and verify all of these controls
before any request to start a container:

```text
pull policy = never
platform = linux/arm64/v8
image reference = repo, platform-manifest, config, and RootFS identities
entrypoint, argv, working directory, and replacement environment = exact
network mode = none
memory.max = 536870912
memory.swap.max = 0
memory.oom.group = unresolved
OOM kill disabled = false
pids limit = 16
read-only root filesystem = true
capabilities dropped = ALL
seccomp profile digest = unresolved; unconfined forbidden
AppArmor or SELinux profile and enforcement = unresolved
user namespace mode = unresolved
cgroup namespace = private
IPC namespace = none
PID, UTS, mount, and network namespaces = private
security option = no-new-privileges:true
user = 65532:65532
tmpfs target, owner, mode, flags, and 16777216-byte bound = unresolved
Docker log driver = none
stdout cap bytes = 16384
stderr cap bytes = 16384
cpu seconds = 900
file size bytes = 67108864
open file descriptors = 32
core bytes = 0
wall timeout seconds = 1800
finite CPU quota = unresolved
stdin = closed
privileged = false
Docker socket mount = forbidden
host namespace sharing = forbidden
added devices, CDI, and GPU requests = forbidden
secrets and credentials = none
```

The future driver must create, inspect, and only then start the container. It
must reject drift in `HostConfig.Memory`,
`HostConfig.MemorySwap`, `HostConfig.OomKillDisable`,
`HostConfig.PidsLimit`, `HostConfig.ReadonlyRootfs`,
`HostConfig.CapDrop`, `HostConfig.SecurityOpt`,
`HostConfig.NetworkMode`, user, namespaces, ulimits, logging, mounts,
image ID, platform manifest, rootfs, runtime, or daemon identity.

The receipt contract must bind pre-start and terminal values for
`memory.max`, `memory.swap.max`,
`memory.high`, `memory.low`, `memory.min`,
`memory.current`, `memory.peak`,
`memory.events`, `memory.swap.events`,
`memory.oom.group`, `pids.max`,
`pids.current`, `pids.events`, `cpu.max`, and
`cpu.stat`. The OOM collector, cgroup path, process topology, receipt
timing, and post-kill retention mechanism are unresolved. A result collected
after the cgroup disappears is insufficient.

The parser's existing CPU, file-size, descriptor, parser, candidate-byte, and
terminal-record limits remain mandatory inside the container. Cgroup memory
containment does not replace them.

## Expected Synthetic Compatibility Contract

Nothing in this section is an observed result. The exact test-ID set and
digest, invariant golden-byte projection, and all receipt schema digests remain
null in the retained record. A later closure phase must define them before a
synthetic run can be authorized.

The future expected outcomes are 68 focused tests, 151 complete
formal-preflight tests, 56 deterministic failure classes, zero skips, and zero
errors. Counts alone are insufficient: the clean commit, every suite-file
digest, exact discovery command, ordered test IDs, and canonical test-ID digest
must be frozen.

Complete candidate-artifact byte equality is not assumed. Python, zlib,
filesystem identities, ownership, timestamps, and inode fields can differ
across substrates. The future boundary must name each byte stream and either:

1. use a runtime whose complete identity is accepted as equivalent to the
   audited Python 3.9.6 path; or
2. freeze an invariant-field projection, reference corpus, and digest list,
   while keeping every excluded host field visible and non-authoritative.

Per-filesystem certificates must separately cover bind mounts, named volumes,
and tmpfs if permitted. They must bind same-device atomic no-replace linking,
inode and link-count correspondence, exact file/directory/parent fsync order,
crash-state validation, and a precise durability claim ceiling.

The OOM probe is not the archive parser and cannot use archive bytes. A normal
compatibility pass and an intentional OOM termination are distinct attempts
with distinct receipts. The OOM attempt must establish its collector and
cgroup-lifetime design before it can claim `State.OOMKilled=true` or
bind raw cgroup events.

## Independent Review Blockers

Two independent read-only reviews returned
`revise_before_A3L1_authorization` and
`STOP_BOUNDARY_INCOMPLETE`. Their 18 findings normalize to ten open
classes:

| ID | Unresolved class |
|---|---|
| C01 | aggregate cgroup memory versus process-RSS semantics |
| C02 | Python runtime identity and invariant golden projection |
| C03 | OOM collector topology and cgroup lifetime |
| C04 | seccomp, LSM, user namespace, and namespace identities |
| C05 | effective resource and cgroup receipts |
| C06 | tmpfs, stream, logging, CPU, and wall-time bounds |
| C07 | platform manifest, runtime dependency, and RootFS provenance |
| C08 | exact test-corpus identity |
| C09 | filesystem ingress, egress, and durability certificates |
| C10 | exact create/start argv, environment, and receipt grammar |

Every class is blocking. The reviews confirm the documentation-only stop is
sound and that no pull, container action, archive ingress, acquisition, or
evidence escalation occurred. They do not accept the boundary for execution.
After correction, both reviewers returned `accept_blocked_assessment` with zero
findings. That decision accepts this blocker record only.

## Ingress and Egress Stop

Docker Desktop crosses a macOS-to-Linux filesystem boundary. A host bind mount
does not preserve host inode or file-descriptor identity inside the Linux VM.
A named volume creates a new Linux object. Neither mechanism may be treated as
same-object correspondence by assertion.

Before any archive acquisition phase, a later boundary must select exactly one
ingress and one egress mechanism and define:

- host pre-open and post-run identities;
- container-side descriptor identity and complete SHA-256;
- byte length and read-only status;
- race-free population and freeze rules;
- filesystem and volume-driver identities;
- network-open downloader termination;
- parser container `network=none` evidence;
- transactional candidate publication and export;
- independent host reconstruction after export; and
- cleanup with no retained raw archive outside the authorized attempt root.

That cross-namespace certificate is unresolved. Synthetic tests may use only
test-owned fixture bytes and cannot close it.

## Phase Route

```text
796-A3L   this documentation-only blocked correspondence assessment
796-A3L1  future docs-only closure of all ten blocker classes
796-A3L2  future separately authorized synthetic compatibility and OOM run
796-A3L3  future clean-commit implementation and receipt audit
796-A3L4  future docs-first archive ingress/egress and acquisition decision
796-A3L5  future separately authorized acquisition-only candidate run
796-A3L6  future independent candidate review and local acceptance decision
```

No successor is implicitly authorized. A failure in any phase returns another
stop.

## Retained Boundary Record

The retained record is 4377 bytes of canonical compact JSON with
lexicographically sorted object keys and no trailing newline. Its digest is
`SHA-256(ASCII("hsai:p01b-linux-container-correspondence-boundary:v1") || 0x00 || json_bytes)`.

```json
{"accepted_evidence_authorized":false,"accepted_evidence_created":false,"archive_acquisition_authorized":false,"backend_execution_authorized":false,"candidate_image":{"accepted":false,"architecture":"arm64","config_digest":"sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4","interpreter_identity_digest":null,"local":true,"os":"linux","package_inventory_digest":null,"platform_manifest_digest":null,"python_source_sha256":"272179ddd9a2e41a0fc8e42e33dfbdca0b3711aa5abf372d3f2d51543d09b625","python_version":"3.11.15","repository_digest":"python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438","repository_tag":"python:3.11-slim-bookworm","rootfs_identity_digest":null,"size_bytes":155411979,"stdlib_tree_digest":null,"variant":"v8","zlib_identity_digest":null},"container_execution_status":"NotRun","container_run_authorized":false,"decision":"blocked","docker":{"app_cdhash":"2a2e8e550e5b9960aff328df6ae6682c8251e02c","app_identifier":"com.docker.docker","app_team_identifier":"9BNSXJN65R","cgroup_driver":"cgroupfs","cgroup_version":2,"client_git_commit":"d1c06ef","client_path":"/Applications/Docker.app/Contents/Resources/bin/docker","client_sha256":"73206884cd100a165e20fbab2b1f9e09e0ae8fc959ec9b02fed46152a99c5e79","client_version":"29.5.3","containerd_version":"v2.2.4","context":"desktop-linux","context_socket":"unix:///Users/shaanp/.docker/run/docker.sock","desktop_version":"4.77.0 (228796)","engine_architecture":"arm64","engine_os":"linux","kernel_version":"6.12.76-linuxkit","memory_limit_supported":true,"pids_limit_supported":true,"runc_version":"1.3.5","server_api_version":"1.54","server_git_commit":"285b471","server_version":"29.5.3","swap_limit_supported":true},"evidence_ceiling":"Level1LocalReplayOrLower","evidence_escalation_authorized":false,"image_pull_authorized":false,"level2_plus_authorized":false,"normalized_blockers":["aggregate-cgroup-memory-versus-process-rss-semantics","python-runtime-and-golden-projection","oom-collector-and-cgroup-lifetime","seccomp-lsm-userns-and-namespace-identity","effective-resource-and-cgroup-receipts","tmpfs-stream-logging-and-wall-time-bounds","platform-manifest-runtime-and-rootfs-provenance","test-corpus-identity","filesystem-ingress-egress-and-durability-certificates","exact-create-start-argv-environment-and-receipt-grammar"],"observed_compatibility_result":null,"parser_source_sha256":"ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f","phase_796_a2_audit_sha256":"5301f672b057396791e85af8c16194617accaf40df087f9a967e4ef148d15dfb","phase_796_a2s_stop_sha256":"b67e4e734deb959328ebd795320e777def9b886f6d3c141f4344a94f64071fa6","phase_796_a3_authorized":false,"phase_796_a3l1_compatibility_run_authorized":false,"predecessor_commit":"a15e91bfe6c4b0ba6c7fc44c6e96f4266f910801","required_compatibility_contract":{"cleanup_receipt_schema_digest":null,"container_receipt_schema_digest":null,"egress_certificate_schema_digest":null,"expected_failure_class_count":56,"expected_focused_test_count":68,"expected_formal_preflight_test_count":151,"filesystem_certificate_schema_digest":null,"ingress_certificate_schema_digest":null,"invariant_golden_projection_digest":null,"oom_receipt_schema_digest":null,"test_id_digest":null,"zero_errors_required":true,"zero_skips_required":true},"required_synthetic_controls":{"added_devices_forbidden":true,"apparmor_profile":null,"cap_drop":["ALL"],"cdi_requests_forbidden":true,"cgroupns_mode":"private","core_bytes":0,"cpu_quota_contract":null,"cpu_seconds":900,"docker_socket_mount_forbidden":true,"file_size_bytes":67108864,"gpu_requests_forbidden":true,"host_namespace_sharing_forbidden":true,"ipc_mode":"none","log_driver":"none","memory_bytes":536870912,"memory_oom_group":null,"memory_swap_bytes":536870912,"network_mode":"none","oom_kill_disable":false,"open_file_descriptors":32,"pid_mode":"private","pids_limit":16,"platform":"linux/arm64/v8","pull_policy":"never","read_only_rootfs":true,"seccomp_profile_digest":null,"security_opt":["no-new-privileges:true"],"selinux_label":null,"stderr_cap_bytes":16384,"stdout_cap_bytes":16384,"tmpfs_contract_digest":null,"user":"65532:65532","userns_mode":null,"uts_mode":"private","wall_timeout_seconds":1800},"reviewer_decisions":["revise_before_A3L1_authorization","STOP_BOUNDARY_INCOMPLETE"],"schema":"hsai-p01b-linux-container-correspondence-boundary-v1"}
```

```text
boundary_sha256 = 87fb100d4454e9cc05c1b19baf47749230324fbc9ccf32f6a150a67e2f4b0ea7
decision = blocked
container_execution_status = NotRun
candidate_image.accepted = false
image_pull_authorized = false
container_run_authorized = false
phase_796_a3l1_compatibility_run_authorized = false
phase_796_a3_authorized = false
archive_acquisition_authorized = false
backend_execution_authorized = false
accepted_evidence_created = false
accepted_evidence_authorized = false
evidence_escalation_authorized = false
level2_plus_authorized = false
```

## Authority Boundary

This phase performs metadata inspection only. It does not pull, build, create,
start, exec, stop, or remove a container. It does not access an archive, use
archive network authority, stage parser bytes into Docker, create a volume, run
tests in Docker, or generate a compatibility receipt.

It creates no candidate archive ledger, proof artifact, accepted evidence,
Level2+ evidence, score-axis result, semantic-correctness claim,
production-readiness claim, SOTA claim, breakthrough claim, full-security
claim, external-audit claim, or action authority. It does not close
`P796-02`, Phase 780 lane `L07`, or the complete Phase 796
stop and does not publish `preparation_contract_sha256`.

## Next Gate

The next legal request is a docs-only Phase 796-A3L1 blocker-closure boundary.
It must resolve all ten normalized classes, replace every null digest or
identity with exact reviewed bytes, and receive two zero-gap reviews. It still
may not run a container. Only a later separately authorized Phase 796-A3L2 may
request local synthetic normal and OOM probes. Until both decisions exist, even
the local candidate image may not be started for HSAI.
