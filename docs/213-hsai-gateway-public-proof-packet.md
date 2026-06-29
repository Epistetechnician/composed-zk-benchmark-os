# Phase 213 HSAI Gateway Public Proof Packet

Status: bounded public claim packet for the green public gateway state.

This packet is a shareable claim artifact. It does not add code, widen the
gateway trust boundary, or convert local tests into production or benchmark
evidence.

## Proof Target

- Commit: `4dfa3e6dfddd8ab79f558691bc10c48b74f47bf7`
- Public branch state: `origin/master` at the Phase 212 gateway baseline
  comparison commit.
- Validated surfaces: Phases 204-212.
- Public claim class: local hermetic gateway
  admission/report/corpus/baseline-comparison stack.

Later local commits are outside this packet unless a new packet explicitly
names them.

## What The Packet Proves

At the target commit, the repository contains a reproducible local Rust gateway
stack with passing verifier commands for:

- typed HSAI Agent Approval Gateway proposals;
- deterministic local gateway policy admission;
- accepted-only handoff metadata with `authority_granted = false` semantics;
- local corpus evaluation and recomputable metrics;
- deterministic in-memory report artifacts with SHA-256 bindings;
- local `gateway-report/*` output materialization and readback validation;
- one-shot local corpus output runs;
- deterministic local cost-routing metadata;
- local model-lane registry validation;
- local adversarial-corpus structure validation;
- local adversarial-corpus output runs;
- local baseline comparison against caller-supplied baseline decisions.

The proven statement is narrow: the source at the named commit builds and the
local verifier suite passes for the listed hermetic gateway surfaces.

## Exact Verifier Commands

Run from the repository root after checking out the target commit:

```sh
cargo fmt --all --check
git diff --check
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```

The public claim depends on every command exiting successfully. A failing command
invalidates the packet for that checkout until the failure is fixed and a new
commit is named.

## Validated Surfaces

Phase 204: local gateway MVP.

- `GatewayActionProposal`
- `GatewayActionPolicy`
- `GatewayActionOutcome`
- `GatewayAcceptedHandoff`
- `GatewayCorpusCase`
- `GatewayCorpusReport`
- deterministic admission through the existing local admission journal

Phase 205: in-memory report artifact.

- report validation
- deterministic JSON and Markdown rendering
- SHA-256 bindings
- required nonclaim text

Phase 206: local report output plumbing.

- declared `gateway-report/*` files
- SHA-256 sidecars
- protected-root rejection
- undeclared-file rejection
- symlink rejection
- readback validation

Phase 207: local corpus output run.

- one-shot local corpus evaluation
- report-bundle materialization only after successful evaluation
- output-root safety propagation

Phase 208: cost router.

- local review-route metadata
- budget-gated premium escalation metadata
- operator-review fallback metadata
- `authority_granted = false`

Phase 209: model-lane registry.

- lane-id validation
- duplicate rejection
- required provenance fields
- stale output-bundle digest rejection
- unbounded rented, hosted, and premium lane metadata rejection

Phase 210: adversarial-corpus validation.

- required threat-label coverage
- duplicate-case rejection
- benign control requirement
- unsafe adversarial expected-accepted rejection
- unknown model-lane rejection

Phase 211: adversarial-corpus output run.

- corpus validation before output creation
- reuse of the Phase 207 output-run path
- reuse of the Phase 206 report-bundle materialization path

Phase 212: baseline comparison.

- caller-supplied local baseline decisions
- HSAI unsafe accepted count
- baseline unsafe accepted count
- HSAI false rejection count
- baseline false rejection count
- audit-bundle completeness metadata
- `authority_granted = false`

## Nonclaims

This packet does not prove:

- production readiness;
- semantic correctness;
- model execution quality;
- live provider evidence;
- hosted model behavior;
- verifier-agent runtime behavior;
- external replay;
- accepted Evidence Ledger mutation;
- score-axis population;
- official benchmark evidence;
- Level2+ evidence;
- live baseline execution;
- signer, wallet, exchange, custody, MCP, ACP, or tool authority;
- deployment safety;
- global software-agent uniqueness;
- full security;
- any claim above `Attested`.

No model was downloaded or executed by this packet. No live provider was called.
No secret, credential, generated corpus, generated output bundle, or benchmark
artifact is part of the claim.

## Reproduction Checklist

1. Fetch the public repository state.

   ```sh
   git fetch origin
   ```

2. Check out the target commit.

   ```sh
   git checkout 4dfa3e6dfddd8ab79f558691bc10c48b74f47bf7
   ```

3. Confirm the checked-out commit.

   ```sh
   git rev-parse HEAD
   ```

   Expected output:

   ```text
   4dfa3e6dfddd8ab79f558691bc10c48b74f47bf7
   ```

4. Run the exact verifier commands in this packet.

5. Treat the claim as valid only if every verifier command exits successfully.

6. Inspect the Phase 204-212 notes for the implementation boundaries and
   anti-goals attached to each surface.

## Buyer-Facing Wording

Use:

> HSAI has a reproducible local proof packet for an Agent Approval Gateway. At
> commit `4dfa3e6dfddd8ab79f558691bc10c48b74f47bf7`, typed agent proposals,
> admission policy, audit reports, corpus validation, output-bundle validation,
> cost-routing metadata, model-lane provenance checks, adversarial-corpus
> validation, and baseline comparison all pass the published local verifier
> suite.

Use:

> The current public packet proves the local gateway boundary is implemented and
> reproducible from source. It does not claim production readiness, semantic
> correctness, model quality, live provider evidence, benchmark evidence, or
> external authority.

Do not say:

- HSAI is production ready.
- HSAI proves agent intent.
- HSAI proves model correctness.
- HSAI is a fully secure agent runtime.
- HSAI has live provider evidence.
- HSAI has official benchmark evidence.
- HSAI has Level2+ evidence.
- HSAI grants signer, wallet, exchange, custody, MCP, ACP, or tool authority.

## Public Claim

The public claim is:

> At commit `4dfa3e6dfddd8ab79f558691bc10c48b74f47bf7`, HSAI has a local
> hermetic Agent Approval Gateway stack whose admission, report, corpus,
> output-bundle, cost-router, model-lane registry, adversarial-corpus, and
> baseline-comparison surfaces are reproducible with the listed verifier
> commands.

That is the full claim. Anything beyond it requires a separately named state
slice, fresh verification, and a new packet.
