# Gemma 3 causal feature-effects V1 independent acceptance and launch

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v1`.

The first GPT-5.6 Luna review rejected packet
`497071dcc14bdd9601747ccee060f2c9b0e7c1ac0c86a871b91b47f9a0911d10` for
missing fresh V1 model/runtime/asset/corpus custody bindings, weak exact-node
and finite-spend admission, weak reviewer identity checks, and missing
pre-load identity enforcement. Those findings were substantive and were
implemented under this V1 slice. The intermediate corrected packet and the
second Luna report remain stale because the runtime probe omitted
`transformer-lens`.

The final packet is
`0d0b90e0d24e3c5d1a10558cbca70670116493a55d98c76f7b76841beafcf683`, with
contract digest
`877fa58ad5cc6236357ee5bcc54a32cc86beaac857b6d3bc694e354c8154c1cf` and
source manifest digest
`5193b75d29f3bc8c7df7b81e1eff549c23764f4dca3625604d7f8a80c0da806e`.
The packet binds the exact model digest
`5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81`, the
re-custodied runtime digest
`104c32975db6f7a80937fee9725312207527d194636be0059b110e70208c0aa0`, fresh
asset-QC digest
`14bbb0a00bcca0863ecd4be8ce87e12b6c3ee89eb9e7bce2a92307db7dc251f8`, and
fresh corpus manifest digest
`9023d99a41d7901a60e51487e19fd8e20874387f9df5e40a7ad459fa1c763c69`.

The four current V1 identity receipts are packet inputs and have receipt
digests:

- model: `4f848576a7a64b38c29f3bf960634ebb7797005be40da2a035ca942e5ec8c1ce`;
- runtime: `9b4f011425f95bb3c05dc876c256f14302f9b56ebf3bb5b8c38e19aed0adae62`;
- asset: `abc9c68f123c51fb14bfcf3c8a321fe62f0d54d4af5530c8a068c6d25f7f2615`;
- corpus: `bd78cf164587f9ee2968793e1e79d938efdab35f3159bf18695f9e07a5ebeb01`.

The final independent GPT-5.6 Luna review is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/review/luna-independent-review-v1-acceptance.json`.
It returned `ACCEPT` with no findings after 18 passing hermetic tests and
adversarial rejection probes. The packet-bound Ed25519 receipt is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/review/independent-acceptance-v1.json`;
its receipt digest is
`d89300ae2802d5349668ba6024560b2ecf203c2db3a984b2bf2b1aa4ef9972ff`, and
the reviewer public key is
`8c2beb89ccf4866f0041e8299ccad57d2dd19c3dc0e2b46bedfd6354cf2390de`.
Both review outputs are owner-only `0600`; the operator is `shaanp`, while
the reviewer role is
`independent-causal-feature-effects-reviewer-v1`.

The rerun preflight is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/aggregate/preflight-v1.json`.
It returned `ACCEPT`, with no findings, valid custody, the exact H100 node
allocation, and `assessment_opened=false`. Preflight does not itself claim a
scientific result or open assessment.

Only after that accepted preflight, GiveMeANode was launched by the exact
packet-bound node name
`astral-trace-completeness-gemma3-causal-feature-effects-v1`, resolving to
node `7289c582-2e04-4d6a-ac3c-6ca8d4139356`. At record time the node was
`restoring (from snapshot)`; the queued command was a non-model GPU identity
check. No V1 model execution, raw trace, assessment effect, or scientific
result has been claimed. Model-bearing qualification remains subject to the
remote runtime, staged asset/model paths, offline flags, event accounting,
feature reconstruction, causal controls, raw expiry, and aggregate validator.

V4 remains permanently frozen and is not a V1 scientific input. The V1 claim
ceiling remains
`LocalDevelopmentGemma3CausalFeatureEffectsQualificationV1` until a later
held-out assessment satisfies its separately gated criteria.
