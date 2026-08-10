# Claim-Packet Forge

State slice: `catalyst-strategy-claim-packet-forge-v1`.

The repeatable recipe for turning one evidence-disciplined module into a
verifiable, buyer-facing claim packet plus a reproduction checker. This
generalizes the worked example already in the repository:

- Phase 214 — HSAI gateway public proof packet (`docs/214-...`).
- Phase 254 — HSAI gateway bridge public claim packet (`docs/254-...`).
- Phase 255 — claim-packet reproduction checker (`docs/255-...`).

Claim boundary: the forge is a Level 0 recipe. Stamping a packet does not create
evidence, raise evidence maturity, widen a trust boundary, or grant authority. A
packet only surfaces existing, already-bounded evidence at a pinned commit.

## Why The Forge Exists

The repository's differentiator — claim-boundary discipline — is harder to demo
than a competitor's single risk score. The forge fixes that by turning "we don't
overclaim" into a shareable artifact a buyer can run. Every packet is narrow,
pinned, reproducible, and explicit about what it does *not* prove.

## Packet Anatomy (canonical)

Every claim packet must contain, in order:

1. **Pinned commit.** The exact commit the packet is true at. Later commits are
   outside the packet unless a new packet names them.
2. **Validated surfaces.** The named phases / crates / modules covered.
3. **Public claim.** A narrow statement of what the module proves at the pinned
   commit. One claim class, no aggregation that hides weak evidence.
4. **Exact verifier commands.** The commands a buyer runs to reproduce, copied
   verbatim. The claim depends on every command exiting successfully.
5. **Explicit nonclaims.** What the packet does *not* prove: not production
   readiness, not SOTA, not benchmark evidence, not accepted evidence, not full
   security, not authority, and any module-specific nonclaims.
6. **Buyer-facing wording.** A short plain-language statement, plus the
   "do not use" phrases a buyer must not infer.
7. **Catalyst index.** Which catalyst(s) from `catalyst-ledger.md` this packet
   answers, so the targeting system can find it.

## Reproduction Checker (canonical)

Every packet must be paired with a hermetic repository test that reads the
committed packet and checks it stays aligned with repository state. Modeled on
`crates/zkbench-core/tests/gateway_claim_packet_reproduction.rs` (Phase 255). The
checker must verify, at minimum:

- the packet path and pinned commit string;
- the covered surfaces;
- the exact documented verifier commands;
- any ignored demo root and `.gitignore` boundary referenced;
- the declared output files, if the packet names a bundle;
- the non-mutating / candidate-only flags;
- the explicit nonclaims and buyer-facing "do not use" phrases;
- the navigation references (README, task list, validation report, AGENTS).

The checker reads committed Markdown and config only. It must not run provider
calls, generate artifacts, inspect credentials, mutate ledgers, execute the demo
command, or require network access. A packet whose checker fails is not shareable.

## Forge Recipe (per module)

1. Confirm the module is at least Level 1 local replay evidence with passing
   verifier commands. If not, the packet is not stampable yet.
2. Choose a pinned commit where the module's verifier suite is green.
3. Write the packet following the anatomy above. Name the catalyst(s) it answers.
4. Write the reproduction checker test following the canonical checks above.
5. Run the checker; it must pass before the packet is shareable.
6. Add a navigation row for the packet in the README documentation table.
7. Record the packet in `module-sensitivity-matrix.md` under the module's
   packaging state.

## Stamp Order

Priority from `module-sensitivity-matrix.md`: stamp M1 (attestation & identity)
and M3 (evidence ledger & audit) first because they answer the privacy thesis
directly, then M4 (formal lane), then M5/M7 as their catalysts warm. M2 (gateway)
is already packet'd and is the reference template.

## Nonclaims

The forge does not claim any packet is production ready, that packaging creates
or raises evidence, that any packet grants authority or executes a backend, or
that any catalyst will fire. A packet is a narrow, pinned, reproducible statement
of existing bounded evidence, with explicit nonclaims.
