"""CLI for the bounded signed independent-review mailbox.

State slice: aligned-holistic-continual-learning-interpretability-monorepo-v1.

The CLI operates on already provisioned keys and registry files. It does not
configure Tailscale, OpenSSH, SFTP, model execution, provider calls, or review
authority.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

try:
    from . import protocol
except ImportError:  # pragma: no cover - supports direct script invocation
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import protocol


def _write_json_exclusive(path: Path, value: object, *, mode: int = 0o600) -> None:
    raw = (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")
    protocol._write_exclusive(path, raw, mode=mode)


def _mailbox(args: argparse.Namespace) -> protocol.FileMailbox:
    return protocol.FileMailbox(
        Path(args.mailbox),
        packet_digest=args.packet_digest,
        max_messages=args.max_messages,
        deadline=args.deadline,
        registry=protocol.load_registry(Path(args.registry)),
    )


def _add_mailbox_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mailbox", type=Path, required=True)
    parser.add_argument("--packet-digest", required=True)
    parser.add_argument("--max-messages", type=int, required=True)
    parser.add_argument("--deadline", required=True)
    parser.add_argument("--registry", type=Path, required=True)


def _cmd_keygen(args: argparse.Namespace) -> int:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError as exc:
        raise protocol.ProtocolError("Ed25519 runtime unavailable") from exc
    private = Ed25519PrivateKey.generate()
    public_key = private.public_key().public_bytes_raw()
    protocol._write_exclusive(args.private_output, private.private_bytes_raw(), mode=0o600)
    _write_json_exclusive(
        args.public_output,
        {
            "schema_version": f"{protocol.PROTOCOL_ID}-key-registry",
            "keys": [
                {
                    "key_id": args.key_id,
                    "identity": args.identity,
                    "role": args.role,
                    "public_key_base64": base64.b64encode(public_key).decode("ascii"),
                    "independently_administered": args.independently_administered,
                    "conflict_free": args.conflict_free,
                }
            ],
        },
        mode=0o644,
    )
    print(json.dumps({"key_id": args.key_id, "public_output": str(args.public_output)}, sort_keys=True))
    return 0


def _cmd_packet_digest(args: argparse.Namespace) -> int:
    print(protocol.packet_digest_from_json(args.input))
    return 0


def _cmd_append(args: argparse.Namespace) -> int:
    mailbox = _mailbox(args)
    body = protocol._read_regular(args.body)
    envelope = protocol.sign_message(
        packet_digest=args.packet_digest,
        parent_message_id=args.parent_message_id,
        turn=args.turn,
        kind=args.kind,
        sender_id=args.sender_id,
        sender_role=args.sender_role,
        recipient_role=args.recipient_role,
        signing_key_id=args.signing_key_id,
        created_at=args.created_at,
        body=body,
        private_key=protocol.load_private_key(args.private_key),
    )
    mailbox.append(envelope, body)
    print(json.dumps(envelope, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


def _cmd_import_message(args: argparse.Namespace) -> int:
    mailbox = _mailbox(args)
    value = protocol.load_json_bytes(protocol._read_regular(args.message_file))
    if not isinstance(value, dict):
        raise protocol.ProtocolError("imported message object")
    body = protocol._read_regular(args.body_file)
    mailbox.append(value, body)
    print(json.dumps({"imported": True, "message_id": value["message_id"]}, sort_keys=True))
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    mailbox = _mailbox(args)
    messages, _ = mailbox.read()
    print(
        json.dumps(
            {
                "sealed": mailbox.seal_path.is_file() and not mailbox.seal_path.is_symlink(),
                "message_count": len(messages),
                "last_message_id": messages[-1]["message_id"] if messages else None,
            },
            sort_keys=True,
        )
    )
    return 0


def _cmd_seal(args: argparse.Namespace) -> int:
    seal = _mailbox(args).seal(
        claim_ceiling=args.claim_ceiling,
        operator_identity=args.operator_identity,
        operator_key_id=args.operator_key_id,
        sealed_at=args.sealed_at,
    )
    print(json.dumps(seal, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


def _cmd_verify_seal(args: argparse.Namespace) -> int:
    seal = _mailbox(args).read_seal()
    print(json.dumps({"valid": True, "sealed_packet_sha256": seal["sealed_packet_sha256"]}, sort_keys=True))
    return 0


def _cmd_sign_verdict(args: argparse.Namespace) -> int:
    mailbox = _mailbox(args)
    messages, bodies = mailbox.read()
    seal = mailbox.read_seal()
    verdict = protocol.sign_verdict(
        seal,
        messages=messages,
        bodies=bodies,
        registry=mailbox.registry,
        decision=args.decision,
        reviewer_identity=args.reviewer_identity,
        signing_key_id=args.signing_key_id,
        conflict_of_interest=False,
        reviewed_at=args.reviewed_at,
        private_key=protocol.load_private_key(args.private_key),
    )
    _write_json_exclusive(args.output, verdict)
    print(json.dumps({"decision": verdict["decision"], "output": str(args.output)}, sort_keys=True))
    return 0


def _cmd_verify_verdict(args: argparse.Namespace) -> int:
    mailbox = _mailbox(args)
    messages, bodies = mailbox.read()
    seal = mailbox.read_seal()
    value = protocol.load_json_bytes(protocol._read_regular(args.verdict))
    if not isinstance(value, dict):
        raise protocol.ProtocolError("verdict object")
    trusted = protocol.verify_verdict(value, seal=seal, messages=messages, bodies=bodies, registry=mailbox.registry)
    print(json.dumps({"valid": True, "decision": value["decision"], "reviewer_key_id": trusted.key_id}, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="bounded independent-review communication boundary")
    subparsers = parser.add_subparsers(dest="command", required=True)

    keygen = subparsers.add_parser("keygen")
    keygen.add_argument("--private-output", type=Path, required=True)
    keygen.add_argument("--public-output", type=Path, required=True)
    keygen.add_argument("--key-id", required=True)
    keygen.add_argument("--identity", required=True)
    keygen.add_argument("--role", choices=[protocol.OPERATOR_ROLE, protocol.ADVISORY_REVIEWER_ROLE, protocol.FINAL_REVIEWER_ROLE], required=True)
    keygen.add_argument("--independently-administered", action="store_true")
    keygen.add_argument("--conflict-free", action="store_true")
    keygen.set_defaults(handler=_cmd_keygen)

    packet_digest = subparsers.add_parser("packet-digest")
    packet_digest.add_argument("--input", type=Path, required=True)
    packet_digest.set_defaults(handler=_cmd_packet_digest)

    append = subparsers.add_parser("append")
    _add_mailbox_arguments(append)
    append.add_argument("--body", type=Path, required=True)
    append.add_argument("--private-key", type=Path, required=True)
    append.add_argument("--parent-message-id")
    append.add_argument("--turn", type=int, required=True)
    append.add_argument("--kind", choices=sorted(protocol.MESSAGE_KINDS), required=True)
    append.add_argument("--sender-id", required=True)
    append.add_argument("--sender-role", choices=[protocol.OPERATOR_ROLE, protocol.ADVISORY_REVIEWER_ROLE], required=True)
    append.add_argument("--recipient-role", choices=[protocol.OPERATOR_ROLE, protocol.ADVISORY_REVIEWER_ROLE], required=True)
    append.add_argument("--signing-key-id", required=True)
    append.add_argument("--created-at", required=True)
    append.set_defaults(handler=_cmd_append)

    import_message = subparsers.add_parser("import-message")
    _add_mailbox_arguments(import_message)
    import_message.add_argument("--message-file", type=Path, required=True)
    import_message.add_argument("--body-file", type=Path, required=True)
    import_message.set_defaults(handler=_cmd_import_message)

    inspect = subparsers.add_parser("inspect")
    _add_mailbox_arguments(inspect)
    inspect.set_defaults(handler=_cmd_inspect)

    seal = subparsers.add_parser("seal")
    _add_mailbox_arguments(seal)
    seal.add_argument("--claim-ceiling", required=True)
    seal.add_argument("--operator-identity", required=True)
    seal.add_argument("--operator-key-id", required=True)
    seal.add_argument("--sealed-at", required=True)
    seal.set_defaults(handler=_cmd_seal)

    verify_seal = subparsers.add_parser("verify-seal")
    _add_mailbox_arguments(verify_seal)
    verify_seal.set_defaults(handler=_cmd_verify_seal)

    sign_verdict = subparsers.add_parser("sign-verdict")
    _add_mailbox_arguments(sign_verdict)
    sign_verdict.add_argument("--private-key", type=Path, required=True)
    sign_verdict.add_argument("--decision", choices=sorted(protocol.DECISIONS), required=True)
    sign_verdict.add_argument("--reviewer-identity", required=True)
    sign_verdict.add_argument("--signing-key-id", required=True)
    sign_verdict.add_argument("--reviewed-at", required=True)
    sign_verdict.add_argument("--output", type=Path, required=True)
    sign_verdict.set_defaults(handler=_cmd_sign_verdict)

    verify_verdict = subparsers.add_parser("verify-verdict")
    _add_mailbox_arguments(verify_verdict)
    verify_verdict.add_argument("--verdict", type=Path, required=True)
    verify_verdict.set_defaults(handler=_cmd_verify_verdict)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except protocol.ProtocolError as exc:
        print(f"protocol error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
