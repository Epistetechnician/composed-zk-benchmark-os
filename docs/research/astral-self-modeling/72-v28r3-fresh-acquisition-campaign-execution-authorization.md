# V28R3 Fresh Acquisition Campaign Execution Authorization

State slice:
`astral-rgs-v28r3-fresh-acquisition-campaign-execution`.

Status: `OneShotAuthorized / NotRun`.

This authorization binds RGS implementation commit
`5c4ea4d7478fbdadbbeb9be214644230f4221c90` and Astral implementation commit
`1fdbf9d03fcf75c1eff70d0fa95e934269b17960`. It permits exactly one fresh
V28R3 run with the pinned Python/MLX runtime, cached Qwen checkpoint, immutable
predecessor inputs, exclusive repository-external ledger, and content-addressed
artifact.

All preregistered pre-ledger checks must pass before entropy is drawn. Novelty
must pass before any update exists. Every negative, crash, exclusion, null, and
validator rejection is final for the campaign and must be retained. This
authorization cannot be used to repair or rerun the campaign, open later
gates, or promote the result beyond the claim ceiling encoded by the
independent validator.
