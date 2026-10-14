# V41R8 H100 Profile Execution Authorization

State slice: `V41R8H100ProfileExecution`.

Status: `OneModelBackedRuntimeProfileAuthorized / PilotUnauthorized`.

The passed no-model parity receipt authorizes one fresh model-backed runtime
profile against RGS implementation commit
`d13fc6c8468f2dd3aa26a818fd468f09dc4af92e`, GPT-OSS-20B revision
`d0e2aa76789354d715f8b22553b9feb6c462fcf0`, context `ctx-f71c03bd`, and OCI
manifest
`sha256:137a686d2840f0ecf38756edd4e738c87537ed974ae201527b140049dca78558`.

The job is limited to one clock-locked H100, zero restarts, 300 run minutes,
and `$13.50`. It may load the real tokenizer and checkpoint and run only the
frozen V41R8 four-case, one-step profile. Tune and assessment remain closed.
The repository-external artifact must be independently checked by
`tools/astral-v41r8-h100-profile/validate.py` before any status update.

The first terminal model-backed outcome consumes the identity. Failure is
retained and cannot be overridden or retried. A pass establishes only bounded
runtime operability through `RemoteH100RuntimeProfileOnlyV41R8`; it does not
authorize or establish acquisition, retention, continual learning, Astral
selection, self-improvement, or a breakthrough. Pilot authorization remains a
separate prospective decision.
