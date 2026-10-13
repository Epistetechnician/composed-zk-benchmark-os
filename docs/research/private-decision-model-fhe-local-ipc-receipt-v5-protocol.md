# Private Decision Model FHE Local IPC Receipt V5

State slices: `private-decision-model-fhe-local-ipc-receipt-v5` and
`global-experiment-assurance-lifecycle-v1`. Frozen implementation dependency:
`private-decision-model-fhe-local-ipc-contract-v3`. V4 is terminally closed
as `QualificationFailedReceiptTestImport` and is not an execution input.

## Purpose and claim ceiling

V5 qualifies a packet-bound source digest for the frozen V3 local synthetic
FHE IPC run. V1 through V3 remain byte-for-byte frozen. V5 uses a small
receipt adapter over the exact V3 runner and worker; its only runtime override
supplies V5's canonical digest function while the V3 runner is executing, then
restores the original function. The V5 test directory is explicitly added to
`sys.path` before importing the V5 runner. The V4 failed test output is kept
only as failure history and no V4 FHE result exists to reuse.

The maximum claim is
`LocalDevelopmentSyntheticFHEIPCReceiptQualificationV5`: one local run of
the frozen V3 synthetic IPC workload emitted a source digest that matches the
V5 packet and is invariant to relative paths containing `..` versus canonical
absolute paths. This is local receipt qualification only, not cryptographic
security, hostile-process isolation, remote-service behavior, real-data
utility, benchmark validity, or production readiness. No external review,
review task, or transfer is part of the slice.

## Frozen question and hypothesis

Does V5 resolve every packet-bound source path before forming its repository-
relative digest name, verify all V5 packet and predecessor digests before
execution, and pass the exact V5 digest into the frozen V3 aggregate regardless
of invocation path spelling?

The hypothesis is that the canonical-path digest closes the V3 receipt issue,
and the import-path correction lets the V5 test suite execute while the frozen
V3 FHE workload retains its score and ranking results.

## Workload, budgets, and custody

- Source: the V5 receipt adapter and receipt tests plus digest-pinned V3
  runner, worker, parser, and parser tests; the V1 scorer, fixture, manifest,
  and dependency lock remain unchanged.
- Data: the deterministic V1 synthetic fixture only: eight evaluation
  requests, four options per request, six signed integer features in `[-8,8]`,
  128 training rows, and 12 calibration requests.
- Focused checks: run the frozen 14-test V3 parser/worker suite once and the
  V5 receipt-adapter suite once. The V5 suite checks importability, relative
  `..` versus absolute path normalization, all frozen packet and composite
  digests, result labeling, and restoration of V3's original digest supplier.
- FHE qualification: at most one local run of eight encrypted requests. The
  V3 parser-control test may launch one malformed-envelope subprocess; the
  V3 FHE runner launches one client-spec subprocess and one evaluation
  subprocess. Worker timeout is 900 seconds and parser-only timeout is 30
  seconds.
- Runtime: Python 3.12.13, Concrete 2.11.0, NumPy 1.26.4, and PyTorch 2.14.1
  from the exact V1 lock, installed and run offline from the verified local
  cache.
- Network/spend: no provider, network service, remote worker, paid execution,
  external reviewer, task submission, secure transfer, or public service.
- Custody: V3's frozen runner keeps generated keys, circuit bundle,
  ciphertexts, responses, and synthetic arrays only in memory or a system
  temporary directory and removes them at completion. No raw IPC or FHE
  artifacts are retained.

## Fixed digest contract and gates

V5 hashes the ordered paths in the packet's `composite_files` list. For each
path it appends the resolved canonical UTF-8 repository-relative name followed
by the exact bytes. The source digest is independent of invocation path. Before
FHE execution, the runner verifies every listed file hash, the protocol hash,
the V3 predecessor composite, the V5 composite, and the declared ordered file
list.

The V5 adapter temporarily supplies the verified V5 digest to the frozen V3
aggregate builder and restores the original V3 digest function in a `finally`
block. It labels the resulting aggregate as V5 and records the V5 packet,
V5 source composite, and frozen V3 source composite. It does not alter V3.

All 14 V3 tests and all V5 receipt tests must pass before the sole FHE run.
The run passes only if `v5_source_sha256` equals the packet composite,
encrypted scores and top rankings match, the client secret key and clear
features stay client-side, no network is used, and temporary FHE artifacts are
removed.

## Stop conditions and nonclaims

Stop V5 on any packet, protocol, V3 predecessor, or source digest mismatch;
any test or parser control failure; a score or ranking mismatch; worker timeout;
failure to restore the original V3 digest supplier; or failed temporary
cleanup. Do not change source or repeat qualification under this packet. A
correction requires a new state slice and packet.

V5 does not amend or reopen V1 through V4. It does not authorize real or user
data, remote execution, paid work, public release, security claims, benchmark
claims, or production deployment. Those actions require a fresh scope and the
applicable owner or independent authority.

## Freeze and validation order

1. Add only V5 receipt source, tests, protocol, packet, result record, and
   navigation. Keep V1-V4 files unchanged.
2. Freeze V5 and pinned V3 dependency bytes, V1 source/fixture/manifest/lock
   digests, runtime, budgets, custody, nonclaims, and claim ceiling.
3. Recompute all file, protocol, predecessor, composite, and packet digests
   before running tests.
4. Run the frozen V3 test suite, then the V5 receipt tests. Run at most one
   FHE qualification only if both suites pass.
5. Verify all frozen digests and temporary cleanup, and record exact
   assurance, reviewer status, reproducibility, custody, limitations, claim
   ceiling, and next blocked authority gate.
