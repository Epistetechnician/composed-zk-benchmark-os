# Private Decision Model FHE Local IPC Receipt V4

State slices: `private-decision-model-fhe-local-ipc-receipt-v4` and
`global-experiment-assurance-lifecycle-v1`. Frozen implementation dependency:
`private-decision-model-fhe-local-ipc-contract-v3`. Frozen workload
dependency: `private-decision-model-fhe-inference-v1`.

## Purpose and claim ceiling

V4 qualifies a packet-bound, invocation-path-invariant source digest for the
V3 local synthetic FHE IPC run. V3 remains byte-for-byte frozen. V4 uses a
small receipt adapter around the exact V3 runner and worker; its only runtime
override supplies V4's canonical digest function while the V3 runner is
executing, then restores the original function. It does not change the FHE
workload, parser, worker, scorer, or fixture.

The maximum claim is
`LocalDevelopmentSyntheticFHEIPCReceiptQualificationV4`: one local run of
the frozen V3 synthetic IPC workload emitted a source digest that matches the
V4 packet and is invariant to relative paths containing `..` versus canonical
absolute paths. This is a receipt-integrity qualification for the named local
source only. It is not cryptographic security, hostile-process isolation,
remote-service behavior, real-data utility, benchmark validity, or production
readiness. No external review or transfer is part of this slice.

## Frozen question and hypothesis

Does V4 compute repository-relative source names only after resolving each
source path, validate every listed V4 packet source and protocol digest before
execution, and make the returned aggregate use the V4 packet's exact source
composite regardless of how `run_v4.py` was invoked?

The hypothesis is that canonical source-path resolution removes the V3
receipt discrepancy while the frozen V3 code still returns the same exact
synthetic encrypted scores and rankings.

## Workload, budgets, and custody

- Source: V4 receipt adapter and tests plus the digest-pinned V3 runner,
  worker, parser, and test suite; the digest-pinned V1 scorer is unchanged.
- Data: only the V1 deterministic synthetic fixture. It remains eight
  evaluation requests, four options, six signed integer features in `[-8,8]`,
  128 training rows, and 12 calibration requests, all fixed by V1.
- Focused checks: run the frozen 14-test V3 parser/worker suite once and the
  V4 receipt-adapter suite once. V4 tests compare canonicalized paths for
  relative `..` and absolute spellings, recompute all packet digests, and
  validate adapter result labeling and digest-supplier restoration.
- FHE qualification: at most one local run with eight encrypted requests. The
  V3 parser-control test may start one malformed-input subprocess; the V3 FHE
  runner starts one client-spec subprocess and one evaluation subprocess.
  Worker timeout is 900 seconds and parser-control timeout is 30 seconds.
- Runtime: only the V1 locked Python 3.12.13 environment with Concrete 2.11.0,
  NumPy 1.26.4, and PyTorch 2.14.1; dependency setup is offline from the
  existing verified cache.
- Network/spend: no provider, network service, remote worker, paid execution,
  reviewer task, secure transfer, or public service.
- Custody: the V3 runner retains keys, circuit bundle, ciphertexts, responses,
  and synthetic arrays only in memory or a system temporary directory and
  removes them at completion. No raw IPC or FHE artifacts are retained.

## Fixed digest contract and gates

The source digest uses the ordered files listed by `source_identity` in the
V4 packet's `composite_files` array. For each file it appends the canonical
UTF-8 repository-relative path followed by the exact file bytes to SHA-256.
The canonical path is computed as `path.resolve().relative_to(repository_root)`
and is independent of the original invocation spelling. The V4 packet lists
per-file digests for those sources plus the V3 protocol, V1 manifest, and V1
lock. The runner verifies every listed digest, the V4 protocol digest, the
V3 predecessor composite, and the V4 composite before starting FHE work.

After packet validation, V4 temporarily supplies that verified V4 composite
to the frozen V3 aggregate builder. The adapter restores the original V3
digest function in a `finally` block even if execution fails. It relabels the
aggregate as V4 and records both the V4 composite and the frozen V3 source
composite; it does not modify V3 files.

V4 source/path tests and all 14 V3 parser tests must pass before one FHE run.
The run passes only if its `v4_source_sha256` equals the packet composite,
every encrypted score matches, all top rankings match, the client secret key
and clear features stay client-side, no network is used, and temporary
artifacts are removed.

## Stop conditions and nonclaims

Stop V4 if any packet/source digest differs, the relative/absolute path test
fails, any parser control fails, score or ranking parity fails, a worker times
out, the digest supplier is not restored, or temporary cleanup fails. Do not
change source or repeat qualification under the V4 packet. Any correction
requires a new local state slice and packet.

V4 does not amend or reopen V1, V2, or V3. It does not authorize user or real
data, remote execution, paid work, public release, external review, security
claims, benchmark claims, or production deployment. Any such action requires
a fresh scope and the applicable owner or independent authority.

## Freeze and validation order

1. Add only V4 adapter, receipt tests, protocol, packet, result record, and
   navigation. Keep V1, V2, and V3 files unchanged.
2. Freeze exact V4 and V3 dependency bytes, V1 source/fixture/manifest/lock
   digests, runtime, budgets, custody, nonclaims, and claim ceiling in the
   machine-readable V4 packet.
3. Recompute every file, protocol, predecessor, composite, and canonical
   packet digest before running tests.
4. Run the frozen V3 focused suite, then the V4 receipt tests. Only if both
   pass, run at most one V4 local synthetic FHE qualification.
5. Recompute all packet identities and verify temporary cleanup. Record the
   exact outcomes, assurance, reviewer status, reproducibility, custody,
   limitations, ceiling, and next blocked authority gate.
