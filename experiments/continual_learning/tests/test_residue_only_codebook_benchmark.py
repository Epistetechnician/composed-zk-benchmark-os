from experiments.continual_learning.compositional_calibration_benchmark import make_tasks
from experiments.continual_learning.residue_only_codebook_benchmark import residue_only_prompt_for


def test_v11_prompt_is_residue_only_and_label_hidden():
    fact = make_tasks(20260810)[0].test_facts[0]
    prompt = residue_only_prompt_for(fact)
    assert f"Derived residue: {fact.residue}." in prompt
    assert "Compose " not in prompt
    assert f"option {fact.label}" not in prompt
    assert prompt.endswith("\nAnswer:")


def test_v11_preserves_disjoint_task_facts():
    tasks = make_tasks(20260810)
    assert all(len(task.train_facts) == 8 and len(task.test_facts) == 8 for task in tasks)
    assert all(
        not {fact.fact_id for fact in task.train_facts} & {fact.fact_id for fact in task.test_facts}
        for task in tasks
    )
