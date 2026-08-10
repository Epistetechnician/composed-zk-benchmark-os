# Phase 796-A2S HSAI P01B Resident-Memory Supervisor Feasibility Stop

## Status

Complete as a docs-first feasibility stop. No acceptable native macOS
resident-memory enforcement primitive was established, and the available
Docker cgroup path does not preserve the current Phase 796-A3 execution
correspondence. Phase 796-A3 remains unauthorized.

State slice:
`phase-796a2s-hsai-p01b-resident-memory-supervisor-feasibility-stop`.

Classification: `P01BResidentMemorySupervisorPrerequisiteBlocked`.

Execution status: `HostFeasibilityObservationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Question

Phase 796-A2 returned a zero-gap parser audit, but the immutable Phase 796-A
boundary still requires an accepted supervisor that enforces:

```text
max_resident_bytes = 536870912
```

This slice determines whether the selected native macOS path can satisfy that
prerequisite without weakening it or silently changing execution substrates.
It does not authorize an acquisition-only attempt.

## Primary-Source Findings

Darwin does not expose `RLIMIT_RSS` as an independent resident-set
limit. Current Apple XNU
[`resource.h`](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/resource.h#L504-L512)
defines `RLIMIT_RSS` as a source-compatibility alias for
`RLIMIT_AS`. Current XNU
[`kern_resource.c`](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_resource.c#L1647-L1654)
routes that value through `vm_map_set_size_limit`, which is an
address-space limit.

Apple's archived
[`setrlimit(2)` manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setrlimit.2.html)
describes the RSS behavior as a preference under memory pressure, not a
synchronous hard rejection guaranteeing that resident bytes never cross a
threshold.

Docker documents
[`--memory`](https://docs.docker.com/engine/containers/resource_constraints/)
as a hard container memory limit implemented by the Linux cgroup controller.
Docker Desktop's
[settings documentation](https://docs.docker.com/desktop/settings-and-maintenance/settings/)
separately identifies the memory assigned to its Linux VM on macOS. This is an
available alternate containment substrate, not the selected native macOS
`/usr/bin/python3` path.

## Selected-Host Observations

Read-only host inspection observed:

```text
macOS product version = 15.7.5
macOS build = 24G624
Darwin release = 24.6.0
architecture = arm64
/usr/bin/python3 = 3.9.6
RLIMIT_AS = 5
RLIMIT_RSS = 5
RLIMIT_AS == RLIMIT_RSS = true
initial soft limit = 9223372036854775807
initial hard limit = 9223372036854775807
```

A fresh idle `/usr/bin/python3` process was observed at 1,088 KiB
RSS but 410,069,040 KiB virtual size. A direct libc request for both soft and
hard `RLIMIT_AS=536870912` failed closed:

```json
{"errno":22,"getrlimit_rc":0,"observed_hard":9223372036854775807,"observed_soft":9223372036854775807,"requested_hard":536870912,"requested_soft":536870912,"setrlimit_rc":-1}
```

This result is consistent with XNU rejecting an address-space limit lower than
the process's current virtual usage. Raising the address-space limit above the
large baseline would no longer establish a 512-MiB resident-memory ceiling.

No polling design is accepted. Sampling `proc_pid_rusage`,
`ps`, or another userspace counter and then sending a signal observes
allocation after it occurs. The process can cross the bound between samples,
so that design cannot prove the required invariant.

Local Docker inspection observed Docker Desktop 4.77.0, a Linux arm64 engine,
LinuxKit kernel 6.12.76, and cgroup v2 using the `cgroupfs` driver.
No container was launched and no image was pulled. The available hard cgroup
primitive therefore remains an unexercised alternate substrate.

## Independent Reviews

Two fresh read-only reviewers returned `accept`:

1. The native-enforcement reviewer confirmed that XNU aliases
   `RLIMIT_RSS` to `RLIMIT_AS`, the kernel applies
   address-space rather than independent resident-set control, and userspace
   polling cannot prove zero overshoot.
2. The correspondence reviewer confirmed that Docker can supply hard cgroup
   memory containment but changes the execution substrate from native macOS to
   a Linux VM/container.

The minimum acceptable native primitive would be a kernel-enforced synchronous
resident-memory or physical-footprint ceiling installed before execution,
which rejects page commitment or terminates before usage can exceed
536,870,912 bytes. No such accepted primitive was identified.

## Correspondence Consequence

Docker cannot be substituted into Phase 796-A3 by changing only an argv field.
An alternate container path would need a separate documentation-first contract
that freezes at least:

- Docker Desktop, engine, Linux kernel, cgroup, and OCI image identities;
- an immutable image digest and complete Python/runtime dependency identity;
- parser-source ingress and exact source-digest verification;
- archive ingress or an in-container downloader with its own descriptor and
  network-closure correspondence;
- `memory.max`, swap, OOM, process, filesystem, capability, and
  network controls;
- cgroup evidence such as `memory.max`, `memory.peak`, and
  `memory.events`;
- exact stdout, stderr, exit, cleanup, and container-destruction receipts; and
- a proof that the resulting parser bytes and artifact schemas remain
  equivalent to the reviewed Phase 796-A1 contract.

None of those facts is frozen or accepted here. A container route would be a
new execution-correspondence boundary, not completion of the existing native
macOS prerequisite.

## Retained Decision

The retained record is canonical compact JSON with lexicographically sorted
object keys and no trailing newline. Its digest is
`SHA-256(ASCII("hsai:p01b-resident-memory-supervisor-feasibility:v1") || 0x00 || json_bytes)`.

```json
{"acquisition_authorized":false,"decision":"blocked","docker":{"cgroup_driver":"cgroupfs","cgroup_version":2,"client_version":"29.5.3","desktop_version":"4.77.0 (228796)","engine_architecture":"arm64","engine_os":"linux","kernel_version":"6.12.76-linuxkit","server_version":"29.5.3"},"docker_substrate_correspondence_accepted":false,"evidence_ceiling":"Level1LocalReplayOrLower","host":{"architecture":"arm64","build_version":"24G624","darwin_release":"24.6.0","product_version":"15.7.5"},"native_hard_rss_enforcement_available":false,"network_run_authorized":false,"phase_796_a3_authorized":false,"polling_supervisor_accepted":false,"predecessor_commit":"eeb5228c1c1c24afc9418e99b6517047db32e245","python":{"errno":22,"executable":"/usr/bin/python3","idle_rss_kib":1088,"idle_vsz_kib":410069040,"observed_hard":"9223372036854775807","observed_soft":"9223372036854775807","requested_limit_bytes":536870912,"rlimit_alias":true,"rlimit_as":5,"rlimit_rss":5,"setrlimit_rc":-1,"version":"3.9.6"},"schema":"hsai-p01b-resident-memory-supervisor-feasibility-v1"}
```

```text
decision_sha256 = b67e4e734deb959328ebd795320e777def9b886f6d3c141f4344a94f64071fa6
decision = blocked
native_hard_rss_enforcement_available = false
polling_supervisor_accepted = false
docker_substrate_correspondence_accepted = false
phase_796_a3_authorized = false
acquisition_authorized = false
network_run_authorized = false
```

## Authority Boundary

This phase reads public primary-source documentation and local host metadata
only. It performs no archive request, archive read, download, extraction,
container run, image pull, parser run, materialization, transcript capture,
candidate generation, or accepted-bound proposal.

It creates no proof artifact, accepted evidence, Level2+ evidence, score-axis
result, semantic-correctness claim, production-readiness claim, SOTA claim,
breakthrough claim, full-security claim, external-audit claim, or action
authority. It does not close `P796-02`, Phase 780 lane
`L07`, or the complete Phase 796 stop and does not publish
`preparation_contract_sha256`.

## Next Gate

Phase 796-A3 remains blocked. The next legal request must choose and separately
authorize one of two non-equivalent routes:

1. provision and independently validate a native macOS kernel-enforced hard
   physical-footprint primitive that satisfies the frozen 512-MiB contract; or
2. define a new docs-first Linux-container acquisition correspondence boundary
   with pinned image, engine, cgroup, ingress, and receipt identities.

Neither route is authorized by this stop record.
