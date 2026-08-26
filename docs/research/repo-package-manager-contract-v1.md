# Repository package-manager contract V1

State slice: `repo-package-manager-contract-v1`

The repository now owns a minimal package-manager contract solely for
orchestrating existing Rust and Python gates. It pins pnpm `10.32.1`, defines
the heavy `pnpm run lint` gate, and exposes faster focused gates without adding
JavaScript or TypeScript runtime code or dependencies. Every nested pnpm call
uses `--ignore-workspace`, so an ancestor Yarn/Corepack workspace cannot
redirect the gate.

## Gates

- `pnpm --ignore-workspace run lint:fast`: Rust formatting, Python AST parsing,
  and diff hygiene.
- `pnpm --ignore-workspace run test:focused`: continual-learning and
  self-model benchmark/control-plane Python tests.
- `pnpm --ignore-workspace run verify:provider`: feature-gated Phala
  provider-client tests with
  fake transport and no credentials.
- `pnpm --ignore-workspace run verify:contracts`: `zkbench-core`, provider-client,
  continual-learning, and self-model benchmark/control-plane tests.
- `pnpm --ignore-workspace run verify:full`: complete Cargo workspace tests.
- `pnpm --ignore-workspace run verify:features`: complete Cargo workspace
  tests with every declared crate feature enabled, including the opt-in
  provider and TLS paths.
- `pnpm --ignore-workspace run verify:clippy`: all workspace targets with all
  features enabled under Clippy's warnings-as-errors policy.
- `pnpm --ignore-workspace run lint`: all six gates in order.

The parent package is not part of this contract. The repository-local
`packageManager` field and explicit workspace isolation make the package
boundary explicit; no dependency installation is required.

## Claim ceiling

These gates establish local source, contract, and test evidence only. They do
not establish provider delivery, production deployment, scientific evidence,
official benchmark evidence, or model quality.
