"""Concurrent append-only action and proof store for V1.

State slice: proof-carrying-nano-interp-v1.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .protocol import PROTOCOL_ID, STATE_SLICE, ProtocolError, canonical_bytes, canonical_digest, load_json_bytes
from .proof import LeanProofEngine, ProofAttempt
from .runtime import MiniAction


class StoreError(ValueError):
    """Raised when an immutable store invariant is violated."""


HYPOTHESIS_RECORD_ID = "__hypothesis_ranking__"
INTERVENTION_RECORD_ID = "__intervention_observation__"


class ConcurrentStore:
    """SQLite WAL store with one short transaction per public operation."""

    def __init__(self, path: Path, *, proof_engine: LeanProofEngine | None = None) -> None:
        self.path = Path(path)
        self.proof_engine = proof_engine or LeanProofEngine()
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

    def __enter__(self) -> "ConcurrentStore":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    @staticmethod
    def assert_action_digest(payload: dict[str, Any]) -> None:
        provided = payload.get("action_digest")
        unsigned = {key: value for key, value in payload.items() if key != "action_digest"}
        if provided != canonical_digest(unsigned):
            raise StoreError("action digest mismatch")
        if payload.get("state_slice") != STATE_SLICE or payload.get("protocol_identity") != PROTOCOL_ID:
            raise StoreError("action identity mismatch")

    def commit_action(self, action: MiniAction) -> str:
        payload = action.to_dict()
        try:
            self.assert_action_digest(payload)
        except (ProtocolError, StoreError) as exc:
            raise StoreError(str(exc)) from exc
        claim = payload["claim"]
        claim_type = claim.get("type")
        if claim_type == "feature_activation_exact":
            claim_subject = claim.get("feature_id")
            claim_value = claim.get("value")
        elif claim_type == "hypothesis_ranking":
            if payload["outputs"].get("status") != "HypothesisOnly":
                raise StoreError("hypothesis action must have HypothesisOnly status")
            claim_subject = HYPOTHESIS_RECORD_ID
            claim_value = claim.get("selected_option")
        elif claim_type == "intervention_effect_exact":
            if payload["outputs"].get("status") != "InterventionObserved":
                raise StoreError("intervention action must have InterventionObserved status")
            if claim.get("hypothesis_action_digest") != payload["inputs"].get(
                "hypothesis_action_digest"
            ):
                raise StoreError("intervention hypothesis reference is not bound")
            claim_subject = INTERVENTION_RECORD_ID
            claim_value = claim.get("effect")
        else:
            raise StoreError("unsupported action claim type")
        if not isinstance(claim_subject, str) or not claim_subject:
            raise StoreError("claim subject is missing")
        if claim_value is None:
            raise StoreError("claim value is missing")
        encoded = canonical_bytes(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if claim_type == "intervention_effect_exact":
                hypothesis_digest = payload["inputs"].get("hypothesis_action_digest")
                if hypothesis_digest is not None:
                    if not isinstance(hypothesis_digest, str) or not hypothesis_digest.startswith("sha256:"):
                        raise StoreError("intervention hypothesis reference is invalid")
                    reference = connection.execute(
                        """
                        SELECT a.payload,
                               EXISTS(
                                   SELECT 1 FROM proofs p
                                   WHERE p.action_digest = a.action_digest
                                     AND p.status = 'checked'
                               ) AS has_checked_proof
                        FROM actions a
                        WHERE a.action_digest = ?
                        """,
                        (hypothesis_digest,),
                    ).fetchone()
                    if reference is None:
                        raise StoreError("intervention hypothesis reference is unknown")
                    if not reference["has_checked_proof"]:
                        raise StoreError("intervention hypothesis reference has no checked proof")
                    reference_payload = self._decode(bytes(reference["payload"]))
                    if reference_payload.get("claim", {}).get("type") != "hypothesis_ranking":
                        raise StoreError("intervention hypothesis reference is not a ranking")
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
                    claim_subject,
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

    def commit_proof(self, proof: ProofAttempt) -> str:
        payload = proof.to_dict()
        try:
            ProofAttempt.assert_digest(payload)
        except ProtocolError as exc:
            raise StoreError(str(exc)) from exc
        encoded = canonical_bytes(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            action_row = connection.execute(
                "SELECT payload FROM actions WHERE action_digest = ?", (proof.action_digest,)
            ).fetchone()
            if action_row is None:
                raise StoreError("proof references unknown action")
            if proof.status == "checked":
                try:
                    action = MiniAction.from_dict(self._decode(bytes(action_row["payload"])))
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
                "SELECT payload FROM proofs WHERE proof_digest = ?", (proof.proof_digest,)
            ).fetchone()
            if row is None or bytes(row["payload"]) != encoded:
                raise StoreError("immutable proof payload conflict")
            connection.commit()
        return proof.proof_digest

    @staticmethod
    def _decode(raw: bytes) -> dict[str, Any]:
        value = load_json_bytes(raw)
        if not isinstance(value, dict):
            raise StoreError("stored payload is not an object")
        return value

    def query_proven_claims(
        self,
        *,
        layer: int | None = None,
        feature_id: str | None = None,
    ) -> list[dict[str, Any]]:
        predicates = ["p.status = 'checked'"]
        parameters: list[Any] = []
        if layer is not None:
            predicates.append("a.layer = ?")
            parameters.append(layer)
        if feature_id is not None:
            predicates.append("a.feature_id = ?")
            parameters.append(feature_id)
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
            result.append(
                {
                    "action_digest": row["action_digest"],
                    "action": self._decode(bytes(row["action_payload"])),
                    "proof": self._decode(bytes(row["proof_payload"])),
                }
            )
        return result

    def query_hypotheses(
        self,
        *,
        layer: int | None = None,
        candidate_id: str | None = None,
        option_set_digest: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return checked hypothesis rankings outside semantic claims."""

        predicates = ["p.status = 'checked'", "a.feature_id = ?"]
        parameters: list[Any] = [HYPOTHESIS_RECORD_ID]
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

    def query_interventions(
        self,
        *,
        layer: int | None = None,
        intervention_id: str | None = None,
        hypothesis_action_digest: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return checked intervention observations separately from rankings."""

        predicates = ["p.status = 'checked'", "a.feature_id = ?"]
        parameters: list[Any] = [INTERVENTION_RECORD_ID]
        if layer is not None:
            predicates.append("a.layer = ?")
            parameters.append(layer)
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
            claim = action.get("claim", {})
            inputs = action.get("inputs", {})
            if intervention_id is not None and claim.get("intervention_id") != intervention_id:
                continue
            if (
                hypothesis_action_digest is not None
                and inputs.get("hypothesis_action_digest") != hypothesis_action_digest
            ):
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

    def action_count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM actions").fetchone()
        return int(row["count"])

    def export_bundle(self, *, action_digest: str) -> dict[str, Any]:
        with self._connect() as connection:
            action_row = connection.execute(
                "SELECT payload FROM actions WHERE action_digest = ?", (action_digest,)
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
        if claim.get("type") == "hypothesis_ranking":
            bundle = {
                "action": action,
                "proofs": proofs,
                "protocol_identity": PROTOCOL_ID,
                "state_slice": STATE_SLICE,
                "status": "HypothesisOnly",
                "summary": (
                    f"hypothesis_ranking at layer {action['layer']} {action['site']} "
                    f"observed value {claim['option_set_digest']}; "
                    f"{checked}/{len(proofs)} proof attempts kernel-checked."
                ),
            }
        elif claim.get("type") == "intervention_effect_exact":
            bundle = {
                "action": action,
                "proofs": proofs,
                "protocol_identity": PROTOCOL_ID,
                "state_slice": STATE_SLICE,
                "status": "InterventionObserved",
                "summary": (
                    f"intervention_effect_exact at layer {action['layer']} {action['site']} "
                    f"observed value {claim['effect']}; "
                    f"{checked}/{len(proofs)} proof attempts kernel-checked."
                ),
            }
        elif claim.get("type") == "feature_activation_exact":
            bundle = {
                "action": action,
                "proofs": proofs,
                "protocol_identity": PROTOCOL_ID,
                "state_slice": STATE_SLICE,
                "summary": (
                    f"{claim['feature_id']} at layer {action['layer']} {action['site']} "
                    f"observed value {claim['value']}; "
                    f"{checked}/{len(proofs)} proof attempts kernel-checked."
                ),
            }
        else:
            raise StoreError("unsupported action claim type")
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
        proof_engine: LeanProofEngine | None = None,
        recheck_checked: bool = True,
    ) -> dict[str, int | str]:
        ConcurrentStore.assert_bundle_digest(bundle)
        if bundle.get("state_slice") != STATE_SLICE or bundle.get("protocol_identity") != PROTOCOL_ID:
            raise StoreError("bundle identity mismatch")
        action_value = bundle.get("action")
        proofs = bundle.get("proofs")
        if not isinstance(action_value, dict) or not isinstance(proofs, list):
            raise StoreError("bundle schema is invalid")
        if action_value.get("claim", {}).get("type") == "hypothesis_ranking":
            if bundle.get("status") != "HypothesisOnly":
                raise StoreError("hypothesis bundle status is invalid")
        if action_value.get("claim", {}).get("type") == "intervention_effect_exact":
            if bundle.get("status") != "InterventionObserved":
                raise StoreError("intervention bundle status is invalid")
        try:
            action = MiniAction.from_dict(action_value)
        except (KeyError, ProtocolError) as exc:
            raise StoreError(f"bundle action is invalid: {exc}") from exc
        checked = 0
        engine = proof_engine or LeanProofEngine()
        for proof_value in proofs:
            if not isinstance(proof_value, dict):
                raise StoreError("bundle proof is invalid")
            try:
                proof = ProofAttempt.from_dict(proof_value)
            except (KeyError, ProtocolError) as exc:
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
                action = MiniAction.from_dict(self._decode(bytes(row["payload"])))
            except (KeyError, ProtocolError) as exc:
                raise StoreError(f"action integrity check failed: {exc}") from exc
            actions[action.action_digest] = action
        checked = 0
        for row in proof_rows:
            try:
                proof = ProofAttempt.from_dict(self._decode(bytes(row["payload"])))
            except (KeyError, ProtocolError) as exc:
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

    def _detect_conflicts(self, *, record_type: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            if record_type == "hypothesis":
                predicate = "a.feature_id = ?"
                parameters = (HYPOTHESIS_RECORD_ID,)
            elif record_type == "intervention":
                predicate = "a.feature_id = ?"
                parameters = (INTERVENTION_RECORD_ID,)
            elif record_type == "feature":
                predicate = "a.feature_id NOT IN (?, ?)"
                parameters = (HYPOTHESIS_RECORD_ID, INTERVENTION_RECORD_ID)
            else:
                raise StoreError("unknown conflict record type")
            rows = connection.execute(
                f"""
                SELECT a.claim_key, a.claim_value, a.action_digest
                FROM actions a JOIN proofs p ON p.action_digest = a.action_digest
                WHERE p.status = 'checked' AND {predicate}
                ORDER BY a.claim_key, a.action_digest
                """,
                parameters,
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
                        "action_digests": [digest for value in sorted(values) for digest in values[value]],
                        "status": "conflict",
                    }
                )
        return conflicts

    def detect_conflicts(self) -> list[dict[str, Any]]:
        return self._detect_conflicts(record_type="feature")

    def detect_hypothesis_conflicts(self) -> list[dict[str, Any]]:
        return self._detect_conflicts(record_type="hypothesis")

    def detect_intervention_conflicts(self) -> list[dict[str, Any]]:
        return self._detect_conflicts(record_type="intervention")
