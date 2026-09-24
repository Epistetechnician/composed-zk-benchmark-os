"""Append-only store and record-only bundle export for causal observations.

State slice: proof-carrying-nano-causal-intervention-record-v1.

This store persists declarations and proof attempts. It never runs a host
model, applies an activation replacement, or authorizes causal assessment.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping

from tools.proof_carrying_nano_interp_v1.protocol import canonical_bytes, canonical_digest, load_json_bytes

from .proof import CausalInterventionLeanProofEngine, CausalInterventionProofAttempt
from .record import (
    ASSESSMENT_STATUS,
    CLAIM_TYPE,
    PROTOCOL_ID,
    RECORD_STATUS,
    STATE_SLICE,
    validate_record,
)


BUNDLE_STATUS = "CausalInterventionRecordOnly"


class CausalInterventionStoreError(ValueError):
    """Raised when an immutable causal record store invariant is violated."""


class CausalInterventionStore:
    """SQLite WAL store with immutable causal records and proof attempts."""

    def __init__(
        self,
        path: Path,
        *,
        proof_engine: CausalInterventionLeanProofEngine | None = None,
    ) -> None:
        self.path = Path(path)
        self.proof_engine = proof_engine or CausalInterventionLeanProofEngine()
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
                CREATE TABLE IF NOT EXISTS causal_records (
                    record_digest TEXT PRIMARY KEY,
                    claim_key TEXT NOT NULL,
                    target_layer INTEGER NOT NULL,
                    target_site TEXT NOT NULL,
                    payload BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS causal_intervention_proofs (
                    proof_digest TEXT PRIMARY KEY,
                    record_digest TEXT NOT NULL REFERENCES causal_records(record_digest),
                    status TEXT NOT NULL CHECK (status IN ('checked', 'failed')),
                    payload BLOB NOT NULL
                );
                CREATE INDEX IF NOT EXISTS causal_intervention_proofs_record_idx
                    ON causal_intervention_proofs(record_digest);
                CREATE INDEX IF NOT EXISTS causal_records_target_idx
                    ON causal_records(target_layer, target_site);
                """
            )

    def __enter__(self) -> "CausalInterventionStore":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    @staticmethod
    def _assert_record(record: Mapping[str, Any]) -> dict[str, Any]:
        try:
            normalized = validate_record(record)
        except (TypeError, KeyError, ValueError) as exc:
            raise CausalInterventionStoreError(str(exc)) from exc
        if normalized["state_slice"] != STATE_SLICE or normalized["protocol_identity"] != PROTOCOL_ID:
            raise CausalInterventionStoreError("causal record identity mismatch")
        if normalized["claim"]["type"] != CLAIM_TYPE:
            raise CausalInterventionStoreError("unsupported causal record claim type")
        if normalized["record_status"] != RECORD_STATUS:
            raise CausalInterventionStoreError("causal record status is invalid")
        if normalized["assessment_status"] != ASSESSMENT_STATUS:
            raise CausalInterventionStoreError("causal assessment is not review-sealed")
        return normalized

    def commit_record(self, record: Mapping[str, Any]) -> str:
        """Commit one immutable, unreviewed record declaration."""

        normalized = self._assert_record(record)
        encoded = canonical_bytes(normalized)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO causal_records(record_digest, claim_key, target_layer, target_site, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(record_digest) DO NOTHING
                """,
                (
                    normalized["record_digest"],
                    normalized["claim"]["claim_key"],
                    normalized["target"]["layer"],
                    normalized["target"]["site"],
                    encoded,
                ),
            )
            row = connection.execute(
                "SELECT payload FROM causal_records WHERE record_digest = ?",
                (normalized["record_digest"],),
            ).fetchone()
            if row is None or bytes(row["payload"]) != encoded:
                raise CausalInterventionStoreError("immutable causal record payload conflict")
            connection.commit()
        return normalized["record_digest"]

    def commit_proof(self, proof: CausalInterventionProofAttempt) -> str:
        """Commit a proof attempt, kernel-rechecking checked artifacts."""

        payload = proof.to_dict()
        try:
            parsed = CausalInterventionProofAttempt.from_dict(payload)
        except (TypeError, KeyError, ValueError) as exc:
            raise CausalInterventionStoreError(str(exc)) from exc
        encoded = canonical_bytes(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload FROM causal_records WHERE record_digest = ?",
                (parsed.action_digest,),
            ).fetchone()
            if row is None:
                raise CausalInterventionStoreError("proof references unknown causal record")
            record = load_json_bytes(bytes(row["payload"]))
            try:
                normalized = self._assert_record(record)
            except CausalInterventionStoreError:
                raise
            if parsed.status != normalized["proof_status"]:
                raise CausalInterventionStoreError("proof status is inconsistent with causal record")
            if parsed.status == "checked":
                verified = self.proof_engine.attempt(normalized)
                if verified.to_dict() != parsed.to_dict():
                    raise CausalInterventionStoreError("checked causal proof failed kernel recheck")
            else:
                if not parsed.diagnostics:
                    raise CausalInterventionStoreError("failed causal proof has no diagnostics")
            connection.execute(
                """
                INSERT INTO causal_intervention_proofs(proof_digest, record_digest, status, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(proof_digest) DO NOTHING
                """,
                (parsed.proof_digest, parsed.action_digest, parsed.status, encoded),
            )
            stored = connection.execute(
                "SELECT payload FROM causal_intervention_proofs WHERE proof_digest = ?",
                (parsed.proof_digest,),
            ).fetchone()
            if stored is None or bytes(stored["payload"]) != encoded:
                raise CausalInterventionStoreError("immutable causal proof payload conflict")
            connection.commit()
        return parsed.proof_digest

    def export_bundle(self, *, record_digest: str) -> dict[str, Any]:
        """Export a digest-bound record-only bundle."""

        with self._connect() as connection:
            record_row = connection.execute(
                "SELECT payload FROM causal_records WHERE record_digest = ?",
                (record_digest,),
            ).fetchone()
            if record_row is None:
                raise CausalInterventionStoreError("unknown causal intervention record")
            proof_rows = connection.execute(
                """
                SELECT payload FROM causal_intervention_proofs
                WHERE record_digest = ? ORDER BY proof_digest
                """,
                (record_digest,),
            ).fetchall()
        record = load_json_bytes(bytes(record_row["payload"]))
        proofs = [load_json_bytes(bytes(row["payload"])) for row in proof_rows]
        checked = sum(proof.get("status") == "checked" for proof in proofs)
        unsigned = {
            "assessment_status": ASSESSMENT_STATUS,
            "proofs": proofs,
            "protocol_identity": PROTOCOL_ID,
            "record": record,
            "state_slice": STATE_SLICE,
            "status": BUNDLE_STATUS,
            "summary": (
                f"causal_intervention_record at layer {record['target']['layer']} "
                f"{record['target']['site']} token {record['target']['token_position']}; "
                f"{checked}/{len(proofs)} proof attempts kernel-checked."
            ),
        }
        return {**unsigned, "bundle_digest": canonical_digest(unsigned)}

    def validate_integrity(self) -> dict[str, int | str]:
        with self._connect() as connection:
            records = connection.execute("SELECT COUNT(*) AS count FROM causal_records").fetchone()["count"]
            attempts = connection.execute("SELECT COUNT(*) AS count FROM causal_intervention_proofs").fetchone()["count"]
            checked = connection.execute(
                "SELECT COUNT(*) AS count FROM causal_intervention_proofs WHERE status = 'checked'"
            ).fetchone()["count"]
        return {
            "state_slice": STATE_SLICE,
            "records": int(records),
            "proof_attempts": int(attempts),
            "checked_proofs": int(checked),
        }
