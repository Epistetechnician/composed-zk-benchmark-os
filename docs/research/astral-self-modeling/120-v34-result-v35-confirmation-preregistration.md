# V34 Result and V35 Fresh Confirmation Preregistration

V34 status: `ProtectedReplayQualified / Consumed / ValidDevelopment`.

Artifact `astral-rgs-v34-protected-replay-cc777697532e-r1`, manifest
`sha256:cc777697532eafd12bc2d18831e6227b70e832a19a57c6b6f2e803a5a80058cd`.
The selected 25% replay arm scored 0.75 direct, 0.75 paraphrase and 1.0
protected; the 50% arm failed acquisition.

V35 freezes the selected method on eight untouched words, indices 8 through 15,
and new keys. Model, target-free objective, 25% replay, seed, optimizer,
adapter geometry, 32-step budget, evaluator and thresholds are immutable.
Direct/paraphrase must each reach 0.75, V30 protection 0.95, loss must be
finite and nonincreasing, and adapter reload scores must agree within `1e-5`.

Maximum claim: `LocalFreshAcquisitionConfirmationV35`. This still does not test
a continual-learning stream, recovery, selector advantage, SOTA, or autonomous
self-improvement.
