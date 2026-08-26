# V26 task-routed adapter-bank candidate record

State slice: `continual-learning-candidate-task-routed-adapter-bank-v26`.

Classification: `TaskRoutedAdapterBankCandidateNoProductionClaim`.

Claim ceiling: `LocalDevelopmentTaskRoutedAdapterBankCandidate`.

## Execution

Three fresh cases were executed independently against the cached
Qwen2.5-0.5B-Instruct-4bit through the MLX training seam. The task/update
contract, 160-step objective, route-bound prompt, held-out split, and validator
were fixed before execution. The campaign used no network access.

External artifact root:

`/tmp/continual-learning-candidate-v26-20260820-r2`

Campaign report:

`.autoresearch/continual-learning-candidate-v26-20260820/campaign-report.json`

| seed | order | no-update acquisition | naive acquisition | naive retention | routed-bank retention | result digest |
| ---: | :--- | ---: | ---: | ---: | ---: | :--- |
| 20260840 | `0,1,2,3` | 4/8 | 8/8 | 2/8 | 8/8 | `8913f411c9dc2a8dafbe8bac97a96c35d1801c3ca558e685c9d2ede9eefde87d` |
| 20260841 | `0,1,3,2` | 4/8 | 8/8 | 2/8 | 8/8 | `d7ee353441160629c4749dc0be82c1e87ad35c6644e4236dcf93590b1b419d83` |
| 20260842 | `0,2,1,3` | 4/8 | 8/8 | 2/8 | 8/8 | `2fe1b17e10f6ed94e22c181e94d54d6937d4da264a10e42f2a05ac2abbdd6f11` |

## Validation

All three cases were independently validated. Every case passed:

- retrieval acquisition above no-update;
- routed-bank acquisition above no-update;
- routed-bank held-out retention above shared naive retention; and
- routed-bank held-out retention at least `6/8`.

The validator also confirmed exact route-bound prompt bytes, no raw-pair
leakage, held-out disjointness, twelve 32-row datasets, fresh non-resumed
adapters, route keys `T0` through `T3`, and result/manifest digests.

## Decision

V26 is a viable bounded local architecture candidate for task-routed adapter
memory under this protocol. It is not evidence that shared replay learns
continually, and it does not establish general continual-learning ability,
second-model replication, provider execution, production readiness, or a
breakthrough claim.

The next authorized scientific boundary is a separately preregistered
replication on another eligible cached model with the same route contract.
The provider/production lane remains independent and gated by its operator
inputs; V26 does not authorize live provider execution.
