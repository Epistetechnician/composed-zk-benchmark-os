# Phase 761 HSAI Gateway Threat Ordinal Bounded Self-Test Closure

## Status

Complete as a documentation-first parser-invocation correction.

State slice:
`phase-761-hsai-gateway-threat-ordinal-bounded-self-test-closure`.

Classification: `CanonicalBoundedRawParserSelfTestSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

Phase 762 uses run root `hsai-phase762-efa3782c`, detached repository root
`hsai-phase762-repo-efa3782c`, and witness
`phase762ExtractedThreatOrdinalWitnesses`.

After every inherited gate and the 30 focused helper tests pass, Phase 762 must
run exactly one bounded producer whose child argv is:

```text
/usr/bin/python3 tools/hsai-formal-preflight/raw_archive_validator.py self-test
```

The producer must use the committed `bounded_runner.py run-v1`, a 120-second
timeout, a 1,048,576-byte stdout cap, a 262,144-byte stderr cap, and distinct
mode-`0600` status/stdout/stderr files under the run root. It may not pass
`--output`, redirect the child itself, invoke `run_self_test()` directly, or
run the parser unbounded.

The next top-level command must be the standalone acceptance parser and must
assert only:

1. bounded-runner reason `exit` and return code zero;
2. empty retained stderr;
3. one duplicate-key-safe canonical stdout JSON object;
4. schema `hsai-raw-archive-self-test-v1`;
5. exactly 31 ordered case identifiers, `passed = 31`, and `failed = 0`.

The acceptance parser must propagate nonzero directly and may not display,
hash, checkpoint, clean up, or start a later stage. A separate later command
may record transcript hashes only after acceptance succeeds.

After this correction is committed and all inherited Phase 749-760 gates pass,
Phase 762 may make one attempt. The first failure stops the phase without repair
or replay.

Phase 761 runs no helper, parser, network, compiler, backend, or kernel command
and creates no proof, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.
