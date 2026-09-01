# Oak Lab H100 replication V10 synthetic stale-input closure

State slice: `oaklab-experience-learning-h100-replication-v10`.

The V10 fit-only synthetic qualification produced result digest
`5c74e910ea1e8c2c8232484a9d0654ca73eef392568165ef4663ff31b98cd400` with
disposition `no_candidate`. Its result validator passed with 288
family/seed rows, assessment absent, real execution prohibited, and hardware
energy not run.

After qualification, the current `AGENTS.md` bytes changed from the digest
frozen in the accepted V10 packet
(`43b7553003e34793ac60b37411b4cbed1b1af3b3605af907fe683f29b9d57a70`) to
`3ca4f128dc0ce64aecbbf719d33f958465d24a5d210a7f8807dc927bb003db80`.
The protocol validator therefore fails closed on the campaign-manifest
binding. The V10 packet and qualification are stale against the current
repository state and cannot authorize further work.

V10 is closed as `SyntheticQualificationStaleNoCandidate`. No V10 real
stream, provider, H100, energy, assessment, or publication execution occurred.
Do not patch or retune V10. Any continuation requires a fresh protocol
identity, a new freeze including the current `AGENTS.md`, a new independent
review, and a new synthetic qualification.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v10`.
