# V24 provider and production validation protocol

State slice: `continual-learning-provider-production-validation-v24`  
Claim ceilings: `LocalDevelopmentProviderValidation` for continual-learning
provider checks and `Attested` for the existing Phala/dstack provider client.

The repository already contains the feature-gated Phala operator-live client
and runner in `crates/hsai-attestation-phala`. The package contract validates
that client with hermetic fake transport tests through
`pnpm run verify:provider`. A live run remains an operator action and requires
all of the following outside git:

- explicit operator acknowledgement;
- a non-secret invocation JSON file containing the endpoint, nonce,
  report-data binding, timeout, retry, and output-root fields;
- an allowlisted environment credential source with a real secret;
- a named target environment and rollback boundary; and
- an operator-controlled acceptance decision.

The existing runner writes only the redacted `operator-live/*` bundle. It does
not establish local Intel DCAP verification, PCCS collateral verification,
managed-service signature verification, TLS channel binding, deployment
correctness, production readiness, or accepted Evidence Ledger evidence.

No live provider call was executed in this promotion because the required
operator acknowledgement, endpoint, input JSON, and credential source were
absent from the environment.
