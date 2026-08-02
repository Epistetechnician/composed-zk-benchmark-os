# V41R18 Registry Cache-Hit Canary Failure

State slice: `V41R18RegistryRepairCanaryAndGradientProfile`.

Status: `CanaryConsumed / FailedBeforeContainerStart / ScientificExecutionUnauthorized`.

Job `job-exijp` used the exact build key that previously produced successful
V41R15 job `job-kgyid`. It skipped building and entered the H100 queue, then
failed on three free provider start attempts while pulling the already-published
internal image. No container started and every run-log stream was empty.

The mission closed at USD 0.00. No runtime verification, H100 command, model
access, source injection, gradient, artifact, or scientific result occurred.
V41R18 scientific execution was never authorized.

The provider registry is now mechanically blocked across new-image push,
prebuilt-image import, and existing cached-image pull. Ticket `tkt-uktwn`
retains all three reproductions. No further job is admissible before a
provider-side end-to-end canary, a pinned snapshot bypassing the registry, or
a separately authorized migration to another H100 provider. V41R16 remains
scientifically `NotRun`.
