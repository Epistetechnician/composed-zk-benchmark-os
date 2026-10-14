# V41R17 Prebuilt-Image Gradient Profile Infrastructure Failure

State slice: `V41R17ProviderResolvedGradientProfileExecution`.

Status: `Consumed / InfrastructureFailureBeforeAttempt / NoScientificResult`.

Job `job-842y9` cache-hit the exact pinned public image in one second, with no
bytes or layers transferred. Its distinct prebuilt-image import then failed on
the same provider internal-registry failure class as V41R16: HTTP 500 from a
blob `HEAD` request, this time for a different blob digest.

The two-path reproduction excludes the V41R16 Dockerfile, context extraction,
dependency installation, tests, and scientific runner as causes. CNCF
Distribution specifies blob `HEAD` as the layer-existence check before upload
and says non-502/503/504 5xx responses are terminal:
<https://distribution.github.io/distribution/spec/api/>.

Attempt count remained zero. No H100 runtime, model, source download, gradient,
artifact, or scientific result exists. Mission
`astral-v41r17-prebuilt-gradient-profile-r1` closed at USD 0.00. Provider ticket
`tkt-uktwn` retains both jobs and requests either a repaired passing canary or
direct reuse of a previously published per-org digest without another push.

No third submission is authorized. V41R16 remains `NotRun`, with only local
implementation and independent-validator evidence.
