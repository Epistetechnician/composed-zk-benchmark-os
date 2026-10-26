# Neuron-level subject-verb agreement: findings, assets, and expected-value roadmap
Status: owner-attested exploratory research (ceiling OwnerSelfAttestedLocalDevelopment); not independently reviewed. Campaign V50-V59, about USD 45 of 50.00 spent.

## 1. What the evidence supports (strongest to weakest)
| Claim | Evidence | Grade |
|---|---|---|
| Necessity: a few MLP units carry the agreement preference in Pythia-2.8b | V53/V54: 96 selected units, 0.81/0.71 logit drop, p = 0.001 vs 1000 matched-random sets, specificity z 34-39, fresh books | strong for one model |
| Concentration: ~8 units carry >90% of it; one unit alone 0.32 logits | V57/V58 | strong (post-hoc) |
| Not a zeroing artifact | V57 mean ablation 1.02x zero | moderate |
| **Sufficiency: swapping 7 number-selective units to the other number's code moves the verb choice by 1.31 logits (matched-random max 0.07)** | V59 | strong (post-hoc, single model) |
| Units are number-selective (active for one number, write that verb form) | V58 post-hoc table + V59 swap | moderate |
| Narrowness: little transfer to reflexive agreement | V59 R: 0.061 logits, above controls, below floor | weak-moderate |
| NOT supported: other model (1.4B), mechanism/circuit beyond direct path, monotone dose-response | V55, V56, V57 | negative, recorded |

## 2. Reusable assets (where the durable value is)
1. **The instrument**: pre-registered, null-calibrated neuron-causality pipeline (sign-flip noise gate, known-bad shuffles, positive/near-miss controls, matched-random controls, many-item specificity control, prediction locks, spend guards, hash-chained claim ledger). It produced informative negatives (V51-V52 NoCandidate on a one-item control, V55, V56) as well as positives. This is the novel contribution; the neuron result is the demonstration.
2. **A concrete, checkable neuron map** for Pythia-2.8b number agreement (unit ids, layers 10/18/26) that others can falsify in minutes.
3. **A packaged negative-results record** and an independent-review packet (manifest with hashes, preregistration order, hermetic tests).
4. **A bridge to this repo's thesis**: claims are digest-bound, ledgered and fail-closed; the next step toward "proof-carrying interpretability" is committing the ablation/swap experiments in a verifiable log (zkML proofs of a 2.8B forward pass are infeasible today; a tiny-model analogue or a commitment-plus-replay protocol is feasible).

## 3. Expected-value ranking of next steps
| Rank | Step | Cost | P(success) | Value if it works | Why |
|---|---|---|---|---|---|
| 1 | Independent review/replication of the packet (any outside reader) | ~0 | high | converts "owner-attested" into evidence others can cite | only route above the current ceiling; owner has chosen to skip it for now |
| 2 | **Cleaner intervention**: last-position-only swap and true activation patching with counterfactual (opposite-number) activations, plus a "swap one unit at a time" dose curve | ~USD 0.5-1 | high | removes the main V59 caveat (out-of-distribution constants at all positions); supports a causal-handle claim | cheapest way to harden the headline |
| 3 | Scale/family: Pythia-6.9B and one non-Pythia model with a **scale-aware floor fixed in advance** | USD 8-12 (needs a higher ceiling) | medium (V55 shows effect shrinks with size) | converts a one-model finding into a scaling statement | biggest scope gap |
| 4 | Other phenomena (gender/reflexive done; add negation, quantifier agreement, tense) to map what the unit set encodes | USD 1-2 | medium | specificity map; V59 says narrow | cheap, but incremental |
| 5 | Application: use the unit set as a number-steering/editing probe (e.g. targeted agreement-error injection and repair test on held-out text) | USD 1-2 | medium | shows a usable control, not just a diagnosis | link to downstream value |
| 6 | Write-up + OSS release of the pipeline (methods + negative-results framing) | time only | high | visibility, reuse, credibility; independent review likely comes from here | do alongside 2 |
| 7 | Proof-carrying commitment layer for interpretability claims (hash-chained replayable experiments; tiny-model zk analogue) | high effort | low-medium | differentiator for this repo's thesis | longer horizon |

## 4. Recommendation
Do 2 and 6 first (low cost, hardest to dismiss), then 3 only after the scale-aware criterion is written and committed, and treat 7 as the long-horizon bet. Keep the discipline that made V53-V59 informative: commit the protocol before the run, keep controls matched, report failures, never retune after seeing a result.
