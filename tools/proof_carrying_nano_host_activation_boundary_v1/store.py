"""Append-only SQLite store and export for activation records.

State slice: proof-carrying-nano-host-activation-boundary-v1.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from tools.proof_carrying_nano_interp_v1.protocol import canonical_bytes, canonical_digest, load_json_bytes

from .adapter import BUNDLE_STATUS, CLAIM_TYPE, PROTOCOL_ID, STATE_SLICE
from .proof import ActivationLeanProofEngine, ActivationProofAttempt


class ActivationStoreError(ValueError):
    """Raised when an immutable activation store invariant is violated."""


class ActivationStore:
    """SQLite WAL store with immutable activation and proof payloads."""

    def __init__(self, path: Path, *, proof_engine: ActivationLeanProofEngine | None = None) -> None:
        self.path = Path(path)
        self.proof_engine = proof_engine or ActivationLeanProofEngine()
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
                CREATE TABLE IF NOT EXISTS activation_actions (
                    action_digest TEXT PRIMARY KEY,
                    claim_key TEXT NOT NULL,
                    layer INTEGER NOT NULL,
                    site TEXT NOT NULL,
                    payload BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activation_proofs (
                    proof_digest TEXT PRIMARY KEY,
                    action_digest TEXT NOT NULL REFERENCES activation_actions(action_digest),
                    status TEXT NOT NULL CHECK (status IN ('checked', 'failed')),
                    payload BLOB NOT NULL
                );
                CREATE INDEX IF NOT EXISTS activation_proofs_action_idx
                    ON activation_proofs(action_digest);
                """
            )

    def __enter__(self) -> "ActivationStore":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    @staticmethod
    def _assert_action(action: Mapping[str, Any]) -> None:
        if action.get("state_slice") != STATE_SLICE or action.get("protocol_identity") != PROTOCOL_ID:
            raise ActivationStoreError("activation action identity mismatch")
        if action.get("action_digest") != canonical_digest(
            {key: value for key, value in action.items() if key != "action_digest"}
        ):
            raise ActivationStoreError("activation action digest mismatch")
        if action.get("claim", {}).get("type") != CLAIM_TYPE:
            raise ActivationStoreError("unsupported activation claim type")
        if action.get("outputs", {}).get("status") != "ActivationCaptured":
            raise ActivationStoreError("activation action status is invalid")

    def commit_action(self, action: Mapping[str, Any]) -> str:
        self._assert_action(action)
        encoded = canonical_bytes(dict(action))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO activation_actions(action_digest, claim_key, layer, site, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(action_digest) DO NOTHING
                """,
                (
                    action["action_digest"],
                    action["claim"]["claim_key"],
                    action["layer"],
                    action["site"],
                    encoded,
                ),
            )
            row = connection.execute(
                "SELECT payload FROM activation_actions WHERE action_digest = ?",
                (action["action_digest"],),
            ).fetchone()
            if row is None or bytes(row["payload"]) != encoded:
                raise ActivationStoreError("immutable activation payload conflict")
            connection.commit()
        return action["action_digest"]

    def commit_proof(self, proof: ActivationProofAttempt) -> str:
        payload = proof.to_dict()
        encoded = canonical_bytes(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload FROM activation_actions WHERE action_digest = ?",
                (proof.action_digest,),
            ).fetchone()
            if row is None:
                raise ActivationStoreError("proof references unknown activation action")
            if proof.status == "checked":
                action = load_json_bytes(bytes(row["payload"]))
                verified = self.proof_engine.attempt(action)
                if (
                    verified.status != "checked"
                    or verified.theorem_name != proof.theorem_name
                    or verified.statement != proof.statement
                    or verified.source != proof.source
                ):
                    raise ActivationStoreError("checked activation proof failed kernel recheck")
            connection.execute(
                """
                INSERT INTO activation_proofs(proof_digest, action_digest, status, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(proof_digest) DO NOTHING
                """,
                (proof.proof_digest, proof.action_digest, proof.status, encoded),
            )
            stored = connection.execute(
                "SELECT payload FROM activation_proofs WHERE proof_digest = ?",
                (proof.proof_digest,),
            ).fetchone()
            if stored is None or bytes(stored["payload"]) != encoded:
                raise ActivationStoreError("immutable activation proof conflict")
            connection.commit()
        return proof.proof_digest

    def export_bundle(self, *, action_digest: str) -> dict[str, Any]:
        with self._connect() as connection:
            action_row = connection.execute(
                "SELECT payload FROM activation_actions WHERE action_digest = ?",
                (action_digest,),
            ).fetchone()
            if action_row is None:
                raise ActivationStoreError("unknown activation action")
            proof_rows = connection.execute(
                "SELECT payload FROM activation_proofs WHERE action_digest = ? ORDER BY proof_digest",
                (action_digest,),
            ).fetchall()
        action = load_json_bytes(bytes(action_row["payload"]))
        proofs = [load_json_bytes(bytes(row["payload"])) for row in proof_rows]
        unsigned = {
            "action": action,
            "proofs": proofs,
            "protocol_identity": PROTOCOL_ID,
            "state_slice": STATE_SLICE,
            "status": BUNDLE_STATUS,
            "summary": (
                f"host_activation_capture at layer {action['layer']} {action['site']} "
                f"token {action['token_position']}; "
                f"{sum(proof.get('status') == 'checked' for proof in proofs)}/{len(proofs)} "
                "proof attempts kernel-checked."
            ),
        }
        return {**unsigned, "bundle_digest": canonical_digest(unsigned)}

    def validate_integrity(self) -> dict[str, int | str]:
        with self._connect() as connection:
            actions = connection.execute("SELECT COUNT(*) AS count FROM activation_actions").fetchone()["count"]
            attempts = connection.execute("SELECT COUNT(*) AS count FROM activation_proofs").fetchone()["count"]
            checked = connection.execute(
                "SELECT COUNT(*) AS count FROM activation_proofs WHERE status = 'checked'"
            ).fetchone()["count"]
        return {
            "state_slice": STATE_SLICE,
            "actions": int(actions),
            "proof_attempts": int(attempts),
            "checked_proofs": int(checked),
        }
