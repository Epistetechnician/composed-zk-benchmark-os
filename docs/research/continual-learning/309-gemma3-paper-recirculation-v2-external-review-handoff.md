# Gemma 3 paper-recirculation V2 external-review handoff

State slice: `gemma3-paper-recirculation-schema-resolution-v2`

Status: `ReadyForExternalCustodian / VerdictAbsent`

## Exact packet

The external custodian must transfer these five files byte-for-byte and no
others as the scientific review packet:

1. `docs/research/continual-learning/303-gemma3-paper-recirculation-schema-resolution-v2-protocol.md`
2. `docs/research/continual-learning/304-gemma3-paper-recirculation-schema-resolution-v2-manifest.json`
3. `experiments/continual_learning/verify_gemma3_paper_recirculation_schema_v2.py`
4. `experiments/continual_learning/acquire_gemma3_paper_recirculation_schema_v2.py`
5. `experiments/continual_learning/tests/test_verify_gemma3_paper_recirculation_schema_v2.py`

The current packet identity is:

- protocol: `gemma3-paper-recirculation-schema-resolution-v2`;
- corpus schema: `gemma3-paper-recirculation-corpus-v2`;
- protocol SHA-256: `1586965f528ccf012475f7366cd6b65035a9942929ab8f54cbd23ab847252a56`;
- manifest SHA-256: `a042f223791149cbbe31ebbd81f9c6ed93ab4faee996434067cd14d6ffdbde4e`;
- packet SHA-256: `d37365a7cf12d0dc67cb78b444a20683aee7dd05cb5a32d63571be744906d33f`.

The local pre-review result is `valid_preacquisition_packet` with
`acquisition_authorized=false`.

## Required external sequence

1. An unrelated administrator provisions a fresh encrypted host or VM that the
   operator cannot access.
2. That administrator generates the final-review Ed25519 key and publishes
   only its public entry, with `independently_administered=true` and
   `conflict_free=true`, to the external registry.
3. The operator and advisory reviewer seal their packet-bound mailboxes and
   compare the packet and seal digests out of band. No writes continue after
   sealing.
4. The administrator verifies the host key through a separate channel and
   transfers only the exact sealed bundle to the final-review host.
5. The final reviewer starts a fresh process and runs `verify-seal` against the
   copied bundle and external registry before reading the packet as evidence.
6. The final reviewer independently checks the five packet files, current
   instructions, custody/licensing boundaries, and claim ceiling.
7. The final reviewer emits exactly one signed `ACCEPT` or `REJECT` verdict
   bound to packet SHA-256
   `d37365a7cf12d0dc67cb78b444a20683aee7dd05cb5a32d63571be744906d33f`.

## Review exclusions

The verdict may authorize only the separately named acquisition command and
external owner-only custody roots. It must not authorize model execution,
Weco execution, provider calls, spending, assessment, publication, or Evidence
Ledger mutation. The operator cannot generate the final-review key or sign the
verdict.

## Reviewer command shape

On the fresh final-review host, after the administrator has transferred the
sealed bundle and registry:

```text
./scripts/python -B tools/independent_review_communication_v1/cli.py verify-seal \
  --mailbox /external/final-review-mailbox-P0 \
  --packet-digest sha256:d37365a7cf12d0dc67cb78b444a20683aee7dd05cb5a32d63571be744906d33f \
  --max-messages 6 \
  --deadline <frozen-deadline> \
  --registry /external/key-registry.json
```

No verdict exists in this repository. Until the external signed verdict is
returned and independently validated, acquisition remains closed.
