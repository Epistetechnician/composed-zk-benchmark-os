# V27 Authorization Record

State slice: `astral-public-abi-final-embedding-feasibility-v27-authorization`.

Date: 2026-08-13.

## Authorized action

The latest user instruction authorizes continued end-to-end work. This record
narrows that authority to the new V27 public-ABI feasibility phase:

- inspect and validate the declared local ABI, header, library, and GGUF path;
- implement the offline ABI preflight and hermetic tests;
- record the exact capability result and claim ceiling.

This record authorizes no model loading, forward execution, control-vector
generation, assessment collection, artifact export, network access,
provider/API probing, V26 reuse, V25 reuse, Stage 0C, Stage 1, or Evidence
Ledger mutation. The separate [V27 execution authorization record](53-v27-execution-authorization-record.md)
contains the exact one-shot execution gate.

## Identity and ceiling

- protocol: `astral-public-abi-final-embedding-feasibility-v27`;
- state slice: `astral-public-abi-final-embedding-feasibility-v27`;
- status: `Executed / PublicAbiFinalEmbeddingInterventionFeasible`;
- claim ceiling: `LocalDevelopmentPublicAbiFinalEmbeddingFeasibility`;
- protocol: [V27 public-ABI feasibility](51-public-abi-final-embedding-feasibility-v27.md).

## Required transition gate

Execution may transition beyond preflight only when all of these are recorded:

1. ABI symbols resolve from the exact library digest;
2. the header digest matches the inspected declarations;
3. the GGUF path is regular, local, and digest-bound;
4. the runner has no network or provider imports;
5. the model-loading and output-retention policy is independently checked;
6. the exact vector/prompt/layer/tolerance configuration is sealed;
7. the independent validator rejects claim or execution escalation.

The execution record is [V27 execution record](54-v27-execution-record-2026-08-13.md).
It is a local feasibility result only and does not authorize V26, observer
training, Stage 0C, Stage 1, or any claim escalation.
