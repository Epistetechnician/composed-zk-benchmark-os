# Phase 796-A3L1 HSAI P01B Linux-Container Contract Closure Stop

## Status

Complete as a documentation-only closure attempt with a retained blocked
decision. One of the ten Phase 796-A3L classes closes at the documentation
layer. Nine remain open because their authoritative values require a new
collector, supervisor, security profile, snapshot builder, receipt parser, or
runtime observation.

State slice: `phase-796a3l1-hsai-p01b-linux-container-contract-closure-stop`.

Classification: `P01BLinuxContainerContractClosureBlocked`.

Execution status: `ReadOnlyMetadataAndTestDiscoveryOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

No image was pulled or built. No container was created, started, executed,
copied from, killed, or removed. No archive was requested or read. No backend,
Lean, SMT, Z3, or COBALT execution occurred.

## Bound Predecessor

```text
predecessor commit = 96ab928bb086eb47ecb9ae2724b4514affea3f5f
Phase 796-A3L boundary = 87fb100d4454e9cc05c1b19baf47749230324fbc9ccf32f6a150a67e2f4b0ea7
Phase 796-A1 parser source = ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f
Phase 796-A2 audit = 5301f672b057396791e85af8c16194617accaf40df087f9a967e4ef148d15dfb
Phase 796-A2S stop = b67e4e734deb959328ebd795320e777def9b886f6d3c141f4344a94f64071fa6
```

The dirty `crates/hsai-agent-admission/src/lib.rs` state slice is unrelated.
Its SHA-256 remained
`41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de`.

## Read-Only Image Recheck

The candidate remains local and unaccepted. Read-only inspection by config ID
resolved the tag-resolution ambiguity and added the RootFS diff-ID sequence:

```text
repository digest = python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438
config digest = sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4
RootFS[0] = sha256:3bfd0b5a99a1f25a488230217defd5c2781ad861f692f5df22d9734bbddfc53d
RootFS[1] = sha256:e3866ac24baf965b1d6445dab2a6697dc8c5e633e961cdeb8664e947af0afcd8
RootFS[2] = sha256:58c826d6f8b6c49949dcff1a49bcc504e95bdd68a1e7822c397599576ca5842e
RootFS[3] = sha256:4a0f4c378bc5afc903ba2f580dd5e0a2e45fb6599e4635133e6662c7acad0e7a
platform = linux/arm64/v8
Python = 3.11.15
candidate accepted = false
```

The platform-manifest digest, ordered compressed-layer descriptors, package
inventory, interpreter and ELF dependency closure, standard-library tree,
zlib identity, and runtime binary digest remain absent. A repo digest, config
digest, and diff IDs do not close runtime provenance.

The daemon reports `name=seccomp,profile=builtin` and `name=cgroupns`. It does
not expose the built-in seccomp profile bytes or an effective LSM profile
digest through ordinary image or daemon inspection. Those values remain open;
`seccomp=unconfined` is forbidden.

## Candidate Test-Corpus Identity

Phase 796-A3L reviewer C08 advances but does not close. The historical A2 argv
was not retained. The candidate facts below are reproducible, but the retained
record does not yet bind the full ordered-ID payload, suite/source manifest,
discovery-checker identity, replacement environment, and clean-tree identity.

| Suite | IDs | SHA-256 |
|---|---:|---|
| `test_bounded_runner.py` | 12 | `9c392c9b6b0804eeed730c03f35743176bc51e9953c6496f8888c32d7bc46e6a` |
| `test_execution_state_machine.py` | 53 | `de805bfb3ca08856dd2a13e2759686b24031d0aa82ff39ce888434e570aa81c6` |
| `test_fixture_validator.py` | 13 | `c6ec9bcd6e79d823e2cd2f4c7ea16c6f1cce908e6195606290efb42fbb2122c1` |
| `test_p01b_archive_ledger.py` | 68 | `0ae3a2b348e491af7d2b362272255b0bd278961f4a4b7ca24718a4470692f81b` |
| `test_raw_archive_validator.py` | 5 | `48e15976ba9a1dcbb86e1d5adc400a41dba328ebea1f156c5f0469e6a9ebdc77` |

Discovery loads tests without running them, recursively flattens
`unittest.TestSuite`, requires ASCII and unique `TestCase.id()` values, requires
lexicographic order, and independently reconstructs the same IDs from the
Python AST. The canonical payload is compact sorted-key ASCII JSON with no
trailing newline:

```text
schema = hsai-p01b-test-corpus-v1
focused IDs = 68
full IDs = 151
canonical bytes = 23610
focused ID-array sha256 = 43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543
full ID-array sha256 = 87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8
test_id_digest = 1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726
```

The digest domain is
`SHA-256(ASCII("hsai:p01b-test-corpus:v1") || 0x00 || json_bytes)`.

The proposed future container argv, if separately adopted and authorized after
implementation and audit, is:

```json
["/usr/local/bin/python3","-B","-m","unittest","discover","-s","tools/hsai-formal-preflight/tests","-p","test_p01b_archive_ledger.py"]
```

and:

```json
["/usr/local/bin/python3","-B","-m","unittest","discover","-s","tools/hsai-formal-preflight/tests","-p","test_*.py"]
```

The working directory is the read-only clean repository snapshot root. The
expected counts remain 68 focused and 151 complete, with zero skips and zero
errors. These candidate values do not authorize either command or close C08.

## Aggregate-Memory Claim

Reviewer C01 closes only by changing the synthetic claim to the quantity Linux
cgroup v2 actually controls:

```text
aggregate cgroup memory.max = 536870912
aggregate cgroup memory.swap.max = 0
per-process RSS ceiling claim = forbidden
exact never-exceeds-536870912 claim = forbidden
native-macOS correspondence claim = forbidden
```

The [Linux cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)
defines `memory.max` as a hard limit while allowing temporary overage in some
circumstances. A later accepted receipt may support only bounded aggregate
cgroup containment under the observed kernel and runtime. It cannot satisfy
the original native per-process RSS contract by renaming the metric.

## Proposed Frozen Controls

These are required future inputs, not observed effective values and not run
authority:

```text
image = immutable config ID plus separately rechecked platform manifest
pull = never
platform = linux/arm64/v8
runtime = runc
network = none
IPC = none
cgroup namespace = private
user = 65532:65532
root filesystem = read-only
privileged = false
capabilities dropped = ALL
no-new-privileges = true
memory = 536870912
memory-swap total = 536870912
memory swappiness = 0
OOM kill disabled = false
pids = 16
CPU period = 100000 microseconds
CPU quota = 100000 microseconds
RLIMIT_CPU = 900:900
RLIMIT_FSIZE = 67108864:67108864
RLIMIT_NOFILE = 32:32
RLIMIT_CORE = 0:0
tmpfs = /work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700
shared memory = 1048576
Docker log driver = none
stdout cap = 16384
stderr cap = 16384
wall timeout = 1800 seconds
restart = no
healthcheck = disabled
stdin = closed
TTY = false
```

Docker's [resource-constraint](https://docs.docker.com/engine/containers/resource_constraints/),
[container-run](https://docs.docker.com/reference/cli/docker/container/run/),
and [seccomp](https://docs.docker.com/engine/security/seccomp/) documentation
remain references, not evidence that these proposed values were enforced.

## Non-Executable Command Grammar

The future implementation must build argv arrays directly. It may not invoke a
shell. Every placeholder below is a typed unresolved input; the template is
non-executable until all placeholders and their schema digests are committed
and independently audited.

```text
D = /Applications/Docker.app/Contents/Resources/bin/docker
    --config ${EMPTY_DOCKER_CONFIG_ABS}
    --host unix:///Users/shaanp/.docker/run/docker.sock
    --log-level error

D container create
  --pull=never --platform=linux/arm64/v8
  --name=hsai-p01b-${ATTEMPT_ID} --hostname=hsai-p01b
  --runtime=runc --network=none --ipc=none --cgroupns=private
  --user=65532:65532 --read-only --privileged=false
  --cap-drop=ALL
  --security-opt=no-new-privileges:true
  --security-opt=seccomp=${SECCOMP_PROFILE_ABS}
  --memory=536870912 --memory-swap=536870912
  --memory-swappiness=0 --oom-kill-disable=false
  --pids-limit=16 --cpu-period=100000 --cpu-quota=100000
  --ulimit=cpu=900:900 --ulimit=fsize=67108864:67108864
  --ulimit=nofile=32:32 --ulimit=core=0:0
  --tmpfs=/work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700
  --shm-size=1048576 --log-driver=none --restart=no --no-healthcheck
  --mount=type=bind,src=${CLEAN_CORPUS_ROOT_ABS},dst=/input,readonly,bind-propagation=rprivate
  --workdir=/input --entrypoint=/usr/bin/env
  ${PINNED_PLATFORM_MANIFEST_REFERENCE}
  -i HOME=/nonexistent LANG=C.UTF-8 LC_ALL=C.UTF-8
  PATH=/usr/local/bin:/usr/bin:/bin PYTHONHASHSEED=0
  PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 TMPDIR=/work TZ=UTC
  ${WORKLOAD_ARGV...}

D container inspect --format={{json .}} ${CID}
D container start --attach ${CID}
D container wait ${CID}
D container inspect --format={{json .}} ${CID}
D container rm ${CID}
```

On stream-cap or wall-time breach, the future supervisor must issue exactly:

```text
D container kill --signal=KILL ${CID}
```

Cleanup after every success or failure is mandatory. A later artifact-export
contract would require a separately specified stopped-container copy, host
reconstruction, transactional publication, and cleanup sequence. None is
authorized here.

## Receipt and Collector Contract

The future command receipt must bind schema, ordinal, exact argv array, Docker
executable SHA-256, closed host environment, working-directory identity, stdin
policy, monotonic start and end, wall duration, exit status, signal, complete
stdout and stderr lengths and SHA-256 values, truncation flags, container ID,
and predecessor-receipt digest.

The future cgroup collector must retain exact raw bytes and parsed values at
`pre_workload` and `terminal` for:

```text
cgroup.events
cgroup.procs
memory.current
memory.peak
memory.min
memory.low
memory.high
memory.max
memory.swap.current
memory.swap.max
memory.events
memory.events.local
memory.swap.events
memory.oom.group
pids.current
pids.max
pids.events
cpu.max
cpu.stat
```

Normal compatibility requires exit zero, `State.OOMKilled=false`, and zero OOM
event deltas. An OOM probe is a distinct synthetic attempt. Its collector
topology, readiness barrier, victim selection, cgroup path, terminal-file
retention, and acceptance grammar remain unresolved. Missing terminal raw bytes
rejects the attempt.

## Golden Projection Boundary

The focused suite emits host-bearing manifest fields. Cross-substrate equality
must therefore compare:

- exact header-ledger bytes;
- exact inventory-ledger bytes;
- manifest canonical JSON after removing `python_version`, `zlib_version`,
  `archive_device`, `archive_inode`, `archive_mode`, `archive_owner_uid`,
  `archive_link_count`, both modified-time fields, and both changed-time fields;
- status canonical JSON after removing `manifest_bytes` and `manifest_sha256`;
  and
- the removed values as visible non-authoritative telemetry.

No retained native reference candidate exists from Phase 796-A2, so the native
projected-reference digest remains null. C02 stays open until a separately
authorized implementation produces and independently validates that reference.

## Closure Matrix

| Class | A3L1 result | Reason |
|---|---|---|
| C01 | closed for docs | Claim is aggregate cgroup containment only; RSS equivalence is forbidden. |
| C02 | open | Projection is defined, but native reference and runtime identities are absent. |
| C03 | open | No audited collector topology or terminal cgroup-byte retention. |
| C04 | open | Seccomp bytes, LSM enforcement, user mapping, and namespace receipts are absent. |
| C05 | open | Receipt fields are defined, but schema and parser are unimplemented. |
| C06 | open | Supervisor, stream kill, timeout, tmpfs, and CPU enforcement tests are absent. |
| C07 | open | Platform manifest and complete runtime provenance are absent. |
| C08 | open | Candidate suite bytes and ID digests exist, but the canonical corpus artifact and checker identity are absent. |
| C09 | open | Snapshot ingress, export, reconstruction, fsync, and cleanup certificates are absent. |
| C10 | open | Typed placeholders, parsers, state machine, and exceptional receipts are unimplemented. |

The one documentation closure does not authorize execution. The nine open
classes prevent Phase 796-A3L2 implementation authorization and every later
run.

After correction, both independent re-reviews returned
`accept_blocked_assessment` with zero findings. That decision accepts this
blocked record only; it does not accept the candidate corpus or any execution
contract.

## Retained Stop Record

The retained record is 2738 bytes of canonical compact JSON with
lexicographically sorted object keys and no trailing newline. Its digest is
`SHA-256(ASCII("hsai:p01b-linux-container-contract-closure-stop:v1") || 0x00 || json_bytes)`.

```json
{"accepted_evidence_authorized":false,"accepted_evidence_created":false,"archive_acquisition_authorized":false,"backend_execution_authorized":false,"candidate_image":{"config_digest":"sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4","inspectable_by_config_id":true,"platform_manifest_digest":null,"repository_digest":"python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438","rootfs_diff_ids":["sha256:3bfd0b5a99a1f25a488230217defd5c2781ad861f692f5df22d9734bbddfc53d","sha256:e3866ac24baf965b1d6445dab2a6697dc8c5e633e961cdeb8664e947af0afcd8","sha256:58c826d6f8b6c49949dcff1a49bcc504e95bdd68a1e7822c397599576ca5842e","sha256:4a0f4c378bc5afc903ba2f580dd5e0a2e45fb6599e4635133e6662c7acad0e7a"],"runtime_identity_complete":false},"closed_documentation_classes":["C01"],"container_execution_status":"NotRun","container_run_authorized":false,"decision":"blocked","evidence_ceiling":"Level1LocalReplayOrLower","evidence_escalation_authorized":false,"image_pull_authorized":false,"level2_plus_authorized":false,"open_classes":["C02","C03","C04","C05","C06","C07","C08","C09","C10"],"phase_796_a3_authorized":false,"phase_796_a3l2_implementation_authorized":false,"phase_796_a3l5_run_authorized":false,"phase_796_a3l_boundary_sha256":"87fb100d4454e9cc05c1b19baf47749230324fbc9ccf32f6a150a67e2f4b0ea7","predecessor_commit":"96ab928bb086eb47ecb9ae2724b4514affea3f5f","required_controls":{"cap_drop":["ALL"],"cgroupns":"private","core_bytes":0,"cpu_period_us":100000,"cpu_quota_us":100000,"cpu_seconds":900,"file_size_bytes":67108864,"ipc":"none","log_driver":"none","memory_bytes":536870912,"memory_swap_total_bytes":536870912,"memory_swappiness":0,"network":"none","nofile":32,"oom_kill_disable":false,"pids_limit":16,"platform":"linux/arm64/v8","pull_policy":"never","read_only_rootfs":true,"runtime":"runc","security_opt":["no-new-privileges:true"],"shm_bytes":1048576,"stderr_cap_bytes":16384,"stdout_cap_bytes":16384,"tmpfs_bytes":16777216,"user":"65532:65532","wall_timeout_seconds":1800},"schema":"hsai-p01b-linux-container-contract-closure-stop-v1","test_corpus_candidate":{"focused_count":68,"focused_id_array_sha256":"43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543","full_count":151,"full_id_array_sha256":"87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8","test_id_digest":"1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726"},"unresolved_digests":{"collector_identity":null,"egress_certificate_schema":null,"golden_projection":null,"ingress_certificate_schema":null,"lsm_profile":null,"package_inventory":null,"platform_manifest":null,"receipt_schema":null,"runtime_dependency_closure":null,"seccomp_profile":null,"supervisor_identity":null}}
```

```text
closure_stop_sha256 = 458d1d7c0688f45920d5308fa6670ef5f0ec2e6a4a30da6cd52af31424c3bb12
decision = blocked
closed_documentation_classes = C01
open_classes = C02,C03,C04,C05,C06,C07,C08,C09,C10
container_execution_status = NotRun
phase_796_a3l2_implementation_authorized = false
phase_796_a3l5_run_authorized = false
backend_execution_authorized = false
accepted_evidence_authorized = false
level2_plus_authorized = false
```

## Corrected Route

The Phase 796-A3L route is superseded by the following fail-closed sequence:

```text
796-A3L1  this docs-only closure attempt and stop
796-A3L2  future docs-first collector/supervisor/profile/corpus/certificate boundary
796-A3L3  future implementation plus hermetic adversarial and synthetic-C09 tests
796-A3L4  future clean-commit implementation, receipt, and synthetic-C09 audit
796-A3L5  future separately authorized synthetic-run decision
796-A3L6  future compatibility and OOM attempts, if A3L5 authorizes them
796-A3L7  future independent run review and correspondence decision
796-A3L8  future real-archive ingress/egress and acquisition boundary only
```

No successor is implicitly authorized. Phase 796-A3L2 must remain docs-first
and may only define a minimal implementation state slice, schema digests,
hermetic tests, and stop rules. It may not run a container.

## Claim Boundary

Phase 796-A3L1 is not a compatibility run, OOM result, image acceptance,
runtime-provenance result, sandbox result, archive acquisition, parser run,
backend execution, Lean/SMT/Z3/COBALT run, proof artifact, checker transcript,
accepted evidence, Level2+ evidence, score-axis result, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
action authority.
