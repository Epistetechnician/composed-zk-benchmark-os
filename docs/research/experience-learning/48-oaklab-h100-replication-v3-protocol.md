# Oak Lab H100 replication V3 protocol

State slice: `oaklab-experience-learning-h100-replication-v3`.

This is a new protocol identity. V2, V6, and Phase 836 are historical and
cannot be used as scientific inputs. This package is static and no-spend:
implementation, custody, provider access, and effects remain prohibited until
an independent review returns `ACCEPT` for the frozen packet.

## Estimand and treatment assignment

Each unit is an episode with one immutable ordered stream and one immutable
initial learner checkpoint. The runner clones that checkpoint and executes the
fixed reference `sgd_b1` and the treatment `lagged_selective_credit` on the
same stream bytes. A SHA-256-counter draw randomizes which clone executes first
(`propensity=1/2`); the second clone receives the identical stream and no
information from the first. The pair is therefore an executable paired unit,
not two unrelated arms.

The primary estimand is the mean paired post-washout regret difference:

`ATE = mean_e mean_{b=2..33}(loss_treatment(e,b) - loss_control(e,b))`.

Block 1 is a fixed washout. There are 32 post-washout blocks of 128 items.
Learner state resets at episode boundaries. Current-block outcomes cannot
affect treatment decisions. The controller may use only the previous block’s
residual, uncertainty, and resource counters. This lag and the fixed paired
trajectory prevent sequential-utility and carryover confounding.

## Qualification, locking, and real execution

Synthetic qualification covers predictable signal plus noise, delayed reward,
feature-relevance drift, and sparse events. Real assessment requires fresh,
row/document-disjoint NoisyMNIST and event-camera or sensor panels with
fit/tune/assessment separation. Fit chooses nothing for assessment. Tune emits
one signed lock containing the selected controller bytes, hyperparameters,
seed roster, and prediction digest. An independent validator must accept that
lock before assessment effects exist.

## Exact custody and resource contracts

Every campaign manifest is canonical UTF-8 JSON with lexicographic keys,
compact separators, a trailing newline, and `manifest_sha256` equal to SHA-256
of the body with that field removed. The result manifest binds the campaign,
compiled protocol, code, model, data, backend, guard, lock, and every receipt.

Provider receipts are canonical JSON with exact fields, UTC timestamps matching
`YYYY-MM-DDTHH:MM:SSZ`, a provider Ed25519 public key and signature over the
receipt body, allocation/node identity, start/stop records, charged USD, hard
ceiling, and launch-manifest digest. Charged cost must be finite, nonnegative,
and no greater than the declared ceiling.

The result root is closed-world. Exactly the allowlisted files may exist;
symlinks, extra files/directories, missing files, digest mismatches, malformed
JSON, non-finite numbers, and unbound manifests are terminal failures.

The primary quality and adaptation tests use Holm correction at `alpha=0.05`,
paired randomization tests, a predeclared minimum effect of `0.05`, and planned
power `0.80`. Resource non-inferiority margins are 5% for active operations,
updates, storage bytes, and latency, and 5% for joules per learned event.
Joules are trapezoidal integration of finite nonnegative watt samples over
monotone UTC nanoseconds; the denominator is the count of successfully learned
events. Operation counts remain separate from measured energy.

## Execution order and stop rules

1. Freeze this protocol, compiler, compiled artifact, validator, tests, and
   current `AGENTS.md` digest.
2. Obtain an independent packet-bound `ACCEPT`.
3. Implement and qualify synthetic streams; stop on any contract failure.
4. Obtain an independently validated tune lock.
5. Obtain separate real-execution authorization, fresh custody, GiveMeANode
   allocation, and a positive hard USD ceiling.
6. Run no-spend preflight, then exactly one bounded H100 batch job.
7. Independently validate provider receipts, raw joules, result-root closure,
   and the multi-family publication gate.

Any rejection or failed gate closes V3 as `no_candidate` without retuning. No
SOTA, breakthrough, benchmark, production, or cross-runtime equivalence claim
is permitted without the complete gate.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v3`.
