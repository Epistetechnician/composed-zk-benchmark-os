from __future__ import annotations

import hashlib
import random
from unittest.mock import patch

import pytest
import torch
from peft import LoraConfig, get_peft_model
from peft.tuners.lora.layer import LoraLayer
from transformers import Qwen3Config, Qwen3ForCausalLM

from experiments.continual_learning import aligned_rsi_billsum_chat_template_v7 as experiment


class FakeTokenizer:
    eos_token_id = 151645
    trailer_token_id = 198

    def apply_chat_template(
        self,
        messages,
        *,
        tokenize,
        add_generation_prompt,
        enable_thinking,
        return_dict,
    ):
        assert tokenize is True
        assert enable_thinking is False
        assert return_dict is False
        user_ids = [abs(hash(token)) % 10_000 for token in messages[1]["content"].split()]
        prefix = [151644, 8948, *user_ids, 151644, 77091]
        if messages[-1]["role"] == "assistant":
            assistant_ids = [abs(hash(token)) % 10_000 for token in messages[-1]["content"].split()]
            return [*prefix, *assistant_ids, self.eos_token_id, self.trailer_token_id]
        return prefix

    def __call__(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return {"input_ids": text.split()}


def _row(split: str, index: int, text: str | None = None, summary: str | None = None):
    source = text or f"{split} bill {index} carries a policy change."
    target = summary or f"The bill changes policy area {index}."
    return {
        "doc_id": experiment._document_id(source),
        "legacy_v1_doc_id": experiment._legacy_v1_document_id(source, target),
        "text": source,
        "summary": target,
    }


def test_json_loader_rejects_duplicate_keys(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"same": 1, "same": 2}', encoding="utf-8")
    with pytest.raises(experiment.ExperimentError, match="duplicate JSON key"):
        experiment.load_json(path)


def test_source_identifier_does_not_depend_on_reference():
    source = "A bill text remains the same."
    first = experiment._document_id(source)
    second = experiment._document_id(source)
    assert first == second == hashlib.sha256(source.encode()).hexdigest()
    assert experiment._legacy_v1_document_id(source, "one summary") != experiment._legacy_v1_document_id(
        source, "different summary"
    )


def test_chat_training_masks_prompt_keeps_end_marker_and_excludes_template_newline():
    row = _row("train", 1)
    encoded = experiment._tokenize_row(FakeTokenizer(), row)
    prompt_count = len(encoded["prompt_ids"])
    assert encoded["input_ids"][:prompt_count] == encoded["prompt_ids"]
    assert encoded["labels"][:prompt_count] == [-100] * prompt_count
    assert encoded["labels"][prompt_count:] == encoded["target_ids"]
    assert encoded["target_ids"][-1] == FakeTokenizer.eos_token_id
    assert FakeTokenizer.trailer_token_id not in encoded["target_ids"]
    assert encoded["target_token_count"] == len(encoded["target_ids"])


def test_chat_training_rejects_unexpected_template_trailer():
    row = _row("train", 2)
    with patch.object(experiment, "TEMPLATE_TRAILER_TOKEN_ID", 199):
        with pytest.raises(experiment.ExperimentError, match="terminator or trailer"):
            experiment._tokenize_row(FakeTokenizer(), row)


def test_fresh_rosters_exclude_v1_v5_v6_and_use_source_hash_order():
    train = [_row("train", index) for index in range(8)]
    test = [_row("test", index) for index in range(6)]
    duplicate = _row("train", 99, text=train[0]["text"], summary="A separate paraphrased reference.")
    train.append(duplicate)
    with (
        patch.object(experiment, "V1_FIT_PREFIX", 1),
        patch.object(experiment, "V1_ASSESSMENT_PREFIX", 1),
        patch.object(experiment, "V5_FIT_EXCLUSION", 1),
        patch.object(experiment, "V5_ASSESSMENT_EXCLUSION", 1),
        patch.object(experiment, "V6_FIT_EXCLUSION", 1),
        patch.object(experiment, "V6_ASSESSMENT_EXCLUSION", 1),
        patch.object(experiment, "FIT_POOL_SIZE", 2),
        patch.object(experiment, "ASSESSMENT_SIZE", 1),
    ):
        result = experiment._fresh_rosters(FakeTokenizer(), train, test)
    expected_train_exclusion = {
        row["doc_id"] for row in sorted(train, key=lambda row: row["legacy_v1_doc_id"])[:1]
    }
    expected_test_exclusion = {
        row["doc_id"] for row in sorted(test, key=lambda row: row["legacy_v1_doc_id"])[:1]
    }
    assert result["v1_excluded"]["fit_source_ids_sha256"] == experiment.sha256_bytes(
        experiment.canonical_bytes(sorted(expected_train_exclusion))
    )
    assert result["v1_excluded"]["assessment_source_ids_sha256"] == experiment.sha256_bytes(
        experiment.canonical_bytes(sorted(expected_test_exclusion))
    )
    assert result["v5_excluded"]["fit_count"] == 1
    assert result["v5_excluded"]["assessment_count"] == 1
    assert result["v6_excluded"]["fit_count"] == 1
    assert result["v6_excluded"]["assessment_count"] == 1
    assert result["duplicate_source_groups_excluded"] == {
        "train_groups": 1,
        "train_rows": 2,
        "test_groups": 0,
        "test_rows": 0,
    }
    assert len(result["fit_ids"]) == 2
    assert len(result["assessment_ids"]) == 1
    assert duplicate["doc_id"] not in result["fit_ids"]
    assert not set(result["fit_ids"]) & set(result["assessment_ids"])
    assert [row["doc_id"] for row in result["fit_rows"]] == sorted(
        row["doc_id"] for row in result["fit_rows"]
    )


def test_generation_seed_is_stable_and_training_seed_sensitive():
    doc_id = "0123456789abcdef" + "0" * 48
    first = experiment._generation_seed(17, doc_id)
    assert first == experiment._generation_seed(17, doc_id)
    assert first != experiment._generation_seed(29, doc_id)


def test_bootstrap_interval_is_paired_and_deterministic():
    values = [0.1, 0.2, -0.1, 0.3, 0.0]
    assert experiment._bootstrap_interval(values) == experiment._bootstrap_interval(values)
    with pytest.raises(experiment.ExperimentError, match="non-finite"):
        experiment._bootstrap_interval([0.1, float("nan")])


def test_google_rouge_scorer_returns_standard_f1_metrics():
    result = experiment._rouge_rows(
        {"doc-a": "A concise bill summary."},
        {"doc-a": "A concise bill summary."},
    )
    assert set(result["doc-a"]) == {"rouge1", "rouge2", "rougeL"}
    assert all(value == pytest.approx(1.0) for value in result["doc-a"].values())


def test_frozen_manifest_matches_memory_bounded_32_example_eight_step_plan():
    manifest = experiment._verify_protocol()
    assert manifest["cohorts"]["assessment_size"] == 64
    assert manifest["arms"][1]["selection"] == "top_32_fit_pool_assistant_target_nll"
    assert manifest["arms"][2]["selection"] == "uniform_32_fit_pool_per_seed"
    assert manifest["training"]["batch_size"] == 4
    assert manifest["training"]["microbatch_size"] == 1
    assert manifest["training"]["gradient_accumulation_examples"] == 4
    assert manifest["training"]["equal_optimizer_steps_per_updated_arm"] == 8
    assert manifest["training"]["gradient_checkpointing"] == "transformer_layer_checkpointing_non_reentrant"
    assert manifest["training"]["generation_pad_token_id"] == 151643
    assert manifest["training"]["seeds"] == [109, 127, 149]
    assert manifest["cohorts"]["fit_v6_exclusion"].startswith("reconstruct_and_exclude")
    assert manifest["cohorts"]["v6_scientific_outputs_reused"] is False
    assert manifest["execution"]["wall_clock_limit_minutes"] == 360


def test_peft_adapter_reset_is_seeded_and_only_lora_is_trainable():
    class ToyProjectionModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.q_proj = torch.nn.Linear(4, 4)
            self.v_proj = torch.nn.Linear(4, 4)

        def forward(self, values):
            return self.q_proj(values) + self.v_proj(values)

    model = get_peft_model(
        ToyProjectionModel(),
        LoraConfig(
            r=2,
            lora_alpha=4,
            lora_dropout=0.0,
            bias="none",
            target_modules=["q_proj", "v_proj"],
        ),
    )
    layers = [module for module in model.modules() if isinstance(module, LoraLayer)]
    parameters = experiment._reset_peft_adapter_for_seed(model, layers, 17)
    first_state = [parameter.detach().clone() for parameter in parameters]
    assert len(layers) == 2
    assert parameters
    assert all("lora_" in name for name, value in model.named_parameters() if value.requires_grad)
    assert all(torch.count_nonzero(layer.lora_B["default"].weight).item() == 0 for layer in layers)

    experiment._reset_peft_adapter_for_seed(model, layers, 17)
    second_state = [parameter.detach().clone() for parameter in parameters]
    assert all(torch.equal(first, second) for first, second in zip(first_state, second_state, strict=True))

    with model.disable_adapter():
        pass


def test_target_only_gradient_accumulation_matches_full_causal_loss_and_gradients():
    config = Qwen3Config(
        vocab_size=128,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=2,
        max_position_embeddings=64,
        head_dim=8,
    )
    model = get_peft_model(
        Qwen3ForCausalLM(config),
        LoraConfig(
            r=2,
            lora_alpha=4,
            lora_dropout=0.0,
            bias="none",
            target_modules=["q_proj", "v_proj"],
            task_type="CAUSAL_LM",
            init_lora_weights=True,
        ),
    )
    layers = [module for module in model.modules() if isinstance(module, LoraLayer)]
    parameters = experiment._reset_peft_adapter_for_seed(model, layers, 17)
    samples = [
        {
            "input_ids": [1, 2, 3, 4, 5, 6, 7, 8],
            "target_start": 4,
            "target_ids": [5, 6, 7, 8],
        },
        {
            "input_ids": [2, 3, 4, 9, 10],
            "target_start": 3,
            "target_ids": [9, 10],
        },
    ]
    padded_ids = torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8], [2, 3, 4, 9, 10, 0, 0, 0]])
    attention = torch.tensor([[1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 0, 0, 0]])
    labels = torch.tensor([
        [-100, -100, -100, -100, 5, 6, 7, 8],
        [-100, -100, -100, 9, 10, -100, -100, -100],
    ])
    model.train()
    standard = model(
        input_ids=padded_ids,
        attention_mask=attention,
        labels=labels,
        use_cache=False,
        return_dict=True,
    ).loss
    standard.backward()
    standard_grads = [parameter.grad.detach().clone() for parameter in parameters]
    standard_value = standard.detach()

    model.zero_grad(set_to_none=True)
    base = model.get_base_model()
    base.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    token_total = sum(len(sample["target_ids"]) for sample in samples)
    accumulated_sum = torch.tensor(0.0)
    for sample in samples:
        loss_sum, count = experiment._assistant_target_loss_sum(model, sample, torch.device("cpu"))
        accumulated_sum += loss_sum.detach().cpu()
        (loss_sum / token_total).backward()
    accumulated = accumulated_sum / token_total
    accumulated_grads = [parameter.grad.detach().clone() for parameter in parameters]
    base.gradient_checkpointing_disable()

    assert accumulated == pytest.approx(float(standard_value), rel=2e-4, abs=2e-4)
    assert all(torch.allclose(left, right, rtol=2e-3, atol=2e-4) for left, right in zip(
        standard_grads, accumulated_grads, strict=True
    ))
    assert len(layers) == 2
    assert parameters
    assert any(torch.count_nonzero(parameter.grad).item() > 0 for parameter in parameters)
    assert all(not parameter.requires_grad for name, parameter in model.named_parameters() if "lora_" not in name)


def test_pinned_peft_adapter_seal_hashes_readme_config_and_weights(tmp_path):
    class ToyProjectionModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.q_proj = torch.nn.Linear(4, 4)
            self.v_proj = torch.nn.Linear(4, 4)

        def forward(self, values):
            return self.q_proj(values) + self.v_proj(values)

    model = get_peft_model(
        ToyProjectionModel(),
        LoraConfig(
            r=2,
            lora_alpha=4,
            lora_dropout=0.0,
            bias="none",
            target_modules=["q_proj", "v_proj"],
        ),
    )
    sealed = experiment._save_adapter(model, tmp_path / "adapter")
    assert {item["path"] for item in sealed["files"]} == {
        "README.md",
        "adapter_config.json",
        "adapter_model.safetensors",
    }
    assert sealed["sha256"] == experiment._tree_digest(sealed["files"])
    assert (tmp_path / "adapter" / "README.md").stat().st_mode & 0o777 == 0o600




def test_adapter_seal_rejects_nested_files_hidden_by_generic_input_manifest(tmp_path):
    class AdapterWithNestedFile:
        def save_pretrained(self, directory, *, safe_serialization):
            assert safe_serialization is True
            for name in ("README.md", "adapter_config.json", "adapter_model.safetensors"):
                (directory / name).write_text("metadata", encoding="utf-8")
            nested = directory / ".cache"
            nested.mkdir()
            (nested / "extra").write_text("unexpected", encoding="utf-8")

    with pytest.raises(experiment.ExperimentError, match="nested directory"):
        experiment._save_adapter(AdapterWithNestedFile(), tmp_path / "adapter")
