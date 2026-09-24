"""Read-only activation capture for one cached small transformer.

State slice: proof-carrying-nano-host-activation-boundary-v1.

The adapter binds one decoder block output hook, captures one token position,
and never writes to model parameters or activations. The action contains only
digests and replayable token inputs; raw activation bytes are returned to the
caller so qualification code can place them in external custody.
"""

from __future__ import annotations

import hashlib
import json
import platform
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "proof-carrying-nano-host-activation-boundary-v1"
PROTOCOL_ID = STATE_SLICE
ACTIVATION_SCHEMA = "host-activation-capture-v1"
RUNTIME_SCHEMA = "host-runtime-identity-v1"
MUTATION_POLICY_SCHEMA = "read-only-host-mutation-policy-v1"
HOOK_SCHEMA = "torch-forward-hook-identity-v1"
SITE = "decoder_block_output"
CLAIM_TYPE = "host_activation_binding"
CLAIM_SEMANTICS = "declared_host_slice_read_only_activation_capture_v1"
ACTION_STATUS = "ActivationCaptured"
BUNDLE_STATUS = "ActivationCaptureOnly"
CLAIM_CEILING = "LocalCachedSmallTransformerActivationCaptureOnly"
MODEL_ID = "HuggingFaceTB/SmolLM2-135M"
MODEL_SNAPSHOT = "93efa2f097d58c2a74874c7e644dbc9b0cee75a2"


class ActivationAdapterError(ValueError):
    """Raised when the activation boundary cannot be satisfied."""


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ActivationAdapterError("value is not canonical JSON") from exc


def canonical_digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_bytes(value)).hexdigest()}"


def bytes_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _tensor_bytes(tensor: Any) -> bytes:
    import torch

    if not isinstance(tensor, torch.Tensor):
        raise ActivationAdapterError("activation is not a tensor")
    value = tensor.detach().to(device="cpu").contiguous()
    return value.view(torch.uint8).numpy().tobytes()


def activation_digest(tensor: Any) -> str:
    return activation_digest_from_raw(
        _tensor_bytes(tensor),
        dtype=str(tensor.dtype),
        shape=list(tensor.shape),
    )


def activation_digest_from_raw(raw: bytes, *, dtype: str, shape: Sequence[int]) -> str:
    metadata = {"dtype": dtype, "shape": list(shape)}
    return bytes_digest(canonical_bytes(metadata) + b"\0" + raw)


def parameter_digest(model: Any) -> str:
    """Hash all named parameter bytes and metadata in deterministic order."""

    digest = hashlib.sha256()
    try:
        parameters = sorted(model.named_parameters(), key=lambda item: item[0])
    except AttributeError as exc:
        raise ActivationAdapterError("host model does not expose named parameters") from exc
    for name, tensor in parameters:
        metadata = {"dtype": str(tensor.dtype), "name": name, "shape": list(tensor.shape)}
        digest.update(canonical_bytes(metadata))
        digest.update(b"\0")
        digest.update(_tensor_bytes(tensor))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def runtime_identity() -> dict[str, Any]:
    import torch
    import transformers

    return {
        "device": "cpu",
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "python": platform.python_version(),
        "schema": RUNTIME_SCHEMA,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
    }


def _module_at_path(model: Any, path: str) -> Any:
    current = model
    for part in path.split("."):
        if not part or not hasattr(current, part):
            raise ActivationAdapterError(f"hook module path is not reachable: {path}")
        current = getattr(current, part)
    try:
        import torch

        if not isinstance(current, torch.nn.Module):
            raise ActivationAdapterError(f"hook target is not a module: {path}")
    except ImportError as exc:
        raise ActivationAdapterError("torch is required for host activation capture") from exc
    return current


@dataclass(frozen=True)
class MutationPolicy:
    schema: str
    adapter_mode: str
    allow_forward_hooks: bool
    activation_mutation: bool
    host_parameter_mutation: bool

    @classmethod
    def read_only(cls) -> "MutationPolicy":
        return cls(
            schema=MUTATION_POLICY_SCHEMA,
            adapter_mode="read_only",
            allow_forward_hooks=True,
            activation_mutation=False,
            host_parameter_mutation=False,
        )

    def __post_init__(self) -> None:
        expected = {
            "schema": MUTATION_POLICY_SCHEMA,
            "adapter_mode": "read_only",
            "allow_forward_hooks": True,
            "activation_mutation": False,
            "host_parameter_mutation": False,
        }
        if self.to_dict() != expected:
            raise ActivationAdapterError("mutation policy is not read-only")

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_mode": self.adapter_mode,
            "activation_mutation": self.activation_mutation,
            "allow_forward_hooks": self.allow_forward_hooks,
            "host_parameter_mutation": self.host_parameter_mutation,
            "schema": self.schema,
        }


@dataclass(frozen=True)
class ActivationCapture:
    action: dict[str, Any]
    raw_activation: bytes
    raw_metadata: dict[str, Any]


def _hook_identity(layer: int) -> dict[str, Any]:
    return {
        "capture_point": "module_output",
        "module_path": f"model.layers.{layer}",
        "read_only": True,
        "registration": "register_forward_hook",
        "schema": HOOK_SCHEMA,
    }


def _input_digest(input_ids: Sequence[int], attention_mask: Sequence[int], replay_seed: int) -> str:
    return canonical_digest(
        {
            "attention_mask": list(attention_mask),
            "input_ids": list(input_ids),
            "replay_seed": replay_seed,
        }
    )


def _host_slice_digest(
    *,
    host_checkpoint_digest: str,
    host_runtime_digest: str,
    layer: int,
    site: str,
    token_position: int,
    hook_identity: Mapping[str, Any],
    replay_seed: int,
    mutation_policy: Mapping[str, Any],
) -> str:
    return canonical_digest(
        {
            "host_checkpoint_digest": host_checkpoint_digest,
            "host_runtime_digest": host_runtime_digest,
            "hook_identity": dict(hook_identity),
            "layer": layer,
            "mutation_policy": dict(mutation_policy),
            "replay_seed": replay_seed,
            "site": site,
            "token_position": token_position,
        }
    )


class CachedSmallTransformerAdapter:
    """Attach one read-only hook to a locally cached Transformers model."""

    def __init__(
        self,
        *,
        identity: str,
        model: Any,
        host_checkpoint_digest: str,
        host_runtime_digest: str,
        checkpoint_root: Path,
        model_identity: str,
        tokenizer_identity: str,
        tokenizer: Any | None = None,
    ) -> None:
        if not identity or not model_identity or not tokenizer_identity:
            raise ActivationAdapterError("adapter identities must be non-empty")
        if not host_checkpoint_digest.startswith("sha256:") or not host_runtime_digest.startswith("sha256:"):
            raise ActivationAdapterError("host digests are invalid")
        if getattr(model, "training", True):
            raise ActivationAdapterError("host model must be in eval mode for read-only capture")
        self.identity = identity
        self.model = model
        self.host_checkpoint_digest = host_checkpoint_digest
        self.host_runtime_digest = host_runtime_digest
        self.checkpoint_root = Path(checkpoint_root)
        self.model_identity = model_identity
        self.tokenizer_identity = tokenizer_identity
        self.tokenizer = tokenizer
        self.mutation_policy = MutationPolicy.read_only()

    @classmethod
    def from_cached_checkpoint(
        cls,
        *,
        checkpoint_root: Path,
        host_checkpoint_digest: str,
        model_identity: str = MODEL_ID,
        tokenizer_identity: str = "GPT2Tokenizer",
        identity: str = "smollm2-135m-activation-nano-v1",
    ) -> "CachedSmallTransformerAdapter":
        """Load a local checkpoint with network and remote-code loading disabled."""

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ActivationAdapterError("torch and transformers are required") from exc
        root = Path(checkpoint_root)
        if not root.is_dir() or root.is_symlink():
            raise ActivationAdapterError("checkpoint root is not a real directory")
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                root,
                local_files_only=True,
                trust_remote_code=False,
            )
            model = AutoModelForCausalLM.from_pretrained(
                root,
                local_files_only=True,
                trust_remote_code=False,
                torch_dtype=torch.float32,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            raise ActivationAdapterError(f"cached checkpoint could not be loaded: {exc}") from exc
        model.to("cpu")
        model.eval()
        identity_payload = runtime_identity()
        return cls(
            identity=identity,
            model=model,
            host_checkpoint_digest=host_checkpoint_digest,
            host_runtime_digest=canonical_digest(identity_payload),
            checkpoint_root=root,
            model_identity=model_identity,
            tokenizer_identity=tokenizer_identity,
            tokenizer=tokenizer,
        )

    def tokenize(self, prompt: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
        if self.tokenizer is None:
            raise ActivationAdapterError("tokenizer is not configured")
        if not isinstance(prompt, str):
            raise ActivationAdapterError("prompt must be text")
        encoded = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        ids = tuple(int(value) for value in encoded["input_ids"][0].tolist())
        mask = tuple(int(value) for value in encoded["attention_mask"][0].tolist())
        return ids, mask

    def capture_prompt(
        self,
        *,
        prompt: str,
        layer: int,
        site: str,
        token_position: int,
        replay_seed: int,
        timestamp: str,
    ) -> ActivationCapture:
        input_ids, attention_mask = self.tokenize(prompt)
        return self.capture_tokens(
            input_ids=input_ids,
            attention_mask=attention_mask,
            layer=layer,
            site=site,
            token_position=token_position,
            replay_seed=replay_seed,
            timestamp=timestamp,
        )

    def capture_tokens(
        self,
        *,
        input_ids: Sequence[int],
        attention_mask: Sequence[int],
        layer: int,
        site: str,
        token_position: int,
        replay_seed: int,
        timestamp: str,
        action_version: int = 1,
    ) -> ActivationCapture:
        import torch

        ids = tuple(input_ids)
        mask = tuple(attention_mask)
        if not ids or len(ids) != len(mask):
            raise ActivationAdapterError("input ids and attention mask must have equal nonzero length")
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in ids):
            raise ActivationAdapterError("input ids are invalid")
        if any(value not in (0, 1) for value in mask):
            raise ActivationAdapterError("attention mask is invalid")
        if not isinstance(layer, int) or isinstance(layer, bool) or layer < 0:
            raise ActivationAdapterError("layer is invalid")
        if site != SITE:
            raise ActivationAdapterError("site is not the closed activation site")
        if not isinstance(token_position, int) or isinstance(token_position, bool) or token_position < 0 or token_position >= len(ids):
            raise ActivationAdapterError("token position is invalid")
        if not isinstance(replay_seed, int) or isinstance(replay_seed, bool):
            raise ActivationAdapterError("replay seed is invalid")
        if not isinstance(timestamp, str) or not timestamp or action_version < 1:
            raise ActivationAdapterError("timestamp and action version are invalid")

        hook_identity = _hook_identity(layer)
        target = _module_at_path(self.model, hook_identity["module_path"])
        before = parameter_digest(self.model)
        captured: list[Any] = []

        def capture_hook(_module: Any, _inputs: Any, output: Any) -> None:
            value = output[0] if isinstance(output, (tuple, list)) else output
            if not isinstance(value, torch.Tensor) or value.ndim != 3 or value.shape[0] != 1:
                raise ActivationAdapterError("hook output is not a [1, sequence, hidden] tensor")
            captured.append(value.detach().to(device="cpu").contiguous().clone())

        handle = target.register_forward_hook(capture_hook)
        try:
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(replay_seed)
                with torch.no_grad():
                    self.model(
                        input_ids=torch.tensor([ids], dtype=torch.long),
                        attention_mask=torch.tensor([mask], dtype=torch.long),
                        use_cache=False,
                    )
        except (ActivationAdapterError, OSError, RuntimeError, TypeError) as exc:
            raise ActivationAdapterError(f"host activation capture failed: {exc}") from exc
        finally:
            handle.remove()

        after = parameter_digest(self.model)
        if after != before:
            raise ActivationAdapterError("host parameters mutated during read-only capture")
        if len(captured) != 1:
            raise ActivationAdapterError("hook was not reached exactly once")
        sequence_activation = captured[0]
        activation = sequence_activation[0, token_position]
        raw = _tensor_bytes(activation)
        digest = activation_digest(activation)
        input_digest = _input_digest(ids, mask, replay_seed)
        mutation_policy = self.mutation_policy.to_dict()
        host_slice = _host_slice_digest(
            host_checkpoint_digest=self.host_checkpoint_digest,
            host_runtime_digest=self.host_runtime_digest,
            layer=layer,
            site=site,
            token_position=token_position,
            hook_identity=hook_identity,
            replay_seed=replay_seed,
            mutation_policy=mutation_policy,
        )
        unsigned = {
            "action_version": action_version,
            "activation_schema": ACTIVATION_SCHEMA,
            "claim": {
                "activation_digest": digest,
                "claim_key": f"{self.host_checkpoint_digest}:{layer}:{site}:{token_position}:{digest}",
                "host_slice_digest": host_slice,
                "kind": "activation",
                "layer": layer,
                "parameter_digest_after": after,
                "parameter_digest_before": before,
                "semantics": CLAIM_SEMANTICS,
                "site": site,
                "token_position": token_position,
                "type": CLAIM_TYPE,
            },
            "host_checkpoint_digest": self.host_checkpoint_digest,
            "host_runtime_digest": self.host_runtime_digest,
            "hook_identity": hook_identity,
            "inputs": {
                "attention_mask": list(mask),
                "input_digest": input_digest,
                "input_ids": list(ids),
                "replay_seed": replay_seed,
            },
            "layer": layer,
            "mutation_policy": mutation_policy,
            "nano_identity": self.identity,
            "outputs": {
                "activation_digest": digest,
                "activation_dtype": str(activation.dtype),
                "activation_shape": list(activation.shape),
                "hook_reached": True,
                "parameter_digest_after": after,
                "parameter_digest_before": before,
                "status": ACTION_STATUS,
            },
            "protocol_identity": PROTOCOL_ID,
            "replay_seed": replay_seed,
            "site": site,
            "state_slice": STATE_SLICE,
            "timestamp": timestamp,
            "token_position": token_position,
        }
        action = {**unsigned, "action_digest": canonical_digest(unsigned)}
        return ActivationCapture(
            action=action,
            raw_activation=raw,
            raw_metadata={
                "activation_digest": digest,
                "activation_dtype": str(activation.dtype),
                "activation_shape": list(activation.shape),
                "action_digest": action["action_digest"],
            },
        )

    def replay(self, action: Mapping[str, Any]) -> ActivationCapture:
        if not isinstance(action, Mapping):
            raise ActivationAdapterError("activation action is invalid")
        if action.get("nano_identity") != self.identity:
            raise ActivationAdapterError("activation action identity does not match adapter")
        inputs = action.get("inputs")
        if not isinstance(inputs, Mapping):
            raise ActivationAdapterError("activation action inputs are invalid")
        result = self.capture_tokens(
            input_ids=tuple(inputs["input_ids"]),
            attention_mask=tuple(inputs["attention_mask"]),
            layer=action["layer"],
            site=action["site"],
            token_position=action["token_position"],
            replay_seed=action["replay_seed"],
            timestamp=action["timestamp"],
            action_version=action["action_version"],
        )
        if result.action != dict(action):
            raise ActivationAdapterError("activation replay did not reproduce the action exactly")
        return result
