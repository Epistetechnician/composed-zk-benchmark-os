from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


VERSION = "mesh.astral_v41r11_novelty_instrument.v1"
STATE_SLICE = "V41R11NoveltyInstrumentDesignAndLocalQualification"
SEED_COMMITMENT = "sha256:8f222fcadaedbc1bb650dae781aea3bf608901f5491cf90376e066eadad7117d"
CASE_COUNT = 32
QUERY_CLASSES = ("direct", "paraphrase", "composition")
LABELS = ("zavren", "kelvix", "morqen", "tulvash")


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def opaque(kind: str, index: int) -> str:
    digest = hashlib.sha256(
        f"{VERSION}|{SEED_COMMITMENT}|{kind}|{index}".encode()
    ).hexdigest()[:16]
    return f"v41r11-{kind}-{digest}"


def expected_packet() -> dict[str, Any]:
    cases = []
    for index in range(CASE_COUNT):
        subject = opaque("subject", index)
        bridge = opaque("bridge", index)
        target = LABELS[index % 4]
        rotation = (index // 4) % 4
        candidates = list(LABELS[rotation:] + LABELS[:rotation])
        cases.append(
            {
                "case_id": f"v41r11-{index:02d}",
                "subject": subject,
                "bridge": bridge,
                "target": target,
                "candidates": candidates,
                "training_facts": [
                    f"In sealed registry R11, {subject} points to {bridge}.",
                    f"In sealed registry R11, {bridge} resolves to {target}.",
                ],
                "training_rows": [
                    {
                        "prompt": f"In sealed registry R11, what does {subject} point to? Return only the entry.",
                        "answer": bridge,
                    },
                    {
                        "prompt": f"In sealed registry R11, what does {bridge} resolve to? Return only the value.",
                        "answer": target,
                    },
                ],
                "direct_prompt": f"In sealed registry R11, what does {bridge} resolve to? Return only the value.",
                "paraphrase_prompt": f"Give only the terminal label assigned to {bridge} by sealed registry R11.",
                "composition_prompt": (
                    f"In sealed registry R11, {subject} points to an intermediate entry. "
                    "What terminal label does that entry resolve to? Return only the label."
                ),
            }
        )
    body = {
        "version": VERSION,
        "state_slice": STATE_SLICE,
        "seed_commitment": SEED_COMMITMENT,
        "case_count": CASE_COUNT,
        "query_classes": list(QUERY_CLASSES),
        "opaque_labels": list(LABELS),
        "cases": cases,
        "source_text_present": False,
        "tune_present": False,
        "assessment_present": False,
    }
    return {**body, "instrument_sha256": canonical_hash(body)}


def validate(packet: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return {"valid": False, "errors": ["packet_type"], "claim_ceiling": None}
    if packet != expected_packet():
        errors.append("canonical_packet")
    cases = packet.get("cases")
    if not isinstance(cases, list) or len(cases) != CASE_COUNT:
        errors.append("case_count")
        cases = []
    target_counts = {label: 0 for label in LABELS}
    target_position_counts = {position: 0 for position in range(4)}
    label_position_counts = {label: {position: 0 for position in range(4)} for label in LABELS}
    training_prompts: set[str] = set()
    withheld_prompts: set[str] = set()
    for case in cases:
        target = case.get("target")
        candidates = case.get("candidates")
        if target not in target_counts or not isinstance(candidates, list) or set(candidates) != set(LABELS):
            errors.append("case_panel")
            continue
        target_counts[target] += 1
        target_position_counts[candidates.index(target)] += 1
        for position, label in enumerate(candidates):
            label_position_counts[label][position] += 1
        training_prompts.update(row.get("prompt", "") for row in case.get("training_rows", []))
        withheld_prompts.update(
            case.get(f"{kind}_prompt", "") for kind in ("paraphrase", "composition")
        )
    if set(target_counts.values()) != {8}:
        errors.append("target_balance")
    if set(target_position_counts.values()) != {8}:
        errors.append("target_position_balance")
    if {
        count for positions in label_position_counts.values() for count in positions.values()
    } != {8}:
        errors.append("label_position_balance")
    if training_prompts & withheld_prompts:
        errors.append("prompt_overlap")
    if packet.get("source_text_present") or packet.get("tune_present") or packet.get("assessment_present"):
        errors.append("sealed_boundary")
    return {
        "version": "astral.v41r11_novelty_instrument_validation.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "instrument_sha256": packet.get("instrument_sha256"),
        "case_count": len(cases),
        "query_count": len(cases) * 3,
        "target_counts": target_counts,
        "target_position_counts": target_position_counts,
        "label_position_counts": label_position_counts,
        "claim_ceiling": "LocalQualifiedNoveltyInstrumentV41R11" if not errors else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(json.loads(args.instrument.read_text()))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
