"""Pure-data Project Gutenberg custody contract for Astral V39.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The downloader and independent validator share only these pure-data helpers.
The module never selects books, creates scientific concepts, or executes a
model. Raw documents remain in a repository-external custody root.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import protocol_v39 as protocol


CORPUS_KIND = "project-gutenberg-plain-text-utf8"
CORPUS_CLAIM_CEILING = "LocalDevelopmentExternalCorpusCustodyOnly"
EXPECTED_DOCUMENT_COUNT = 12
EXPECTED_DOCUMENTS_PER_SPLIT = 4
SPLITS = ("fit", "tune", "assessment")
DEFAULT_LANGUAGE = "en"
GUTENBERG_HOSTS = frozenset({"gutenberg.org", "www.gutenberg.org"})
GUTENBERG_BASE = "https://www.gutenberg.org"
GUTENBERG_LICENSE_URL = "https://www.gutenberg.org/policy/license.html"
MAX_TEXT_BYTES = 50 * 1024 * 1024
MAX_METADATA_BYTES = 5 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_DELAY_SECONDS = 1.0
SELECTION_KEYS = {"protocol", "state_slice", "documents"}
SELECTION_DOCUMENT_KEYS = {"gutenberg_id", "split"}
CORPUS_KEYS = {
    "protocol",
    "state_slice",
    "corpus_kind",
    "claim_ceiling",
    "selection_manifest_sha256",
    "document_count",
    "documents_per_split",
    "split_counts",
    "documents",
    "concept_registry_sha256",
    "assessment_ready",
    "raw_documents_retained_externally",
    "retrieved_at_utc",
}
DOCUMENT_KEYS = {
    "gutenberg_id",
    "split",
    "title",
    "authors",
    "language",
    "rights",
    "license_url",
    "ebook_url",
    "text_url",
    "metadata_url",
    "text_path",
    "metadata_path",
    "text_byte_len",
    "text_sha256",
    "metadata_byte_len",
    "metadata_sha256",
}
NAMESPACES = {
    "pgterms": "http://www.gutenberg.org/2009/pgterms/",
    "dcterms": "http://purl.org/dc/terms/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}
RDF_RESOURCE = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"
RDF_VALUE = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value"


class CorpusError(ValueError):
    """Fail-closed corpus acquisition or validation error."""


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    descriptor = path.open("rb")
    try:
        before = path.stat()
        if not stat.S_ISREG(before.st_mode):
            raise CorpusError(f"not a regular file: {path}")
        digest = hashlib.sha256()
        while chunk := descriptor.read(1024 * 1024):
            digest.update(chunk)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise CorpusError(f"file changed during hashing: {path}")
        return digest.hexdigest()
    finally:
        descriptor.close()


def strict_json_bytes(payload: bytes) -> Any:
    def reject_constant(value: str) -> Any:
        raise CorpusError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise CorpusError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorpusError(f"invalid JSON: {exc}") from exc


def read_strict_json(path: Path) -> Any:
    return strict_json_bytes(path.read_bytes())


def _is_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_gutenberg_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 999999


def parse_selection(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        raise CorpusError("selection manifest must be an object")
    unknown = sorted(set(value) - SELECTION_KEYS)
    missing = sorted(SELECTION_KEYS - set(value))
    if unknown:
        raise CorpusError(f"selection manifest has unknown fields: {','.join(unknown)}")
    if missing:
        raise CorpusError(f"selection manifest is missing fields: {','.join(missing)}")
    if value["protocol"] != protocol.PROTOCOL_ID:
        raise CorpusError("selection protocol mismatch")
    if value["state_slice"] != protocol.STATE_SLICE:
        raise CorpusError("selection state slice mismatch")
    return parse_selection_documents(value["documents"])


def parse_selection_documents(documents: object) -> list[dict[str, Any]]:
    if not isinstance(documents, list) or len(documents) != EXPECTED_DOCUMENT_COUNT:
        raise CorpusError(f"selection must contain exactly {EXPECTED_DOCUMENT_COUNT} documents")
    seen: set[int] = set()
    counts = {split: 0 for split in SPLITS}
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(documents):
        if not isinstance(item, dict):
            raise CorpusError(f"selection document {index} is not an object")
        unknown = sorted(set(item) - SELECTION_DOCUMENT_KEYS)
        missing = sorted(SELECTION_DOCUMENT_KEYS - set(item))
        if unknown:
            raise CorpusError(f"selection document {index} has unknown fields")
        if missing:
            raise CorpusError(f"selection document {index} is missing fields")
        gutenberg_id = item["gutenberg_id"]
        split = item["split"]
        if not _is_gutenberg_id(gutenberg_id):
            raise CorpusError(f"selection document {index} has invalid gutenberg_id")
        if not isinstance(split, str):
            raise CorpusError(f"selection document {index} has invalid split")
        if gutenberg_id in seen:
            raise CorpusError(f"duplicate gutenberg_id: {gutenberg_id}")
        if split not in SPLITS:
            raise CorpusError(f"selection document {index} has invalid split")
        seen.add(gutenberg_id)
        counts[split] += 1
        normalized.append({"gutenberg_id": gutenberg_id, "split": split})
    if counts != {split: EXPECTED_DOCUMENTS_PER_SPLIT for split in SPLITS}:
        raise CorpusError(f"selection split counts must be {EXPECTED_DOCUMENTS_PER_SPLIT} each")
    return normalized


def _text(node: ET.Element | None) -> str | None:
    if node is None or node.text is None:
        return None
    value = " ".join(node.text.split())
    return value or None


def parse_metadata(payload: bytes, gutenberg_id: int) -> dict[str, Any]:
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise CorpusError(f"metadata {gutenberg_id} contains a forbidden XML declaration")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise CorpusError(f"metadata {gutenberg_id} is not valid RDF/XML") from exc
    ebook = root.find("pgterms:ebook", NAMESPACES)
    if ebook is None:
        raise CorpusError(f"metadata {gutenberg_id} has no pgterms:ebook")
    expected_about = f"ebooks/{gutenberg_id}"
    if ebook.attrib.get(f"{{{NAMESPACES['rdf']}}}about") != expected_about:
        raise CorpusError(f"metadata {gutenberg_id} ebook identity mismatch")
    title = _text(ebook.find("dcterms:title", NAMESPACES))
    rights = _text(ebook.find("dcterms:rights", NAMESPACES))
    issued = _text(ebook.find("dcterms:issued", NAMESPACES))
    license_node = ebook.find("dcterms:license", NAMESPACES)
    license_resource = license_node.attrib.get(RDF_RESOURCE) if license_node is not None else None
    authors = [
        author
        for author in (
            _text(agent.find("pgterms:name", NAMESPACES))
            for creator in ebook.findall("dcterms:creator", NAMESPACES)
            for agent in creator.findall("pgterms:agent", NAMESPACES)
        )
        if author is not None
    ]
    languages = []
    for language in ebook.findall("dcterms:language", NAMESPACES):
        value = language.find("rdf:Description/rdf:value", NAMESPACES)
        if value is not None and value.text:
            languages.append(value.text.strip())
    if not title or not rights or not languages:
        raise CorpusError(f"metadata {gutenberg_id} lacks title, rights, or language")
    if "public domain" not in rights.lower():
        raise CorpusError(f"metadata {gutenberg_id} is not marked public domain")
    if len(set(languages)) != 1:
        raise CorpusError(f"metadata {gutenberg_id} has ambiguous languages")
    return {
        "title": title,
        "authors": authors,
        "language": languages[0],
        "rights": rights,
        "license_resource": license_resource,
        "issued": issued,
    }


def validate_text(payload: bytes, gutenberg_id: int) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CorpusError(f"text {gutenberg_id} is not UTF-8") from exc
    if not text.strip() or "\x00" in text:
        raise CorpusError(f"text {gutenberg_id} is empty or contains NUL")
    if "project gutenberg" not in text.lower():
        raise CorpusError(f"text {gutenberg_id} lacks Project Gutenberg header")
    ebook_pattern = re.compile(rf"\bebook\s*#?\s*{gutenberg_id}\b", re.IGNORECASE)
    if not ebook_pattern.search(text):
        raise CorpusError(f"text {gutenberg_id} lacks its ebook identifier")
    if "*** START OF" not in text.upper() or "*** END OF" not in text.upper():
        raise CorpusError(f"text {gutenberg_id} lacks Project Gutenberg boundaries")
    return text


def assert_external(path: Path, repository_root: Path) -> None:
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return
    raise CorpusError("corpus root must be outside the repository")


def document_urls(gutenberg_id: int) -> dict[str, str]:
    return {
        "ebook_url": f"{GUTENBERG_BASE}/ebooks/{gutenberg_id}",
        "text_url": f"{GUTENBERG_BASE}/ebooks/{gutenberg_id}.txt.utf-8",
        "metadata_url": f"{GUTENBERG_BASE}/cache/epub/{gutenberg_id}/pg{gutenberg_id}.rdf",
    }


def fetch_url(
    url: str,
    *,
    max_bytes: int,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    user_agent: str,
    opener: Callable[..., Any] = urlopen,
) -> tuple[bytes, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in GUTENBERG_HOSTS:
        raise CorpusError(f"refusing non-Project-Gutenberg URL: {url}")
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
    try:
        response = opener(request, timeout=timeout_seconds)
        try:
            final_url = response.geturl()
            final = urlparse(final_url)
            if final.scheme != "https" or final.hostname not in GUTENBERG_HOSTS:
                raise CorpusError(f"redirect escaped Project Gutenberg: {final_url}")
            status = getattr(response, "status", getattr(response, "code", 200))
            if status != 200:
                raise CorpusError(f"Project Gutenberg returned HTTP {status} for {url}")
            chunks: list[bytes] = []
            total = 0
            while chunk := response.read(min(1024 * 1024, max_bytes - total + 1)):
                total += len(chunk)
                if total > max_bytes:
                    raise CorpusError(f"download exceeds {max_bytes} bytes: {url}")
                chunks.append(chunk)
            return b"".join(chunks), final_url
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
    except CorpusError:
        raise
    except Exception as exc:
        raise CorpusError(f"download failed for {url}: {type(exc).__name__}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def manifest_errors(root: Path, repository_root: Path) -> list[str]:
    """Recompute the complete external corpus custody contract."""

    errors: list[str] = []
    try:
        assert_external(root, repository_root)
    except CorpusError as exc:
        errors.append(str(exc))
    if not root.is_dir() or root.is_symlink():
        return errors + ["corpus root is not a regular directory"]
    expected_root_files = {
        "corpus-manifest.json",
        "corpus-manifest.sha256",
        "selection-manifest.json",
    }
    root_entries = list(root.iterdir())
    symlinks = sorted(path.name for path in root_entries if path.is_symlink())
    if symlinks:
        errors.append(f"symlinks in corpus root:{','.join(symlinks)}")
    actual_root_files = {path.name for path in root_entries if path.is_file()}
    actual_root_dirs = {path.name for path in root_entries if path.is_dir()}
    if actual_root_dirs != {"documents"}:
        errors.append("corpus root directory census mismatch")
    missing = sorted(expected_root_files - actual_root_files)
    unexpected = sorted(actual_root_files - expected_root_files - {"validator-receipt.json"})
    if missing:
        errors.append(f"missing corpus files:{','.join(missing)}")
    if unexpected:
        errors.append(f"unexpected corpus files:{','.join(unexpected)}")
    documents_root = root / "documents"
    if not documents_root.is_dir() or documents_root.is_symlink():
        return errors + ["documents root is not a regular directory"]
    try:
        manifest = read_strict_json(root / "corpus-manifest.json")
        selection_payload = (root / "selection-manifest.json").read_bytes()
        selection = parse_selection(strict_json_bytes(selection_payload))
        sidecar = (root / "corpus-manifest.sha256").read_text(encoding="utf-8")
    except (OSError, CorpusError) as exc:
        return errors + [f"manifest read failed:{type(exc).__name__}:{exc}"]
    expected_sidecar = f"{sha256_file(root / 'corpus-manifest.json')}  corpus-manifest.json\n"
    if sidecar != expected_sidecar:
        errors.append("corpus manifest sidecar digest mismatch")
    if not isinstance(manifest, dict):
        return errors + ["corpus manifest is not an object"]
    unknown = sorted(set(manifest) - CORPUS_KEYS)
    missing = sorted(CORPUS_KEYS - set(manifest))
    if unknown:
        errors.append(f"unknown corpus manifest fields:{','.join(unknown)}")
    if missing:
        errors.append(f"missing corpus manifest fields:{','.join(missing)}")
    if manifest.get("protocol") != protocol.PROTOCOL_ID:
        errors.append("corpus protocol mismatch")
    if manifest.get("state_slice") != protocol.STATE_SLICE:
        errors.append("corpus state slice mismatch")
    if manifest.get("corpus_kind") != CORPUS_KIND:
        errors.append("corpus kind mismatch")
    if manifest.get("claim_ceiling") != CORPUS_CLAIM_CEILING:
        errors.append("corpus claim ceiling mismatch")
    if manifest.get("selection_manifest_sha256") != sha256_bytes(selection_payload):
        errors.append("selection manifest digest mismatch")
    try:
        expected_selection = parse_selection_documents(
            [
                {
                    "gutenberg_id": item.get("gutenberg_id"),
                    "split": item.get("split"),
                }
                for item in manifest.get("documents", [])
                if isinstance(item, dict)
            ]
        )
    except CorpusError as exc:
        errors.append(f"manifest document selection invalid:{exc}")
        expected_selection = []
    if expected_selection != selection:
        errors.append("manifest selection differs from selection manifest")
    if manifest.get("document_count") != EXPECTED_DOCUMENT_COUNT:
        errors.append("document count mismatch")
    expected_counts = {split: EXPECTED_DOCUMENTS_PER_SPLIT for split in SPLITS}
    if manifest.get("documents_per_split") != EXPECTED_DOCUMENTS_PER_SPLIT:
        errors.append("documents per split mismatch")
    if manifest.get("split_counts") != expected_counts:
        errors.append("split counts mismatch")
    if manifest.get("concept_registry_sha256") is not None:
        errors.append("concept registry must not be sealed by downloader")
    if manifest.get("assessment_ready") is not False:
        errors.append("assessment must remain closed")
    if manifest.get("raw_documents_retained_externally") is not True:
        errors.append("raw external-retention flag mismatch")
    if not isinstance(manifest.get("retrieved_at_utc"), str) or not manifest["retrieved_at_utc"].endswith("Z"):
        errors.append("retrieval timestamp invalid")

    expected_dirs = {str(item["gutenberg_id"]) for item in selection}
    actual_dirs = {
        path.name
        for path in documents_root.iterdir()
        if path.is_dir() and not path.is_symlink()
    }
    if actual_dirs != expected_dirs:
        errors.append("document directory census mismatch")
    manifest_documents = manifest.get("documents") if isinstance(manifest.get("documents"), list) else []
    if len(manifest_documents) != len(selection):
        return errors + ["manifest document list length mismatch"]
    manifest_by_id = {
        item.get("gutenberg_id"): item
        for item in manifest_documents
        if isinstance(item, dict)
    }
    text_digests: set[str] = set()
    for selected in selection:
        gutenberg_id = selected["gutenberg_id"]
        entry = manifest_by_id.get(gutenberg_id)
        if not isinstance(entry, dict):
            errors.append(f"missing manifest document:{gutenberg_id}")
            continue
        unknown_doc = sorted(set(entry) - DOCUMENT_KEYS)
        missing_doc = sorted(DOCUMENT_KEYS - set(entry))
        if unknown_doc:
            errors.append(f"unknown document fields:{gutenberg_id}")
        if missing_doc:
            errors.append(f"missing document fields:{gutenberg_id}")
            continue
        if entry.get("split") != selected["split"]:
            errors.append(f"document split mismatch:{gutenberg_id}")
        document_root = documents_root / str(gutenberg_id)
        if not document_root.is_dir() or document_root.is_symlink():
            errors.append(f"document root invalid:{gutenberg_id}")
            continue
        document_entries = list(document_root.iterdir())
        if any(path.is_symlink() for path in document_entries):
            errors.append(f"document symlink present:{gutenberg_id}")
        actual_files = {path.name for path in document_entries if path.is_file()}
        if actual_files != {"text.txt", "metadata.rdf"}:
            errors.append(f"document file census mismatch:{gutenberg_id}")
            continue
        text_path = document_root / "text.txt"
        metadata_path = document_root / "metadata.rdf"
        try:
            text_bytes = text_path.read_bytes()
            metadata_bytes = metadata_path.read_bytes()
            metadata = parse_metadata(metadata_bytes, gutenberg_id)
            validate_text(text_bytes, gutenberg_id)
        except (OSError, CorpusError) as exc:
            errors.append(f"document content invalid:{gutenberg_id}:{exc}")
            continue
        if metadata["language"] != DEFAULT_LANGUAGE:
            errors.append(f"document language mismatch:{gutenberg_id}")
        text_digest = sha256_bytes(text_bytes)
        metadata_digest = sha256_bytes(metadata_bytes)
        if text_digest in text_digests:
            errors.append(f"duplicate document text digest:{gutenberg_id}")
        text_digests.add(text_digest)
        expected_entry = {
            "gutenberg_id": gutenberg_id,
            "split": selected["split"],
            "title": metadata["title"],
            "authors": metadata["authors"],
            "language": metadata["language"],
            "rights": metadata["rights"],
            "license_url": GUTENBERG_LICENSE_URL,
            **document_urls(gutenberg_id),
            "text_path": f"documents/{gutenberg_id}/text.txt",
            "metadata_path": f"documents/{gutenberg_id}/metadata.rdf",
            "text_byte_len": len(text_bytes),
            "text_sha256": text_digest,
            "metadata_byte_len": len(metadata_bytes),
            "metadata_sha256": metadata_digest,
        }
        if entry != expected_entry:
            errors.append(f"document manifest binding mismatch:{gutenberg_id}")
    return errors
