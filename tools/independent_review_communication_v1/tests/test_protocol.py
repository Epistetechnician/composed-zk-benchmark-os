"""Contract tests for the bounded independent-review communication boundary.

State slice: aligned-holistic-continual-learning-interpretability-monorepo-v1.
"""

from __future__ import annotations

import json
import base64
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


from tools.independent_review_communication_v1 import cli, protocol


PACKET_DIGEST = protocol.digest_bytes(b"frozen-review-packet-P0")
DEADLINE = "2026-09-12T00:00:00Z"
QUESTION_TIME = "2026-09-11T12:00:00Z"
ANSWER_TIME = "2026-09-11T12:01:00Z"


def _key(
    key_id: str,
    identity: str,
    role: str,
    private: Ed25519PrivateKey,
    *,
    independent: bool = False,
) -> protocol.TrustedKey:
    return protocol.TrustedKey(
        key_id=key_id,
        identity=identity,
        role=role,
        public_key=private.public_key().public_bytes_raw(),
        independently_administered=independent,
        conflict_free=independent,
    )


@pytest.fixture
def identities() -> tuple[dict[str, protocol.TrustedKey], dict[str, Ed25519PrivateKey]]:
    operator = Ed25519PrivateKey.generate()
    advisory = Ed25519PrivateKey.generate()
    final = Ed25519PrivateKey.generate()
    keys = {
        "operator-key": _key("operator-key", "operator", protocol.OPERATOR_ROLE, operator),
        "advisory-key": _key("advisory-key", "advisory-reviewer", protocol.ADVISORY_REVIEWER_ROLE, advisory),
        "final-key": _key("final-key", "external-reviewer", protocol.FINAL_REVIEWER_ROLE, final, independent=True),
    }
    return keys, {"operator": operator, "advisory": advisory, "final": final}


def _messages(
    identities: tuple[dict[str, protocol.TrustedKey], dict[str, Ed25519PrivateKey]],
) -> tuple[dict, dict, dict[str, bytes]]:
    _, private = identities
    question_body = b"Which exact runtime digest is bound to P0?"
    answer_body = b"The packet binds the frozen runtime manifest digest recorded in P0."
    question = protocol.sign_message(
        packet_digest=PACKET_DIGEST,
        parent_message_id=None,
        turn=0,
        kind="QUESTION",
        sender_id="advisory-reviewer",
        sender_role=protocol.ADVISORY_REVIEWER_ROLE,
        recipient_role=protocol.OPERATOR_ROLE,
        signing_key_id="advisory-key",
        created_at=QUESTION_TIME,
        body=question_body,
        private_key=private["advisory"],
    )
    answer = protocol.sign_message(
        packet_digest=PACKET_DIGEST,
        parent_message_id=question["message_id"],
        turn=1,
        kind="ANSWER",
        sender_id="operator",
        sender_role=protocol.OPERATOR_ROLE,
        recipient_role=protocol.ADVISORY_REVIEWER_ROLE,
        signing_key_id="operator-key",
        created_at=ANSWER_TIME,
        body=answer_body,
        private_key=private["operator"],
    )
    return question, answer, {question["message_id"]: question_body, answer["message_id"]: answer_body}


def test_canonical_json_rejects_duplicate_keys():
    with pytest.raises(protocol.ProtocolError, match="duplicate JSON key"):
        protocol.load_json_bytes(b'{"packet_digest":"x","packet_digest":"y"}')


def test_signed_messages_verify_and_bind_body_and_registry(identities):
    keys, _ = identities
    question, _, bodies = _messages(identities)
    trusted = protocol.verify_message(
        question,
        body=bodies[question["message_id"]],
        registry=keys,
        expected_packet_digest=PACKET_DIGEST,
    )
    assert trusted.key_id == "advisory-key"
    with pytest.raises(protocol.ProtocolError, match="message body binding"):
        protocol.verify_message(question, body=b"changed", registry=keys, expected_packet_digest=PACKET_DIGEST)


def test_seal_requires_every_message_body(identities):
    keys, _ = identities
    question, answer, bodies = _messages(identities)
    with pytest.raises(protocol.ProtocolError, match="clarification body missing"):
        protocol.seal_clarifications(
            [question, answer],
            packet_digest=PACKET_DIGEST,
            max_messages=4,
            deadline=DEADLINE,
            claim_ceiling="LocalDevelopmentInstrumentFeasibilityOnly",
            operator_identity="operator",
            operator_key_id="operator-key",
            registry=keys,
            bodies={question["message_id"]: bodies[question["message_id"]]},
            sealed_at="2026-09-11T12:02:00Z",
        )


def test_clarification_log_is_contiguous_alternating_and_bounded(identities):
    keys, _ = identities
    question, answer, bodies = _messages(identities)
    protocol.validate_clarification_log(
        [question, answer],
        packet_digest=PACKET_DIGEST,
        max_messages=4,
        deadline=DEADLINE,
        registry=keys,
        bodies=bodies,
    )
    with pytest.raises(protocol.ProtocolError, match="clarification turns"):
        protocol.validate_clarification_log(
            [answer, question],
            packet_digest=PACKET_DIGEST,
            max_messages=4,
            deadline=DEADLINE,
            registry=keys,
            bodies=bodies,
        )
    with pytest.raises(protocol.ProtocolError, match="message limit"):
        protocol.validate_clarification_log(
            [question, answer],
            packet_digest=PACKET_DIGEST,
            max_messages=1,
            deadline=DEADLINE,
            registry=keys,
            bodies=bodies,
        )


def test_clarification_deadline_is_fail_closed(identities):
    keys, private = identities
    late = protocol.sign_message(
        packet_digest=PACKET_DIGEST,
        parent_message_id=None,
        turn=0,
        kind="QUESTION",
        sender_id="advisory-reviewer",
        sender_role=protocol.ADVISORY_REVIEWER_ROLE,
        recipient_role=protocol.OPERATOR_ROLE,
        signing_key_id="advisory-key",
        created_at="2026-09-12T00:00:01Z",
        body=b"late",
        private_key=private["advisory"],
    )
    with pytest.raises(protocol.ProtocolError, match="deadline"):
        protocol.validate_clarification_log(
            [late],
            packet_digest=PACKET_DIGEST,
            max_messages=4,
            deadline=DEADLINE,
            registry=keys,
            bodies={late["message_id"]: b"late"},
        )


def test_scope_escalation_cannot_be_signed_or_accepted(identities):
    keys, _ = identities
    question, _, bodies = _messages(identities)
    question["scope"]["model_execution"] = True
    with pytest.raises(protocol.ProtocolError, match="communication scope escalation"):
        protocol.verify_message(
            question,
            body=bodies[question["message_id"]],
            registry=keys,
            expected_packet_digest=PACKET_DIGEST,
        )


def test_file_mailbox_is_append_only_and_seals(tmp_path: Path, identities):
    keys, _ = identities
    question, answer, bodies = _messages(identities)
    mailbox = protocol.FileMailbox(
        tmp_path / "mailbox",
        packet_digest=PACKET_DIGEST,
        max_messages=4,
        deadline=DEADLINE,
        registry=keys,
    )
    mailbox.append(question, bodies[question["message_id"]])
    mailbox.append(answer, bodies[answer["message_id"]])
    seal = mailbox.seal(
        claim_ceiling="LocalDevelopmentInstrumentFeasibilityOnly",
        operator_identity="operator",
        operator_key_id="operator-key",
        sealed_at="2026-09-11T12:02:00Z",
    )
    assert seal["communication_closed"] is True
    assert mailbox.read_seal()["sealed_packet_sha256"] == seal["sealed_packet_sha256"]
    with pytest.raises(protocol.ProtocolError, match="sealed"):
        mailbox.append(question, bodies[question["message_id"]])


def test_post_seal_mailbox_mutation_is_detected(tmp_path: Path, identities):
    keys, _ = identities
    question, answer, bodies = _messages(identities)
    mailbox = protocol.FileMailbox(tmp_path / "mailbox", packet_digest=PACKET_DIGEST, max_messages=4, deadline=DEADLINE, registry=keys)
    mailbox.append(question, bodies[question["message_id"]])
    seal = mailbox.seal(
        claim_ceiling="LocalDevelopmentInstrumentFeasibilityOnly",
        operator_identity="operator",
        operator_key_id="operator-key",
        sealed_at="2026-09-11T12:02:00Z",
    )
    extra = dict(answer)
    extra["turn"] = 1
    extra["parent_message_id"] = question["message_id"]
    extra["message_id"] = protocol.canonical_digest({key: value for key, value in extra.items() if key not in {"signature", "message_id"}})
    (mailbox.messages_dir / "0001-post-seal.json").write_text(json.dumps(extra), encoding="utf-8")
    (mailbox.bodies_dir / f"{extra['message_id'].removeprefix('sha256:')}.bin").write_bytes(b"answer")
    with pytest.raises(protocol.ProtocolError):
        mailbox.read_seal()
    assert seal["message_count"] == 1


def test_final_verdict_requires_independent_registry_key_and_binds_seal(identities):
    keys, private = identities
    question, answer, bodies = _messages(identities)
    seal = protocol.seal_clarifications(
        [question, answer],
        packet_digest=PACKET_DIGEST,
        max_messages=4,
        deadline=DEADLINE,
        claim_ceiling="LocalDevelopmentInstrumentFeasibilityOnly",
        operator_identity="operator",
        operator_key_id="operator-key",
        registry=keys,
        bodies=bodies,
        sealed_at="2026-09-11T12:02:00Z",
    )
    verdict = protocol.sign_verdict(
        seal,
        decision="ACCEPT",
        messages=[question, answer],
        bodies=bodies,
        registry=keys,
        reviewer_identity="external-reviewer",
        signing_key_id="final-key",
        conflict_of_interest=False,
        reviewed_at="2026-09-11T12:10:00Z",
        private_key=private["final"],
    )
    trusted = protocol.verify_verdict(verdict, seal=seal, messages=[question, answer], bodies=bodies, registry=keys)
    assert trusted.key_id == "final-key"
    assert verdict["execution_enabled"] is False
    assert verdict["model_execution_authorized"] is False
    assert verdict["assessment_opened"] is False


def test_final_verdict_rejects_operator_and_untrusted_reviewer(identities):
    keys, private = identities
    question, answer, bodies = _messages(identities)
    seal = protocol.seal_clarifications(
        [question, answer],
        packet_digest=PACKET_DIGEST,
        max_messages=4,
        deadline=DEADLINE,
        claim_ceiling="LocalDevelopmentInstrumentFeasibilityOnly",
        operator_identity="operator",
        operator_key_id="operator-key",
        registry=keys,
        bodies=bodies,
        sealed_at="2026-09-11T12:02:00Z",
    )
    with pytest.raises(protocol.ProtocolError, match="reviewer cannot be operator"):
        protocol.sign_verdict(
            seal,
            decision="ACCEPT",
            messages=[question, answer],
            bodies=bodies,
            registry=keys,
            reviewer_identity="operator",
            signing_key_id="operator-key",
            conflict_of_interest=False,
            reviewed_at="2026-09-11T12:10:00Z",
            private_key=private["operator"],
        )
    verdict = protocol.sign_verdict(
        seal,
        decision="REJECT",
        messages=[question, answer],
        bodies=bodies,
        registry=keys,
        reviewer_identity="external-reviewer",
        signing_key_id="final-key",
        conflict_of_interest=False,
        reviewed_at="2026-09-11T12:10:00Z",
        private_key=private["final"],
    )
    untrusted = dict(keys)
    untrusted["final-key"] = protocol.TrustedKey(
        key_id="final-key",
        identity="external-reviewer",
        role=protocol.FINAL_REVIEWER_ROLE,
        public_key=b"\x00" * 32,
        independently_administered=False,
        conflict_free=False,
    )
    with pytest.raises(protocol.ProtocolError, match="externally independent|registry-bound"):
        protocol.verify_verdict(verdict, seal=seal, messages=[question, answer], bodies=bodies, registry=untrusted)


def test_packet_digest_is_explicit_and_not_a_symbolic_placeholder():
    with pytest.raises(protocol.ProtocolError, match="sha256"):
        protocol.sign_message(
            packet_digest="sha256:P0",
            parent_message_id=None,
            turn=0,
            kind="QUESTION",
            sender_id="advisory-reviewer",
            sender_role=protocol.ADVISORY_REVIEWER_ROLE,
            recipient_role=protocol.OPERATOR_ROLE,
            signing_key_id="advisory-key",
            created_at=QUESTION_TIME,
            body=b"placeholder must not enter a real packet",
            private_key=Ed25519PrivateKey.generate(),
        )


def test_cli_keygen_writes_external_raw_key_and_registry(tmp_path: Path):
    private_path = tmp_path / "reviewer.key"
    registry_path = tmp_path / "reviewer-registry.json"
    assert cli.main(
        [
            "keygen",
            "--private-output",
            str(private_path),
            "--public-output",
            str(registry_path),
            "--key-id",
            "final-key",
            "--identity",
            "external-reviewer",
            "--role",
            "FINAL_REVIEWER",
            "--independently-administered",
            "--conflict-free",
        ]
    ) == 0
    assert len(private_path.read_bytes()) == 32
    assert protocol.load_private_key(private_path).public_key().public_bytes_raw()
    registry = protocol.load_registry(registry_path)
    assert registry["final-key"].independently_administered is True
    assert registry["final-key"].conflict_free is True


def test_mailbox_rejects_symlinked_root_before_mutating_target(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    original_mode = target.stat().st_mode & 0o777
    link = tmp_path / "mailbox-link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(protocol.ProtocolError, match="root symlink"):
        protocol.FileMailbox(
            link,
            packet_digest=PACKET_DIGEST,
            max_messages=4,
            deadline=DEADLINE,
            registry={},
        )
    assert target.stat().st_mode & 0o777 == original_mode


def test_cli_completes_append_seal_and_verdict_lifecycle(tmp_path: Path, identities, capsys):
    keys, private = identities
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": f"{protocol.PROTOCOL_ID}-key-registry",
                "keys": [
                    {
                        "key_id": key.key_id,
                        "identity": key.identity,
                        "role": key.role,
                        "public_key_base64": base64.b64encode(key.public_key).decode("ascii"),
                        "independently_administered": key.independently_administered,
                        "conflict_free": key.conflict_free,
                    }
                    for key in keys.values()
                ],
            }
        ),
        encoding="utf-8",
    )
    private_paths = {}
    for name, key in private.items():
        path = tmp_path / f"{name}.key"
        path.write_bytes(key.private_bytes_raw())
        path.chmod(0o600)
        private_paths[name] = path
    packet_path = tmp_path / "packet.json"
    packet_path.write_text('{"state_slice":"aligned-holistic-continual-learning-interpretability-monorepo-v1"}\n', encoding="utf-8")
    packet_digest = protocol.packet_digest_from_json(packet_path)
    mailbox_path = tmp_path / "mailbox"
    common = [
        "--mailbox", str(mailbox_path),
        "--packet-digest", packet_digest,
        "--max-messages", "4",
        "--deadline", DEADLINE,
        "--registry", str(registry_path),
    ]
    question_body = tmp_path / "question.txt"
    question_body.write_bytes(b"question")
    assert cli.main([
        "append", *common,
        "--body", str(question_body),
        "--private-key", str(private_paths["advisory"]),
        "--turn", "0",
        "--kind", "QUESTION",
        "--sender-id", "advisory-reviewer",
        "--sender-role", protocol.ADVISORY_REVIEWER_ROLE,
        "--recipient-role", protocol.OPERATOR_ROLE,
        "--signing-key-id", "advisory-key",
        "--created-at", QUESTION_TIME,
    ]) == 0
    question = protocol.FileMailbox(mailbox_path, packet_digest=packet_digest, max_messages=4, deadline=DEADLINE, registry=keys).read()[0][0]
    answer_body = tmp_path / "answer.txt"
    answer_body.write_bytes(b"answer")
    assert cli.main([
        "append", *common,
        "--body", str(answer_body),
        "--private-key", str(private_paths["operator"]),
        "--parent-message-id", question["message_id"],
        "--turn", "1",
        "--kind", "ANSWER",
        "--sender-id", "operator",
        "--sender-role", protocol.OPERATOR_ROLE,
        "--recipient-role", protocol.ADVISORY_REVIEWER_ROLE,
        "--signing-key-id", "operator-key",
        "--created-at", ANSWER_TIME,
    ]) == 0
    assert cli.main([
        "seal", *common,
        "--claim-ceiling", "LocalDevelopmentInstrumentFeasibilityOnly",
        "--operator-identity", "operator",
        "--operator-key-id", "operator-key",
        "--sealed-at", "2026-09-11T12:02:00Z",
    ]) == 0
    verdict_path = tmp_path / "verdict.json"
    assert cli.main([
        "sign-verdict", *common,
        "--private-key", str(private_paths["final"]),
        "--decision", "REJECT",
        "--reviewer-identity", "external-reviewer",
        "--signing-key-id", "final-key",
        "--reviewed-at", "2026-09-11T12:10:00Z",
        "--output", str(verdict_path),
    ]) == 0
    assert cli.main(["verify-verdict", *common, "--verdict", str(verdict_path)]) == 0
    assert '"valid": true' in capsys.readouterr().out


def test_cli_imports_received_signed_message_without_resigning(tmp_path: Path, identities, capsys):
    keys, private = identities
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": f"{protocol.PROTOCOL_ID}-key-registry",
                "keys": [
                    {
                        "key_id": key.key_id,
                        "identity": key.identity,
                        "role": key.role,
                        "public_key_base64": base64.b64encode(key.public_key).decode("ascii"),
                        "independently_administered": key.independently_administered,
                        "conflict_free": key.conflict_free,
                    }
                    for key in keys.values()
                ],
            }
        ),
        encoding="utf-8",
    )
    advisory_key = tmp_path / "advisory.key"
    advisory_key.write_bytes(private["advisory"].private_bytes_raw())
    advisory_key.chmod(0o600)
    common = [
        "--packet-digest", PACKET_DIGEST,
        "--max-messages", "4",
        "--deadline", DEADLINE,
        "--registry", str(registry_path),
    ]
    source = tmp_path / "reviewer-mailbox"
    destination = tmp_path / "operator-mailbox"
    body = tmp_path / "question.txt"
    body.write_bytes(b"received question")
    assert cli.main([
        "append", "--mailbox", str(source), *common,
        "--body", str(body),
        "--private-key", str(advisory_key),
        "--turn", "0",
        "--kind", "QUESTION",
        "--sender-id", "advisory-reviewer",
        "--sender-role", protocol.ADVISORY_REVIEWER_ROLE,
        "--recipient-role", protocol.OPERATOR_ROLE,
        "--signing-key-id", "advisory-key",
        "--created-at", QUESTION_TIME,
    ]) == 0
    source_message = next((source / "messages").glob("*.json"))
    source_body = next((source / "bodies").glob("*.bin"))
    assert cli.main([
        "import-message", "--mailbox", str(destination), *common,
        "--message-file", str(source_message),
        "--body-file", str(source_body),
    ]) == 0
    assert cli.main(["inspect", "--mailbox", str(destination), *common]) == 0
    assert '"message_count": 1' in capsys.readouterr().out


def test_cli_packet_digest_uses_strict_canonical_json(tmp_path: Path, capsys):
    packet = tmp_path / "packet.json"
    packet.write_text('{"b": 2, "a": 1}\n', encoding="utf-8")
    assert cli.main(["packet-digest", "--input", str(packet)]) == 0
    assert capsys.readouterr().out.strip() == protocol.canonical_digest({"a": 1, "b": 2})
