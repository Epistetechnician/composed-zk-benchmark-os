import json

from experiments.astral_fsm.actor_client import build_request
from experiments.astral_fsm.evaluate import evaluate
from experiments.astral_fsm.generate_cases import case_to_prompt, generate_cases
from experiments.astral_fsm.oracle import run


def test_generation_is_deterministic_and_curriculum_balanced():
    first = generate_cases(100)
    second = generate_cases(100)
    assert first == second
    assert len(first) == 100
    assert len({case["case_id"] for case in first}) == 100
    assert {stage: sum(case["stage"] == stage for case in first) for stage in (1, 2, 3)} == {
        1: 25,
        2: 40,
        3: 35,
    }


def test_easy_profile_is_unseen_and_shorter_than_initial_curriculum():
    cases = generate_cases(100, profile="easy", case_offset=1000)
    assert min(case["case_id"] for case in cases) == 1001
    assert max(case["case_id"] for case in cases) == 1100
    assert max(len(case["input"]) for case in cases) < 30
    assert all(len(case["input"]) >= 6 for case in cases)


def test_micro_profile_is_unseen_and_bounded():
    cases = generate_cases(100, profile="micro", case_offset=2000)
    assert [case["case_id"] for case in cases] == list(range(2001, 2101))
    assert all(case["stage"] == 1 for case in cases)
    assert all(len(case["states"]) == 3 for case in cases)
    assert min(len(case["input"]) for case in cases) == 2
    assert max(len(case["input"]) for case in cases) == 5


def test_intermediate_profile_is_unseen_and_longer_than_micro():
    cases = generate_cases(100, profile="intermediate", case_offset=3000)
    assert [case["case_id"] for case in cases] == list(range(3001, 3101))
    assert all(len(case["states"]) == 3 for case in cases)
    assert min(len(case["input"]) for case in cases) == 6
    assert max(len(case["input"]) for case in cases) == 10


def test_short_profile_is_unseen_between_micro_and_intermediate():
    cases = generate_cases(100, profile="short", case_offset=4000)
    assert [case["case_id"] for case in cases] == list(range(4001, 4101))
    assert min(len(case["input"]) for case in cases) == 4
    assert max(len(case["input"]) for case in cases) == 6


def test_actor_prompt_excludes_evaluator_context_and_retired_case():
    case = generate_cases(100)[0]
    prompt = case_to_prompt(case).lower()
    assert "oracle" not in prompt
    assert "evaluator" not in prompt
    assert "repository" not in prompt
    assert not (case["input"] == "001011" and case["states"] == ["A", "B", "C"])


def test_oracle_trajectory_has_initial_state_plus_each_symbol():
    for case in generate_cases(100):
        answer = run(case)
        assert len(answer["trajectory"]) == len(case["input"]) + 1
        assert answer["trajectory"][0] == case["start"]
        assert answer["final_state"] == answer["trajectory"][-1]
        assert answer["accepted"] == (answer["final_state"] in case["accepting"])


def test_actor_request_is_bounded_and_stateless():
    case = generate_cases(100)[0]
    request = build_request(case, "test-model")
    assert request["temperature"] == 0.0
    assert request["max_tokens"] == 1024
    assert request["chat_template_kwargs"] == {"enable_thinking": False}
    assert len(request["messages"]) == 2
    serialized = json.dumps(request).lower()
    assert "oracle" not in serialized
    assert "evaluator" not in serialized
    assert "previous answer" not in serialized


def test_evaluator_accepts_strict_json_and_reports_exact_success():
    case = generate_cases(100)[0]
    expected = run(case)
    raw = {"response": {"choices": [{"message": {"content": json.dumps(expected)}}]}}
    result = evaluate(case, raw)
    assert result["valid_json"] is True
    assert result["recoverable_json"] is True
    assert result["schema_valid"] is True
    assert result["overall_exact"] is True
    assert result["first_divergence_index"] is None


def test_evaluator_distinguishes_recoverable_markdown_from_strict_json():
    case = generate_cases(100)[0]
    expected = run(case)
    content = "```json\n" + json.dumps(expected) + "\n```"
    raw = {"response": {"choices": [{"message": {"content": content}}]}}
    result = evaluate(case, raw)
    assert result["valid_json"] is False
    assert result["recoverable_json"] is True
    assert result["overall_exact"] is True


def test_evaluator_records_first_divergence():
    case = generate_cases(100)[0]
    expected = run(case)
    reported = dict(expected)
    reported["trajectory"] = list(expected["trajectory"])
    reported["trajectory"][2] = next(
        state for state in case["states"] if state != reported["trajectory"][2]
    )
    raw = {"response": {"choices": [{"message": {"content": json.dumps(reported)}}]}}
    result = evaluate(case, raw)
    assert result["trajectory_exact"] is False
    assert result["overall_exact"] is False
    assert result["first_divergence_index"] == 2
    assert result["expected_state_at_divergence"] == expected["trajectory"][2]


def test_evaluator_rejects_missing_model_response_without_fabricating_metrics():
    case = generate_cases(100)[0]
    result = evaluate(case, {"response": None})
    assert result["valid_json"] is False
    assert result["recoverable_json"] is False
    assert result["schema_valid"] is False
    assert result["overall_exact"] is False
    assert result["state_accuracy"] == 0.0
