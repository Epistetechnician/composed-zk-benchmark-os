# V29 Positive-Control Instrument Repair Execution Record

State slice:
`astral-rgs-v29-positive-control-instrument-repair-execution`.

Status: `Completed / InstrumentStillBlocked / AstralValid / ExternalReviewNotRun`.

## Immutable result

The one authorized model process completed against RGS commit
`9ca244ff556d3fae68304805f45db6609d776f29` and Astral commit
`0bc48cf0e8bc006b752bcaecb42f9c8bac21ddec`.

- artifact: `astral-rgs-v29-positive-control-80ac177a2c77-r1`
- manifest: `sha256:80ac177a2c77b63d965f21d2ad5313c579751cf2cd1eee3546bd4bc27f35c755`
- packet: `sha256:c5df613937876738242254269bf5f1f25b41384193f034317e93069c9d28c46b`
- validation report file: `sha256:252b968ff71af4c936ccab501e5f1cf80516fb336a75e115719237f261655f82`
- fixture: `sha256:b1567784d35275bab2a4a1e0a98998d7e808c8279e1975d513e9c0aff8fbb675`

Astral independently rederived the fixture and decisions, rehashed all 11
manifest entries, and returned `valid=true`, `errors=[]`,
`InstrumentStillBlocked`.

## Results

| Format | Literal | Direct | One hop | Two hop | Eligible |
|---|---:|---:|---:|---:|---|
| legacy raw | 0.5000 | 0.2500 | 0.2500 | 0.2500 | no |
| chat template | 0.2500 | 0.2500 | 0.2500 | 0.2500 | no |
| chat template plus `Answer: ` | 0.2500 | 0.3125 | 0.6875 | 0.7500 | no |

No format met every prospective threshold. Training and acquisition remained
false, and the candidate corpus and assessment remained absent.

## Post-result boundary diagnosis

Tokenizer-only inspection showed that the answer cue ended in tokenized space
and then scored bare labels, whereas canonical `Answer: A` tokenization uses a
single leading-space label token. That is a concrete response-boundary defect,
not a basis for revising this outcome. V29 stays consumed and negative. Only a
new preregistered identity may test canonical leading-space scoring.

The truthful claim remains a valid local negative instrument result. There is
no acquisition, continual-learning, self-improvement, SOTA, breakthrough,
confirmation, replication, or external-review evidence.
