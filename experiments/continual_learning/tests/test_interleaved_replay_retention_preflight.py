from experiments.continual_learning.interleaved_replay_retention_preflight import interleave_rows


def row(task: str, index: int) -> dict[str, str]:
    return {"prompt": f"Task token: {task}.\nindex {index}", "completion": " A"}


def test_interleave_rows_round_robins_task_routes_without_changing_rows():
    rows = [row("T1", 0), row("T1", 1), row("T0", 0), row("T0", 1)]
    scheduled = interleave_rows(rows)
    assert [item["prompt"].split("Task token: ", 1)[1].split(".", 1)[0] for item in scheduled] == ["T0", "T1", "T0", "T1"]
    assert sorted(item["prompt"] for item in scheduled) == sorted(item["prompt"] for item in rows)


def test_interleave_rows_drains_longer_route_after_shorter_route():
    rows = [row("T2", 0), row("T2", 1), row("T2", 2), row("T0", 0)]
    scheduled = interleave_rows(rows)
    assert [item["prompt"].split("Task token: ", 1)[1].split(".", 1)[0] for item in scheduled] == ["T0", "T2", "T2", "T2"]
