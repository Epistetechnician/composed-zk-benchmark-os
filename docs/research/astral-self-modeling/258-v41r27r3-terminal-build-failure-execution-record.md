# V41R27R3 terminal build-failure execution record

The authorized V41R27R3 recovery campaign terminated before scientific
execution. The spend-safe `astral-v41r27r3-recovery-r3` sweep had exactly 22
frozen variants, zero restarts, six-minute limits, and a `$6.59340` declared
sweep ceiling. All 22 jobs became `build_failed` at attempt zero.

The builder resolved the pinned PyTorch base digest, then failed in `apt-get
update` because rootless BuildKit could not set groups or effective gid 65534.
Representative job: `job-qfcc5`. Provider ticket: `tkt-gdntm`.

No worker container started, no optimizer was constructed, and no V41R27R3
result exists. The campaign was not retried. Incremental provider spend was
`$1.00011`, entirely from the preceding snapshot restore and below the
authorized `$8` ceiling.

Qualification remains `NotAssessed`; 22 workers remain missing. The active
claim ceiling remains
`RemoteH100AGEMPartialQualificationInfrastructureInterruptedV41R27R2`.
Confirmation, SOTA, introspection, self-improvement, and independent
replication remain unauthorized.
