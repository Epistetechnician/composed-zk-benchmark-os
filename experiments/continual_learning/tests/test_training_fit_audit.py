from experiments.continual_learning.training_fit_audit import digest, summarize


def test_v12_summary_preserves_accuracy_fields():
    assert summarize({"correct": 2, "n": 8, "accuracy": 0.25, "rows": []}) == {
        "correct": 2,
        "n": 8,
        "accuracy": 0.25,
    }


def test_v12_digest_is_order_stable():
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})
