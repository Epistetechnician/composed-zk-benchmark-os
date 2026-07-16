# Phase 796-A3L5E HSAI P01B Gate Sandbox Root-Read Correction

## Status

Documentation-only correction required before the A3L6 immutable gate can be
accepted.

Named state slice:
`phase-796a3l5e-hsai-p01b-gate-sandbox-root-read-correction`.

Execution status: `NotRun`. Correspondence remains `2/10`. Commercial moat
remains `3/10`; defensible breakthrough evidence remains `2-3/10`.

## Measured Failure

The exact A3L5C Seatbelt profile aborts the positive control with signal 6 on
the pinned host. Minimization reproduced the same empty-stream SIGABRT for
`/usr/bin/true`. Adding only the literal-root data-read clause below made that
control exit zero. No Docker, network, A3L7, or A3L8 action was used to measure
this failure.

The observation establishes a required profile capability on this host. It
does not establish which undocumented macOS implementation detail performs the
root-directory data read.

## Correction

A3L5E supersedes only the byte-exact A3L5C sandbox profile by inserting this
line immediately after `(allow file-read-metadata)`:

```text
(allow file-read-data (literal "/"))
```

The complete corrected profile is exactly:

```text
(version 1)
(deny default)
(allow process*)
(allow signal)
(allow sysctl-read)
(allow file-read-metadata)
(allow file-read-data (literal "/"))
(allow file-read* (subpath "<materialized_root>") (subpath "<gate_temp_root>") (subpath "/System/Library") (subpath "/usr/lib") (subpath "/usr/bin") (subpath "/bin") (subpath "/Library/Developer/CommandLineTools") (subpath "/private/etc") (literal "/dev/null") (literal "/dev/urandom"))
(allow file-write* (subpath "<gate_temp_root>") (literal "/dev/null"))
(deny network*)
```

The literal filter applies only to `/`; it is not a subpath filter and does not
authorize descendant file data. The declared source tree, scratch tree, system
runtime roots, system tools, `/private/etc`, `/dev/null`, and `/dev/urandom`
remain the only broader data-read allowances. General writes remain limited to
the gate scratch root and `/dev/null`. Network remains denied.

## Rejected Alternatives

- importing opaque `system.sb`, because it would add an unenumerated policy;
- allowing general or home-directory file reads, because they exceed the
  immutable project-source closure;
- deleting the positive control, because the actual Python gates must start;
- using an unsandboxed fallback, because A3L5C forbids one.

## Keep Gate

A3L5E is kept only if two independent reviewers confirm that the change is one
literal-root data-read capability, preserves every other A3L5C policy line,
does not authorize descendant reads, keeps all four network/Mach negative
controls, and creates no runtime authority or evidence.

The corrected A3L6 focused test must show the process/tempfile positive control
exits zero and direct IPv4, IPv6, DNS, and arbitrary Mach-service lookup remain
denied under these exact bytes. A3L6 remains unaccepted until its five-file
implementation passes the immutable gate and two code reviews. A3L7/A3L8 remain
prohibited. No runtime evidence, class closure, score movement, accepted
Evidence Ledger evidence, Level2+ evidence, benchmark evidence, proof,
production-readiness, SOTA, breakthrough, full-security, or external-audit
claim is created by this correction.
