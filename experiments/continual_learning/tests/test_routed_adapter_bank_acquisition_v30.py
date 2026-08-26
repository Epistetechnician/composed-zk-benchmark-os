from experiments.continual_learning.routed_adapter_bank_acquisition_v30 import raw_text_training_example


def test_raw_text_repair_keeps_exact_route_prompt_before_label():
    fact = type(
        "Fact",
        (),
        {
            "task_token": "T0",
            "residue": 2,
            "label": "C",
        },
    )()
    row = raw_text_training_example(fact)
    assert set(row) == {"text"}
    assert row["text"].endswith("Task route binding: T0.\nAnswer: C")


def test_raw_text_repair_does_not_emit_prompt_completion_fields():
    fact = type("Fact", (), {"task_token": "T1", "residue": 0, "label": "B"})()
    row = raw_text_training_example(fact)
    assert "prompt" not in row
    assert "completion" not in row
