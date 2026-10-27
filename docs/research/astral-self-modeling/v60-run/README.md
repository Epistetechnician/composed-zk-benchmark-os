# V60 run records (LocalDevelopmentUnreviewed, exploratory, not independent)

## Cloud run (cmd-kq5i9, node v51-full-r1, 2026-10-26)
Exit 0, but the output (`out_v60.json`) was never retrieved: the node stopped and re-queued for about 53 h. The node was then dequeued (stopped, disk intact). Billed node total rose from USD 19.45 to 21.05 across the wake and idle time, slightly above the 1.50 V60 cap; exact V60 share unknown. No V60 result is claimed from this run.

## V60-local (protocol doc 200, addendum 1): CLOSED, selection mismatch, no result
Checks that passed: Pythia-2.8b config and weights match the packet SHA-256 values (revision 2a259cdd); the rebuilt V54 corpus (35 books, 2400 items, counts 800/800/800) reproduces manifest digest 59c514f0...; spaCy 3.8.16 / en_core_web_sm 3.8.0. Tokenizer files (tokenizer.json, tokenizer_config.json, special_tokens_map.json from the same revision) are not hash-pinned in the packet; their SHA-256 values are recorded here only for provenance: c24618a1..., 70e38394..., 6f50ab5a....
Failure: on Apple MPS (torch 2.14.1, bfloat16) the fit-split reselection of 32 units differed from the locked V54 selection, so the frozen guard raised `V50Error: k=32 reselection differs from the locked V54 selection` before any swap or patch measurement. Per the protocol, a selection mismatch closes V60 without retuning; no dtype, device, tolerance or threshold change was tried. Zero spend.
Reading: the unit scores depend on numerics; the H100 and MPS bfloat16 runs rank near-ties differently. A local result for these units therefore needs either the cloud output or a new, separately authorized protocol (for example float32 reselection with its own locked set), which would be a different experiment.
`corpus54-rebuild-public.json` is the public record of the local corpus rebuild (IDs, sizes, hashes, manifest).
