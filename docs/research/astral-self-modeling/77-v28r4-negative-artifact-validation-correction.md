# V28R4 Retained-Negative Artifact Validation Correction

State slice:
`astral-rgs-v28r4-negative-artifact-validation-correction`.

Status: `Implemented / ModelRerunProhibited / ExistingArtifactOnly`.

The first V28R4 validation pass conflated a deliberately retained nonzero child
process with artifact corruption. The correction accepts a failed child only
when its complete process record is manifest-bound, its nonzero return code and
absent result agree, the packet records a null result hash, and all recomputed
qualification gates remain false. Missing or inconsistent process evidence
still invalidates the artifact.

The correction does not alter the sealed packet, artifact manifest, thresholds,
or model output. It can establish that the existing bytes are a valid negative
infrastructure artifact; it cannot turn that artifact into a qualification
pass or scientific evidence.
