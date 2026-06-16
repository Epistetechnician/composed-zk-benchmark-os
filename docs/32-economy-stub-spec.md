# L3 Economy Stub — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase: a new crate `hsai-economy`
depending on the shipped `hsai-claim-envelope` and `hsai-distinct-agent` crates. It
is not source code. It models the L3 economy mechanics in memory: a credit ledger,
two swappable `PoolPolicy` variants, the peg, and the flywheel, with the whole
economy gated on the L2 identity registry.

This is a stub of mechanics, not a validated economy. A credit certifies that an
oracle admitted some work; it does not certify the work's value or correctness. The
"1:1 regenerative" property is NOT asserted here — this phase builds the machinery
so the peg and circulation can later be tested by simulation (ledger A5). Demurrage
and mutual credit are offered as swappable variants; neither is endorsed as the
economy.

## Purpose

Make the flywheel concrete: a distinct identity earns credits for admitted work,
credits decay or clear, identities gift or fund into a shared pool, and the pool
funds other distinct identities. Gate every operation on the L2 registry so the
economy inherits the Sybil floor. Add a minimal freeze hook as a corrigibility
preview.

## Dependencies

Reuse, do not redefine: from `hsai-claim-envelope` — `ClaimEnvelope`, `admits`,
`AcceptancePolicy`, `Rejection`, `SubjectId`. From `hsai-distinct-agent` —
`IdentityRegistry` (and its `identity()` lookup). The economy never creates
identities; it reads them.

## Types

```text
struct Credits(i128);   // signed: mutual credit may go negative; demurrage stays >= 0

struct WorkRecord {
  worker:   SubjectId,
  admitted: bool,        // did the work's claim envelope pass the AcceptancePolicy
  demand:   u64,         // count of DISTINCT agents who built on / requested this work
}

trait PegPolicy {
  // floor for admitted work plus a multiplier in distinct-agent demand
  fn reward(&self, work: &WorkRecord) -> Credits;
}

struct FloorPlusDemandPeg { floor: u64, demand_multiplier: u64 }
// reward = if work.admitted { floor + demand_multiplier * work.demand } else { 0 }

trait PoolPolicy {
  fn issue(&self, work: &WorkRecord) -> Credits;          // mint for verified work (via peg)
  fn decay(&self, balance: Credits, ticks: u64) -> Credits;
  fn min_balance(&self) -> i128;                          // floor a balance may reach
  fn name(&self) -> &'static str;
}

struct DemurragePolicy   { peg: FloorPlusDemandPeg, rate: u64 }
// issue = peg.reward; decay = max(0, balance - rate*ticks); min_balance = 0; name "demurrage"

struct MutualCreditPolicy { peg: FloorPlusDemandPeg, credit_limit: u64 }
// issue = peg.reward; decay = balance (no demurrage); min_balance = -(credit_limit as i128);
// name "mutual-credit"
```

## The Economy

```text
struct Economy<P: PoolPolicy> {
  policy:   P,
  accounts: BTreeMap<SubjectId, Credits>,
  pool:     Credits,
  frozen:   BTreeSet<SubjectId>,
  tick:     u64,
}

enum EconomyError {
  NotRegistered(SubjectId),     // subject is not in the identity registry (Sybil gate)
  Frozen(SubjectId),            // account is frozen by the corrigibility hook
  WorkNotAdmitted(Vec<Rejection>),
  InsufficientBalance,          // would drop below policy.min_balance
  PoolInsufficient,             // pool cannot cover a fund
}

impl<P: PoolPolicy> Economy<P> {
  // Earn ties a credit directly to an ADMITTED claim envelope and a REGISTERED worker.
  fn earn(&mut self, reg: &IdentityRegistry, worker: SubjectId,
          work_env: ClaimEnvelope, policy: AcceptancePolicy, demand: u64)
      -> Result<Credits, EconomyError> {
    require reg.identity(&worker).is_some();        // -> NotRegistered
    require !self.frozen.contains(&worker);          // -> Frozen
    admits(policy, work_env)?;                        // -> WorkNotAdmitted
    let credits = self.policy.issue(&WorkRecord{ worker, admitted:true, demand });
    self.accounts[worker] += credits; return credits;
  }

  fn gift(&mut self, reg, from, amount) -> Result<(), EconomyError>;   // account -> pool, no return
  fn fund(&mut self, reg, to, amount)   -> Result<(), EconomyError>;   // pool -> account
  fn tick(&mut self);                                                   // apply decay to all accounts
  fn freeze(&mut self, subject); fn unfreeze(&mut self, subject);      // corrigibility hook
  fn balance(&self, subject) -> Credits;
}
```

`gift` and `fund` both require a registered, non-frozen subject; `gift` fails with
`InsufficientBalance` if the debit would drop the account below
`policy.min_balance()`; `fund` fails with `PoolInsufficient` if the pool cannot
cover it. Neither creates nor destroys credits — they move them.

## The Flywheel

```text
earn (admitted work, registered worker)  -> credits minted to worker
gift (worker -> pool)                     -> worker funds the commons, no return
fund (pool -> other registered worker)    -> pool funds another distinct agent
tick                                       -> demurrage decays idle balances (mutual credit clears)
```

Mission economies are pools funding a shared goal; gift versus trust-staked giving
are future `PoolPolicy`/funding variants. This phase ships the gift path and the
two currency variants; it does not pick a peg or a winner.

## Claim Boundaries (hard statements)

- A credit certifies an oracle admitted some work; not its value or correctness.
- The peg is a stub; no regenerative property is asserted (ledger A5).
- Demurrage and mutual credit are swappable; neither is endorsed.
- The economy is gated on the L2 registry; an unregistered subject has no account.
- `freeze` is a corrigibility preview, not the full off-switch (ledger A8/A9).
- `demand` is an input here, not verified; a real demand signal is future work.

## Invariants (property-test statements)

```text
EC-1  sybil-gate:   earn / gift / fund for an unregistered subject -> NotRegistered
EC-2  conservation: gift and fund preserve sum(accounts) + pool exactly
EC-3  demurrage:    DemurragePolicy.decay is monotone non-increasing in ticks, floored at 0
EC-4  mutual-clear: MutualCreditPolicy.decay(balance, t) == balance for all t
EC-5  peg:          admitted work earns floor + multiplier*demand; unadmitted earns 0;
                    reward is non-decreasing in demand
EC-6  freeze:       a frozen subject cannot gift or fund-from; balances unchanged
EC-7  min-balance:  gift never drops an account below policy.min_balance(); else InsufficientBalance
EC-8  determinism:  identical operation sequences yield identical ledgers
```

## Test Vectors

### E1 — Sybil gate

```text
empty registry; earn(agentA, admitted work) == Err(NotRegistered(agentA))
```

### E2 — Flywheel and conservation

```text
registry has agentA (anchor hwA) and agentB (anchor hwB)
peg: floor=10, demand_multiplier=2 ; policy: demurrage rate=5
earn(agentA, admitted work, demand=3) == Ok(Credits(16))      // 10 + 2*3
gift(agentA -> pool, 8)
fund(pool -> agentB, 8)
balance(agentA)=8, balance(agentB)=8, pool=0
sum(accounts)+pool == 16   // unchanged by gift+fund (conservation)
```

### E3 — Decay differs by policy

```text
demurrage(rate=5):  balance 8 -> tick -> 3 -> tick -> 0 (floored)
mutual-credit:      balance 8 -> tick -> 8 -> tick -> 8 (no demurrage)
```

### E4 — Freeze blocks movement

```text
freeze(agentA); gift(agentA -> pool, 1) == Err(Frozen(agentA)); balance(agentA) unchanged
unfreeze(agentA); gift(agentA -> pool, 1) == Ok(())
```

### E5 — Mutual credit may go negative; demurrage may not

```text
agentA balance 0
mutual-credit (credit_limit=100): gift(agentA -> pool, 8) == Ok(())  // balance -8 (within -100)
demurrage:                        gift(agentA -> pool, 8) == Err(InsufficientBalance) // min_balance 0
```

## Out Of Scope (later phases)

The membrane and external-rail conversion (L5; gated internal->external boundary),
the trust-staked funding variant and mission-economy goal binding, the real demand
signal, real attestation verification, the harness/corrigibility gate beyond the
freeze hook (L4), and economic simulation of the peg. Do not resolve doc 22 open
decisions; ship both currency variants and leave the choice to the consumer.

## Implementation Phase Notes

- New crate `crates/hsai-economy`, workspace member, path-depending on
  `hsai-claim-envelope` and `hsai-distinct-agent`. Do not modify any existing crate.
- Dev-dependency `proptest`. Encode E1–E5 as unit tests and EC-1..8 as proptests.
- Deterministic: `BTreeMap`/`BTreeSet`, signed `i128` arithmetic with saturating or
  checked ops, no `HashMap`, no floats.
- Definition of done: `cargo test -p hsai-economy` green, `cargo fmt --check` and
  `cargo clippy -p hsai-economy --all-targets -- -D warnings` clean, E1–E5 exact.
