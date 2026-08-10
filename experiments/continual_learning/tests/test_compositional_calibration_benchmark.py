from experiments.continual_learning.compositional_calibration_benchmark import make_tasks


def test_calibration_changes_only_task_mapping_family():
    tasks = make_tasks(20260810)
    assert tasks[0].mapping == ("A", "B", "C", "D")
    assert tasks[1].mapping == ("B", "C", "D", "A")
    for task in tasks:
        assert len(task.train_facts) == 8
        assert len(task.test_facts) == 8
        assert not {fact.fact_id for fact in task.train_facts} & {fact.fact_id for fact in task.test_facts}
        assert {fact.residue for fact in task.train_facts} == set(range(4))
        assert {fact.residue for fact in task.test_facts} == set(range(4))
