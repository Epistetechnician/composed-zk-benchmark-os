from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from experiments.continual_learning import acquire_gemma3_bounded_webtextlike_wet_v1 as acquisition


def test_iter_wet_records_reads_target_and_payload(tmp_path: Path):
    payload = b"A bounded WET text record."
    raw = (
        b"WARC/1.0\r\n"
        b"WARC-Type: conversion\r\n"
        b"WARC-Target-URI: https://example.com/page\r\n"
        + f"Content-Length: {len(payload)}\r\n".encode()
        + b"Content-Type: text/plain\r\n\r\n"
        + payload
        + b"\r\n"
    )
    path = tmp_path / "sample.warc.wet.gz"
    with gzip.open(path, "wb") as handle:
        handle.write(raw)

    records = list(acquisition._iter_wet_records(path))

    assert len(records) == 1
    headers, actual_payload = records[0]
    assert headers["warc-target-uri"] == "https://example.com/page"
    assert actual_payload == payload


def test_normalize_text_collapses_whitespace_and_applies_minimum():
    assert acquisition._normalize_text(b"alpha\n\t beta", 5) == "alpha beta"
    assert acquisition._normalize_text(b"short", 6) is None


def test_first_path_requires_crawl_data_path(tmp_path: Path):
    path = tmp_path / "paths.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("crawl-data/CC-MAIN-2019-30/segments/example.wet.gz\n")

    assert acquisition._first_paths(path, 1)[0].startswith("crawl-data/")


def test_first_path_rejects_non_crawl_path(tmp_path: Path):
    path = tmp_path / "paths.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("not-a-common-crawl-path\n")

    with pytest.raises(ValueError, match="WET manifest path is invalid"):
        acquisition._first_paths(path, 1)


def test_first_paths_requires_requested_count(tmp_path: Path):
    path = tmp_path / "paths.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("crawl-data/CC-MAIN-2019-30/segments/example.wet.gz\n")

    with pytest.raises(ValueError, match="fewer than 2 objects"):
        acquisition._first_paths(path, 2)


def test_capacity_guard_rejects_insufficient_space(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        acquisition.shutil,
        "disk_usage",
        lambda path: acquisition.shutil._ntuple_diskusage(100, 90, 10),
    )

    with pytest.raises(OSError, match="insufficient free space"):
        acquisition._capacity_guard(tmp_path, max_bytes=20, reserve_bytes=1)
