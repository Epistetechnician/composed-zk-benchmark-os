# V41R33R1 Fresh Source-Freeze Record

State slice: `V41R33R1FreshSourceFreeze`.

The historical V41R27R19 source archive is unavailable and cannot be recreated
without changing its identity. A new source freeze was therefore created for
any future experiment. This record is provenance only; it contains no H100
result and does not revise V41R27.

## Frozen inputs

- RGS commit: `754220f7fc360d8dd15e5837190b895ea0550f30`;
- archive format: Git commit tar archive;
- archive SHA-256:
  `sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580`;
- extracted-tree manifest SHA-256:
  `sha256:652633475af44cd6053b9dec6f44c7420c2668eb0e9253c4b994e9199ff9b9f5`;
- local custody path:
  `/Users/shaanp/.codex/source-freezes/v41r33r1-rgs-754220f7.tar`;
- source worktree branch:
  `codex/astral-rgs-v28-acquisition-novelty-v1`;
- source worktree was clean at freeze time.

The archive must be copied into the future GMAN node, re-hashed from its actual
archive path, extracted into a clean checkout, and checked against both the
locked commit and extracted-tree manifest before any worker starts. A missing,
altered, dirty, or unverified archive/tree is an
`InfrastructureSourceFreezeIncomplete` result and consumes no scientific arm.

## Governance

This identity only establishes fresh provenance. It does not authorize a
worker, modify the frozen method, alter the V41R27 census, open qualification,
or support a breakthrough claim. A separate preregistration must bind this
archive, a content-addressed wrapper, runtime identity, validator, artifact
custody, and budget before H100 execution.
