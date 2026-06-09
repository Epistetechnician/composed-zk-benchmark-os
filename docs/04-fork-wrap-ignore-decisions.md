# Fork, Wrap, Ignore Decisions

## Decision Policy

Default to wrap or reference. Fork only when a concrete adapter cannot be built without upstream changes or when contributing upstream. Ignore sources that create scope drag or lack executable relevance.

## When To Fork

Fork only when:

- upstream changes are needed for a benchmark adapter,
- licensing and provenance are understood,
- the fork has a narrow maintenance plan,
- the fork produces evidence unavailable through wrapping,
- the state slice names the exact upstream and files affected.

No first-pass source is marked `fork`.

## When To Wrap

Wrap when a repo can supply execution, proof, verification, metric, trace, or benchmark behavior through a stable boundary. The wrapper must define input spec, generated instance, capability flags, replay command, output metrics, provenance, evidence class, claim boundary, failure mode, and reproducibility metadata.

## When To Ignore

Ignore when a source is not useful for the first implementation, creates dependency sprawl, or is only adjacent to the thesis. Ignoring is not permanent; it means no initial adapter or docs dependency.

## When To Reference

Reference when a repo is useful for background or legacy comparison but should not become an adapter target. zkp-gravity/zkml-benchmark is a reference source in this scaffold.

## When To Use Discovery-Only

Use discovery-only for curated lists such as awesome-zk and awesome-zero-knowledge-proofs. They can suggest candidate sources, but they do not provide evidence.

## When To Use Local-Pattern-Source

Use local-pattern-source for ZAQOS, Mesh, Orbital Mesh, Mesh Intelligence, MeshQRC, and Recoverable Ghost States. These repos offer patterns around evidence ladders, orchestration, benchmark packs, and claim boundaries. They are not copied or forked as project bases.

## Why Wrap/Reference Is The Default

The benchmark OS should own the Semantic IR and evidence model. Existing repos should remain independent systems with adapters. Copying feature sets would blur responsibility, increase maintenance, and make future claims harder to audit.

## Risks Of Copying Feature Sets

- Duplicated code without upstream updates.
- License and provenance ambiguity.
- Backend assumptions leaking into core semantics.
- Benchmark claims becoming tied to unverified local modifications.
- Adapter sprawl before the DSL is stable.

## Maintenance Risk

Each adapter must declare version, source path or URL, replay command, capability flags, and failure-mode policy. A stale adapter is worse than no adapter because it can produce misleading evidence.

## Licensing And Provenance Caution

Before copying code in any future phase, verify license compatibility and record provenance. This scaffold does not copy external source code.

## Adapter-Boundary Principles

- Semantic IR is owned here.
- Backends report capabilities, not universal support.
- Negative tests are first-class.
- Evidence class is explicit.
- Claim boundaries are enforced before scoring.

