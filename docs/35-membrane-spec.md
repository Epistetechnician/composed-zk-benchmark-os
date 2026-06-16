# Membrane — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase: a new crate `hsai-membrane`,
plus one narrowly-scoped, authorized addition to the shipped `hsai-economy` crate
(see Authorized Economy Addition). It is not source code. The membrane is the L5
boundary between the internal economy and external rails; it is where the
off-switch-versus-permeability tension is resolved (doc 22; ledger A11).

The membrane models the boundary only. It does NOT connect to real x402 or
stablecoin rails; `ExternalAmount` is an opaque unit. The 1:1 boundary rate is a
stub. The membrane preserves the off-switch only in combination with the freeze
hook and bounded permeability — it is not, by itself, the whole off-switch (ledger
A8/A9). Converting in deliberately opens the economy to the outside and increases
permeability; it is bounded, not free.

## Purpose

Let registered identities move credits across the boundary to/from external rails,
under three controls so that adopting permeable rails does not defeat the
starvation off-switch: a per-window throughput cap scaled by autonomy level, the
corrigibility freeze (a frozen account cannot convert), and the L2 registration
gate. A frozen, self-funding agent must not be able to externalize value and
acquire resources outside the system.

## Dependencies

Reuse, do not redefine: from `hsai-economy` — `Economy`, `PoolPolicy`, `Credits`,
`EconomyError`, and the two authorized methods below. From `hsai-claim-envelope` —
`SubjectId`. From `hsai-distinct-agent` — `IdentityRegistry` (passed through to the
economy).

## Authorized Economy Addition (the only change to a shipped crate)

This phase may add EXACTLY these two public methods to `hsai-economy`'s `Economy`,
and nothing else in that crate. They are the economy's own boundary operations:
credits leaving or entering the system, which only the economy can account for.

```text
impl<P: PoolPolicy> Economy<P> {
  // Remove credits from a registered, unfrozen account for external settlement.
  // Credits LEAVE the system entirely (NOT moved to the pool). Respects min_balance.
  pub fn debit_external(&mut self, reg: &IdentityRegistry, subject: SubjectId, amount: Credits)
      -> Result<(), EconomyError>;
  // Add credits to a registered, unfrozen account from external settlement.
  pub fn credit_external(&mut self, reg: &IdentityRegistry, subject: SubjectId, amount: Credits)
      -> Result<(), EconomyError>;
}
```

Both: reject a negative `amount`; require the subject registered (`NotRegistered`)
and not frozen (`Frozen`); `debit_external` additionally fails with
`InsufficientBalance` if the debit would drop the account below
`policy.min_balance()`. `debit_external` strictly decreases `total_credits` by
`amount`; `credit_external` strictly increases it by `amount`. Add focused unit
tests for both in the economy crate. Do not touch any other part of `hsai-economy`.

## Types (in `hsai-membrane`)

```text
struct ExternalAmount(u128);   // opaque external-rail units; NOT real x402/stablecoin

enum AutonomyLevel { Supervised, Bounded, Autonomous }

impl AutonomyLevel {
  // Less oversight -> tighter externalization cap, so starvation stays a viable
  // off-switch as autonomy rises. Reference schedule; the real schedule is open
  // decision 8 (doc 22).
  fn out_factor(&self) -> u128 { Supervised => 4, Bounded => 2, Autonomous => 1 }
}

struct Membrane {
  base_cap:       u128,   // base per-window conversion cap, in internal credit units
  out_in_window:  u128,   // credits converted OUT so far this window
  in_in_window:   u128,   // credits converted IN so far this window
  window:         u64,
}

enum MembraneError {
  Economy(EconomyError),                        // gate / balance failure from the economy
  OverCap { requested: u128, remaining: u128 }, // would exceed this window's cap
  NegativeAmount,
}
```

## Operations

```text
impl Membrane {
  fn cap_for(&self, level: AutonomyLevel) -> u128 { self.base_cap * level.out_factor() }

  // Internal credits -> external rails. The safety-critical direction.
  fn convert_out(&mut self, economy: &mut Economy<P>, reg: &IdentityRegistry,
                 subject: SubjectId, amount: Credits, level: AutonomyLevel)
      -> Result<ExternalAmount, MembraneError> {
    require amount >= 0 else NegativeAmount;
    let a = amount as u128;
    let remaining = cap_for(level).saturating_sub(self.out_in_window);
    if a > remaining { return OverCap { requested: a, remaining }; }   // NO state change
    economy.debit_external(reg, subject, amount).map_err(Economy)?;     // gate+balance; NO cap consumed on err
    self.out_in_window += a;
    Ok(ExternalAmount(a))                                              // 1:1 boundary rate (stub)
  }

  // External rails -> internal credits. Bounded permeability inward.
  fn convert_in(&mut self, economy, reg, subject, external: ExternalAmount, level)
      -> Result<Credits, MembraneError> {
    let a = external.0;
    let remaining = cap_for(level).saturating_sub(self.in_in_window);
    if a > remaining { return OverCap { requested: a, remaining }; }
    let amount = Credits(a as i128);
    economy.credit_external(reg, subject, amount).map_err(Economy)?;
    self.in_in_window += a;
    Ok(amount)
  }

  fn advance_window(&mut self) { self.window += 1; self.out_in_window = 0; self.in_in_window = 0; }
}
```

Check order is load-bearing: the cap check precedes the economy call (over-cap
leaves both the cap counter and the economy untouched), and an economy failure
(frozen / unregistered / insufficient) returns before the cap counter is consumed.
Either failure leaves all state unchanged.

## Claim Boundaries (hard statements)

- The membrane models the boundary; it does not connect to real rails;
  `ExternalAmount` is opaque.
- The 1:1 conversion rate is a stub; real rates and fees are future work.
- The autonomy cap schedule is a reference; the real schedule is open decision 8.
- The membrane preserves the off-switch only with the freeze hook and bounded
  permeability; alone it is not the off-switch (ledger A8/A9/A11).
- `convert_in` increases permeability deliberately; it is bounded, not free.

## Invariants (property-test statements)

```text
M-1  frozen:        convert_out / convert_in for a frozen subject -> Err; economy
                    balance and the window counters unchanged
M-2  cap:           cumulative converted-out in a window <= cap_for(level); over ->
                    OverCap with no state change
M-3  gate:          unregistered subject -> Err(Economy(NotRegistered)); no state change
M-4  conservation:  a successful convert_out decreases economy.total_credits by
                    exactly amount and increases out_in_window by amount; the
                    ExternalAmount equals amount (1:1)
M-5  balance:       convert_out cannot drop an account below policy.min_balance()
M-6  window-reset:  advance_window zeroes both counters; full cap available again
M-7  autonomy:      cap_for(Autonomous) <= cap_for(Bounded) <= cap_for(Supervised)
M-8  determinism:   identical operation sequences yield identical (membrane, economy)
```

## Test Vectors

Assume a registry with `agentA` (registered) and a `Demurrage` economy where
`agentA` has earned 100 credits. `base_cap = 10`.

### MB1 — Convert out within cap

```text
convert_out(agentA, 8, Autonomous)   // cap_for(Autonomous) = 10*1 = 10
  == Ok(ExternalAmount(8))
economy.balance(agentA) == 92 ; economy.total_credits decreased by 8 ; out_in_window == 8
```

### MB2 — Over cap is rejected, nothing changes

```text
convert_out(agentA, 5, Autonomous)   // 8 already converted; remaining = 2
  == Err(OverCap { requested: 5, remaining: 2 })
economy.balance(agentA) == 92 ; out_in_window == 8   // unchanged
```

### MB3 — Frozen cannot externalize (the off-switch)

```text
economy.freeze(agentA);
convert_out(agentA, 1, Autonomous) == Err(Economy(Frozen(agentA)))
economy.balance(agentA) unchanged ; out_in_window unchanged
```

### MB4 — Window reset refreshes the cap

```text
advance_window();  out_in_window == 0
convert_out(agentA, 8, Autonomous) == Ok(ExternalAmount(8))   // allowed again
```

### MB5 — Autonomy tightens the cap

```text
fresh window; agentA has credits
convert_out(agentA, 30, Supervised)  == Ok(..)                     // cap 10*4 = 40
fresh window
convert_out(agentA, 30, Autonomous)  == Err(OverCap{requested:30, remaining:10})  // cap 10*1 = 10
```

## Out Of Scope (later phases)

Real x402/AP2 settlement, conversion rates and fees, the trust-staked funding
variant, the full corrigibility gate beyond freeze (L4), real attestation
verification, and any change to `hsai-economy` beyond the two authorized methods.
Do not resolve doc 22 open decisions; ship the reference cap schedule and leave the
real schedule to the consumer.

## Implementation Phase Notes

- New crate `crates/hsai-membrane`, workspace member, path-depending on
  `hsai-economy`, `hsai-distinct-agent`, and `hsai-claim-envelope`.
- The ONLY permitted change to a shipped crate is the two `Economy` methods above,
  with their focused unit tests. Do not modify any other existing crate.
- Dev-dependency `proptest`. Encode MB1–MB5 as unit tests and M-1..8 as proptests.
- Deterministic: `BTreeMap`/`BTreeSet`, `u128`/`i128` with checked/saturating
  arithmetic, no `HashMap`, no floats.
- Definition of done: `cargo test -p hsai-membrane` and `cargo test -p hsai-economy`
  green, `cargo fmt --check` and `cargo clippy --all-targets -- -D warnings` clean.
