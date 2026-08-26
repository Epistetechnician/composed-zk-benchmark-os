# V27 second-model routed adapter-bank replication record

State slice: `continual-learning-replication-task-routed-adapter-bank-v27`.

Runtime preflight passed for the cached
`Llama-3.2-1B-Instruct-4bit` model:

- model manifest digest: `ea36d761a8af224a35f644ff77e9871d80452288174012e6c82884327bfde680`;
- runtime receipt digest: `80f423bbf5a3dc1edc0965610068323d9225181df2607bca4512b90eec714a25`;
- offline inference only; no network access and no training in the preflight.

The first attempt at
`/tmp/continual-learning-replication-v27-20260820/seed-20260850-order-0321`
was rejected by the independent validator because the wrapper had rebound its
contract configuration after computing the manifest digest. The runner defect
was repaired without changing the scientific contract. The rejected artifact
remains immutable and is not used as evidence.

The corrected sealed campaign completed at
`/tmp/continual-learning-replication-v27-20260820-r2` and is recorded in
`.autoresearch/continual-learning-replication-v27-20260820/campaign-report.json`.

Status: `NotReplicated`.

All three corrected cases were structurally valid and independently
validator-checked. All three failed the candidate gates. Each case produced
`0.25` no-update acquisition, `0.25` routed-bank acquisition, `0.25` naive
held-out retention, and `0.25` routed-bank held-out retention. The retention
delta was therefore `0.00` in every case, and routed-bank retention was below
the preregistered `6/8` floor in every case.

| seed | order | result digest | manifest digest | valid | candidate eligible |
| ---: | :--- | :--- | :--- | :---: | :---: |
| 20260850 | `0,3,2,1` | `5cd03df117cf7b795d95a87975ab9dc65b18afe7428f419bd81ae03482789282` | `925e0270633e1d2dd25253b1fe85f2ce0caff4d3c3e44a96c668ec8e6f80d7e5` | true | false |
| 20260851 | `0,2,3,1` | `d6339d86e4be63e53b3f61f750cfcbb4e14effd66d1be5f0be5a3beb21ce39b6` | `ac9446e92ae2896a25437e4f337dacb708727ed8201dc9b940958a2308b79edc` | true | false |
| 20260852 | `0,1,3,2` | `7c0378acdb0cb3ea1fd224fd2d721050a602b7044940f028b184975a649ad771` | `ec997064ea4be9f16b4b1f69c67edd796471441ecd3f4ff45cf97b179152ce38` | true | false |

The four gate outcomes were identical for every case: retrieval above
no-update `true`; routed-bank acquisition above no-update `false`;
routed-bank retention above naive `false`; routed-bank held-out solubility
floor `false`.

Claim ceiling: `LocalDevelopmentTaskRoutedAdapterBankReplication` for this
bounded negative replication record. It does not promote V26 to a
second-model result and does not establish general continual-learning ability,
a benchmark claim, provider execution, production readiness, or a
breakthrough. The sealed protocol stops here; no additional seed mining or
adaptive tuning is authorized by this record.
