# Phase 796-A3L6S: P01B Gate-Sandbox Test-Root Correction

Named state slice:
`phase-796a3l6s-p01b-gate-sandbox-test-root-correction`.

## Finding

The first clean detached A3L6 audit-run retained a `rejected` result because
`test_cli_refuses_runtime_without_a3l7_material` unconditionally created a
test-owned `TemporaryDirectory` under `/private/tmp`. The A3L6 nested Seatbelt
profile correctly permits writes only beneath its supplied scratch root, so the
execution-focused test could not start that fixture.

The failure is a test-fixture location mismatch, not container execution,
runtime authority, a review result, or A3L6 acceptance. The retained rejected
record remains diagnosis only.

## Correction

Only `tools/hsai-formal-preflight/p01b_container_execution_tests.py` changes.
When `P01B_GATE_SANDBOX_ACTIVE=1`, this test now lets `TemporaryDirectory` use
the pre-existing gate `TMPDIR` scratch root. Outside the gate it preserves the
host-only explicit `/private/tmp` test location. The production runner,
Seatbelt profile, source census, gate invocation, and authority boundaries are
unchanged.

## Required follow-through

This source correction creates a new implementation identity. The rejected
audit/run must not be relabeled or promoted. A new immutable audit must bind
the new clean commit/tree, all five reviewed blobs, the exact 22-path census,
32+33 focused tests, 172 discovery census, caps, and 201/202/271 counts, then
run `a3l6-gate-v1` from a fresh detached checkout into a new mode-0700
non-repository output root.

Even a resulting `pending-review` record is local regression evidence only. It
does not accept A3L6, prove reviewer identity, authorize A3L7/A3L8/A3L9,
invoke Docker, registry, network, container, or external replay, move a score,
promote evidence, submit a benchmark, or create production authority.
