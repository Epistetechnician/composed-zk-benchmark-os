"""Concurrent store and bundle export for the pinned Jevlike boundary.

State slice: proof-carrying-nano-interp-jevlike-adapter-v1.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tools.proof_carrying_nano_interp_v1.protocol import (
    ProtocolError,
    canonical_bytes,
    canonical_digest,
    load_json_bytes,
)
from tools.proof_carrying_nano_interp_v1.runtime import MiniAction

from .adapter import PROTOCOL_ID, STATE_SLICE
from .proof import JevlikeLeanProofEngine, JevlikeProofAttempt, ProofError


JEVLIKE_RECORD_ID = "__jevlike_hypothesis_ranking__"


class StoreError(ValueError):
    """Raised when an immutable Jevlike store invariant is violated."""


def _action_from_dict(payload: dict[str, Any]) -> MiniAction:
    if not isinstance(payload, dict):
        raise StoreError("stored action is not an object")
    provided = payload.get("action_digest")
    unsigned = {key: value for key, value in payload.items() if key != "action_digest"}
    if provided != canonical_digest(unsigned):
        raise StoreError("action digest mismatch")
    if payload.get("state_slice") != STATE_SLICE or payload.get("protocol_identity") != PROTOCOL_ID:
        raise StoreError("action identity mismatch")
    expected_keys = {
        "action_digest",
        "action_version",
        "claim",
        "host_checkpoint_id",
        "host_context_hash",
        "inputs",
        "layer",
        "nano_identity",
        "outputs",
        "protocol_identity",
        "site",
        "state_slice",
        "timestamp",
    }
    if set(payload) != expected_keys:
        raise StoreError("action schema is not closed")
    try:
        return MiniAction(
            state_slice=payload["state_slice"],
            protocol_identity=payload["protocol_identity"],
            action_version=payload["action_version"],
            timestamp=payload["timestamp"],
            inputs=payload["inputs"],
            outputs=payload["outputs"],
            host_context_hash=payload["host_context_hash"],
            host_checkpoint_id=payload["host_checkpoint_id"],
            nano_identity=payload["nano_identity"],
            layer=payload["layer"],
            site=payload["site"],
            claim=payload["claim"],
            action_digest=payload["action_digest"],
        )
    except (KeyError, TypeError) as exc:
        raise StoreError("action fields are invalid") from exc


class JevlikeHypothesisStore:
    """SQLite WAL store that extends the V1 append-only schema for Jevlike."""

    def __init__(
        self,
        path: Path,
        *,
        proof_engine: JevlikeLeanProofEngine | None = None,
    ) -> None:
        self.path = Path(path)
        self.proof_engine = proof_engine or JevlikeLeanProofEngine()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS actions (
                    action_digest TEXT PRIMARY KEY,
                    claim_key TEXT NOT NULL,
                    claim_value TEXT NOT NULL,
                    layer INTEGER NOT NULL,
                    feature_id TEXT NOT NULL,
                    payload BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proofs (
                    proof_digest TEXT PRIMARY KEY,
                    action_digest TEXT NOT NULL REFERENCES actions(action_digest),
                    status TEXT NOT NULL CHECK (status IN ('checked', 'failed')),
                    payload BLOB NOT NULL
                );
                CREATE INDEX IF NOT EXISTS proofs_action_idx ON proofs(action_digest);
                CREATE INDEX IF NOT EXISTS actions_claim_idx ON actions(layer, feature_id);
                """
            )

    def __enter__(self) -> "JevlikeHypothesisStore":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    @staticmethod
    def _decode(raw: bytes) -> dict[str, Any]:
        value = load_json_bytes(raw)
        if not isinstance(value, dict):
            raise StoreError("stored payload is not an object")
        return value

    def commit_action(self, action: MiniAction) -> str:
        payload = action.to_dict()
        try:
            _action_from_dict(payload)
            self.proof_engine._validate_action(action)
        except (ProtocolError, ProofError, StoreError, KeyError, TypeError) as exc:
            raise StoreError(str(exc)) from exc
        claim = payload["claim"]
        if payload["outputs"].get("status") != "HypothesisOnly":
            raise StoreError("Jevlike action must have HypothesisOnly status")
        if claim.get("type") != "jevlike_hypothesis_ranking":
            raise StoreError("unsupported Jevlike action claim type")
        claim_value = claim.get("selected_option")
        if not isinstance(claim.get("claim_key"), str) or not claim.get("claim_key"):
            raise StoreError("claim key is missing")
        if not isinstance(claim_value, str) or not claim_value:
            raise StoreError("selected hypothesis is missing")
        encoded = canonical_bytes(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO actions(action_digest, claim_key, claim_value, layer, feature_id, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(action_digest) DO NOTHING
                """,
                (
                    payload["action_digest"],
                    claim["claim_key"],
                    canonical_bytes(claim_value).decode("utf-8"),
                    payload["layer"],
                    JEVLIKE_RECORD_ID,
                    encoded,
                ),
            )
            row = connection.execute(
                "SELECT payload FROM actions WHERE action_digest = ?",
                (payload["action_digest"],),
            ).fetchone()
            if row is None or bytes(row["payload"]) != encoded:
                raise StoreError("immutable action payload conflict")
            connection.commit()
        return payload["action_digest"]

    def commit_proof(self, proof: JevlikeProofAttempt) -> str:
        payload = proof.to_dict()
        try:
            JevlikeProofAttempt.assert_digest(payload)
        except ProtocolError as exc:
            raise StoreError(str(exc)) from exc
        encoded = canonical_bytes(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            action_row = connection.execute(
                "SELECT payload FROM actions WHERE action_digest = ?",
                (proof.action_digest,),
            ).fetchone()
            if action_row is None:
                raise StoreError("proof references unknown action")
            if proof.status == "checked":
                try:
                    action = _action_from_dict(self._decode(bytes(action_row["payload"])))
                    verified = self.proof_engine.attempt(action)
                except (ProtocolError, OSError) as exc:
                    raise StoreError(f"checked proof recheck failed: {exc}") from exc
                if (
                    verified.status != "checked"
                    or verified.theorem_name != proof.theorem_name
                    or verified.statement != proof.statement
                    or verified.source != proof.source
                ):
                    raise StoreError("checked proof failed kernel recheck")
            connection.execute(
                """
                INSERT INTO proofs(proof_digest, action_digest, status, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(proof_digest) DO NOTHING
                """,
                (proof.proof_digest, proof.action_digest, proof.status, encoded),
            )
            row = connection.execute(
                "SELECT payload FROM proofs WHERE proof_digest = ?",
                (proof.proof_digest,),
            ).fetchone()
            if row is None or bytes(row["payload"]) != encoded:
                raise StoreError("immutable proof payload conflict")
            connection.commit()
        return proof.proof_digest

    def query_hypotheses(
        self,
        *,
        layer: int | None = None,
        candidate_id: str | None = None,
        option_set_digest: str | None = None,
    ) -> list[dict[str, Any]]:
        predicates = ["p.status = 'checked'", "a.feature_id = ?"]
        parameters: list[Any] = [JEVLIKE_RECORD_ID]
        if layer is not None:
            predicates.append("a.layer = ?")
            parameters.append(layer)
        if candidate_id is not None:
            predicates.append("a.claim_value = ?")
            parameters.append(canonical_bytes(candidate_id).decode("utf-8"))
        query = f"""
            SELECT a.action_digest, a.payload AS action_payload, p.payload AS proof_payload
            FROM actions a JOIN proofs p ON p.action_digest = a.action_digest
            WHERE {' AND '.join(predicates)}
            ORDER BY a.action_digest, p.proof_digest
        """
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        result = []
        for row in rows:
            action = self._decode(bytes(row["action_payload"]))
            if option_set_digest is not None and action["claim"].get("option_set_digest") != option_set_digest:
                continue
            result.append(
                {
                    "action_digest": row["action_digest"],
                    "action": action,
                    "proof": self._decode(bytes(row["proof_payload"])),
                }
            )
        return result

    def list_proof_attempts(self, *, action_digest: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT payload FROM proofs"
        parameters: list[Any] = []
        if action_digest is not None:
            query += " WHERE action_digest = ?"
            parameters.append(action_digest)
        query += " ORDER BY proof_digest"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._decode(bytes(row["payload"])) for row in rows]

    def export_bundle(self, *, action_digest: str) -> dict[str, Any]:
        with self._connect() as connection:
            action_row = connection.execute(
                "SELECT payload FROM actions WHERE action_digest = ?",
                (action_digest,),
            ).fetchone()
            if action_row is None:
                raise StoreError("cannot export unknown action")
            proof_rows = connection.execute(
                "SELECT payload FROM proofs WHERE action_digest = ? ORDER BY proof_digest",
                (action_digest,),
            ).fetchall()
        action = self._decode(bytes(action_row["payload"]))
        proofs = [self._decode(bytes(row["payload"])) for row in proof_rows]
        checked = sum(proof["status"] == "checked" for proof in proofs)
        claim = action["claim"]
        if claim.get("type") != "jevlike_hypothesis_ranking":
            raise StoreError("unsupported Jevlike action claim type")
        bundle = {
            "action": action,
            "proofs": proofs,
            "protocol_identity": PROTOCOL_ID,
            "state_slice": STATE_SLICE,
            "status": "HypothesisOnly",
            "summary": (
                f"jevlike_hypothesis_ranking at layer {action['layer']} {action['site']} "
                f"selected {claim['selected_option']}; "
                f"{checked}/{len(proofs)} proof attempts kernel-checked."
            ),
        }
        return {**bundle, "bundle_digest": canonical_digest(bundle)}

    def write_bundle(self, path: Path, *, action_digest: str) -> str:
        bundle = self.export_bundle(action_digest=action_digest)
        Path(path).write_bytes(canonical_bytes(bundle))
        return bundle["bundle_digest"]

    @staticmethod
    def assert_bundle_digest(bundle: dict[str, Any]) -> None:
        provided = bundle.get("bundle_digest")
        unsigned = {key: value for key, value in bundle.items() if key != "bundle_digest"}
        if provided != canonical_digest(unsigned):
            raise StoreError("bundle digest mismatch")

    @staticmethod
    def validate_bundle(
        bundle: dict[str, Any],
        *,
        proof_engine: JevlikeLeanProofEngine | None = None,
        recheck_checked: bool = True,
    ) -> dict[str, int | str]:
        JevlikeHypothesisStore.assert_bundle_digest(bundle)
        if bundle.get("state_slice") != STATE_SLICE or bundle.get("protocol_identity") != PROTOCOL_ID:
            raise StoreError("bundle identity mismatch")
        action_value = bundle.get("action")
        proofs = bundle.get("proofs")
        if not isinstance(action_value, dict) or not isinstance(proofs, list):
            raise StoreError("bundle schema is invalid")
        if bundle.get("status") != "HypothesisOnly":
            raise StoreError("Jevlike bundle status is invalid")
        try:
            action = _action_from_dict(action_value)
            engine = proof_engine or JevlikeLeanProofEngine()
            engine._validate_action(action)
        except (KeyError, ProtocolError, StoreError, ProofError, TypeError) as exc:
            raise StoreError(f"bundle action is invalid: {exc}") from exc
        checked = 0
        engine = proof_engine or JevlikeLeanProofEngine()
        for proof_value in proofs:
            if not isinstance(proof_value, dict):
                raise StoreError("bundle proof is invalid")
            try:
                proof = JevlikeProofAttempt.from_dict(proof_value)
            except (KeyError, ProtocolError, TypeError) as exc:
                raise StoreError(f"bundle proof is invalid: {exc}") from exc
            if proof.action_digest != action.action_digest:
                raise StoreError("bundle proof action binding mismatch")
            if proof.status == "checked":
                checked += 1
                if recheck_checked:
                    verified = engine.attempt(action)
                    if (
                        verified.status != "checked"
                        or verified.theorem_name != proof.theorem_name
                        or verified.statement != proof.statement
                        or verified.source != proof.source
                    ):
                        raise StoreError("bundle checked proof failed kernel recheck")
        return {
            "state_slice": STATE_SLICE,
            "action": 1,
            "proof_attempts": len(proofs),
            "checked_proofs": checked,
        }

    def validate_integrity(self, *, recheck_checked: bool = True) -> dict[str, int | str]:
        with self._connect() as connection:
            action_rows = connection.execute("SELECT payload FROM actions ORDER BY action_digest").fetchall()
            proof_rows = connection.execute("SELECT payload FROM proofs ORDER BY proof_digest").fetchall()
        actions: dict[str, MiniAction] = {}
        for row in action_rows:
            try:
                action = _action_from_dict(self._decode(bytes(row["payload"])))
                self.proof_engine._validate_action(action)
            except (KeyError, ProtocolError, StoreError, ProofError, TypeError) as exc:
                raise StoreError(f"action integrity check failed: {exc}") from exc
            actions[action.action_digest] = action
        checked = 0
        for row in proof_rows:
            try:
                proof = JevlikeProofAttempt.from_dict(self._decode(bytes(row["payload"])))
            except (KeyError, ProtocolError, StoreError, TypeError) as exc:
                raise StoreError(f"proof integrity check failed: {exc}") from exc
            action = actions.get(proof.action_digest)
            if action is None:
                raise StoreError("proof references unknown action")
            if proof.status == "checked":
                checked += 1
                if recheck_checked:
                    verified = self.proof_engine.attempt(action)
                    if (
                        verified.status != "checked"
                        or verified.theorem_name != proof.theorem_name
                        or verified.statement != proof.statement
                        or verified.source != proof.source
                    ):
                        raise StoreError("checked proof integrity recheck failed")
        return {
            "state_slice": STATE_SLICE,
            "actions": len(actions),
            "proof_attempts": len(proof_rows),
            "checked_proofs": checked,
        }

    def detect_hypothesis_conflicts(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT a.claim_key, a.claim_value, a.action_digest
                FROM actions a JOIN proofs p ON p.action_digest = a.action_digest
                WHERE p.status = 'checked' AND a.feature_id = ?
                ORDER BY a.claim_key, a.action_digest
                """,
                (JEVLIKE_RECORD_ID,),
            ).fetchall()
        grouped: dict[str, dict[str, list[str]]] = {}
        for row in rows:
            grouped.setdefault(row["claim_key"], {}).setdefault(row["claim_value"], []).append(
                row["action_digest"]
            )
        conflicts = []
        for claim_key, values in grouped.items():
            if len(values) > 1:
                conflicts.append(
                    {
                        "claim_key": claim_key,
                        "values": [json.loads(value) for value in sorted(values)],
                        "action_digests": [
                            digest for value in sorted(values) for digest in values[value]
                        ],
                        "status": "conflict",
                    }
                )
        return conflicts
