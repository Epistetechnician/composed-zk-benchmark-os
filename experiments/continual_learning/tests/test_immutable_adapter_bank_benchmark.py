from experiments.continual_learning.compositional_calibration_benchmark import make_tasks


def test_v9_task_bank_contract_preserves_heldout_task_shape():
    tasks = make_tasks(20260810)
    assert len(tasks) == 4
    assert all(len(task.train_facts) == 8 and len(task.test_facts) == 8 for task in tasks)
    assert all(task.mapping == tuple("ABCD"[(i + task.task_id) % 4] for i in range(4)) for task in tasks)
