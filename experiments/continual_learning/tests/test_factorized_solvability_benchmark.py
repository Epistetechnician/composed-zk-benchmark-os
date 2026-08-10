from experiments.continual_learning.compositional_calibration_benchmark import make_tasks
from experiments.continual_learning.factorized_solvability_benchmark import factorized_prompt_for


def test_v10_factorized_prompt_exposes_residue_without_exposing_label():
    task = make_tasks(20260810)[0]
    fact = task.test_facts[0]
    prompt = factorized_prompt_for(fact)
    assert f"Derived residue: {fact.residue}." in prompt
    assert f"option {fact.label}" not in prompt
    assert prompt.endswith("\nAnswer:")


def test_v10_preserves_balanced_heldout_task_shape():
    tasks = make_tasks(20260810)
    assert len(tasks) == 4
    assert all(len(task.train_facts) == 8 and len(task.test_facts) == 8 for task in tasks)
    assert all(task.mapping == tuple("ABCD"[(i + task.task_id) % 4] for i in range(4)) for task in tasks)
