# Phase 796-A3L5D HSAI P01B Inspect Census Correction

## Status

Documentation-only correction required before A3L6 can be accepted or any
A3L7/A3L8 command can run.

Named state slice:
`phase-796a3l5d-hsai-p01b-inspect-census-correction`.

Execution status: `NotRun`. Correspondence remains `2/10`. Commercial moat
remains `3/10`; defensible breakthrough evidence remains `2-3/10`.

## Measured Contradiction

The exact inspect-field list inherited from A3L5 and repeated by A3L5C contains
56 ordered fields. A3L5C nevertheless refers to that unchanged list as having
57 fields in five prose locations. No 57th field is named in A3L5, A3L5C, the
implementation, or the focused tests. Adding a field would therefore guess and
would change the raw transcript grammar without an authorized contract.

The 56-field census is obtained by independently counting the comma-delimited
field names in both exact lists. The implementation constants in
`p01b_container_evidence.py` and `p01b_container_execution.py` reproduce the
same ordered 56 names.

## Correction

This document supersedes only the five A3L5C prose census values below:

- the recovery `present-*` inspect object is a complete 56-field object;
- a valid complete 56-field object with any identity mismatch selects
  `collision`;
- recovery presence accepts one 56-field JSON array plus LF;
- successful prestart and terminal inspect observations contain one
  56-element JSON array plus LF;
- the exact inspect evaluator evaluates every one of the 56 ordered fields.

The ordered list itself is unchanged and remains exactly:

```text
Id,Name,Path,Args,Platform,AppArmorProfile,Config.Image,Config.User,
Config.Entrypoint,Config.Cmd,Config.Env,Config.WorkingDir,Config.Hostname,
Config.Healthcheck,Config.OpenStdin,Config.Tty,Config.Labels,
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
State.StartedAt,State.FinishedAt
```

No field is added, removed, renamed, reordered, or assigned new semantics. All
per-field evaluators, raw transcript framing, recovery rules, evidence graph,
candidate grammar, class predicates, honesty assumptions, nonclaims, and claim
ceilings remain those of A3L5C as corrected here.

## Keep Gate

A3L5D is kept only if two independent reviewers confirm that:

1. both source lists count to 56;
2. no 57th field is named anywhere in the retained-container contract;
3. code and focused tests use the identical ordered 56-field list;
4. the change does not weaken any per-field predicate or authorize execution.

A3L6 remains unaccepted until its five-file implementation passes the exact
immutable gate and two code reviews. A3L7 and A3L8 remain prohibited until the
subsequent corrected gates authorize them. No runtime evidence, class closure,
accepted Evidence Ledger evidence, Level2+ evidence, benchmark evidence, proof,
production-readiness, SOTA, breakthrough, full-security, or external-audit
claim is created by this correction.
