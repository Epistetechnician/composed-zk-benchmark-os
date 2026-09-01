#!/usr/bin/env python3
"""Acquire and normalize the external Gemma3 recirculation corpus.

State slice: continual-learning-gemma3-paper-recirculation-acquisition-v1.

This command is the only network-enabled part of the Gemma3 lane. It downloads
only pinned, documented upstream files, keeps raw inputs outside the
repository, emits the two-field ``gemma3-source-v1`` JSONL contract, and
atomically publishes a source root only after the independent validator passes.
It does not load a model, train, run the scientific experiment, or mutate an
Evidence Ledger.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ACQUISITION_STATE_SLICE = (
    "continual-learning-gemma3-paper-recirculation-acquisition-v1"
)
CONSUMER_STATE_SLICE = "continual-learning-gemma3-paper-recirculation-v1"
MANIFEST_SCHEMA = "gemma3-paper-recirculation-acquisition-v1"
SOURCE_RECORD_SCHEMA = "gemma3-source-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3PaperAlignedRecirculationAcquisition"
SELECTION_POLICY = "fixed-upstream-order-v1"
FIT_RECORD_LIMITS = {"arxiv": 2048, "c4": 2048, "pg19": 32}
BIG_PATENT_RECORD_LIMIT = 10_000

FIT_DATASETS = ("arxiv", "c4", "pg19")
ASSESSMENT_DATASETS = (
    "arxiv",
    "big_patent",
    "billsum",
    "booksum/book",
    "c4/webtextlike",
    "gov_report",
    "lambada",
    "newsroom",
    "pg19",
    "pubmed",
)
OUTPUT_PATHS = {
    "fit/arxiv": Path("fit/arxiv.jsonl"),
    "fit/c4": Path("fit/c4.jsonl"),
    "fit/pg19": Path("fit/pg19.jsonl"),
    "assessment/arxiv": Path("assessment/arxiv.jsonl"),
    "assessment/big_patent": Path("assessment/big_patent.jsonl"),
    "assessment/billsum": Path("assessment/billsum.jsonl"),
    "assessment/booksum/book": Path("assessment/booksum-book.jsonl"),
    "assessment/c4/webtextlike": Path("assessment/c4-webtextlike.jsonl"),
    "assessment/gov_report": Path("assessment/gov_report.jsonl"),
    "assessment/lambada": Path("assessment/lambada.jsonl"),
    "assessment/newsroom": Path("assessment/newsroom.jsonl"),
    "assessment/pg19": Path("assessment/pg19.jsonl"),
    "assessment/pubmed": Path("assessment/pubmed.jsonl"),
}

SCIENTIFIC_PAPERS_REVISION = "1.1.1"
SCIENTIFIC_PAPERS_URLS = {
    "arxiv": "https://s3.amazonaws.com/datasets.huggingface.co/scientific_papers/1.1.1/arxiv-dataset.zip",
    "pubmed": "https://s3.amazonaws.com/datasets.huggingface.co/scientific_papers/1.1.1/pubmed-dataset.zip",
}
PG19_REPO = "deepmind/pg19"
PG19_REVISION = "4d28bd77e66947ad3835cf78ed7aaeb4dd87ad8b"
PG19_GCS_ROOT = "https://storage.googleapis.com/deepmind-gutenberg/"
HF_REVISIONS = {
    "big_patent": "2a5336492ddc4e21cebd3865fd2a7e8b070bfede",
    "billsum": "3d8510441c06a3d9dfb32eb0d7f80151730bcc4f",
    "booksum": "c62321036e5647db5767ecaff139912b554dc938",
    "gov_report": "32feeaede49fed993aef070bc4da09263fd0429a",
    "lambada": "900124bf3b8235c6daf21033af9948b3f07346c4",
}


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def _require_absent(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing {label}: {path}")


def _download(url: str, destination: Path) -> Path:
    """Download one immutable raw file without overwriting a prior file."""

    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ValueError(f"raw destination is not a regular file: {destination}")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.download")
    if temporary.exists():
        raise FileExistsError(f"refusing to reuse incomplete download: {temporary}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "gemma3-paper-recirculation-acquisition-v1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _hf_url(repo: str, revision: str, filename: str) -> str:
    encoded = urllib.parse.quote(filename, safe="/")
    return f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{encoded}?download=true"


def _raw_artifact(path: Path, source: str, *, role: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"raw artifact is not a regular file: {path}")
    return {
        "path": str(path.resolve()),
        "role": role,
        "source": source,
        "byte_len": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _record(document_id: Any, text: Any) -> tuple[str, str]:
    if not isinstance(document_id, str) or not document_id:
        raise ValueError("upstream record has no stable document id")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"upstream record has empty text: {document_id}")
    return document_id, text


def _write_jsonl(destination: Path, rows: Iterable[tuple[str, str]]) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    count = 0
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for document_id, text in rows:
            document_id, text = _record(document_id, text)
            if document_id in seen:
                raise ValueError(f"duplicate normalized document id: {document_id}")
            seen.add(document_id)
            handle.write(
                json.dumps(
                    {"document_id": document_id, "text": text},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            count += 1
    if count == 0:
        raise ValueError(f"normalization produced no records: {destination}")
    return count


def _limit_rows(rows: Iterable[tuple[str, str]], limit: int | None) -> Iterator[tuple[str, str]]:
    for index, row in enumerate(rows):
        if limit is not None and index >= limit:
            break
        yield row


def _scientific_rows(archive: Path, split: str, dataset: str) -> Iterator[tuple[str, str]]:
    with zipfile.ZipFile(archive) as bundle:
        candidates = [
            name
            for name in bundle.namelist()
            if name.endswith(f"/{split}.txt") or name == f"{split}.txt"
        ]
        if len(candidates) != 1:
            raise ValueError(f"could not resolve {dataset}/{split}.txt in {archive}")
        with bundle.open(candidates[0], "r") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    value = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"invalid scientific-papers record {archive}:{line_number}"
                    ) from exc
                article_id = value.get("article_id")
                article_text = value.get("article_text")
                if not isinstance(article_text, list):
                    raise ValueError("scientific-papers article_text is not a list")
                yield _record(
                    f"scientific_papers:{dataset}:{article_id}",
                    "\n".join(str(paragraph) for paragraph in article_text),
                )


def _open_text(path: Path) -> Iterable[str]:
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _jsonl_text_rows(path: Path, dataset: str) -> Iterator[tuple[str, str]]:
    with _open_text(path) as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank raw JSONL line: {path}:{line_number}")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid raw JSONL: {path}:{line_number}") from exc
            if dataset == "c4":
                yield _record(f"c4:{value.get('url', line_number)}", value.get("text"))
            elif dataset == "lambada":
                yield _record(f"lambada:{line_number:06d}", value.get("text"))
            elif dataset == "newsroom":
                yield _record(f"newsroom:{line_number:07d}", value.get("text"))
            else:
                raise ValueError(f"unsupported raw JSONL dataset: {dataset}")


def _gov_report_text(value: Any) -> str:
    parts: list[str] = []

    def visit(section: Any) -> None:
        if not isinstance(section, dict):
            return
        title = section.get("section_title")
        if isinstance(title, str) and title.strip():
            parts.append(title)
        paragraphs = section.get("paragraphs", [])
        if isinstance(paragraphs, list):
            parts.extend(str(item) for item in paragraphs if str(item).strip())
        subsections = section.get("subsections", [])
        if isinstance(subsections, list):
            for child in subsections:
                visit(child)

    visit(value)
    return "\n".join(parts)


def _gov_rows(paths: Iterable[Path]) -> Iterator[tuple[str, str]]:
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid GovReport JSONL: {path}:{line_number}") from exc
                identifier = value.get("id")
                text = _gov_report_text(value.get("reports"))
                yield _record(f"gov_report:{identifier}", text)


def _parquet_rows(path: Path, columns: list[str]) -> Iterator[dict[str, Any]]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError("pyarrow is required for parquet normalization") from exc
    parquet_file = parquet.ParquetFile(path)
    for batch in parquet_file.iter_batches(batch_size=128, columns=columns):
        yield from batch.to_pylist()


def _booksum_rows(path: Path) -> Iterator[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"book_id", "summary_id", "chapter"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"BookSum CSV is missing fields: {sorted(required)}")
        for index, value in enumerate(reader):
            text = value.get("chapter") or value.get("content") or ""
            yield _record(
                f"booksum/book:{value.get('book_id')}:{value.get('summary_id')}:{index}",
                text,
            )


def _write_source(
    source_root: Path,
    key: str,
    rows: Iterable[tuple[str, str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    relative = OUTPUT_PATHS[key]
    destination = source_root / relative
    count = _write_jsonl(destination, rows)
    metadata = {
        **metadata,
        "normalized_path": relative.as_posix(),
        "record_count": count,
        "normalized_sha256": sha256_file(destination),
    }
    return metadata


def _download_hf(raw_root: Path, repo: str, revision: str, filename: str) -> tuple[Path, dict[str, Any]]:
    destination = raw_root / "huggingface" / repo.replace("/", "--") / filename
    url = _hf_url(repo, revision, filename)
    path = _download(url, destination)
    return path, _raw_artifact(path, url, role="download")


def _require_manual_file(root: Path, names: tuple[str, ...], label: str) -> Path:
    if not root.is_dir() or root.is_symlink():
        raise FileNotFoundError(
            f"{label} manual root is required and must contain one of {names}: {root}"
        )
    for name in names:
        candidate = root / name
        if candidate.is_file() and not candidate.is_symlink():
            return candidate
    raise FileNotFoundError(f"{label} manual root is missing {names}: {root}")


def acquire(raw_root: Path, source_root: Path, c4_manual_root: Path | None, newsroom_manual_root: Path | None) -> dict[str, Any]:
    raw_root = _external_path(raw_root, "raw root")
    source_root = _external_path(source_root, "source root")
    if c4_manual_root is None or newsroom_manual_root is None:
        raise RuntimeError(
            "acquisition is blocked until both documented manual inputs are supplied: "
            "C4 webtextlike TFDS JSONL and NEWSROOM test JSONL"
        )
    c4_manual_root = _external_path(c4_manual_root, "C4 manual root")
    newsroom_manual_root = _external_path(newsroom_manual_root, "NEWSROOM manual root")
    c4_train = _require_manual_file(c4_manual_root, ("train.jsonl", "train.jsonl.gz"), "C4")
    c4_validation = _require_manual_file(c4_manual_root, ("validation.jsonl", "validation.jsonl.gz"), "C4")
    newsroom = _require_manual_file(newsroom_manual_root, ("test.jsonl", "test.jsonl.gz"), "NEWSROOM")
    _require_absent(raw_root, "raw root")
    _require_absent(source_root, "source root")
    raw_root.parent.mkdir(parents=True, exist_ok=True)
    source_root.parent.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir()
    temporary_source = Path(tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent))
    artifacts: list[dict[str, Any]] = []
    datasets: dict[str, dict[str, Any]] = {}
    archives: dict[str, Path] = {}

    def scientific(key: str, dataset: str, split: str, limit: int | None) -> None:
        archive = archives.get(dataset)
        if archive is None:
            archive = _download(
                SCIENTIFIC_PAPERS_URLS[dataset],
                raw_root / "scientific_papers" / f"{dataset}-dataset-{SCIENTIFIC_PAPERS_REVISION}.zip",
            )
            archives[dataset] = archive
            artifacts.append(_raw_artifact(archive, SCIENTIFIC_PAPERS_URLS[dataset], role="download"))
        datasets[key] = _write_source(
            temporary_source,
            key,
            _limit_rows(_scientific_rows(archive, split, dataset), limit),
            {
                "source": SCIENTIFIC_PAPERS_URLS[dataset],
                "revision": SCIENTIFIC_PAPERS_REVISION,
                "split": split,
                "config": dataset,
                "selection": "deterministic upstream prefix" if limit else "complete split",
                "raw_artifacts": [str(archive.resolve())],
            },
        )

    try:
        scientific("fit/arxiv", "arxiv", "train", FIT_RECORD_LIMITS["arxiv"])
        scientific("assessment/arxiv", "arxiv", "test", None)
        scientific("assessment/pubmed", "pubmed", "test", None)

        for key, path, split, limit in (
            ("fit/c4", c4_train, "train", FIT_RECORD_LIMITS["c4"]),
            ("assessment/c4/webtextlike", c4_validation, "validation", None),
        ):
            datasets[key] = _write_source(
                temporary_source,
                key,
                _limit_rows(_jsonl_text_rows(path, "c4"), limit),
                {
                    "source": "https://www.tensorflow.org/datasets/catalog/c4",
                    "revision": "3.1.0",
                    "split": split,
                    "config": "webtextlike",
                    "selection": "deterministic upstream prefix" if limit else "complete split",
                    "raw_artifacts": [str(path.resolve())],
                },
            )
        artifacts.extend(
            [
                _raw_artifact(c4_train, "https://www.tensorflow.org/datasets/catalog/c4", role="operator-supplied-manual-input"),
                _raw_artifact(c4_validation, "https://www.tensorflow.org/datasets/catalog/c4", role="operator-supplied-manual-input"),
            ]
        )

        pg19_train_list, pg19_train_artifact = _download_hf(
            raw_root, PG19_REPO, PG19_REVISION, "data/train_files.txt"
        )
        pg19_test_list, pg19_test_artifact = _download_hf(
            raw_root, PG19_REPO, PG19_REVISION, "data/test_files.txt"
        )
        artifacts.extend([pg19_train_artifact, pg19_test_artifact])

        def pg19_rows(list_path: Path, split: str, limit: int | None) -> Iterator[tuple[str, str]]:
            lines = sorted(line.strip() for line in list_path.read_text(encoding="utf-8").splitlines() if line.strip())
            selected = lines[:limit] if limit is not None else lines
            for relative in selected:
                identifier = Path(relative).stem
                url = urllib.parse.urljoin(PG19_GCS_ROOT, relative)
                raw_path = _download(url, raw_root / "pg19" / relative)
                artifacts.append(_raw_artifact(raw_path, url, role="download"))
                yield _record(f"pg19:{split}:{identifier}", raw_path.read_text(encoding="utf-8"))

        datasets["fit/pg19"] = _write_source(
            temporary_source,
            "fit/pg19",
            pg19_rows(pg19_train_list, "train", FIT_RECORD_LIMITS["pg19"]),
            {
                "source": f"https://huggingface.co/datasets/{PG19_REPO}",
                "revision": PG19_REVISION,
                "split": "train",
                "config": "default",
                "selection": "sorted upstream file-list prefix",
                "raw_artifacts": [str(pg19_train_list.resolve())],
            },
        )
        datasets["assessment/pg19"] = _write_source(
            temporary_source,
            "assessment/pg19",
            pg19_rows(pg19_test_list, "test", None),
            {
                "source": f"https://huggingface.co/datasets/{PG19_REPO}",
                "revision": PG19_REVISION,
                "split": "test",
                "config": "default",
                "selection": "complete pinned test file list",
                "raw_artifacts": [str(pg19_test_list.resolve())],
            },
        )

        big_patent, artifact = _download_hf(raw_root, "NortheasternUniversity/big_patent", HF_REVISIONS["big_patent"], "all/test-00000-of-00005.parquet")
        artifacts.append(artifact)
        datasets["assessment/big_patent"] = _write_source(
            temporary_source,
            "assessment/big_patent",
            _limit_rows(
                (
                    _record(f"big_patent:all:{index:05d}", row.get("description"))
                    for index, row in enumerate(_parquet_rows(big_patent, ["description"]))
                ),
                BIG_PATENT_RECORD_LIMIT,
            ),
            {
                "source": "https://huggingface.co/datasets/NortheasternUniversity/big_patent",
                "revision": HF_REVISIONS["big_patent"],
                "split": "test",
                "config": "all",
                "selection": "first 10,000 records in pinned shard order",
                "raw_artifacts": [str(big_patent.resolve())],
            },
        )

        billsum, artifact = _download_hf(raw_root, "FiscalNote/billsum", HF_REVISIONS["billsum"], "data/test-00000-of-00001.parquet")
        artifacts.append(artifact)
        datasets["assessment/billsum"] = _write_source(
            temporary_source,
            "assessment/billsum",
            (_record(f"billsum:test:{index:04d}", row.get("text")) for index, row in enumerate(_parquet_rows(billsum, ["text"]))),
            {
                "source": "https://huggingface.co/datasets/FiscalNote/billsum",
                "revision": HF_REVISIONS["billsum"],
                "split": "test",
                "config": "default",
                "selection": "complete pinned split",
                "raw_artifacts": [str(billsum.resolve())],
            },
        )

        booksum, artifact = _download_hf(raw_root, "kmfoda/booksum", HF_REVISIONS["booksum"], "test.csv")
        artifacts.append(artifact)
        datasets["assessment/booksum/book"] = _write_source(
            temporary_source,
            "assessment/booksum/book",
            _booksum_rows(booksum),
            {
                "source": "https://huggingface.co/datasets/kmfoda/booksum",
                "revision": HF_REVISIONS["booksum"],
                "split": "test",
                "config": "default",
                "upstream_homepage": "https://github.com/salesforce/booksum",
                "selection": "complete pinned split",
                "raw_artifacts": [str(booksum.resolve())],
            },
        )

        gov_paths = []
        for filename in ("data/crs_test.jsonl", "data/gao_test.jsonl"):
            path, artifact = _download_hf(raw_root, "launch/gov_report", HF_REVISIONS["gov_report"], filename)
            gov_paths.append(path)
            artifacts.append(artifact)
        datasets["assessment/gov_report"] = _write_source(
            temporary_source,
            "assessment/gov_report",
            _gov_rows(gov_paths),
            {
                "source": "https://huggingface.co/datasets/launch/gov_report",
                "revision": HF_REVISIONS["gov_report"],
                "split": "test",
                "config": "plain_text",
                "selection": "complete pinned CRS and GAO test files",
                "raw_artifacts": [str(path.resolve()) for path in gov_paths],
            },
        )

        lambada, artifact = _download_hf(raw_root, "EleutherAI/lambada_openai", HF_REVISIONS["lambada"], "data/lambada_test_en.jsonl")
        artifacts.append(artifact)
        datasets["assessment/lambada"] = _write_source(
            temporary_source,
            "assessment/lambada",
            _jsonl_text_rows(lambada, "lambada"),
            {
                "source": "https://huggingface.co/datasets/EleutherAI/lambada_openai",
                "revision": HF_REVISIONS["lambada"],
                "split": "test",
                "config": "en",
                "selection": "complete pinned English test file",
                "raw_artifacts": [str(lambada.resolve())],
            },
        )

        artifacts.append(_raw_artifact(newsroom, "https://lil.nlp.cornell.edu/newsroom/download/index.html", role="operator-supplied-manual-input"))
        datasets["assessment/newsroom"] = _write_source(
            temporary_source,
            "assessment/newsroom",
            _jsonl_text_rows(newsroom, "newsroom"),
            {
                "source": "https://lil.nlp.cornell.edu/newsroom/download/index.html",
                "revision": "1.0.0",
                "split": "test",
                "config": "default",
                "selection": "complete operator-supplied registered test file",
                "raw_artifacts": [str(newsroom.resolve())],
            },
        )

        expected = {f"fit/{name}" for name in FIT_DATASETS} | {
            f"assessment/{name}" for name in ASSESSMENT_DATASETS
        }
        if set(datasets) != expected:
            raise RuntimeError(f"acquisition did not produce the full dataset panel: {sorted(set(datasets) ^ expected)}")
        unique_artifacts: dict[str, dict[str, Any]] = {item["path"]: item for item in artifacts}
        body = {
            "schema": MANIFEST_SCHEMA,
            "state_slice": CONSUMER_STATE_SLICE,
            "acquisition_state_slice": ACQUISITION_STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "source_record_schema": SOURCE_RECORD_SCHEMA,
            "selection_policy": SELECTION_POLICY,
            "paper": "https://arxiv.org/html/2608.17981v1",
            "raw_root": str(raw_root),
            "source_root": str(source_root),
            "datasets": dict(sorted(datasets.items())),
            "raw_artifacts": [unique_artifacts[key] for key in sorted(unique_artifacts)],
            "network_access": True,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
            "created_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        manifest = {**body, "manifest_sha256": digest(body)}
        (temporary_source / "acquisition-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        validator = Path(__file__).with_name("validate_gemma3_paper_recirculation_acquisition_v1.py")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, "-B", str(validator), "--source-root", str(temporary_source)],
            cwd=REPO_ROOT,
            env=environment,
            check=True,
        )
        os.replace(temporary_source, source_root)
        return manifest
    except Exception:
        shutil.rmtree(temporary_source, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--c4-manual-root", type=Path)
    parser.add_argument("--newsroom-manual-root", type=Path)
    args = parser.parse_args()
    manifest = acquire(
        args.raw_root,
        args.source_root,
        args.c4_manual_root,
        args.newsroom_manual_root,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
