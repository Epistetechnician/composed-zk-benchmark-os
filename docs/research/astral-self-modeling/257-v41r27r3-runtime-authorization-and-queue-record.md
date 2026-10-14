# V41R27R3 runtime authorization and queue record

The operator authorized state slice
`V41R27R3LossResilientQualificationRecoveryExecution` against RGS commit
`189b5af071beb3ed8aeb2eb96658a9fbee18953e` and Astral commit
`8d495fa502166a158cc41f90802cad041ba68f01`.

The restored interactive node became `lost (disk lost)` before preflight and
before optimizer construction. The execution surface was corrected to an
independent 22-variant batch sweep with one shared immutable build. The
scientific method and frozen worker partition are unchanged.

An initial sweep whose declared maximum was `$10.989` was canceled at attempt
zero because it exceeded the authorized `$8` aggregate ceiling. The restored
host subsequently charged `$1.00011`; R2 was therefore canceled at attempt zero
because its ceiling would have put worst-case incremental spend above `$8`.
The active `astral-v41r27r3-recovery-r3` sweep uses six-minute variants, zero
restarts, and a provider-declared sweep maximum of `$6.59340`. Combined with
the restore, the worst case is `$7.59351`. It is currently waiting for build
capacity. Queueing and builds are not evidence, and the
scientific identity remains unconsumed until optimizer construction.

The claim ceiling remains
`RemoteH100AGEMRecoveredQualificationV41R27R3`; confirmation, SOTA,
introspection, self-improvement, and independent replication remain forbidden.
