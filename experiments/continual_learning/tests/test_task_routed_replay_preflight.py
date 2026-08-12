from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim

from experiments.continual_learning import task_routed_replay_preflight as preflight


def test_optimizer_state_round_trip_preserves_step(tmp_path: Path):
    model = nn.Linear(3, 2)
    optimizer = optim.AdamW(learning_rate=preflight.ADAMW_LEARNING_RATE)
    optimizer.init(model.trainable_parameters())
    optimizer.state["step"] = mx.array(37, mx.uint64)
    state_path = tmp_path / "optimizer_state.npz"

    preflight.save_optimizer_state(state_path, optimizer)
    restored = preflight.load_optimizer_state(state_path)

    assert preflight.optimizer_step(restored) == 37
    assert set(restored) == set(optimizer.state)


def test_preflight_contract_has_one_changed_variable():
    assert preflight.STATE_SLICE.endswith("-preflight")
    assert preflight.SOURCE_STATE_SLICE == "continual-learning-protocol-v23-task-routed-replay-consolidation"
    assert preflight.SLOT_LAYERS == 2
    assert preflight.FULL_SHARED_LAYERS == 8
