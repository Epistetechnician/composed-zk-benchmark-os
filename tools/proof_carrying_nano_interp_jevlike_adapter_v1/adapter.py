"""Pinned Jevlike scoring boundary with exact fixed-point action inputs.

State slice: proof-carrying-nano-interp-jevlike-adapter-v1.

This module may call an external Jevlike checkout only through
``PinnedJevlikeRunner``. The external model output is recorded as a hypothesis;
the local Lean proof covers only the exact arithmetic performed after output
capture.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP
from numbers import Real
from pathlib import Path
from typing import Any, Protocol, Sequence

from tools.proof_carrying_nano_interp_v1.protocol import (
    ProtocolError,
    canonical_digest,
)
from tools.proof_carrying_nano_interp_v1.ranking import HypothesisOptionSet
from tools.proof_carrying_nano_interp_v1.runtime import (
    ActivationTrace,
    MiniAction,
    ToyHostSlice,
)


STATE_SLICE = "proof-carrying-nano-interp-jevlike-adapter-v1"
PROTOCOL_ID = STATE_SLICE
ADAPTER_CONFIG_SCHEMA = "jevlike-adapter-config-v1"
QUANTIZATION_SCHEMA = "fixed-point-probability-v1"
PINNED_JEVLIKE_REVISION = "94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452"
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_ROUNDING_MODES = {
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_HALF_UP": ROUND_HALF_UP,
}


class AdapterError(ProtocolError):
    """Raised when the external adapter boundary is not satisfied."""


@dataclass(frozen=True)
class JevlikeAdapterConfig:
    """Digestable runtime configuration for one pinned external scorer."""

    upstream_revision: str
    checkout_path: Path
    scorer_checkpoint_digest: str
    encoder_identity: str
    runtime_identity: str
    device: str
    seed: int
    quantization_scale: int = 1_000_000
    rounding: str = "ROUND_HALF_EVEN"
    scorer_checkpoint_path: Path | None = None
    context_tokens: int = 512
    option_tokens: int = 32

    def __post_init__(self) -> None:
        if not isinstance(self.upstream_revision, str) or not _REVISION_PATTERN.fullmatch(
            self.upstream_revision
        ):
            raise AdapterError("upstream_revision must be a full lowercase git revision")
        if self.upstream_revision != PINNED_JEVLIKE_REVISION:
            raise AdapterError("upstream_revision is not the pinned Jevlike revision")
        if not isinstance(self.checkout_path, Path) or not str(self.checkout_path):
            raise AdapterError("checkout_path must be a non-empty Path")
        if not isinstance(self.scorer_checkpoint_digest, str) or not _DIGEST_PATTERN.fullmatch(
            self.scorer_checkpoint_digest
        ):
            raise AdapterError("scorer checkpoint digest must be a sha256 digest")
        for name, value in (
            ("encoder_identity", self.encoder_identity),
            ("runtime_identity", self.runtime_identity),
            ("device", self.device),
        ):
            if not isinstance(value, str) or not value:
                raise AdapterError(f"{name} must be non-empty")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise AdapterError("seed must be an integer")
        if (
            isinstance(self.quantization_scale, bool)
            or not isinstance(self.quantization_scale, int)
            or self.quantization_scale < 1
        ):
            raise AdapterError("quantization_scale must be a positive integer")
        if self.rounding not in _ROUNDING_MODES:
            raise AdapterError("rounding mode is unsupported")
        if (
            isinstance(self.context_tokens, bool)
            or not isinstance(self.context_tokens, int)
            or self.context_tokens < 1
            or isinstance(self.option_tokens, bool)
            or not isinstance(self.option_tokens, int)
            or self.option_tokens < 1
        ):
            raise AdapterError("token limits must be positive integers")
        if self.scorer_checkpoint_path is not None and not isinstance(
            self.scorer_checkpoint_path, Path
        ):
            raise AdapterError("scorer_checkpoint_path must be a Path")

    def to_dict(self) -> dict[str, Any]:
        """Return machine-stable configuration bytes without host-local paths."""

        return {
            "context_tokens": self.context_tokens,
            "device": self.device,
            "encoder_identity": self.encoder_identity,
            "option_tokens": self.option_tokens,
            "quantization_scale": self.quantization_scale,
            "rounding": self.rounding,
            "runtime_identity": self.runtime_identity,
            "schema": ADAPTER_CONFIG_SCHEMA,
            "scorer_checkpoint_digest": self.scorer_checkpoint_digest,
            "seed": self.seed,
            "upstream_revision": self.upstream_revision,
        }

    @property
    def config_digest(self) -> str:
        return canonical_digest(self.to_dict())


class JevlikeRunner(Protocol):
    """Minimal injected boundary, allowing contract tests without model loads."""

    def validate(self, config: JevlikeAdapterConfig) -> None:
        ...

    def score(
        self,
        context: str,
        options: tuple[str, ...],
        *,
        config: JevlikeAdapterConfig,
    ) -> Sequence[object]:
        ...


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise AdapterError(f"cannot read scorer checkpoint: {path}") from exc
    return f"sha256:{digest.hexdigest()}"


class PinnedJevlikeRunner:
    """Run the exact upstream checkout, with imports delayed to call time."""

    def validate(self, config: JevlikeAdapterConfig) -> None:
        checkout = config.checkout_path
        if not checkout.is_dir() or not (checkout / ".git").exists():
            raise AdapterError(f"pinned Jevlike checkout is missing: {checkout}")
        try:
            observed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=checkout,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AdapterError("could not inspect pinned Jevlike revision") from exc
        if observed != config.upstream_revision:
            raise AdapterError(
                f"unexpected Jevlike revision: {observed}; expected {config.upstream_revision}"
            )
        checkpoint = config.scorer_checkpoint_path
        if checkpoint is None or not checkpoint.is_file():
            raise AdapterError("a pinned scorer checkpoint path is required")
        if _file_digest(checkpoint) != config.scorer_checkpoint_digest:
            raise AdapterError("scorer checkpoint digest mismatch")

    def score(
        self,
        context: str,
        options: tuple[str, ...],
        *,
        config: JevlikeAdapterConfig,
    ) -> Sequence[object]:
        """Call Jevlike's public checkpoint/predict path without vendoring it."""

        self.validate(config)
        if len(options) < 2:
            raise AdapterError("Jevlike requires at least two options")
        checkout_text = str(config.checkout_path)
        original_path = list(sys.path)
        sys.path.insert(0, checkout_text)
        try:
            import torch

            from jevlike.data import ChoiceExample
            from jevlike.model import load_checkpoint
            from jevlike.train import move

            torch.manual_seed(config.seed)
            if config.device.startswith("cuda") and torch.cuda.is_available():
                torch.cuda.manual_seed_all(config.seed)
            model, collator, _ = load_checkpoint(
                config.scorer_checkpoint_path,
                torch.device(config.device),
            )
            batch = move(
                collator([ChoiceExample(context, options, 0)]),
                torch.device(config.device),
            )
            model.eval()
            with torch.no_grad():
                probabilities = model(batch).softmax(-1)[0, : len(options)].cpu().tolist()
            return tuple(probabilities)
        except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
            raise AdapterError(f"Jevlike scoring failed: {exc}") from exc
        finally:
            sys.path[:] = original_path


def _decimal_score(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Real, Decimal)):
        raise AdapterError("Jevlike scores must be numeric")
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AdapterError("Jevlike score is not a decimal value") from exc
    if not decimal.is_finite() or decimal < 0:
        raise AdapterError("Jevlike scores must be finite and non-negative")
    return decimal


@dataclass(frozen=True)
class JevlikeRankingResult:
    option_set_digest: str
    raw_scores: tuple[str, ...]
    quantized_scores: tuple[int, ...]
    denominator: int
    probabilities: tuple[dict[str, int], ...]
    selected_index: int
    selected_option: str
    selected_option_kind: str


class JevlikeOptionScorer:
    """Validate and quantize one pinned Jevlike output."""

    def __init__(
        self,
        *,
        identity: str,
        config: JevlikeAdapterConfig,
        runner: JevlikeRunner | None = None,
    ) -> None:
        if not isinstance(identity, str) or not identity:
            raise AdapterError("adapter identity must be non-empty")
        self.identity = identity
        self.config = config
        self.runner = runner or PinnedJevlikeRunner()

    def rank(self, *, context: str, option_set: HypothesisOptionSet) -> JevlikeRankingResult:
        if not isinstance(context, str) or not context:
            raise AdapterError("Jevlike context must be a non-empty string")
        if not isinstance(option_set, HypothesisOptionSet):
            raise AdapterError("option set is invalid")
        option_set.assert_digest()
        if option_set.scorer_identity != self.identity:
            raise AdapterError("option-set scorer does not match Jevlike adapter")
        if option_set.context_digest != canonical_digest(context):
            raise AdapterError("option-set context digest does not match Jevlike context")
        if len(option_set.options) < 2:
            raise AdapterError("Jevlike ranking requires at least two options")

        options = tuple(option.candidate_id for option in option_set.options)
        self.runner.validate(self.config)
        raw_values = self.runner.score(context, options, config=self.config)
        if isinstance(raw_values, (str, bytes)):
            raise AdapterError("Jevlike scores must be a sequence")
        raw_values = tuple(raw_values)
        if len(raw_values) != len(options):
            raise AdapterError("Jevlike score count does not match ordered options")

        quantized: list[int] = []
        raw_scores: list[str] = []
        rounding = _ROUNDING_MODES[self.config.rounding]
        for value in raw_values:
            decimal = _decimal_score(value)
            raw_scores.append(str(decimal))
            quantized_value = int(
                (decimal * self.config.quantization_scale).to_integral_value(
                    rounding=rounding
                )
            )
            if quantized_value < 0:
                raise AdapterError("quantized Jevlike score became negative")
            quantized.append(quantized_value)
        denominator = sum(quantized)
        if denominator <= 0:
            raise AdapterError("quantized Jevlike scores must have a positive sum")
        selected_index = max(range(len(quantized)), key=quantized.__getitem__)
        selected = option_set.options[selected_index]
        probabilities = tuple(
            {"denominator": denominator, "numerator": score} for score in quantized
        )
        return JevlikeRankingResult(
            option_set_digest=option_set.option_set_digest,
            raw_scores=tuple(raw_scores),
            quantized_scores=tuple(quantized),
            denominator=denominator,
            probabilities=probabilities,
            selected_index=selected_index,
            selected_option=selected.candidate_id,
            selected_option_kind=selected.kind,
        )

    def rank_recorded(
        self,
        *,
        context: str,
        option_set: HypothesisOptionSet,
        raw_scores: Sequence[str],
    ) -> JevlikeRankingResult:
        """Replay quantization from recorded decimal text without an external call."""

        if not isinstance(context, str) or not context:
            raise AdapterError("Jevlike context must be a non-empty string")
        option_set.assert_digest()
        if option_set.scorer_identity != self.identity:
            raise AdapterError("option-set scorer does not match Jevlike adapter")
        if option_set.context_digest != canonical_digest(context):
            raise AdapterError("option-set context digest does not match Jevlike context")
        if len(option_set.options) < 2 or len(raw_scores) != len(option_set.options):
            raise AdapterError("recorded Jevlike score count does not match options")
        decimals: list[Decimal] = []
        for value in raw_scores:
            if not isinstance(value, str):
                raise AdapterError("recorded Jevlike scores must be decimal strings")
            try:
                decimal = Decimal(value)
            except (InvalidOperation, ValueError) as exc:
                raise AdapterError("recorded Jevlike score is not decimal text") from exc
            if not decimal.is_finite() or decimal < 0:
                raise AdapterError("recorded Jevlike scores must be finite and non-negative")
            decimals.append(decimal)
        rounding = _ROUNDING_MODES[self.config.rounding]
        quantized = tuple(
            int(
                (decimal * self.config.quantization_scale).to_integral_value(
                    rounding=rounding
                )
            )
            for decimal in decimals
        )
        denominator = sum(quantized)
        if denominator <= 0:
            raise AdapterError("recorded Jevlike scores must have a positive sum")
        selected_index = max(range(len(quantized)), key=quantized.__getitem__)
        selected = option_set.options[selected_index]
        return JevlikeRankingResult(
            option_set_digest=option_set.option_set_digest,
            raw_scores=tuple(raw_scores),
            quantized_scores=quantized,
            denominator=denominator,
            probabilities=tuple(
                {"denominator": denominator, "numerator": score} for score in quantized
            ),
            selected_index=selected_index,
            selected_option=selected.candidate_id,
            selected_option_kind=selected.kind,
        )


@dataclass(frozen=True)
class JevlikeHypothesisRankingNano:
    identity: str
    scorer: JevlikeOptionScorer

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise AdapterError("ranking nano identity must be non-empty")
        if self.scorer.identity != self.identity:
            raise AdapterError("ranking nano and scorer identities must match")

    def attach(
        self,
        host: ToyHostSlice,
        *,
        layer: int,
        site: str,
    ) -> "JevlikeHypothesisRankingAttachment":
        if isinstance(layer, bool) or not isinstance(layer, int) or layer < 0 or not site:
            raise AdapterError("attachment location is invalid")
        return JevlikeHypothesisRankingAttachment(self, host, layer, site)


@dataclass(frozen=True)
class JevlikeHypothesisRankingAttachment:
    nano: JevlikeHypothesisRankingNano
    host: ToyHostSlice
    layer: int
    site: str

    def run(
        self,
        trace: ActivationTrace,
        option_set: HypothesisOptionSet,
        *,
        context: str,
        timestamp: str,
        action_version: int = 1,
    ) -> MiniAction:
        if not timestamp or isinstance(action_version, bool) or action_version < 1:
            raise AdapterError("action timestamp and positive version are required")
        if trace.checkpoint_id != self.host.checkpoint_id:
            raise AdapterError("trace checkpoint does not match attached host")
        if trace.layer != self.layer or trace.site != self.site:
            raise AdapterError("trace location does not match attachment")
        ranking = self.nano.scorer.rank(context=context, option_set=option_set)
        return self._action_from_ranking(
            trace,
            option_set,
            context=context,
            ranking=ranking,
            timestamp=timestamp,
            action_version=action_version,
        )

    def _action_from_ranking(
        self,
        trace: ActivationTrace,
        option_set: HypothesisOptionSet,
        *,
        context: str,
        ranking: JevlikeRankingResult,
        timestamp: str,
        action_version: int,
    ) -> MiniAction:
        provenance = {
            "adapter_identity": self.nano.scorer.identity,
            "config": self.nano.scorer.config.to_dict(),
            "config_digest": self.nano.scorer.config.config_digest,
            "device": self.nano.scorer.config.device,
            "encoder_identity": self.nano.scorer.config.encoder_identity,
            "quantization_schema": QUANTIZATION_SCHEMA,
            "runtime_identity": self.nano.scorer.config.runtime_identity,
            "scorer_checkpoint_digest": self.nano.scorer.config.scorer_checkpoint_digest,
            "seed": self.nano.scorer.config.seed,
            "upstream_revision": self.nano.scorer.config.upstream_revision,
        }
        claim = {
            "claim_key": (
                f"{trace.checkpoint_id}:{self.layer}:{self.site}:jevlike-ranking:"
                f"{option_set.option_set_digest}"
            ),
            "context_digest": option_set.context_digest,
            "kind": "hypothesis",
            "option_ids": [option.candidate_id for option in option_set.options],
            "option_set_digest": option_set.option_set_digest,
            "selected_index": ranking.selected_index,
            "selected_option": ranking.selected_option,
            "selected_option_kind": ranking.selected_option_kind,
            "scorer_identity": self.nano.scorer.identity,
            "type": "jevlike_hypothesis_ranking",
        }
        inputs = {
            "activation": list(trace.activation),
            "context": context,
            "context_digest": option_set.context_digest,
            "external_provenance": provenance,
            "external_scores": list(ranking.raw_scores),
            "option_set": option_set.to_dict(),
            "prompt": trace.prompt,
            "quantization": {
                "rounding": self.nano.scorer.config.rounding,
                "scale": self.nano.scorer.config.quantization_scale,
                "schema": QUANTIZATION_SCHEMA,
            },
            "quantized_scores": list(ranking.quantized_scores),
            "seed": trace.seed,
        }
        outputs = {
            "probabilities": [dict(item) for item in ranking.probabilities],
            "selected_index": ranking.selected_index,
            "selected_option": ranking.selected_option,
            "selected_option_kind": ranking.selected_option_kind,
            "status": "HypothesisOnly",
        }
        unsigned = {
            "action_version": action_version,
            "claim": claim,
            "host_checkpoint_id": trace.checkpoint_id,
            "host_context_hash": trace.host_context_hash,
            "inputs": inputs,
            "layer": self.layer,
            "nano_identity": self.nano.identity,
            "outputs": outputs,
            "protocol_identity": PROTOCOL_ID,
            "site": self.site,
            "state_slice": STATE_SLICE,
            "timestamp": timestamp,
        }
        return MiniAction(
            state_slice=STATE_SLICE,
            protocol_identity=PROTOCOL_ID,
            action_version=action_version,
            timestamp=timestamp,
            inputs=inputs,
            outputs=outputs,
            host_context_hash=trace.host_context_hash,
            host_checkpoint_id=trace.checkpoint_id,
            nano_identity=self.nano.identity,
            layer=self.layer,
            site=self.site,
            claim=claim,
            action_digest=canonical_digest(unsigned),
        )

    def run_and_record(
        self,
        trace: ActivationTrace,
        option_set: HypothesisOptionSet,
        *,
        context: str,
        store: Any,
        timestamp: str,
        action_version: int = 1,
        proof_engine: Any = None,
    ) -> tuple[MiniAction, Any]:
        from .proof import JevlikeLeanProofEngine

        action = self.run(
            trace,
            option_set,
            context=context,
            timestamp=timestamp,
            action_version=action_version,
        )
        proof = (proof_engine or JevlikeLeanProofEngine()).attempt(action)
        store.commit_action(action)
        store.commit_proof(proof)
        return action, proof

    def replay(self, action: MiniAction) -> MiniAction:
        """Replay recorded quantization without importing or calling Jevlike."""

        if action.state_slice != STATE_SLICE or action.protocol_identity != PROTOCOL_ID:
            raise AdapterError("action identity mismatch")
        if action.nano_identity != self.nano.identity:
            raise AdapterError("action nano identity does not match attachment")
        if action.layer != self.layer or action.site != self.site:
            raise AdapterError("action location does not match attachment")
        if action.action_digest != canonical_digest(
            {key: value for key, value in action.to_dict().items() if key != "action_digest"}
        ):
            raise AdapterError("action digest mismatch")
        try:
            option_set = HypothesisOptionSet.from_dict(action.inputs["option_set"])
            context = action.inputs["context"]
            raw_scores = tuple(action.inputs["external_scores"])
            recorded_scores = tuple(action.inputs["quantized_scores"])
        except (KeyError, TypeError, ProtocolError) as exc:
            raise AdapterError("action inputs cannot be replayed") from exc
        ranking = self.nano.scorer.rank_recorded(
            context=context,
            option_set=option_set,
            raw_scores=raw_scores,
        )
        if list(ranking.quantized_scores) != list(recorded_scores):
            raise AdapterError("recorded quantized scores fail replay")
        replayed = self._action_from_ranking(
            self.host.capture(
                prompt=action.inputs["prompt"],
                activation=tuple(action.inputs["activation"]),
                seed=action.inputs["seed"],
                layer=action.layer,
                site=action.site,
            ),
            option_set,
            context=context,
            ranking=ranking,
            timestamp=action.timestamp,
            action_version=action.action_version,
        )
        if replayed.action_digest != action.action_digest:
            raise AdapterError("replayed action digest differs")
        return replayed
