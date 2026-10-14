# V41R27R2 sentinel execution authorization R1 final binding

State slice: `V41R27R2NumericallyStableSentinelReleaseAndExecution`.

Status: `AuthorizedOnce / NotYetConsumed`.

Pre-execution review found a stale v1 result-version expectation in the
sentinel validator. It was corrected and regression-tested before any node or
optimizer execution. Context `ctx-54e79c60` is superseded unused.

The final authorized identity `astral-v41r27r2-sentinel-r1` binds:

- RGS implementation `fb2ddcb61495f98fbb3189cefefb23fd0745903a`;
- Astral validator `3f3c8052cfff111f06451b01e4e2f098eaeab01d`;
- context `ctx-a11201ce`, 46,082,048 bytes, SHA-256
  `d3da5c8ac76a85fe83f2e7522f2921a60d9c92dc49689328fbc0e97a015ad508`;
- preflight result
  `sha256:c1cfc5c19e4d88ab571e4f5b5c63c175996f5661b083c961f5f4b7406f8552bd`;
- contract v2
  `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`.

The frozen nine-run order, one-hour/ten-minute timeouts, USD 5 spend ceiling,
restart-never policy, first-failure stop, export, independent validation, and
immediate node-stop requirements remain unchanged. Only this binding may run.
