# Retry Analysis

```json
{
  "n_paired_cases": 55,
  "accuracy": {
    "control": 0.09090909090909091,
    "localize": 0.2909090909090909,
    "corrective": 0.38181818181818183,
    "sham": 0.03636363636363636,
    "random_fact": 0.07272727272727272
  },
  "effects": {
    "localize_minus_control": {
      "estimate": 0.19999999999999998,
      "ci95": [
        0.0909090909090909,
        0.32727272727272727
      ],
      "bootstrap_seed": 20260810,
      "iterations": 10000
    },
    "corrective_minus_control": {
      "estimate": 0.2909090909090909,
      "ci95": [
        0.1636363636363636,
        0.4363636363636363
      ],
      "bootstrap_seed": 20260810,
      "iterations": 10000
    },
    "localize_minus_sham": {
      "estimate": 0.2545454545454545,
      "ci95": [
        0.14545454545454545,
        0.36363636363636365
      ],
      "bootstrap_seed": 20260810,
      "iterations": 10000
    },
    "corrective_minus_localize": {
      "estimate": 0.09090909090909094,
      "ci95": [
        0.0,
        0.18181818181818182
      ],
      "bootstrap_seed": 20260810,
      "iterations": 10000
    }
  },
  "mcnemar": {
    "localize_vs_control": {
      "a_only": 12,
      "b_only": 1,
      "two_sided_p": 0.00341796875
    },
    "corrective_vs_control": {
      "a_only": 18,
      "b_only": 2,
      "two_sided_p": 0.0004024505615234375
    },
    "localize_vs_sham": {
      "a_only": 14,
      "b_only": 0,
      "two_sided_p": 0.0001220703125
    },
    "random_fact_vs_control": {
      "a_only": 2,
      "b_only": 3,
      "two_sided_p": 1.0
    }
  }
}
```
