# Stage 0 Rust Migration Boundary V8

State slice: `astral-stage0-rust-migration-boundary-v8`.

Status: `RustProtocolMigrationAuthorized`.
Evidence ceiling: `LocalCrossLanguageParityDiagnostic`.

Rust is preferred for the protocol and validation control plane because typed
schemas, closed enums, checked arithmetic, and a single native artifact improve
auditability. Rust is not presumed numerically superior for this experiment.
Replacing PyTorch changes the experimental instrument: random initialization,
AdamW, clipping, GELU, LayerNorm, softmax, floating-point kernels, autograd, and
checkpoint bytes may differ.

The migration is therefore gated:

1. `P0`: authorize a pure-data Rust protocol crate;
2. `P1`: implement family/example contracts, seed and family seals, method
   registry, top-one selection, dead-zone regret, V6 method-selection rules,
   canonical tagged hashing, and negative tests;
3. `P2`: prove cross-language parity against locked exposed-development
   fixtures before replacing Python orchestration;
4. `P3`: add a numerical backend only under a separate explicit phase and
   compare a frozen checkpoint over exposed development data with declared
   tolerances;
5. `P4`: treat Rust-native training as a new actor instrument requiring new
   development and fresh-seed qualification before any method or holdout run.

V9 may add `crates/astral-stage0-protocol`, workspace membership, lockfile
changes, focused tests, and navigation. It must remain pure data: no tensor or
ML dependency, process, filesystem, environment, network, Python invocation,
checkpoint loading, training, scoring, intervention, or holdout construction.

The V9 crate must preserve:

- train families `0..159` and development families `160..191`;
- rejection of every family `>=192`;
- retired and sealed ranges through `511`;
- reserved future families `512..575`;
- reserved future actor seeds `173, 179, 181`;
- the five frozen V6 method formulas as identifiers only;
- competitive baseline identifiers;
- lowest-index absolute-score tie breaking;
- dead zone `1e-4` and normalized regret bounds;
- the V6 assessment eligibility and deterministic winner rule;
- claim fields that cannot represent Stage 0 pass, accepted evidence,
  self-modeling, or independent replication.

Python V1–V7 remain immutable research records. V5 remains `Null`; V7 qualifies
only `family-complete-2000`; Stage 1 remains blocked. Rust parity results cannot
promote those claims.

Backend decision is deferred. `tch` is closest to the current PyTorch runtime
because it binds LibTorch, but introduces a native C++/LibTorch dependency.
Candle and Burn are Rust-oriented alternatives with autodiff capability but
constitute different numerical runtimes. A later backend phase must pin one
choice, prove Rust 1.74 compatibility, disclose native dependencies, and define
parity tolerances before code.
