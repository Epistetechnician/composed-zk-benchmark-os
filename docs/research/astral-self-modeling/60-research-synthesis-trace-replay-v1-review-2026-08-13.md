# Research Synthesis Trace-Replay V1 Review — 2026-08-13

State slice: `research-synthesis-trace-replay-v1-review`.

Disposition: `Reviewed / ClaimBoundaryPreserved / NoOpenFindings`.

## Source and synthesis coverage

- immutable paper source record: `docs/research/2608.09867-source-freeze-v1.md`;
- evidence and claim synthesis: `docs/research/2608.09867-synthesis-v1.md`;
- pure-data benchmark adapter contract: `docs/2608-opaque-trace-replay-adapter-contract-v1.md`;
- HSAI admission boundary remains the source of authority rules;
- Astral V25 remains the latest privileged-telemetry result and is not reused.

The paper is treated as relevant security prior work. Its decoder/token-count
proxy is not promoted to faithful computation, and its findings are not treated
as HSAI security evidence or Astral mechanistic evidence.

## Execution disposition

| Slice | Disposition | Ceiling impact |
|---|---|---|
| V26 | preflight stop: no fresh eligible actor and no public per-layer residual surface | none |
| V27 | local public-ABI final-embedding/intervention feasibility | none |
| V28 | weak channel-ordering signal; held-out utility failed | none |
| V29 | diagnostic-only; shuffled control outperformed both channels | none |

V25 remains `LocalDevelopmentPrivilegedTelemetryInformationPresence`.
Stage 0C and Stage 1 remain blocked. No Evidence Ledger mutation, benchmark
claim, production claim, consciousness claim, global introspection claim, or
provider-architecture claim was introduced.

## Review checks

- paper claims have source locators and explicit limitations;
- V26–V29 have distinct protocol identities and state slices;
- V25 artifacts, concepts, assessment rows, configurations, and results were
  not reused as scientific data;
- V27–V29 emitted only aggregate result JSON to transient external roots; those
  roots are not currently available, so the records preserve captured hashes,
  metrics, and validator output without implying artifact re-openability;
- no raw reasoning traces, credentials, PII, provider artifacts, opaque
  signatures, or runtime logs were added to the repository;
- model execution was offline and local; no provider API or network path was
  used;
- independent validators enforce protocol, execution, privacy-retention,
  prediction-lock, gate, and claim-ceiling fields;
- a validator completeness defect allowing omitted gate fields in malformed
  negative results was fixed and covered by regression tests;
- unrelated pre-existing dirty paths remain untouched.

The transient-result availability finding is documentation-only. Recreating
the missing external result files would require a new separately authorized
execution and is not part of this review.

## Verification

```text
git diff --check                         PASS
git diff --cached --check                PASS
cargo fmt --all -- --check               PASS
cargo test -p zkbench-core --quiet       PASS
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet  PASS
V26 focused tests                         9 PASS
V27 focused tests                         3 PASS
V28 focused tests                         4 PASS
V29 focused tests                         4 PASS
V27 aggregate validator                   valid
V28 aggregate validator                   valid
V29 aggregate validator                   valid
```

The repository has no root `package.json`; the root `pnpm` gate is therefore
not applicable to this checkout. No substitute package-manager command was
run.

## Final review conclusion

The end-to-end trace-replay synthesis, adapter design, bounded local
feasibility work, negative channel experiments, and claim-boundary review are
complete for this checkout. The next scientific action is not another
same-family run. Any successor requires a materially different causal target,
fresh authorization, independent power analysis, and a new protocol identity.
