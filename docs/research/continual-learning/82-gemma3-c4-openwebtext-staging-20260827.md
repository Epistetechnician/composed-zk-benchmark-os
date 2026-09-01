# Gemma3 C4 WebText-like acquisition checkpoint

Date: 2026-08-27

State slice: `continual-learning-gemma3-paper-recirculation-acquisition-v1`.

Consumer slice: `continual-learning-gemma3-paper-recirculation-v1`.

## Status

The official OpenWebText manual input and the official Common Crawl WET path
manifests for TFDS `c4/webtextlike` are staged and mirrored. The required C4
JSONL export is not acquired. The paper-aligned acquisition gate remains
blocked and no scientific execution has started.

## Staged input

The TensorFlow Datasets C4 catalog identifies the Mega OpenWebText source as
the manual input for `c4/webtextlike`:

`https://www.tensorflow.org/datasets/catalog/c4`

`https://mega.nz/#F!EZZD0YwJ!9_PlEQzdMVLaNdKv_ICNVQ`

The canonical archive has the builder-required layout
`OpenWebText/Version 1/URLs/*.txt`. ZIP integrity passed. Its SHA-256 is
`087c1ac06b0be2c078810ad8f7dcdf74553ac8713e119fadfe90e570522841c4`.

The three URL-list SHA-256 values are:

- `RS_2011-01.bz2.deduped.txt`: `42d123d540c73f41a2b0013c9a2edbc81344dee96a95ac09e8701dce2e02b59d`
- `RS_2012-06.bz2.deduped.txt`: `237a8e17bd578014058001ec4381e2baacc276ed907bbd194429b92eaf791047`
- `RS_2014-01.bz2.deduped.txt`: `cb5083a11a529d8d1f530b72aa0812640305520f605bc9fe49e7d19b3fc5b6a6`

Active PrimaryED root:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-c4-webtextlike-manual-v1/raw-upstream`

DAed mirror:

`/Volumes/DAed/Archives/composed-zk-benchmark-os/gemma3-c4-webtextlike-manual-v1/raw-upstream`

The active and mirror trees are byte-identical. The root-independent
`openwebtext-provenance.json` records the source URL, TFDS version/config,
relative paths, sizes, and checksums.

### Common Crawl path manifests

The TFDS v3.1.0 builder identifies these 12 WET collections for the default
WebText-like configuration. Their compressed path manifests were downloaded
from `https://data.commoncrawl.org/crawl-data/CC-MAIN-{version}/wet.paths.gz`
and stored at the `commoncrawl/` subdirectory of both external roots. The
active and mirror files are byte-identical.

| Collection | WET objects | SHA-256 |
| --- | ---: | --- |
| `CC-MAIN-2018-34` | 71,520 | `e3a8addc6a33b54b1dd6488a98c875851ef1aca3b80133d39f6897330a8835fb` |
| `CC-MAIN-2018-39` | 56,320 | `84002b735b0478c40ed154d16cd5183000865fba7901e5f5b4853c8de1c0881d` |
| `CC-MAIN-2018-43` | 56,000 | `f04ef41e401643818ed7cf014e1f8d09e298483e180f8f1cf1691e2a314e01b1` |
| `CC-MAIN-2018-47` | 56,000 | `49cebe85bd380a58997a47494489d7a41cd1f59c23a6ff8d813fe9781cb66a63` |
| `CC-MAIN-2018-51` | 63,840 | `e55a4b92f4ef09d6e4df5909a2a1fc87edd22bcc3bdcd2008010e86cf3f10221` |
| `CC-MAIN-2019-04` | 64,000 | `5480f284eba2633fde2a20ca4e83e44c45190fa05d73308af6bf2374a970b3fb` |
| `CC-MAIN-2019-09` | 64,000 | `f7cff85e2985a861cd8e165c0b64eda218def82af97e75f4724f2a7e34fb55b8` |
| `CC-MAIN-2019-13` | 56,000 | `f6368a4fab92beb42b892ea3c027f79c41fc39d725120b91c5c2f556b9253213` |
| `CC-MAIN-2019-18` | 56,000 | `5ff4f0e1313ce84ef553221a0595f4a3c891b3e96fb20f85669c6c17654f291b` |
| `CC-MAIN-2019-22` | 56,000 | `bc66ea7d05adece388576d6ea0be67946eec248372789a8817cd7a4b1cdf2fa3` |
| `CC-MAIN-2019-26` | 56,000 | `78208955de55e7bfdf05c42d5f6887cf070e0f1c094a4c1e74f59b346fae6cb3` |
| `CC-MAIN-2019-30` | 56,000 | `29c5b4d594f3264c9c6da05cdff9c32c9fa9dd4e857572f8846064ba52adca96` |

The manifests identify 715,680 WET objects. They are only source indexes;
they do not contain page text and are not valid C4 train or validation files.

## Blocking condition

OpenWebText is only the URL filter. The official TFDS builder reads the
Common Crawl WET objects named by these manifests, filters pages by the
OpenWebText URLs, cleans and deduplicates pages, and emits the train/validation
splits. The upstream C4 preparation guidance documents approximately 7 TB of
Common Crawl input and approximately 335 CPU-days for the general build, with
distributed Beam preparation recommended. The local SSDs do not contain a
prepared `train.jsonl` or `validation.jsonl`, and this slice does not
authorize an unbounded local Common Crawl build.

No substitute mirror, synthetic record, partial shard, or NEWSROOM file is
being relabeled as C4 WebText-like data.

## Next gate

Supply a documented, checksum-bound C4 WebText-like `train.jsonl` and
`validation.jsonl` export, or open a separately named bounded-subset protocol
with its own claim ceiling. The bounded follow-up is documented in
`83-gemma3-bounded-webtextlike-acquisition-v1.md`; it remains distinct from
the exact C4 acquisition. Only after the applicable acquisition validator reports the
complete 13-dataset `gemma3-source-v1` bundle may the offline staging and
paper-shaped experiment be considered.

Training, model execution, Evidence Ledger mutation, benchmark claims,
provider calls, production traffic, and Astral claims remain disabled.
