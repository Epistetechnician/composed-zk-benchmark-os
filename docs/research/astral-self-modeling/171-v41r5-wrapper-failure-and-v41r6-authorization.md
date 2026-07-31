# V41R5 Wrapper Failure and V41R6 Authorization

State slices: `V41R5CachedImageRecovery` and
`V41R6PosixWrapperCorrection`.

Job `job-2chx4` cache-hit the exact verified V41 image and reached attempt 1,
but `/bin/sh` exited before Python execution because the wrapper used the
non-POSIX option `set -o pipefail`. The complete run log was:

```text
/bin/sh: 1: set: Illegal option -o pipefail
```

No runner, model, tokenizer, corpus, forward pass, gradient, result, or
artifact was produced. V41R5 is retained as a pre-scientific wrapper failure.

V41R6 authorizes one fresh cache-only identity with exactly one correction:
replace `set -euo pipefail` with POSIX-compatible `set -eu`. All build inputs,
source bytes, dependencies, model revision, corpus, runner, thresholds,
hardware, cost, duration, restart policy, and claim ceilings remain those
frozen by V41R5. Any cache miss must be canceled before execution.

The maximum result remains `RemoteH100RuntimeProfileOnlyV41`.
