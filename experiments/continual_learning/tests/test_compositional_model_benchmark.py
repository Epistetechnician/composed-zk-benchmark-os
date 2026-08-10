from experiments.continual_learning.compositional_model_benchmark import (
    LABELS,
    choose_balanced_full_replay,
    make_tasks,
    prompt_for,
    replay_counts_by_task,
)


def test_compositional_train_test_split_is_disjoint_and_rule_valid():
    tasks = make_tasks(17)
    for task in tasks:
        assert len(task.train_facts) == 8
        assert len(task.test_facts) == 8
        assert not {fact.fact_id for fact in task.train_facts} & {fact.fact_id for fact in task.test_facts}
        assert set(task.mapping) == set(LABELS)
        assert all(fact.label == task.mapping[fact.residue] for fact in task.train_facts + task.test_facts)
        assert {fact.residue for fact in task.train_facts} == set(range(4))
        assert {fact.residue for fact in task.test_facts} == set(range(4))


def test_compositional_prompt_excludes_fact_id_and_keeps_suffix():
    fact = make_tasks(17)[0].train_facts[0]
    prompt = prompt_for(fact)
    assert fact.fact_id not in prompt
    assert prompt.endswith("\nAnswer:")


def test_compositional_replay_is_full_and_task_balanced():
    tasks = make_tasks(17)
    prior = [fact for task in tasks[:3] for fact in task.train_facts]
    replay = choose_balanced_full_replay(prior, capacity=24, limit=24)
    assert replay_counts_by_task(replay) == {"0": 8, "1": 8, "2": 8}
