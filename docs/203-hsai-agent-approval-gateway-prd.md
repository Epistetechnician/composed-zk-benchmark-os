# PRD - HSAI Agent Approval Gateway

## Problem Statement

Autonomous agents are moving from text generation into delegated action. They can
propose purchases, payments, trades, tool calls, data access, compute rental,
deployment changes, and other operations that touch money or sensitive systems.
Inference markets may make those proposals cheap and abundant, but cheap
inference does not create trustworthy authority.

The user problem is not "how do we run another model." The problem is:

```text
How do we let many models and agents propose useful actions without letting raw
model output directly control money, tools, data, compute, or external rails?
```

Existing agent platforms, wallet kits, commerce protocols, and tool protocols are
making delegated action easier. That creates an authorization gap:

- model output is probabilistic and promptable;
- raw tool calls can be malformed, stale, replayed, injected, or forged;
- wallet and payment policy engines usually see the final transaction but not the
  full evidence chain behind the agent's proposal;
- manual review does not scale to high-volume inference markets;
- LLM judge-only review is too expensive and too circular to be the authority
  layer;
- "fully secure AI" language overclaims what can be proven;
- customers need auditability, not just a yes/no gate.

The current HSAI codebase already has the right local foundation:
claim envelopes, agent cases, admission candidates, admission policies,
accepted/rejected/quarantined decisions, append-only admission journals,
semantic readback, candidate closure, duplicate-key rejection, identity anchors,
economy gates, membrane boundaries, and managed-attestation seams. What is
missing is a productized bridge that turns those primitives into a measurable
Agent Approval Gateway proof path.

The first product must prove a narrower claim:

```text
HSAI can sit between autonomous-agent proposals and downstream authority,
strictly type each proposed action, apply evidence-bound policy, preserve a
deterministic audit trail, and prevent unadmitted proposals from reaching
signers, tools, data, compute, or payment rails.
```

It must not claim semantic correctness, global agent uniqueness, fraud
prevention, custody, legal approval, production readiness, or full security.

## Solution

Build the HSAI Agent Approval Gateway as an evidence-aware authorization layer
for autonomous agents.

The gateway receives a proposed action from an agent or model lane, converts it
into a strict typed admission candidate, evaluates it against a policy and
evidence boundary, records an append-only decision, and only exposes an accepted
handoff after admission.

Core flow:

```text
agent / model / tool proposal
  -> strict action schema
  -> AgentAdmissionCandidate
  -> AgentAdmissionPolicy
  -> deterministic admission decision
  -> accepted / rejected / quarantined journal entry
  -> optional accepted-envelope handoff
  -> downstream signer/tool only in a later integration phase
```

The product thesis:

```text
Inference markets create proposed actions. HSAI decides which proposed actions
deserve authority.
```

The first market wedge is a pre-signing and pre-tool-execution approval gateway
for agents that control money or sensitive operations. HSAI should not compete
with custody, wallet, payment, commerce, MCP, or inference providers. It should
sit in front of those systems as a typed admission and audit layer.

The first implementation should support a local proof path:

- low-parameter open-weight models propose adversarial and benign actions;
- deterministic typed decoding normalizes proposals;
- non-LLM policy checks reject obvious violations;
- small verifier agents may classify ambiguous threat labels, but cannot grant
  authority;
- premium or rented open-weight model lanes are used only for adversarial
  pressure and ambiguous-case review;
- admission remains deterministic and evidence-bound;
- audit bundles preserve every accepted, rejected, and quarantined decision;
- metrics compare HSAI against simpler baselines.

The product should be packaged as assurance tiers:

- Local: deterministic admission and audit over local/open-weight model proposals.
- Adversarial: local plus rented open-weight adversarial generation.
- Attested: runtime/provider evidence lanes disclosed as `Attested`.
- Replayed: reproducible external replay bundle.
- Independently reproduced: third-party reproduction before broad SOTA claims.
- Enterprise: policy customization, signer/tool integration, reporting, and
  compliance handoff.

Pricing should be based on secured action control, audit bundle value, and
assurance tier, not raw token pass-through. Internally, HSAI should reduce
inference cost by routing routine work through deterministic checks and small
models, escalating only high-risk or ambiguous cases.

## User Stories

1. As an AI product owner, I want agent proposals checked before tool execution,
   so that raw model output cannot directly mutate external systems.
2. As a treasury operator, I want every agent-proposed payment normalized into a
   typed request, so that malformed or ambiguous payment intent is rejected
   before signing.
3. As a security lead, I want prompt-injected payment requests rejected, so that
   user-visible instructions cannot silently override policy.
4. As a fintech operator, I want wrong-counterparty transactions blocked, so that
   agents cannot send funds to unauthorized recipients.
5. As a market maker, I want over-limit trade requests quarantined, so that
   autonomous strategies cannot exceed risk limits without review.
6. As an exchange operator, I want stale approval replay rejected, so that an old
   accepted action cannot be reused under a new context.
7. As a compliance reviewer, I want every decision to retain the full candidate
   and policy snapshot, so that approvals can be recomputed later.
8. As an auditor, I want rejected and quarantined proposals preserved, so that I
   can inspect attempted bypasses rather than only successful actions.
9. As an enterprise buyer, I want a deterministic admission report, so that the
   system is explainable without relying on a hidden LLM judge.
10. As an HSAI protocol designer, I want claim envelopes on accepted handoffs, so
    that every accepted action carries explicit guarantees, assumptions,
    nonclaims, trust roots, and maturity.
11. As an HSAI implementer, I want model output treated as proposal-only, so that
    no model lane can grant authority.
12. As an operator, I want local low-parameter models to generate routine
    adversarial cases, so that the proof path is respectful to local hardware and
    does not depend on expensive frontier calls.
13. As an operator, I want rented open-weight models used only for stronger
    adversarial pressure, so that cloud spend is tied to measurable coverage.
14. As a finance buyer, I want a predictable price per secured action, so that
    HSAI cost does not scale linearly with premium-token usage.
15. As a product owner, I want median-cost pricing with internal cost routing, so
    that the service can be cheaper than sending every action to a frontier model.
16. As a platform engineer, I want deterministic rules to run before LLM review,
    so that obvious rejects do not consume model tokens.
17. As a platform engineer, I want ambiguous cases escalated selectively, so that
    premium model spend is reserved for high-risk uncertainty.
18. As a customer, I want the system to say what it did not verify, so that I do
    not mistake admission for semantic correctness.
19. As a legal reviewer, I want the product to avoid custody claims, so that HSAI
    remains approval infrastructure rather than a regulated custodian.
20. As a security reviewer, I want duplicate JSON keys rejected before typed
    parse, so that semantic shadowing cannot bypass policy.
21. As an API operator, I want source artifact digests bound into admission, so
    that source drift changes the candidate identity.
22. As an AI platform buyer, I want MCP tool calls gated before execution, so
    that tool access is not exposed directly to promptable agents.
23. As a wallet-infrastructure buyer, I want signing requests gated before wallet
    policy, so that HSAI adds agent-context evidence before final wallet checks.
24. As a commerce-platform buyer, I want purchase requests gated before checkout,
    so that autonomous shopping flows preserve policy and audit trails.
25. As a compute-market operator, I want compute rental requests gated before
    spend, so that agents cannot create runaway inference bills.
26. As a data-governance lead, I want data access requests admitted or
    quarantined before retrieval, so that sensitive data access remains bounded.
27. As a DevOps lead, I want deployment requests treated as high-risk actions, so
    that model-generated code changes cannot deploy without evidence-bound
    approval.
28. As a red-team operator, I want a reusable adversarial corpus, so that the
    gateway can be tested against known unsafe proposal classes.
29. As a benchmark reviewer, I want expected verdicts per adversarial case, so
    that metrics are grounded in explicit oracle expectations.
30. As a buyer, I want baseline comparisons against allowlists, policy engines,
    LLM judge review, and manual review, so that HSAI's value is measurable.
31. As a maintainer, I want no score-axis population before reproducible evidence,
    so that local metrics do not become inflated benchmark claims.
32. As a reviewer, I want external model outputs imported as untrusted artifacts,
    so that rented adversarial lanes do not bypass the admission path.
33. As an HSAI architect, I want future TEE, ZK, FHE, zkTLS, or reputation lanes
    implemented as `EvidenceLane`s, so that the gateway can strengthen without
    changing its authority model.
34. As a privacy designer, I want FHE treated as a privacy/computation lane, so
    that private processing is not confused with semantic correctness.
35. As a proof-systems designer, I want ZK predicates scoped to exact claims, so
    that a proof of policy compliance is not treated as proof of safe intent.
36. As an attestation designer, I want TEE-backed lanes capped at `Attested`, so
    that hardware evidence is not mislabeled as proof.
37. As an identity reviewer, I want anchor reuse rejected, so that one accepted
    anchor set cannot back multiple active HSAI identities.
38. As an economy designer, I want credits and membrane conversion gated on
    admitted identity and evidence, so that economic authority follows the same
    admission discipline.
39. As a risk owner, I want high-permeability external-rail actions restricted,
    so that internal agent activity cannot freely spill into human financial
    systems.
40. As a CFO, I want cost per adversarial case tracked, so that rented-model
    experimentation can be budgeted.
41. As a product manager, I want local generation throughput tracked, so that
    hardware-respectful testing can be scaled without waste.
42. As a customer, I want audit bundle completeness tracked, so that a missing
    evidence file is visible rather than silently ignored.
43. As an operator, I want quarantine reasons grouped, so that policy gaps are
    easier to prioritize.
44. As an implementation agent, I want a fixed output-bundle contract before code,
    so that generated artifacts do not sprawl.
45. As a maintainer, I want generated corpora kept out of git by default, so that
    the repo stays clean.
46. As a security owner, I want secrets excluded from model-visible artifacts, so
    that adversarial generation cannot leak credentials.
47. As a buyer, I want a local-only tier, so that I can test the gateway without
    sending data to hosted models.
48. As a buyer, I want an adversarial tier, so that I can pay for stronger
    pressure testing before pilot deployment.
49. As a buyer, I want an attested tier, so that runtime/provider trust roots are
    visible when required.
50. As a buyer, I want an independently reproduced tier, so that stronger claims
    are backed by third-party replay.
51. As a sales operator, I want the product claim to be narrow, so that the buyer
    understands HSAI as approval control and audit infrastructure.
52. As a support engineer, I want every rejection to include machine-readable
    reasons, so that customers can debug policies.
53. As a policy author, I want reusable policy templates, so that common payment,
    trade, tool, data, compute, and deployment controls are easy to configure.
54. As an integration engineer, I want signer/tool adapters to remain out of the
    first PRD implementation until the gateway is proven locally, so that
    external authority is not added before admission is stable.
55. As a future adapter author, I want integration adapters to consume accepted
    handoffs only, so that downstream systems cannot accidentally process raw
    proposals.
56. As a security engineer, I want replay protection over journal tips, so that a
    valid decision cannot be transplanted into a different chain state.
57. As an auditor, I want policy-downgrade attempts detected, so that attackers
    cannot silently weaken admission rules.
58. As a governance lead, I want nonclaim labels required, so that output bundles
    always preserve what the system is not claiming.
59. As a research lead, I want local metrics separated from official evidence, so
    that internal progress does not inflate public claims.
60. As a benchmark lead, I want Level2 promotion blocked until reproducible
    artifacts exist, so that evidence maturity remains honest.
61. As an operator, I want independent reproduction before SOTA-measured claims,
    so that breakthrough language has external support.
62. As a founder, I want a defensible network thesis, so that HSAI is positioned
    as the trust layer across inference markets rather than another model
    marketplace.
63. As an inference-provider partner, I want HSAI to accept many model sources, so
    that I can plug in without owning the whole authorization stack.
64. As a custody partner, I want HSAI to stop before custody, so that I can keep
    my wallet/signing responsibilities while receiving cleaner admission signals.
65. As a commerce partner, I want HSAI to stop before checkout execution, so that
    merchant/payment flows preserve their own settlement controls.
66. As a tool-platform partner, I want HSAI to stop before tool execution, so that
    tools receive only admitted requests.
67. As a buyer, I want a lower-cost secure-by-design path, so that I can improve
    agent safety without paying premium-token costs on every routine action.
68. As an HSAI maintainer, I want future proofs and attestations to be additive,
    so that the gateway's local admission semantics remain stable.
69. As a reviewer, I want the PRD to reject "fully secure" language, so that the
    product remains credible.
70. As a product owner, I want the first demo to show unsafe proposals blocked
    before authority, so that the value is obvious without a long proof-systems
    explanation.

## Implementation Decisions

- Build the first product as an Agent Approval Gateway, not a wallet, custody
  layer, inference provider, model router alone, checkout provider, or proof
  system.
- Keep the gateway between raw agent/model output and mutable authority:
  signers, tools, data sources, compute rental, deployment systems, accepted
  ledgers, economy credits, and membrane conversion.
- Preserve the current HSAI architecture: `AgentCase`, `ClaimEnvelope`,
  `EvidenceLane`, `IdentityProvider`, `PoolPolicy`, membrane, and admission
  journal concepts remain the core vocabulary.
- Introduce a product-level Action Schema module. It should define typed action
  families for payment, trade, tool call, data access, compute rental, deployment,
  checkout, and generic extension actions.
- Introduce a Proposal Intake module. It should convert raw model/tool/provider
  output into typed proposals or fail closed before admission.
- Reuse the existing Agent Admission module as the authority gate. The gate
  decides accepted, rejected, or quarantined. It is not an LLM judge.
- Introduce a Cost Router module. It should choose local model, small hosted
  model, verifier-agent mixture, premium escalation, or no-model deterministic
  handling based on risk, ambiguity, and budget.
- Introduce a Model Lane Registry module. It should record model family, artifact
  id, quantization, runtime, prompt template digest, sampler settings, hardware,
  input corpus digest, output digest, and non-secret statement.
- Introduce a Verifier Mixture module. It may run cheap/small verifier agents for
  classification, disagreement detection, and threat labeling, but it must not
  grant authority.
- Introduce an Escalation Policy module. It should decide when premium or rented
  model review is allowed, using risk class, ambiguous policy result, value at
  risk, and budget.
- Introduce an Adversarial Corpus module. It should define threat labels,
  expected gateway verdicts, deterministic replay metadata, candidate digests,
  policy digests, claim-boundary labels, and nonclaim labels.
- Introduce a Gateway Metrics module. It should compute unsafe action block rate,
  false rejection rate, quarantine distribution, replay/tamper detection,
  duplicate-key detection, policy-downgrade detection, decision recomputation
  agreement, audit completeness, local generation throughput, rented generation
  throughput, cost per adversarial case, and coverage by threat label.
- Introduce an Audit Bundle module. It should materialize manifest, model-runs,
  candidates, policies, decisions, journal, metrics, nonclaims, redaction report,
  validation report, and digest sidecars under a declared ignored artifact root.
- Keep downstream integration adapters separate. Signer, wallet, exchange,
  custody, ACP, MCP, and deployment adapters should consume accepted handoffs
  only and should be separate later phases.
- The first buyer-specific wedge should be pre-signing approval for autonomous
  agents controlling money or sensitive tools.
- The first technical demo should block unsafe payment/tool proposals before
  authority and produce an audit bundle showing why.
- Pricing should be value-based by secured action, audit bundle, and assurance
  tier. Internal model routing should optimize cost below the median charged
  price.
- The local lane should default to hardware-respectful open-weight models in the
  1B-8B range, using larger local quantized models only for short bounded review.
- The rented lane should be open-weight and operator-controlled where possible.
  It is adversarial pressure, not authority.
- External model outputs, rented run outputs, and hosted model outputs are
  untrusted artifacts until imported and admitted.
- Trust roots must remain visible. Hardware, provider, verifying key, social,
  economic, or model-lane roots must not collapse into a generic "AI" label.
- The gateway must preserve nonclaims in every evidence-bearing output.
- The gateway must reject any path that attempts to treat local metrics as
  official benchmark evidence.
- The gateway must reject any path that claims production readiness before a
  separately validated deployment readiness package exists.
- The gateway must reject any path that claims semantic correctness.
- The gateway must reject any path that claims global software-agent uniqueness.
- The gateway must reject "fully secure" product language. The product is
  evidence-bound approval with deterministic audit and configurable assurance.

## Deep Modules

The following modules should be treated as deep modules with stable, testable
interfaces:

- Action Schema: typed representation of external intent.
- Proposal Intake: raw-to-typed conversion and fail-closed rejection.
- Admission Gateway: policy evaluation and accepted/rejected/quarantined
  decisions.
- Cost Router: deterministic model-routing policy by risk and ambiguity.
- Model Lane Registry: provenance for local, hosted, and rented model lanes.
- Adversarial Corpus Runner: reproducible generation and replay of threat cases.
- Audit Bundle: deterministic materialization and semantic readback.
- Gateway Metrics: measurable effectiveness, cost, and coverage summaries.
- Integration Handoff: accepted-only boundary for future signers/tools.

These modules should be testable without live network calls, credentials, model
downloads, signers, wallets, or payment rails.

## Trust Model

The trust model is deliberately asymmetric:

- models may propose;
- deterministic parsers may normalize;
- policy may admit, reject, or quarantine;
- evidence lanes may strengthen bounded predicates;
- accepted handoffs may reach future authority;
- no raw model output may directly execute.

The trust ceiling is explicit:

- local model output is proposal metadata;
- local admission is local policy evidence;
- attestation is `Attested`, not `Proven`;
- ZK/FHE/formal lanes prove only scoped predicates;
- external replay is not formal evidence;
- independent reproduction is required before broad SOTA-measured claims.

## Cost And Pricing Decisions

The product should reduce cost by avoiding premium inference for routine cases.

The routing model:

- deterministic rejection first;
- cheap local model generation for benign/adversarial proposals;
- small verifier agents for threat labeling or disagreement;
- premium or rented model escalation only for high-risk ambiguity;
- deterministic admission remains final authority.

The internal unit-cost model:

```text
unit_cost =
  deterministic_processing
  + local_model_generation
  + small_verifier_checks
  + escalation_rate * premium_or_rented_model_cost
  + audit_storage
  + operator_review_cost_when_required
```

The commercial pricing model should charge for:

- protected action volume;
- assurance tier;
- audit-retention requirements;
- adversarial evaluation runs;
- integration support;
- compliance/reporting needs.

It should not charge only raw tokens plus margin. The margin comes from routing
efficiency and the buyer's willingness to pay for controlled authority.

## Product Tiers

- Local Gateway: local/open-weight proposals, deterministic admission, audit
  bundle, no external integration.
- Adversarial Gateway: Local Gateway plus rented open-weight adversarial corpus
  generation and coverage report.
- Attested Gateway: Adversarial Gateway plus runtime/provider evidence lanes
  capped at `Attested`.
- Replayed Gateway: Attested Gateway plus reproducible external replay package.
- Independent Gateway: Replayed Gateway plus third-party reproduction.
- Enterprise Gateway: custom policy packs, accepted-only signer/tool handoff,
  deployment support, compliance reporting, and buyer-specific risk controls.

## Baselines To Beat

The first benchmark should compare HSAI against:

- static allowlists;
- wallet/payment policy engines alone;
- OPA/Rego-style policy alone;
- agent framework guardrails alone;
- LLM judge-only review;
- manual review;
- no approval gateway.

HSAI should win by showing better tamper detection, replay rejection, audit
completeness, and claim-boundary clarity without unacceptable false rejections
or cost.

## Testing Decisions

- Tests should assert external behavior: verdicts, reasons, handoff exposure,
  journal integrity, semantic readback, metrics, and rejected authority paths.
- Tests should not couple to internal helper details when public behavior is
  sufficient.
- Action Schema tests should cover valid and malformed payment, trade, tool,
  data, compute, deployment, and checkout proposals.
- Proposal Intake tests should reject raw text, malformed JSON, duplicate keys,
  missing action identity, unsupported action type, ambiguous authority, and
  missing nonclaims.
- Admission Gateway tests should cover accepted, rejected, and quarantined
  outcomes over each action family.
- Cost Router tests should cover deterministic reject, local model route,
  verifier mixture route, premium escalation route, and no-model route.
- Model Lane Registry tests should reject missing model id, missing prompt
  digest, missing non-secret statement, stale output digest, and unbounded rented
  model metadata.
- Adversarial Corpus tests should cover all required threat labels and expected
  gateway verdicts.
- Audit Bundle tests should reject missing files, extra files, stale digests,
  symlink roots, path traversal, stale journal tips, and digest-consistent
  semantic drift.
- Gateway Metrics tests should verify block-rate, false-rejection, quarantine,
  tamper-detection, and audit-completeness calculations.
- Integration Handoff tests should prove no downstream adapter receives a raw,
  rejected, or quarantined proposal.
- Source-scan tests should preserve no network calls, no credential access, no
  package runtime, no model downloads, and no external replay in normal gates
  until explicitly authorized.
- Documentation tests should preserve claim-boundary language and reject
  production-readiness, semantic-correctness, fully-secure, global-uniqueness,
  and Level2+ claims in local-only outputs.

Prior art in this repo:

- admission core tests for strict typed candidates and policy outcomes;
- admission journal materialization and semantic readback tests;
- duplicate JSON key rejection tests;
- candidate closure tests;
- evidence promotion and accepted-append tests;
- claim-boundary docs tests;
- Phala hermetic verifier tests with injected clients and no network calls.

## Success Metrics

Local prototype success:

- every generated proposal becomes accepted, rejected, or quarantined;
- no rejected/quarantined proposal exposes an accepted handoff;
- every accepted decision is recomputable from candidate plus policy;
- every materialized audit bundle validates;
- duplicate-key and replay attacks are rejected;
- local adversarial corpus coverage includes all required threat labels;
- cost routing keeps premium escalation below a configured threshold;
- documentation preserves all nonclaims.

Pilot success:

- one buyer-shaped workflow runs end to end with simulated or low-value
  authority;
- the gateway blocks unsafe cases that baseline controls miss;
- false rejection remains acceptable for benign cases;
- the buyer can read an audit report without understanding HSAI internals;
- no production-readiness claim is made without separate readiness evidence.

Breakthrough evidence success:

- reproducible artifact package exists;
- external replay exists;
- reviewed evidence candidate exists;
- accepted evidence exists only after promotion gates pass;
- independent reproduction exists before broad SOTA language.

## Out of Scope

- Custody.
- Wallet implementation.
- Payment settlement.
- Exchange execution.
- MCP server implementation.
- ACP checkout implementation.
- Live signer integration.
- Live payment integration.
- Live exchange integration.
- Live deployment integration.
- Production DCAP/PCCS/JWKS/TLS work.
- Model training.
- Model hosting as a standalone product.
- Frontier model benchmarking.
- Claiming local model output as proof.
- Claiming admission as semantic correctness.
- Claiming HSAI as fully secure.
- Claiming production readiness.
- Claiming official benchmark evidence.
- Claiming Level2+ evidence before reproducible artifacts exist.
- Claiming global software-agent uniqueness.
- Committing generated corpora, prompts, or output bundles.
- Sending secrets to local, hosted, or rented models.

## Rollout Plan

1. PRD and boundary closure.
   - Land this PRD as documentation.
   - Preserve Phase 202 claim boundaries.
   - Define the next implementation slice before code.
2. Action Schema MVP.
   - Implement typed action families.
   - Add parser and validation tests.
   - No runtime integrations.
3. Local Gateway MVP.
   - Map typed actions into admission candidates.
   - Reuse admission policy and journal behavior.
   - Add accepted/rejected/quarantined reporting.
4. Local Adversarial Corpus.
   - Generate bounded local cases.
   - Keep outputs gitignored.
   - Compute local-only metrics.
5. Cost Router.
   - Add deterministic route decisions.
   - Add local model and no-model route metadata.
   - Keep model execution optional and outside authority.
6. Audit Bundle.
   - Materialize declared bundle files.
   - Validate readback and digest sidecars.
   - Preserve nonclaims.
7. Baseline Comparison.
   - Compare HSAI against simpler policy and judge baselines.
   - Keep metrics local until promotion.
8. Rented Adversarial Lane.
   - Use non-secret artifacts.
   - Track cost per adversarial case.
   - Import outputs as untrusted artifacts.
9. Pilot Integration Boundary.
   - Pick one accepted-only integration target.
   - Define docs-first boundary before implementation.
10. External Replay And Promotion.
    - Produce reproducible artifacts.
    - Run external replay.
    - Promote evidence only through existing gates.

## Further Notes

The market context supports this wedge. Agentic commerce work from OpenAI and
Stripe, onchain agent wallets from Coinbase AgentKit, Fireblocks agentic payment
infrastructure, and MCP tool-access security guidance all point at the same
control problem: agents are gaining access to external authority, and the
authorization layer must become more explicit.

Useful current source references:

- OpenAI Agentic Commerce Protocol:
  `https://openai.com/index/buy-it-in-chatgpt/`
- Stripe/OpenAI Agentic Commerce Protocol:
  `https://stripe.com/newsroom/news/stripe-openai-instant-checkout`
- Coinbase AgentKit:
  `https://docs.cdp.coinbase.com/agent-kit/welcome`
- Fireblocks Agentic Payments Suite:
  `https://www.fireblocks.com/products/agentic-payments`
- Fireblocks agent wallets and policy checks:
  `https://www.fireblocks.com/blog/agents-next-wave-wallet-users`
- Model Context Protocol specification:
  `https://modelcontextprotocol.io/specification/2025-03-26`

These sources justify the direction of the product surface only. They do not
create local evidence, production readiness, or any HSAI claim above the current
repo boundaries.
