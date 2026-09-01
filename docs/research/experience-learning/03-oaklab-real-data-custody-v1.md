# Oak Lab real-data custody V1

State slice: `oaklab-experience-learning-benchmark-v2`

## Receipt

The first real-data custody slice is complete. The source archives and derived
panels are stored outside the repository at:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1`

The root is read-only after acquisition. Its manifest digest is:

`a8ed7027318809bc4fc03b424c683353f1f19698a791ea862ea3dc4ac5230b31`

Independent readback was run in a fresh Python process with:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate_real_data_v1 \
  --root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1
```

The validator recomputed the manifest digest, read each raw archive twice,
recomputed each derived digest, and passed every derived panel through the
contiguous-order JSONL custody loader.

## Custodied streams

| kind | source | panel | feature dimension | target construction |
| --- | --- | ---: | ---: | --- |
| `noisy_mnist` | LSU n-MNIST AWGN archive | 256 | 784 | published train digit label; pixels scaled by fixed `255.0` |
| `sensor` | UCI Human Activity Recognition Using Smartphones | 256 | 561 | published activity label; no data-dependent normalization |
| `long_horizon` | UCI Individual Household Electric Power Consumption | 256 | 7 | next valid minute's `Global_active_power` |
| `event_camera` | EDHT21 DVS hand-tracking AEDAT recording | 256 | 5 | next fixed 256-event window's event rate |

The event-camera derivation uses AEDAT 2.0 big-endian address/timestamp pairs,
fixed 256-event windows, and fixed sensor/timestamp scales. It does not use
magnetic ground truth, future windows as features, or learned preprocessing.

The manifest records the exact raw and derived SHA-256 digests, source URLs,
landing pages, citations, licenses, parser parameters, row counts, and feature
dimensions. Raw redistribution remains subject to source-license review.

## What this does and does not establish

This receipt establishes source custody and deterministic, ordered panel
construction. It does not establish that any learner wins on these streams,
that a stream is representative, or that a backend is efficient. The next
authorized slice is backend parity, followed by a declared hardware joule
measurement. Publication remains closed until the preregistered multi-stream
quality/resource gate passes on fresh cohorts.

## References

- [LSU n-MNIST landing page](https://www.csc.lsu.edu/~saikat/n-mnist/)
- [UCI Human Activity Recognition Using Smartphones](https://archive.ics.uci.edu/dataset/240/human%2Bactivity%2Brecognition%2Busing%2Bsmartphones)
- [UCI Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual%2Bhousehold%2Belectric%2Bpower%2Bconsumption)
- [EDHT21 Zenodo record](https://zenodo.org/records/4918320)
