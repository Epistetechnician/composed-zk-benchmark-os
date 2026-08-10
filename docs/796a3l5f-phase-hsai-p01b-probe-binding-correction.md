# Phase 796-A3L5F HSAI P01B Probe Binding Correction

## Status

Documentation-only correction required before A3L6 can be accepted and before
any A3L7/A3L8 command can run.

Named state slice:
`phase-796a3l5f-hsai-p01b-probe-binding-correction`.

Execution status: `NotRun`. Correspondence remains `2/10`. Commercial moat
remains `3/10`; defensible breakthrough evidence remains `2-3/10`.

## Measured Contradictions

The pinned native command launches `/usr/bin/python3`, whose frozen SHA-256 is
`7f30f076d0e9c38f772a76449fca9da8cf97f6a3d43b94c90a00e4f9ce7ad39e`.
On the pinned host, Python reports a different CommandLineTools path through
`sys.executable`. Treating that reported path as the launch executable makes
the required native C02 equality impossible even though the direct argv is
correct.

The descriptor-bound snapshot-copy manifest includes host-created descriptor
observation digests. Container code can re-inventory the 21 mounted regular
files, but cannot derive those host descriptor digests from container-visible
bytes and inodes. Hashing a different local projection cannot equal the
snapshot-copy manifest domain digest.

Neither contradiction was discovered by Docker, network, A3L7, or A3L8
execution.

## Corrections

For `native-reference` only, `runtime.executable` and its executable-chain
identity mean the exact direct-argv launch path `/usr/bin/python3`. The probe
must descriptor-read and hash that path. `sys_version`, `sysconfig_paths`,
linker observations, dependency observations, and standard-library inventory
continue to disclose the runtime reached by that launch under the existing
system-runtime honesty assumptions. The container modes continue to use their
direct launch path `/usr/local/bin/python3`.

The normal/OOM container command template is superseded only by adding one
required argument before `--output`:

```text
"--mode",ATTEMPT,
"--input-manifest-sha256",SNAPSHOT_COPY_MANIFEST_SHA256,
"--output","/work/result.json"
```

`SNAPSHOT_COPY_MANIFEST_SHA256` is the already frozen domain digest of the
21-entry `hsai-p01b-snapshot-copy-manifest-v1`. It is present in the attempt
plan, expected bindings, authorization, create argv, probe result, candidate
snapshot pair, ingress descriptor set, and A3L9 reconstruction equality chain.
The probe accepts no ambient default and requires 64 lowercase hex characters.
Native-reference mode rejects this argument.

Before emitting the supplied digest, normal/OOM probe execution still performs
its independent exact 21-regular-file mounted-tree inventory and the existing
11-file corpus validation. The argument does not substitute for the candidate
snapshot files, host source/copy manifests, descriptor observations, ingress
mount reconstruction, or A3L9 byte/hash replay. It is a cross-layer join value,
not a container-derived descriptor proof.

## Keep Gate

A3L5F is kept only if two independent reviewers confirm that it resolves both
impossible equalities without weakening snapshot byte/descriptor validation,
adds exactly one closed CLI argument to normal/OOM, leaves native argv
unchanged, and preserves all honesty assumptions, nonclaims, evidence ceilings,
and runtime prohibitions.

A3L6 remains unaccepted until its exact five-file immutable gate and two code
reviews pass. A3L7/A3L8 remain prohibited. No runtime evidence, class closure,
score movement, accepted Evidence Ledger evidence, Level2+ evidence, benchmark
evidence, proof, production-readiness, SOTA, breakthrough, full-security, or
external-audit claim is created by this correction.
