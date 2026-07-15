# Phase 796-A3L5 HSAI P01B Retained Container Execution/Evidence Boundary

## Status

Complete as a documentation-first boundary for the missing runtime driver,
survivor collector, provenance, cross-namespace certificates, retained normal
and child-OOM attempts, and independent local correspondence decision.

State slice:
`phase-796a3l5-hsai-p01b-retained-container-execution-evidence-boundary`.

Classification: `P01BRetainedContainerExecutionEvidenceSpecified`.

Execution status: `NotRun`.

Evidence ceiling before accepted A3L9 review: `Level1LocalReplayOrLower`.

No Docker, registry, container, native-reference, or runtime action is
authorized by this documentation commit.

## Autoresearch Contract

```text
goal = close C02-C07,C09,C10 from retained normal and child-OOM observations
primary metric = independently accepted closed container-correspondence classes
direction = higher
baseline = 2/10 (C01,C08)
target = 10/10
partial credit = forbidden
implementation budget = one boundary, one implementation, one audit/rework loop
runtime budget = one native reference, one normal attempt, one child-OOM attempt
artifact root = .autoresearch/p01b-container-correspondence-2026-07-15/artifacts
git policy = kept immutable commits only
```

The target is atomic. A normal-only run, OOM-only run, incomplete bundle,
cleanup failure, missing provenance, or reviewer rejection leaves the accepted
metric at 2/10. Diagnostic coverage is not class closure.

## Bound State

```text
predecessor commit = e443797acbbd73b321253f799a84e6794c924794
predecessor tree = 93c01a428efd87d5777b7f214bd549f885a0f587
A3L4I accepted implementation = ddb1cca33954c3af98facfd3215b4157483e1c4d
A3L4I accepted tree = f9df55b7abfbe765ffc8f4310243cc0a712c8bb1
preserved dirty admission sha256 = 41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de
user authorization UTF-8 bytes = 204
user authorization sha256 = 86b44d33867eb6f466a7aac23e5872e1d3ed396deae730ef8e76ec06a521ddbd
```

The user authorization is exactly:

```text
okay let's do actual score movement requires retained normal/OOM container execution, closure of C02–C07/C09/C10, and independent correspondence acceptance. No runtime evidence was fabricated end to end
```

That instruction authorizes the bounded program below after implementation and
independent code review. It does not authorize image pulls, arbitrary network,
real archive acquisition, accepted Evidence Ledger mutation, Level2+, or any
stronger claim.

## Observed Readiness Inputs

Read-only rechecks at predecessor HEAD found no identity drift:

```text
Docker client = /Applications/Docker.app/Contents/Resources/bin/docker
Docker client sha256 = 73206884cd100a165e20fbab2b1f9e09e0ae8fc959ec9b02fed46152a99c5e79
Docker client/server = 29.5.3
Docker Desktop = 4.77.0 (228796)
context = desktop-linux
socket = unix:///Users/shaanp/.docker/run/docker.sock
kernel = 6.12.76-linuxkit
containerd = v2.2.4
runc = 1.3.5
cgroup = v2 / cgroupfs
local image index reference = python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438
local image config = sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4
local platform = linux/arm64/v8
container Python = 3.11.15
native reference interpreter = /usr/bin/python3 3.9.6
native reference interpreter sha256 = 7f30f076d0e9c38f772a76449fca9da8cf97f6a3d43b94c90a00e4f9ce7ad39e
Buildx executable = /Applications/Docker.app/Contents/Resources/cli-plugins/docker-buildx
Buildx sha256 = 9d594c8c396e02385b8de8d7594ede893a64ceebbaefb37f7fa99fcd991cf94e
Buildx version = v0.34.1-desktop.1 / c79576280a671664e17eb68da98ec3136b614aed
Docker Desktop immutable VM image sha256 = be2274863e3e008de42f38c6d746a6090b31619715a3c02b4134e1889cdbc9d9
Docker Desktop kernel sha256 = 420cd7ac96572498e74d8593f9bb3e2ed0dbf06d61dc5214be3e5c5f08763d0b
```

The local RepoDigest is an index/reference identity, not an independently
established platform-manifest digest. A3L7 must retain the raw content-
addressed index and selected platform manifest. Docker documents `image save`
as a TAR stream and `imagetools inspect` as a registry view; neither permits
relabeling a RepoDigest as a selected platform manifest. The OCI image spec
requires the platform manifest to bind a config descriptor and ordered layer
descriptors. Sources:

- <https://docs.docker.com/reference/cli/docker/image/save/>
- <https://docs.docker.com/reference/cli/docker/image/inspect/>
- <https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/>
- <https://github.com/opencontainers/image-spec/blob/main/manifest.md>

## A3L6 Implementation State Slice

The A3L5 documentation commit contains exactly the A3L5 hunks in these five
paths and no concurrent state slice:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l5-phase-hsai-p01b-retained-container-execution-evidence-boundary.md
docs/90-whole-codebase-validation-report.md
```

Concurrent Statebook hunks in the four shared navigation files and
`docs/integrations/statebook_terminal_payoff_and_trust_settlement.md` are
user-owned and must remain unstaged. The dirty admission file remains unstaged
at its bound SHA-256.

The implementation commit may add exactly:

```text
tools/hsai-formal-preflight/p01b_container_probe.py
tools/hsai-formal-preflight/p01b_container_evidence.py
tools/hsai-formal-preflight/p01b_container_execution.py
tools/hsai-formal-preflight/p01b_container_execution_tests.py
tools/hsai-formal-preflight/p01b_container_evidence_tests.py
```

It may not modify the accepted A3L4I contract, frozen corpus/profile, archive
parser, Rust source, Cargo metadata, CI, package metadata, or the dirty
admission file. Both test filenames remain outside `test_*.py`; normal formal-
preflight discovery must remain exactly 172 tests.

The following A3L6 audit commit may change exactly:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l6-phase-hsai-p01b-execution-evidence-implementation.md
docs/90-whole-codebase-validation-report.md
```

A3L6 implementation and tests must remain hermetic. They may use fake command
observations and test-owned roots but may not contact Docker, the socket, the
registry, or the network and may not create a real container.

## Frozen V2 Wire Contract

All JSON is ASCII, compact, sorted-key, finite, duplicate-key rejecting, and
newline-free. Integers reject booleans. Paths are canonical POSIX paths. Every
digest below is lowercase SHA-256. A digest is
`SHA256(ASCII(domain) || NUL || canonical_json_bytes(value))`.

| Value | Schema | Domain | Exact fields |
|---|---|---|---|
| authorization | `hsai-p01b-container-authorization-v2` | `hsai:p01b-container-authorization:v2` | `schema,authorization_id,action_sha256,policy_sha256,evidence_bundle_sha256,admission_decision_sha256,implementation_commit,implementation_tree,readiness_sha256` |
| plan | `hsai-p01b-container-plan-v2` | `hsai:p01b-container-plan:v2` | `schema,campaign_id,attempt_id,attempt_kind,authorization_sha256,implementation_commit,platform_manifest_reference,source_manifest_sha256,commands` |
| readiness plan | `hsai-p01b-container-readiness-plan-v1` | `hsai:p01b-container-readiness-plan:v1` | `schema,predecessor_commit,user_authorization_sha256,index_reference,buildx_sha256,docker_sha256,commands,selected_reference_rule` |
| readiness result | `hsai-p01b-container-readiness-result-v1` | `hsai:p01b-container-readiness-result:v1` | `schema,readiness_plan_sha256,index_observation_sha256,index_sha256,selected_descriptor,selected_reference,platform_observation_sha256,platform_sha256,local_image_observation_sha256,context_path,context_bytes,context_sha256,image_config_digest,rootfs_diff_ids,accepted,failure` |
| campaign plan | `hsai-p01b-container-campaign-plan-v1` | `hsai:p01b-container-campaign-plan:v1` | `schema,campaign_id,authorization_sha256,implementation_commit,readiness_plan_sha256,native_command,metadata_commands,normal_plan_sha256,oom_plan_sha256` |
| command | embedded | none | `ordinal,role,argv,environment,cwd,stdin_policy,stdout_cap,stderr_cap,timeout_ns,activation,expected_outcomes` |
| observation | `hsai-p01b-container-observation-v2` | `hsai:p01b-container-observation:v2` | `schema,plan_sha256,launch_ordinal,completion_ordinal,role,argv,environment,cwd,stdin_policy,executable_path,executable_sha256,started_monotonic_ns,ended_monotonic_ns,duration_ns,outcome,exit_code,signal,stdout_path,stdout_total_bytes,stdout_retained_bytes,stdout_raw_sha256,stdout_retained_sha256,stdout_cap,stdout_truncated,stderr_path,stderr_total_bytes,stderr_retained_bytes,stderr_raw_sha256,stderr_retained_sha256,stderr_cap,stderr_truncated,container_id,previous_observation_sha256` |
| receipt | `hsai-p01b-container-receipt-v2` | `hsai:p01b-container-receipt:v2` | `schema,plan_sha256,launch_ordinal,completion_ordinal,role,argv,environment,cwd,stdin_policy,executable_path,executable_sha256,started_monotonic_ns,ended_monotonic_ns,duration_ns,outcome,exit_code,signal,stdout_total_bytes,stdout_retained_bytes,stdout_raw_sha256,stdout_retained_sha256,stdout_cap,stdout_truncated,stderr_total_bytes,stderr_retained_bytes,stderr_raw_sha256,stderr_retained_sha256,stderr_cap,stderr_truncated,container_id,observation_sha256,previous_receipt_sha256,observation_class,container_action_observed,accepted_evidence_created,level2_plus_created,authority_granted` |
| certificate | `hsai-p01b-container-certificate-v2` | `hsai:p01b-container-certificate:v2` | `schema,kind,predicate_schema,authorization_sha256,implementation_commit,attempt_id,subject_manifest_sha256,observation_sha256,predicates,accepted_evidence_created,level2_plus_created,authority_granted` |
| readiness event | `hsai-p01b-container-readiness-event-v1` | `hsai:p01b-container-readiness-event:v1` | `schema,plan_sha256,attempt_id,start_launch_ordinal,stdout_path,prefix_bytes,prefix_sha256,line_offset,line_bytes,line_sha256,observed_monotonic_ns` |
| publication record | `hsai-p01b-container-publication-v1` | `hsai:p01b-container-publication:v1` | `schema,candidate_manifest_sha256,candidate_decision_sha256,staging_identity,final_identity,renamex_np_result,renamex_np_errno,parent_fsync_result,published_path` |
| manifest | `hsai-p01b-container-manifest-v2` | `hsai:p01b-container-manifest:v2` | `schema,authorization_sha256,implementation_commit,entries` |
| decision | `hsai-p01b-container-decision-v2` | `hsai:p01b-container-decision:v2` | `schema,authorization_sha256,implementation_commit,manifest_sha256,class_results,atomic_result,evidence_level,accepted_evidence_created,level2_plus_created,authority_granted` |

Manifest entries are ordered by path and contain exactly
`path,file_type,mode,link_count,bytes,sha256`; only regular mode-0600,
link-count-one files are accepted. The implementation freezes parse/serialize
round trips and golden vectors. For canonical `{}` bytes, the domains above
must respectively produce:

```text
authorization 3fdc727376e6f4186a68dc130bc9810f517b7d326e324c6d0d5c3990f8c97ed2
plan          9a1f5502ab0e31898e9f2ab4269cd42f7ac878ea8c592d75c7f66c616bf41ce5
observation   348241ba8d3b6681deec49968324f42f7d7bda851d269bd5b01c2b67c0dadb0d
receipt       6f5e6021e7d8f26ed1e28d64b619a1dfc5a69f68e8a3ea1ba689e5edbf37761e
certificate   bac9dc7e6718dc89f7a7f653017872ad3cc39d3668b6cea3c75f7ed6bd41070b
manifest      893389c936a8b6afe02318e0deee1eac6c773619776004d0bec77457f4049a22
decision      d0e1a37812c689da0ff590c1acec3cc4a8ffc12439091f440d1cbcf2a05fa99e
readiness     ecd3ac14421ba4b078c42f91fdadf5717f6892eca79e93d04912c09d42855b93
ready-result  f51af3cbf9a99aab8399fb2e43a1898be64fb26bc6d990cb2b0b3e9b05b8e7fa
campaign      b294a225bf33946eb9e8aaaa38c66992a81718eaf6582b7c040887680a34dee1
ready-event   9fa034a4f85ce636d1564d3114a191c6c3c01457dc086f34ff3ea31630070bde
publication   bf65ed0e093ace596935be674be2e00a350d7bc0d7880d053d16958d8fe2ec5d
```

Every receipt is reconstructed from its raw observation and plan. Receipt-only
or digest-only evidence is invalid. Stronger-authority booleans are always
false.

For each stream the raw file contains every byte observed before normal exit or
the first cap-overflow byte; reads are sized never to exceed `cap+1`.
`total_bytes=len(raw)`, `retained_bytes=min(total_bytes,cap)`, raw SHA hashes all
raw bytes, retained SHA hashes that prefix, and `truncated` is exactly
`total_bytes>cap`. Overflow activates process-group termination. The same
arithmetic is independently recomputed for stdout and stderr.

Certificate predicate schemas are closed. `ingress-v1` has exactly
`source_count,source_manifest_sha256,snapshot_manifest_sha256,
source_descriptor_observation_sha256,snapshot_descriptor_observation_sha256,
container_mount_read_only`. `egress-v1` has exactly
`readiness_event_sha256,start_observation_sha256,export_observation_sha256,
raw_tar_sha256,result_sha256,result_bytes,release_observation_sha256,
ordering_valid`. `cleanup-v1` has exactly
`container_id,container_name,labels_sha256,remove_observation_sha256,
cid_absence_observation_sha256,name_absence_observation_sha256,
label_absence_observation_sha256,daemon_recheck_observation_sha256,absent`.
Other predicate schemas are rejected.

Probe results are also closed. Native has exactly `schema,mode,probe_sha256,
fixture_base64,header_ledger_base64,inventory_ledger_base64,
manifest_projection,status_projection,excluded_telemetry,projection_sha256,
runtime`. Normal adds exactly `input_manifest_sha256,corpus_validation,
workload,security,cgroup_pre,cgroup_terminal,mounts,rlimits` to those native
fields. OOM has exactly `schema,mode,probe_sha256,input_manifest_sha256,
security,cgroup_pre,cgroup_terminal,mounts,rlimits,parent,child,workload` and
contains no fixture, parser, ledger, projection, or archive field. Every nested
map has the following exact keys; unknown or missing keys reject:

```text
runtime = python_version,implementation,executable,executable_chain,
  interpreter_sha256,stdlib_root,stdlib_entries,stdlib_sha256,ldd_argv,
  ldd_stdout_base64,dependencies,dependencies_sha256,zlib_compile,zlib_runtime,
  libc,os_release_base64,packages,packages_sha256
security = pid,uid,gid,uid_map_base64,gid_map_base64,status_base64,
  attr_current_base64,namespaces,oom_score_adj
cgroup snapshot = phase,path,files
mounts = mountinfo_sha256,work,shm
rlimits = cpu,fsize,nofile,core
corpus_validation = focused_test_count,full_test_count,source_file_count,
  test_id_digest
normal workload = argv,returncode,signal,stdout_base64,stderr_base64,
  discovered_count,expected_count
parent/child = pid,cgroup_path,oom_score_adj,ready,wait_signal,survived
OOM workload = barrier_sha256,allocation_bytes,child_wait_signal,
  parent_survived,local_event_deltas,terminal_processes
projection = header_ledger_sha256,inventory_ledger_sha256,
  normalized_manifest_sha256,normalized_status_sha256,projection_sha256
```

## Component Boundaries

`p01b_container_probe.py` is the only code executed inside the container and
the only code used for the native reference. Its closed modes are
`native-reference`, `normal`, and `oom-child`. Native mode writes one canonical
result to stdout. Container modes write mode-0600 `/work/result.json`, fsync it,
set mtime to zero, emit exactly
`P01B_RESULT_READY <bytes> <sha256>\n`, and wait for `SIGUSR1`. The signal
handler re-reads and hashes the file, exits zero only on equality, and otherwise
exits nonzero. The driver copies the file while the container is running and
then sends `SIGUSR1`; post-stop tmpfs copy is forbidden.

Native and normal modes generate one deterministic small gzip/USTAR fixture in
memory, run the existing transactional synthetic-candidate publisher in a
test-owned temporary root, validate the candidate, and retain exact fixture,
header-ledger, and inventory-ledger bytes. The inherited golden projection is
preserved exactly: canonical manifest JSON after removing `python_version`,
`zlib_version`, `archive_device`, `archive_inode`, `archive_mode`,
`archive_owner_uid`, `archive_link_count`, both modified-time fields, and both
changed-time fields; canonical status JSON after removing `manifest_bytes` and
`manifest_sha256`; plus exact header/inventory bytes. Removed values remain
visible telemetry. That tuple is reduced under
`hsai:p01b-container-projection:v1`. OOM mode must not import the archive
parser or read fixture bytes.

Normal mode runs the frozen 151-test complete corpus as a direct child. OOM
mode starts exactly one allocation child, writes and reads back child
`oom_score_adj=1000`, proves both PIDs share one cgroup, requires
`memory.oom.group=0`, and only then releases a 640-MiB allocation. PID 1 must
survive and observe that exact child as `SIGKILL`. Accepted local deltas are
`oom>=1`, `oom_kill=1`, and `oom_group_kill=0`; terminal `cgroup.procs`
contains only the collector. Docker terminal `State.OOMKilled` is false and
the collector/container exits zero after `SIGUSR1`. The claim is only that one
workload child was OOM-killed while its collector survived.

The probe result binds input bytes; cgroup path; raw `cgroup.procs`,
`cgroup.events`, `memory.current`, `memory.max`, `memory.swap.current`,
`memory.peak`, `memory.min`, `memory.low`, `memory.high`, `memory.swap.max`,
`memory.swap.events`, `memory.oom.group`, `memory.events`,
`memory.events.local`, `pids.current`, `pids.max`, `pids.events`, `cpu.max`,
and `cpu.stat`
snapshots; namespace links; exact `/proc/self/{uid_map,gid_map,status,attr/current}`
bytes; `/work` and `/dev/shm` mount rows; rlimits; workload/OOM outcome; and
runtime provenance. Scalar grammar is one unsigned decimal plus newline;
key/value grammar is unique ASCII key, one space, unsigned decimal, newline.
Pre-release precedes terminal and counters never decrease.

`uid_map` and `gid_map` are exactly ASCII `         0          0 4294967295\n`
as emitted by procfs and parse to the normalized tuple `(0,0,4294967295)`;
other spacing or rows reject. `attr/current` is exactly one closed byte string:
`docker-default (enforce)\n` or `unconfined\n`. Status keys are unique; UID/GID
rows contain four decimal `65532` values, capability rows are tab-separated
16-hex-digit zero, and `NoNewPrivs`, `Seccomp`, and `Seccomp_filters` are unique
decimal rows. Namespace links use exact `<kind>:[<unsigned inode>]` grammar for
`pid,uts,mnt,net,ipc,cgroup,user`; collector and child equality is checked where
required and inspect modes independently forbid host sharing.

Runtime provenance records the interpreter symlink chain and terminal binary
bytes, raw `/usr/bin/ldd` output and each absolute dependency's symlink chain
and terminal bytes, `sys.version`, `sys.implementation`, `sysconfig` paths,
stdlib regular-file inventory, zlib compile/runtime versions, `ldd --version`,
`/etc/os-release`, and canonical `dpkg-query` package rows. Every inventory row
is `path,mode,bytes,sha256`; rows are sorted, unique, retained in the raw result,
and reduced under an explicit domain digest.

`p01b_container_evidence.py` is pure-data reconstruction. It defines v2
authorization materials, normal/OOM plans, observations and receipts, strict
single-file Docker-copy TAR grammar, certificates, candidate manifest,
per-class predicates, and the atomic decision. It imports no subprocess,
socket, environment, Docker SDK, or filesystem-write surface and never trusts
a driver verdict.

`p01b_container_execution.py` is the sole host authority boundary. Its A3L7
readiness subcommand captures and digest-verifies the two registry responses,
selects exactly one `linux/arm64/v8` descriptor, and emits final authorization
and plans. Its A3L8 run subcommand permits no registry or other network. It
validates implementation identity; freezes an exact no-follow snapshot; runs
the native reference; captures client/daemon/image/runtime provenance; streams
readiness from `start --attach`; copies `/work/result.json` as raw TAR while
running; sends `SIGUSR1`; waits; removes; proves absence; publishes one
candidate; and preserves repository state.

The snapshot contains exactly the 11 frozen source files from
`p01b_container_test_corpus.json`, the corpus checker, corpus JSON, seccomp
profile, seccomp license, seccomp provenance, and the five A3L6 files: 21
regular source mode-0644 files. Each source is opened no-follow under a retained
root descriptor, copied to a sibling root, fsynced, reopened no-follow, and
rehashed. Before mounting, snapshot directories become mode 0555 and files
0444 so container UID 65532 can traverse/read but not write; the content is
non-secret. Candidate copies are separate mode-0600 payload files.

Cleanup may address only a container whose ID, name, attempt ID, authorization
root, implementation commit, and campaign labels match the durable pre-create
intent. A collision stops without cleanup. Crash recovery never resumes a
workload or reuses an authorization ID; it may inspect and remove only an exact
identity/label match and writes a failure audit whether cleanup succeeds or
fails.

The preauthorization readiness plan binds predecessor commit, user-
authorization digest, `BX` identity, `DC` identity, `INDEX`, the exact first
argv, and second and third argv placeholders resolvable only by the unique
descriptor rule. The second command is direct Buildx `PLATFORM` inspection; the
third is `P+["image","inspect","--format={{json .}}",PLATFORM]`. All three
observations bind that readiness-plan digest. Its retained result digest becomes
`authorization.readiness_sha256`. The resulting campaign plan binds the final
authorization, readiness plan/result, native command, metadata commands, and
both attempt-plan digests. Native/global metadata observations bind the
campaign-plan digest; normal/OOM lifecycle, cleanup, and absence observations
bind their respective attempt-plan digest. No observation is retroactively
assigned to a plan.

`selected_descriptor` has exactly `digest,mediaType,size,os,architecture,
variant`; `rootfs_diff_ids` is the exact ordered four-element prefixed-SHA array.
An accepted readiness result requires both raw registry observation digests,
content digests and descriptor correspondence, successful local platform
resolution to the frozen config/RootFS, and exact no-follow context bytes/digest;
then `accepted=true` and `failure=null`. Any failure emits the same schema only
to the durable failure root with `accepted=false` and one closed failure value:
`registry_failed,selection_failed,platform_digest_failed,
local_resolution_failed,context_drift,identity_drift`. A failed result cannot
enter authorization or the candidate.

## Exact Runtime Program

The symbols below are typed bindings, not implementation choices. A3L7 freezes
their ASCII values before A3L8: `DC` Docker client path, `BX` direct Buildx
path, `CFG` empty config, `HOST` socket URI, `SNAP` snapshot root, `SECCOMP`
profile path,
`INDEX=docker.io/library/python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438`, `PLATFORM`
the unique repository-qualified selected digest, `CID` the 64-hex create
output, `NAME=hsai-p01b-<campaign>-<attempt>`, `AUTH` authorization digest,
`IMPL` implementation commit, and `CAMPAIGN`/`ATTEMPT` closed identifiers.

Host environment is exactly `HOME=/nonexistent, LANG=C, LC_ALL=C,
PATH=/usr/bin:/bin, TMPDIR=TMP, TZ=UTC, DOCKER_CONFIG=CFG`, where `TMP` is the
bound attempt-private directory; cwd is `/`, stdin is a closed null descriptor.
Define `P=[DC,"--config",CFG,"--host",HOST,"--log-level","error"]` and
`CENV=["HOME=/nonexistent","LANG=C.UTF-8","LC_ALL=C.UTF-8",
"PATH=/usr/local/bin:/usr/bin:/bin","PYTHONHASHSEED=0",
"PYTHONDONTWRITEBYTECODE=1","PYTHONNOUSERSITE=1","TMPDIR=/work","TZ=UTC"]`.

A3L7 alone executes the two network reads after two zero-finding A3L6 reviews:

```text
[BX,"imagetools","inspect","--raw",INDEX]
[BX,"imagetools","inspect","--raw",PLATFORM]
P+["image","inspect","--format={{json .}}",PLATFORM]
```

`BX` is invoked directly, never through ambient Docker plugin discovery. Each
response cap is 262,144 bytes. The first response SHA-256 equals the digest in
`INDEX`; it contains exactly one `linux/arm64/v8` descriptor. The second call
uses the same repository plus that descriptor digest; response SHA-256 and
descriptor size/media type must match. A3L7 retains both raw responses, binds
the selected ref, then authorizes A3L8. A3L8 has no network command.

A3L8 roles are exact direct argv derived from the following closed templates:

```text
native:
  [/usr/bin/python3,"-B",SNAP/tools/hsai-formal-preflight/p01b_container_probe.py,
   "--mode","native-reference"]
metadata:
  [DC,"--config",CFG,"--host",HOST,"--log-level","error","version","--format={{json .}}"]
  [DC,"--config",CFG,"--host",HOST,"--log-level","error","info","--format={{json .}}"]
  [DC,"--config",CFG,"--host",HOST,"--log-level","error","image","inspect",
   "--format={{json .}}","sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4"]
pre-create absence, per attempt:
  P+["container","inspect",NAME]
  P+["container","ls","--all","--no-trunc",
   "--filter=label=hsai.p01b.campaign="+CAMPAIGN,
   "--filter=label=hsai.p01b.attempt="+ATTEMPT,"--format={{.ID}}"]
create:
  P+["container","create","--pull=never","--platform=linux/arm64/v8",
   "--name="+NAME,"--hostname=hsai-p01b","--runtime=runc","--network=none",
   "--ipc=private","--pid=private","--uts=private","--cgroupns=private",
   "--user=65532:65532","--read-only",
   "--privileged=false","--cap-drop=ALL","--security-opt=no-new-privileges:true",
   "--security-opt=seccomp="+SECCOMP,"--memory=536870912",
   "--memory-swap=536870912","--memory-swappiness=0","--oom-kill-disable=false",
   "--pids-limit=16","--cpu-period=100000","--cpu-quota=100000",
   "--ulimit=cpu=900:900","--ulimit=fsize=67108864:67108864",
   "--ulimit=nofile=32:32","--ulimit=core=0:0",
   "--tmpfs=/work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700",
   "--shm-size=1048576","--log-driver=none","--restart=no","--no-healthcheck",
   "--label=hsai.p01b.campaign="+CAMPAIGN,"--label=hsai.p01b.attempt="+ATTEMPT,
   "--label=hsai.p01b.authorization="+AUTH,"--label=hsai.p01b.implementation="+IMPL,
   "--mount=type=bind,src="+SNAP+",dst=/input,readonly,bind-propagation=rprivate",
   "--workdir=/input","--entrypoint=/usr/bin/env",PLATFORM,"-i"]+CENV+[
   "/usr/local/bin/python3","-B","tools/hsai-formal-preflight/p01b_container_probe.py",
   "--mode",ATTEMPT,"--output","/work/result.json"]
inspect-prestart/terminal:
  P+["container","inspect","--format="+INSPECT_TEMPLATE,CID]
start-attach: P+["container","start","--attach",CID]
export-running: P+["container","cp",CID+":/work/result.json","-"]
release: P+["container","kill","--signal=USR1",CID]
emergency-kill: P+["container","kill","--signal=KILL",CID]
wait: P+["container","wait",CID]
remove: P+["container","rm",CID]
absence: inspect CID; inspect NAME; label-filtered ls; then metadata version
```

`INSPECT_TEMPLATE` is one JSON array containing, in order, `Id,Name,Path,Args,
Platform,AppArmorProfile,Config.Image,Config.User,Config.Entrypoint,Config.Cmd,
Config.Env,Config.WorkingDir,Config.Hostname,Config.Healthcheck,
Config.OpenStdin,Config.Tty,Config.Labels,
HostConfig.Runtime,HostConfig.NetworkMode,HostConfig.IpcMode,
HostConfig.PidMode,HostConfig.UTSMode,HostConfig.CgroupnsMode,
HostConfig.CgroupParent,HostConfig.UsernsMode,HostConfig.ReadonlyRootfs,
HostConfig.Privileged,HostConfig.CapAdd,HostConfig.CapDrop,
HostConfig.SecurityOpt,HostConfig.Memory,HostConfig.MemorySwap,
HostConfig.MemorySwappiness,HostConfig.OomKillDisable,HostConfig.PidsLimit,
HostConfig.CpuPeriod,HostConfig.CpuQuota,HostConfig.Ulimits,HostConfig.Tmpfs,
HostConfig.ShmSize,HostConfig.LogConfig,HostConfig.RestartPolicy,
HostConfig.AutoRemove,HostConfig.Devices,HostConfig.DeviceRequests,
HostConfig.GroupAdd,Mounts,NetworkSettings.Networks,State.Status,
State.Running,State.ExitCode,State.OOMKilled,State.Error,State.Pid,
State.StartedAt,State.FinishedAt` using
literal brackets/commas and `{{json FIELD}}` for every element.

The Docker context command is intentionally absent because `CFG` is empty.
A3L7 instead opens no-follow and retains exact bytes for
`/Users/shaanp/.docker/contexts/meta/fe9c6bd7a66301f49ca9b6a70b217107cd1284598bfc254700c989b916da791e/meta.json`,
requires SHA-256 `c36db611bb2256cd052f36471538d4c8d1ff3dc36a978d325391c3813072cb2c`,
name `desktop-linux`, and the bound `HOST`. The local `image inspect PLATFORM`
must resolve without network to config ID
`sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4`, exact
platform, and exact RootFS before authorization; failure stops A3L7.

Create, prestart inspect, start, readiness, running export, release, wait,
terminal inspect, remove, CID/name absence, label absence, and daemon recheck
are closed roles. `start --attach` is launched before export and remains the
only spanning operation; its exact readiness line activates export, export
activates release, and release lets start complete. Observations chain by
`completion_ordinal`, while `launch_ordinal` must match the plan. `SIGKILL` is
activated only on timeout/stream/protocol breach. Every activation and skipped
role is receipted. Pre-create absence is
exit 1 with exact Docker-29.5.3 stderr
`Error response from daemon: No such container: <subject>\n`, empty stdout,
empty label listing, and a successful daemon version command. Post-remove uses
the same grammar plus empty CID/name/label listings and another successful
daemon version command; a generic nonzero exit is never absence proof.

At the first complete readiness newline, the executor fsyncs a readiness-event
record before export. It binds the start plan/launch ordinal, raw stdout path,
the complete prefix byte count/digest through that newline, exact line offset/
bytes/digest, and monotonic observation time. The egress certificate binds the
readiness-event digest, export observation, release observation, and completed
start observation, and requires
`start_begin <= readiness_observed <= export_begin < export_end <= release_begin
< start_end`. Reviewers re-slice the retained raw stdout prefix and reject any
mismatch or additional readiness line.

Recovery has one closed plan and no resume path. It runs `P+["container",
"inspect","--format="+INSPECT_TEMPLATE,NAME]`. Exact absence routes to the
normal name/label/daemon absence checks. Presence is mutable only when name,
CID if durable, and all four labels equal the fsynced intent. Mismatch emits a
collision receipt and stops without mutation. Exact-match running state runs
`P+["container","kill","--signal=KILL",CID]` then
`P+["container","wait",CID]`; nonrunning state emits those two roles as
`not_run`. Both route to `P+["container","rm",CID]`, CID/name absence,
label-filtered empty listing, and daemon version recheck. Completion-order
receipts cover inspect, optional kill/wait, remove, three absence roles, and
daemon recheck. Any command/cap/grammar/identity failure is terminal and leaves
the failure audit; recovery never uses `--force`, name-only removal, or an
unlabeled enumeration.

Every observation retains the complete raw stdout/stderr bytes, not only their
digests. Metadata/inspect/registry caps are 262,144 bytes, raw TAR is
16,777,216 bytes, native/result JSON is 1,048,576 bytes, and other streams are
16,384 bytes. Truncation, timeout, identity drift, or readiness mismatch stops
the run. Receipts remain `untrusted_external_candidate` with all escalation
booleans false.

## Frozen Container Controls

The A3L4 controls remain mandatory except that v2 explicitly supersedes
`ipc=none` with `ipc=private` so the bounded `/dev/shm` mount is observable:
immutable image/config, `pull=never`, `linux/arm64/v8`, runc, network none,
private IPC and cgroup namespaces, user
65532:65532, read-only rootfs, privileged false, cap-drop ALL, exact custom
seccomp, no-new-privileges, 512-MiB memory, zero swap, OOM kill enabled, 16
PIDs, one CPU, rlimits, 16-MiB `/work` tmpfs, 1-MiB shared memory, log driver
none, restart no, healthcheck disabled, closed stdin, and no TTY.

The exact targeted inspect replaces unrestricted `{{json .}}`. Every role cap,
activation, expected outcome, and the 1,800-second attempt wall bound is plan
data.

## Retained Candidate Shape

```text
candidate/
  authority/{action,policy,evidence-bundle,admission-decision,authorization-root}.json
  readiness/{preauthorization-plan,readiness-result,authorization,campaign-plan,normal-plan,oom-plan}.json
  provenance/{git,docker-desktop,docker-client,docker-daemon,docker-context,image-config,rootfs}.json
  provenance/registry/{index,platform-manifest}.{stdout,stderr,observation}
  snapshot/{source-manifest,ingress-observations,ingress-certificate}.json
  snapshot/files/<all 21 canonical relative paths>
  operations/<zero-padded ordinal>-<role>/{observation.json,stdout.bin,stderr.bin}
  reference/{native-result,projection}.json
  attempts/normal/{receipts,result,readiness-event,inspect-prestart,inspect-terminal,egress-certificate,cleanup}.json
  attempts/normal/export.tar
  attempts/oom/{receipts,result,readiness-event,inspect-prestart,inspect-terminal,egress-certificate,cleanup}.json
  attempts/oom/export.tar
  publication/prepublication-descriptor-plan.json
  candidate-manifest.json
  candidate-decision.json
```

Every command has raw stdout/stderr files, including native, metadata,
registry, lifecycle, export, cleanup, and absence commands. Raw registry bytes,
raw Docker-copy TAR bytes, exact snapshot files, and raw descriptor observations
are therefore reviewer inputs rather than driver digest assertions.

The hash graph is acyclic. `candidate-manifest.json` inventories every payload
file except itself and `candidate-decision.json`. The decision binds the
manifest digest. Reviews are outside the immutable candidate and bind both
digests. The review aggregate binds the two review digests. The final
acceptance record binds the aggregate. No later artifact is inserted back into
an earlier manifest. After exclusive rename and final-parent fsync, the driver
writes an external canonical publication record under
`artifacts/publication/<candidate-manifest-sha256>/publication-record.json`.
Both reviews, their aggregate, and final acceptance bind its domain digest.

## Strict Docker-Copy TAR Grammar

`export.tar` is at most 16,777,216 bytes and contains exactly one USTAR regular
member. Its name is `result.json`, prefix/linkname/uname/gname are empty,
typeflag is ASCII `0`, mode is `0600`, UID/GID are `65532`, size is between 1
and 1,048,576, mtime is zero, and device numbers are zero. Header checksum is
recomputed with checksum bytes treated as spaces. Magic is exactly `ustar\0`,
version is `00`, and all unused bytes are zero. Numeric fields are canonical
fixed-width ASCII octal with leading zeroes and their field-specific terminating
NUL; base-256, signed, blank, space-terminated, or noncanonical encodings are
rejected. The checksum field is exactly six octal digits, NUL, space. PAX, GNU, sparse, link,
device, directory, duplicate, and extra members are rejected. Payload padding
is zero. At least two terminal zero blocks are required; any remaining bytes
must be zero. The parser never calls `tarfile` extraction or Docker extraction.

The payload must be ASCII canonical JSON with exact mode-specific fields,
duplicate rejection, depth at most 32, nodes at most 65,536, and no trailing
newline. The readiness byte count/digest, TAR header size, retained payload,
result JSON self-digest fields, egress certificate, and raw TAR observation
must all agree.

## Descriptor And Publication Protocol

The output parent, sibling staging directory, and final candidate directory are
walked from retained directory descriptors with no-follow opens. They must be
owned by the effective UID/GID, have no symlink ancestor, reside on one device,
and not overlap the repo or snapshot. Directories are mode 0700. Files are
created with `O_CREAT|O_EXCL|O_NOFOLLOW` mode 0600 and must remain regular,
owner-matched, and link-count one after write, fsync, reopen, and rehash.

Publication is Darwin-only `renamex_np(staging, final, RENAME_EXCL)` through the
system C library with `RENAME_EXCL=0x00000004`; unavailable symbols, nonzero
return, or unexpected `errno` stop. Standard replacing `rename` is forbidden.
The order is: write/fsync/reopen every file; fsync child directories bottom-up;
fsync staging; revalidate staging and final-parent identity/device; call
`renamex_np`; fsync final parent. The evidence claims only that these calls
returned success, not physical-media power-loss durability.

Before the exclusive rename, failure cleanup removes only the exact staging
files inventoried by the driver, bottom-up, after identity rechecks. After a
successful rename, any later fsync/revalidation failure leaves an explicitly
ambiguous failure root and forbids acceptance; it never deletes the final
candidate. A durable mode-0700 failure root is created and fsynced before each
container create. It retains pre-create intent, every raw operation, first
failure, recovery decisions, cleanup observations, and staging disposition
even when no candidate is published.

## Atomic C02-C10 Acceptance

| Class | Required retained predicate |
|---|---|
| C02 | Native `/usr/bin/python3` 3.9.6 exact binary digest and normal Python 3.11.15 interpreter chain are visible; fixture, exact ledger bytes, normalized manifest, normalized status, and projection digest match; only the explicitly enumerated manifest/status fields are excluded and retained as telemetry. |
| C03 | Barrier follows `oom_score_adj=1000` readback; exactly collector/child share one cgroup; `memory.oom.group=0`; child wait status is `SIGKILL`; collector survives; local `oom>=1,oom_kill=1,oom_group_kill=0`; terminal procs contains only collector; Docker OOMKilled is false and final exit is zero. |
| C04 | Exact no-follow seccomp bytes/digest were requested; inspect's inlined seccomp JSON parses equal to the source JSON; `/proc` has `Seccomp=2`, filters at least one, `NoNewPrivs=1`; CapInh/Prm/Eff/Bnd/Amb are zero; UID/GID are 65532; uid/gid maps are exactly `0 0 4294967295\n`; PID/UTS/mount/network/IPC/cgroup namespace and inspect identities reconstruct; LSM bytes are exactly one closed value, `docker-default (enforce)\n` or `unconfined\n`, and agree with `AppArmorProfile`. |
| C05 | Inspect and both complete raw cgroup censuses prove memory max 536870912, swap max 0, memory min/low 0, high `max`, pids max 16, cpu max `100000 100000`, oom-group 0, peak at least current, monotonic event/cpu counters, zero normal memory/swap/pids event deltas, and the exact C03 OOM deltas. |
| C06 | Live `/work` tmpfs, private 1-MiB `/dev/shm`, logging, rlimits, CPU quota, closed stdin, no TTY, normal wall-time, and streams match. Hermetic A3L6 tests use real test-owned child/grandchild processes through the actual executor to prove timeout, stream-limit kill, process-group cleanup, and skipped-role receipts. No live breach claim is made. |
| C07 | Raw index/platform bytes hash to requested digests and bind ordered layers/config; local config/RootFS order matches; probe retains interpreter/dependency/stdlib/zlib/libc/package identity; host retains signed-app CDHash, direct Buildx digest/version, Docker client digest, Docker Desktop VM-image/kernel digests, daemon/containerd/runc versions and commits, OS/kernel, and architecture. |
| C09 | Exact 21-file snapshot bytes and descriptor observations reconstruct; inspect proves read-only ingress; running export TAR reconstructs strictly before controlled release/remove; `renamex_np(RENAME_EXCL)` and fsync order validate; exact container/staging absence validates. |
| C10 | Authorization and domains recompute; all commands are plan-derived; raw observations reconstruct every receipt; CID/name/labels are stable; running export precedes release/wait/remove; exact absence grammar plus empty listings and reachable-daemon recheck prove cleanup. |

C04 does not claim the kernel BPF program is byte-equivalent to the profile;
the association is descriptor-stable source bytes, exact argv path, semantic
equality with inspect's inlined JSON, process seccomp state, and an explicit
Docker-daemon honesty assumption. The A3L5 correspondence metric explicitly
resolves the formerly unknown LSM identity by retaining either enforced or
unconfined state; `unconfined` closes identity correspondence only and sets
`lsm_enforced=false`, with no LSM-enforcement or full-security claim. C07 binds the complete
Docker Desktop VM bundle plus reported containerd/runc commits, not a separately
extracted runc binary, and makes the same signed-app/daemon honesty assumption.
Either assumption failing rejects the local decision.

## Review, Keep, And Phase Route

A3L6 is kept only after two zero-finding immutable-code reviews plus new
focused tests, 21 A3L4I tests, 21 corpus tests, exactly 172 normal tests, Ruff,
Python compile/forbidden-surface scans, Rust fmt/tests/Clippy, diff hygiene,
exact five paths, and preserved admission SHA-256.

A3L8 is kept only if both attempts complete, every container and staging root
is absent, the candidate validates twice in fresh processes, repo state is
unchanged, and the dirty hash is preserved.

A3L9 review records have schema `hsai-p01b-container-review-v1`, domain
`hsai:p01b-container-review:v1`, and exact fields `schema,role,reviewer_id,
candidate_manifest_sha256,candidate_decision_sha256,implementation_commit,
publication_record_sha256,validator_sha256,reconstructed_class_results,
findings,result`. Roles are
exactly `security-capability` and `correspondence-reproducibility`; reviewer IDs
must be distinct nonempty ASCII, class results must be the ordered C02-C07/C09/
C10 set, findings are ordered strings, and result is `accept` only with no
finding and all true.

The aggregate schema/domain are `hsai-p01b-container-review-aggregate-v1` /
`hsai:p01b-container-review-aggregate:v1`; fields are `schema,
candidate_manifest_sha256,candidate_decision_sha256,implementation_commit,
publication_record_sha256,ordered_reviews,atomic_result`. Reviews sort by fixed role order. Missing,
duplicate, same-reviewer, binding-drifted, validator-drifted, finding-bearing,
or non-accept records force `reject`.

The final record schema/domain are `hsai-p01b-container-acceptance-v1` /
`hsai:p01b-container-acceptance:v1`; fields are `schema,
candidate_manifest_sha256,candidate_decision_sha256,review_aggregate_sha256,
publication_record_sha256,closed_classes,correspondence_score,evidence_level,accepted_evidence_created,
level2_plus_created,authority_granted`. Only aggregate accept permits the exact
ordered eight classes and score `10/10`; all stronger booleans remain false.
The `{}` domain vectors for review, aggregate, and final acceptance are
`56d67ce2eb94fb4e427f29a7546fd2d4978b187b018a4360eea2a3bd95bf5de8`,
`3e567f1b5c7f1138aa6dbdb35f34d37080f8c97f164457f8e8619241cabf8823`,
and `9b5ecc2778fd26744ac4e985f51d7ec94b56b4bdfb21ee855d8aadcd0d86aa0d`.

Reviews, aggregate, and final record are stored under the ignored artifact root
outside `candidate/`. Subagent review is internal procedural independence, not
external reproduction, cryptographic identity, or external audit.

```text
796-A3L5  this docs-first execution/evidence boundary
796-A3L6  hermetic implementation, immutable-code reviews, and audit
796-A3L7  two raw registry reads, exact machine/image readiness, final authorization
796-A3L8  network-disabled retained native-reference, normal, and child-OOM execution
796-A3L9  independent reconstruction and atomic local correspondence decision
```

## Score Ceiling And Stop Rules

Before A3L9 acceptance, correspondence remains 2/10, commercial moat 3/10,
and defensible breakthrough evidence 2-3/10. A zero-gap A3L9 decision on one
local host may move correspondence to 10/10 and the two estimates to at most
4/10. It remains synthetic Level 1 local evidence, not Level2, external
reproduction, benchmark evidence, semantic proof, production readiness, SOTA,
breakthrough, full security, or external audit.

Stop before runtime on any implementation, identity, manifest, seccomp, plan,
capacity, or preserved-state failure. Stop after either attempt on collector,
cgroup, projection, provenance, export, cleanup, or publication failure. Stop
acceptance on either reviewer finding. No stop converts into partial closure or
a stronger claim.
