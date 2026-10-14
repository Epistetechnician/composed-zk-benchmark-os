# V40R2 Fit Probe Qualification Record

State slice: `V40R2FitProbeOverlayLock`.

The content-addressed R2 artifact is:
`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v40r2-fit-probes-fadf0a814514-r2`.

Independent validation reports:

- `valid: true` with no errors;
- 128 fit cases;
- 16 balanced protected cases disjoint from V40R2 targets;
- 400 prompt-token records;
- maximum input length 83 of 96;
- exact evaluation-forward budget 3,256,320 tokens;
- no model forward pass.

The R1 construction is retained as invalid provenance. R2 resolves the
fit-probe and evaluation-budget locks only. Model acquisition, label
generation, router fitting, tune access, assessment access, and scientific
claims remain unauthorized.

## R3 correction

R2 omitted the protected-margin feature-probe compute surface. R3 is the
runner-authoritative artifact:
`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v40r2-fit-probes-97e7ebe81c9f-r3`.

Independent validation reports:

- evaluation-forward tokens: 3,256,320;
- feature-probe forward tokens: 25,728;
- maximum input length: 83;
- qualification:
  `sha256:d643943239ea1aea3dc3ec03737a2cedd103b1877903c4772415beb2f198ee87`;
- no model forward pass.

R2 remains valid for its narrower evaluation-probe scope but is superseded for
runner authorization.
