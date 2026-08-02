# V41R14 POSIX Shell Wrapper Recovery Authorization

State slice: `V41R14ShellWrapperRecoveryExecution`.

Status: `WrapperOnlyRecoveryAuthorized`.

One fresh V41R14 identity is authorized because V41R13 failed before Python and
before any outcome access. V41R14 must reuse RGS executable
`478bfca2d42d86e71accfbc51b9dce5053c8f78e`, Astral validator
`d878608d65307b1ff6c17b10fdbcdccd23e7bcba`, and context `ctx-a08af0d2`
byte-for-byte.

The sole change is the submitted wrapper preamble: POSIX `set -eu` replaces
Bash-only `set -euo pipefail`. The command must pass `/bin/sh -n` locally. One
clock-locked H100, zero restarts, a 180-minute ceiling, a fresh mission, and a
fresh idempotency key are required. Any terminal result consumes V41R14. No
additional recovery, adaptive scientific change, tune, assessment, or second
cell is authorized.

Any completed artifact remains subject to the committed independent validator
and the unchanged `RemoteH100PersistentAcquisitionPilotV41R13` claim ceiling.
