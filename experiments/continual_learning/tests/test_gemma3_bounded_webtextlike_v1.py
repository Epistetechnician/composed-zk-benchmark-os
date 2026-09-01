from __future__ import annotations

import bz2
import gzip
import json
import zipfile
from pathlib import Path

import pytest

from experiments.continual_learning import acquire_gemma3_bounded_webtextlike_v1 as acquisition


def test_selection_is_deterministic_and_bounded(tmp_path: Path):
    archive = tmp_path / "OpenWebText.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for index, member in enumerate(acquisition.URL_MEMBERS):
            bundle.writestr(member, f"https://example.com/{index}/a\nhttps://example.com/{index}/b\n")

    first = acquisition.select_urls(archive, 3)
    second = acquisition.select_urls(archive, 3)

    assert first == second
    assert len(first) == 3
    assert [item["selection_rank"] for item in first] == [0, 1, 2]
    assert len({item["url"] for item in first}) == 3


def test_selection_supports_plain_and_bzip2_named_members(tmp_path: Path):
    archive = tmp_path / "OpenWebText.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(acquisition.URL_MEMBERS[0], "https://example.com/plain\n")
        bundle.writestr(acquisition.URL_MEMBERS[1], bz2.compress(b"https://example.com/bzip2\n"))
        bundle.writestr(acquisition.URL_MEMBERS[2], "https://example.com/plain-2\n")

    selected = acquisition.select_urls(archive, 10)

    assert {item["url"] for item in selected} == {
        "https://example.com/plain",
        "https://example.com/plain-2",
        "https://example.com/bzip2",
    }


def test_html_to_text_decompresses_warc_and_omits_script_content():
    plain_warc = (
        b"WARC/1.0\r\nContent-Type: application/http; msgtype=response\r\n"
        b"Content-Length: 100\r\n\r\n"
        b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        b"<html><script>secret</script><p>Hello&nbsp;world</p></html>"
    )

    text = acquisition.html_to_text(gzip.compress(plain_warc), min_chars=1)

    assert text == "Hello world"
    assert "secret" not in text


def test_split_and_record_id_are_stable():
    url = "https://example.com/stable"

    assert acquisition._split_for(url) == acquisition._split_for(url)
    assert acquisition._record_id(url, "CC-MAIN-2019-30", "sha1:abc") == acquisition._record_id(
        url, "CC-MAIN-2019-30", "sha1:abc"
    )


def test_capacity_guard_rejects_insufficient_free_space(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        acquisition.shutil,
        "disk_usage",
        lambda path: acquisition.shutil._ntuple_diskusage(100, 90, 10),
    )

    with pytest.raises(OSError, match="insufficient free space"):
        acquisition._capacity_guard(tmp_path, max_bytes=20, reserve_bytes=1)


def test_external_destination_rejects_repository(tmp_path: Path):
    with pytest.raises(ValueError, match="outside the repository"):
        acquisition.external_path(acquisition.REPO_ROOT / "bounded", "destination root")


def test_manifest_json_remains_json_object_contract():
    value = {"schema": acquisition.SCHEMA, "full_c4_webtextlike": False}

    assert json.loads(json.dumps(value)) == value
