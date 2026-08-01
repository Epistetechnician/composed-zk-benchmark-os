# Domain Documentation

State slice: `agent-skills-repository-routing-configuration`.

This repository uses a single documentation context. No root `CONTEXT.md`,
`CONTEXT-MAP.md`, or `docs/adr/` directory is currently authoritative.

Before product, architecture, or implementation work, read the relevant parts
of:

- `AGENTS.md` for capability and claim boundaries;
- `README.md` for current implementation status and navigation;
- `docs/00-project-brief.md` for the project problem and objective;
- `docs/03-sota-architecture.md` for the benchmark-OS architecture;
- `docs/12-task-list.md` for accepted and future slices;
- `docs/90-whole-codebase-validation-report.md` for current evidence ceilings;
- the narrow phase or integration specification governing the requested slice.

Use the repository's established nouns exactly: Surface DSL, Parsed AST,
Semantic IR, Benchmark Family, Benchmark Instance, Mutation Variant, Oracle,
Expected Verdict, Backend Outcome, Evidence Record, Claim Boundary, and Score
Report. HSAI work additionally preserves ClaimEnvelope, evidence maturity,
admission, action proposal, and explicit non-authority boundaries.

If a future `CONTEXT.md`, `CONTEXT-MAP.md`, or ADR hierarchy is introduced, it
supersedes this fallback routing only where it explicitly says so.
