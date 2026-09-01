# Gemma3 paper recirculation acquisition v1

State slice: `continual-learning-gemma3-paper-recirculation-acquisition-v1`.

This slice acquires and normalizes the corpus required by the separately
authorized `continual-learning-gemma3-paper-recirculation-v1` execution lane.
It permits network access only inside
`experiments/continual_learning/acquire_gemma3_paper_recirculation_v1.py`.
Raw files, normalized JSONL, staged windows, and results remain outside the
repository. The acquisition command never loads a model, trains, runs the
scientific campaign, changes the Evidence Ledger, or raises a benchmark or
production claim.

## Frozen source map

The paper’s fit counts are 484 arXiv, 488 C4, and 500 PG-19 1024-token
windows. The assessment panel is arXiv, BigPatent, BillSum, BookSum, C4
WebText-like, GovReport, LAMBADA, NEWSROOM, PG-19, and PubMed; C4 uses
validation while the other assessment sources use test. The acquisition tool
records the exact source revision, split/configuration, raw-file digest, and
normalized-file digest in `acquisition-manifest.json`.

| Contract key | Pinned source | Split/configuration | Selection |
| --- | --- | --- | --- |
| `fit/arxiv`, `assessment/arxiv`, `assessment/pubmed` | Scientific Papers 1.1.1 archive URLs from the upstream loader | `arxiv/train`, `arxiv/test`, `pubmed/test` | Fit is a fixed prefix; assessment is complete |
| `fit/c4`, `assessment/c4/webtextlike` | [TFDS C4 catalog](https://www.tensorflow.org/datasets/catalog/c4) | `webtextlike/train`, `webtextlike/validation`, TFDS 3.1.0 | Fit is a fixed prefix; assessment is complete |
| `fit/pg19`, `assessment/pg19` | [DeepMind PG-19 dataset](https://huggingface.co/datasets/deepmind/pg19) at commit `4d28bd77e66947ad3835cf78ed7aaeb4dd87ad8b`, with text files from the documented DeepMind storage root | `train`, `test` | Sorted file-list prefix for fit; complete pinned test list for assessment |
| `assessment/big_patent` | [NortheasternUniversity/big_patent](https://huggingface.co/datasets/NortheasternUniversity/big_patent) at commit `2a5336492ddc4e21cebd3865fd2a7e8b070bfede` | `all/test` | First 10,000 records in pinned shard order |
| `assessment/billsum` | [FiscalNote/billsum](https://huggingface.co/datasets/FiscalNote/billsum) at commit `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f` | `default/test` | Complete pinned split |
| `assessment/booksum/book` | [kmfoda/booksum](https://huggingface.co/datasets/kmfoda/booksum) at commit `c62321036e5647db5767ecaff139912b554dc938`, with [BookSum](https://github.com/salesforce/booksum) as homepage | `default/test` | Complete pinned split |
| `assessment/gov_report` | [launch/gov_report](https://huggingface.co/datasets/launch/gov_report) at commit `32feeaede49fed993aef070bc4da09263fd0429a` | `plain_text/test`, CRS and GAO | Complete pinned test files |
| `assessment/lambada` | [EleutherAI/lambada_openai](https://huggingface.co/datasets/EleutherAI/lambada_openai) at commit `900124bf3b8235c6daf21033af9948b3f07346c4` | `en/test` | Complete pinned English test file |
| `assessment/newsroom` | [NEWSROOM manual-download instructions](https://lil.nlp.cornell.edu/newsroom/download/index.html) | `test` | Complete registered operator-supplied test file |

The TFDS C4 catalog explicitly requires the WebText-like manual input, and
the NEWSROOM loader explicitly requires registration/manual data. The command
fails closed unless the operator supplies external roots containing
`train.jsonl` and `validation.jsonl` (or gzip variants) for C4 and
`test.jsonl` (or gzip variant) for NEWSROOM. It does not bypass registration,
use an unofficial substitute, or infer equivalence from a mirror.

## Acquisition gate

Run the acquisition command with external roots only:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  /Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/acquire_gemma3_paper_recirculation_v1.py \
  --raw-root /Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/gemma3-raw-v1 \
  --source-root /Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/gemma3-source-v1 \
  --c4-manual-root /ABS/external-c4-webtextlike \
  --newsroom-manual-root /ABS/external-newsroom
```

The command performs an independent validation before publishing the source
root. A valid result must report `valid: true`, `dataset_count: 13`,
`training: false`, `scientific_execution: false`, and
`evidence_ledger_mutation: false`:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  /Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_gemma3_paper_recirculation_acquisition_v1.py \
  --source-root /Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/gemma3-source-v1
```

Only after that gate passes may the existing offline staging command be used.
This document does not authorize that execution step.
