# V29 Positive-Control Instrument Repair Preregistration

State slice:
`astral-rgs-v29-positive-control-instrument-repair-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

## Falsified premise

The V28R7 artifact is immutable and remains a valid `PilotNoSignal` result.
Read-only inspection shows a stronger instrument diagnosis: the unchanged
checkpoint, context, retrieval, and five persistent arms predicted `A` on all
9,216 balanced rows. Context and retrieval therefore failed their positive
control purpose at exactly `0.25` accuracy. A powered acquisition campaign is
blocked until the response instrument itself qualifies.

## Frozen diagnostic

RGS will deterministically derive 16 balanced non-candidate cases for each of
four rungs: explicit literal symbol, direct dossier lookup, one-hop lookup, and
two-hop composition. The same 64 cases are scored under `legacy_raw`,
`chat_template`, and `chat_template_answer_cue`, in that frozen complexity
order. All expected labels occur exactly four times per rung.

The committed Qwen tokenizer must serialize chat formats through its own chat
template. `chat_template_answer_cue` appends only `Answer: ` after the assistant
generation marker. Each format then uses the existing single-token A-D logits,
batch 8, deterministic argmax, and no learned or post-hoc calibration.

## Locked gate

A format qualifies only with accuracy at least `0.95`, `0.90`, `0.80`, and
`0.70` on the literal, direct, one-hop, and two-hop rungs respectively. The
first qualifying format in frozen order is selected. No qualifier yields
`InstrumentStillBlocked`; a qualifier yields
`PositiveControlInstrumentQualified`.

Astral must independently rederive every fixture row, verify all prompt/token,
score, prediction, census, identity, source, process, manifest, and decision
bindings, and reject any missing or extra model process. Validation may not
invoke the model or mutate the artifact.

## Boundary

V29 uses no candidate corpus, training, update, adapter, assessment, recovery,
or selector. Its maximum claim is
`LocalPositiveControlInstrumentQualificationV29`. Passing only authorizes a
fresh, separately preregistered acquisition pilot. It cannot prove continual
learning, self-improvement, SOTA, or a breakthrough.
