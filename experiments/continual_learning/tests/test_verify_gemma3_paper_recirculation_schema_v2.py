from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning.verify_gemma3_paper_recirculation_schema_v2 import (
    CORPUS_SCHEMA,
    validate_packet,
    validate_corpus_root,
)


ROOT = Path(__file__).parents[3]
MANIFEST = ROOT / "docs/research/continual-learning/304-gemma3-paper-recirculation-schema-resolution-v2-manifest.json"
PROTOCOL = ROOT / "docs/research/continual-learning/303-gemma3-paper-recirculation-schema-resolution-v2-protocol.md"


def test_v2_packet_is_valid_but_not_authorized() -> None:
    result = validate_packet(MANIFEST, PROTOCOL)
    assert result["status"] == "valid_preacquisition_packet"
    assert result["corpus_schema"] == CORPUS_SCHEMA
    assert result["acquisition_authorized"] is False
    assert len(result["packet_digest"]) == 64
    assert len(result["packet_files"]) == 5


def test_packet_rejects_authorization_flip(tmp_path: Path) -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    value["acquisition_authorized"] = True
    altered = tmp_path / "manifest.json"
    altered.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="cannot authorize"):
        validate_packet(altered, PROTOCOL)


def test_corpus_validator_rejects_incomplete_manifest(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    root.chmod(0o700)
    (root / "manifest.json").write_text(
        json.dumps({"schema": CORPUS_SCHEMA, "state_slice": "gemma3-paper-recirculation-schema-resolution-v2"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="token count"):
        validate_corpus_root(root)
