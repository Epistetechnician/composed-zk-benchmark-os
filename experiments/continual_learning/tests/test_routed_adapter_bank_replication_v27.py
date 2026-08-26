from experiments.continual_learning.routed_adapter_bank_candidate_v26 import route_bound_prompt_for
from experiments.continual_learning.routed_adapter_bank_replication_v27 import (
    CLAIM_CEILING,
    EXCLUDED_MODEL,
    STATE_SLICE,
)
from experiments.continual_learning import routed_adapter_bank_replication_v27 as v27


def test_v27_reuses_the_frozen_route_contract():
    class Fact:
        task_token = "T3"
        residue = 1

    prompt = route_bound_prompt_for(Fact())
    assert prompt.endswith("Task route binding: T3.\nAnswer:")
    assert "Compose " not in prompt


def test_v27_is_second_model_replication_only():
    assert STATE_SLICE == "continual-learning-replication-task-routed-adapter-bank-v27"
    assert CLAIM_CEILING == "LocalDevelopmentTaskRoutedAdapterBankReplication"
    assert EXCLUDED_MODEL.endswith("Qwen2.5-0.5B-Instruct-4bit")


def test_v27_runner_source_recomputes_manifest_after_contract_rebinding():
    source = v27.__file__
    text = open(source, encoding="utf8").read()
    assert 'result["manifest_sha256"] = v26.v11.base.digest' in text
    assert '"config": config, "tasks": result["tasks"], "audits": audits' in text
