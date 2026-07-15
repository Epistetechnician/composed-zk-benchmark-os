#!/usr/bin/python3
"""Hermetic Phase 796-A1 P01B archive-ledger candidate generator.

State slice: phase-796a1-hsai-p01b-archive-ledger-helper.

This helper directly parses one RFC 1952 member and its strict ustar stream.
It never extracts archive members and never performs network or subprocess I/O.
"""

import hashlib
import json
import os
import resource
import stat
import struct
import sys
import zlib
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Type


# Pinned input authority.
ASSET_ID = "aeneas-main-nightly-2026-07-10-c2015b8"
ASSET_URL = (
    "https://github.com/AeneasVerif/aeneas/releases/download/"
    "nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz"
)
RELEASE_ID = 351909376
GITHUB_ASSET_ID = 472143319
ARCHIVE_FILENAME = "aeneas-macos-aarch64.tar.gz"
TAG_COMMIT = "c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d"
EXPECTED_COMPRESSED_BYTES = 123234656
EXPECTED_ARCHIVE_SHA256 = "fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45"
RELEASE_IMMUTABLE = False

EMBEDDED_LEAN_PATH = "backends/lean/.lake/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz"
EXPECTED_EMBEDDED_LEAN_BYTES = 50447755
EXPECTED_EMBEDDED_LEAN_SHA256 = "f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59"

EXPECTED_LOGICAL_MEMBERS = 2471
EXPECTED_ROOT_COUNT = 0
EXPECTED_REGULAR_MEMBERS = 2305
EXPECTED_DIRECTORY_MEMBERS = 166
EXPECTED_TOP_LEVEL = ["aeneas", "backends", "charon", "charon-driver", "libs", "rust-toolchain"]
EXPECTED_LEGACY_INVENTORY_SHA256 = "26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e"

# Fixed resource limits. These names and values are contract-digest inputs.
READ_CHUNK_BYTES = 65536
GZIP_MEMBERS = 1
MAX_GZIP_FILENAME_BYTES = 4096
MAX_GZIP_COMMENT_BYTES = 4096
MAX_GZIP_EXTRA_BYTES = 65535
MAX_GZIP_OPTIONAL_BYTES_TOTAL = 73727
MAX_COMPRESSION_RATIO = 72
MAX_UNCOMPRESSED_TAR_BYTES = 8589934592
MAX_PHYSICAL_TAR_HEADERS = 8192
MAX_LOGICAL_MEMBERS = 4096
MAX_EXTENSION_HEADERS = 512
MAX_EXTENSION_PAYLOAD_BYTES = 65536
MAX_EXTENSION_PAYLOAD_BYTES_TOTAL = 4194304
MAX_MEMBER_BYTES = 1073741824
MAX_AGGREGATE_REGULAR_BYTES = 6442450944
MAX_TOTAL_EXTRACTION_OUTPUT_BYTES = 6442450944
MAX_EFFECTIVE_PATH_BYTES = 1024
MAX_PATH_COMPONENT_BYTES = 255
MAX_PATH_COMPONENTS = 128
MAX_TRAILING_ZERO_BYTES = 1048576
MAX_HEADER_LEDGER_BYTES = 67108864
MAX_INVENTORY_LEDGER_BYTES = 16777216
MAX_MANIFEST_BYTES = 1048576
MAX_STATUS_BYTES = 65536
MAX_TOTAL_CANDIDATE_BYTES = 85000192

CPU_SECONDS = 900
MAX_OPEN_FILE_DESCRIPTORS = 32
BLOCK_BYTES = 512
U64_MAX = (1 << 64) - 1
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
ZERO_BLOCK_SHA256 = hashlib.sha256(b"\0" * BLOCK_BYTES).hexdigest()

BOUNDARY_DOCUMENT_SHA256 = "2b52a3b24d94b565434dc341d808fe7ee3ad44757ea5ff8365f8dc88aefe1ba0"
FAILURE_SCHEMA = "hsai-p01b-archive-ledger-failure-v1"
GRAMMAR_PROFILE = "hsai-p01b-single-gzip-strict-ustar-v1"
CONTRACT_SCHEMA = "hsai-p01b-archive-ledger-contract-v1"
CONTRACT_DOMAIN = b"hsai:p01b-archive-ledger-contract:v1\0"

MANIFEST_FILENAME = "archive-source-manifest-v1.json"
HEADER_LEDGER_FILENAME = "gzip-tar-header-ledger-v1.jsonl"
INVENTORY_LEDGER_FILENAME = "ordered-logical-member-inventory-v1.jsonl"
STATUS_FILENAME = "archive-ledger-capture-status-v1.json"
PENDING_STATUS_FILENAME = ".archive-ledger-capture-status-v1.pending"
CANDIDATE_DIRECTORY = "archive-ledger-candidate"
DECLARED_FILES = sorted(
    [MANIFEST_FILENAME, HEADER_LEDGER_FILENAME, INVENTORY_LEDGER_FILENAME, STATUS_FILENAME]
)

# Hermetic tests replace this callback to inject deterministic failures. It is
# not configurable through argv, environment, or the production entrypoint.
_TEST_CHECKPOINT_HOOK = None

LIMITS = {
    "READ_CHUNK_BYTES": READ_CHUNK_BYTES,
    "GZIP_MEMBERS": GZIP_MEMBERS,
    "MAX_GZIP_FILENAME_BYTES": MAX_GZIP_FILENAME_BYTES,
    "MAX_GZIP_COMMENT_BYTES": MAX_GZIP_COMMENT_BYTES,
    "MAX_GZIP_EXTRA_BYTES": MAX_GZIP_EXTRA_BYTES,
    "MAX_GZIP_OPTIONAL_BYTES_TOTAL": MAX_GZIP_OPTIONAL_BYTES_TOTAL,
    "MAX_COMPRESSION_RATIO": MAX_COMPRESSION_RATIO,
    "MAX_UNCOMPRESSED_TAR_BYTES": MAX_UNCOMPRESSED_TAR_BYTES,
    "MAX_PHYSICAL_TAR_HEADERS": MAX_PHYSICAL_TAR_HEADERS,
    "MAX_LOGICAL_MEMBERS": MAX_LOGICAL_MEMBERS,
    "MAX_EXTENSION_HEADERS": MAX_EXTENSION_HEADERS,
    "MAX_EXTENSION_PAYLOAD_BYTES": MAX_EXTENSION_PAYLOAD_BYTES,
    "MAX_EXTENSION_PAYLOAD_BYTES_TOTAL": MAX_EXTENSION_PAYLOAD_BYTES_TOTAL,
    "MAX_MEMBER_BYTES": MAX_MEMBER_BYTES,
    "MAX_AGGREGATE_REGULAR_BYTES": MAX_AGGREGATE_REGULAR_BYTES,
    "MAX_TOTAL_EXTRACTION_OUTPUT_BYTES": MAX_TOTAL_EXTRACTION_OUTPUT_BYTES,
    "MAX_EFFECTIVE_PATH_BYTES": MAX_EFFECTIVE_PATH_BYTES,
    "MAX_PATH_COMPONENT_BYTES": MAX_PATH_COMPONENT_BYTES,
    "MAX_PATH_COMPONENTS": MAX_PATH_COMPONENTS,
    "MAX_TRAILING_ZERO_BYTES": MAX_TRAILING_ZERO_BYTES,
    "MAX_HEADER_LEDGER_BYTES": MAX_HEADER_LEDGER_BYTES,
    "MAX_INVENTORY_LEDGER_BYTES": MAX_INVENTORY_LEDGER_BYTES,
    "MAX_MANIFEST_BYTES": MAX_MANIFEST_BYTES,
    "MAX_STATUS_BYTES": MAX_STATUS_BYTES,
    "MAX_TOTAL_CANDIDATE_BYTES": MAX_TOTAL_CANDIDATE_BYTES,
}

CANDIDATE_ARTIFACT_SCHEMAS = sorted(
    [
        "hsai-p01b-archive-ledger-capture-status-v1",
        "hsai-p01b-archive-source-manifest-v1",
        "hsai-p01b-gzip-tar-header-ledger-v1",
        "hsai-p01b-ordered-logical-member-inventory-v1",
    ]
)
CONTRACT_OBJECT = {
    "boundary_document_sha256": BOUNDARY_DOCUMENT_SHA256,
    "candidate_artifact_schemas": CANDIDATE_ARTIFACT_SCHEMAS,
    "failure_taxonomy_schema": FAILURE_SCHEMA,
    "grammar_profile": GRAMMAR_PROFILE,
    "limits": LIMITS,
    "schema": CONTRACT_SCHEMA,
}


class ArchiveLedgerError(Exception):
    """Base class for one closed, stable failure category."""

    failure_class = "ArchiveLedgerError"

    def __init__(self, diagnostic: str = "rejected") -> None:
        super().__init__(diagnostic)
        self.diagnostic = diagnostic


class InvalidCli(ArchiveLedgerError):
    failure_class = "InvalidCli"


class InvalidInputPath(ArchiveLedgerError):
    failure_class = "InvalidInputPath"


class InvalidOutputPath(ArchiveLedgerError):
    failure_class = "InvalidOutputPath"


class InputOverlap(ArchiveLedgerError):
    failure_class = "InputOverlap"


class InputOpen(ArchiveLedgerError):
    failure_class = "InputOpen"


class InputNotRegular(ArchiveLedgerError):
    failure_class = "InputNotRegular"


class InputIdentityDrift(ArchiveLedgerError):
    failure_class = "InputIdentityDrift"


class InputLengthMismatch(ArchiveLedgerError):
    failure_class = "InputLengthMismatch"


class InputDigestMismatch(ArchiveLedgerError):
    failure_class = "InputDigestMismatch"


class ResourceLimitUnavailable(ArchiveLedgerError):
    failure_class = "ResourceLimitUnavailable"


class GzipMagic(ArchiveLedgerError):
    failure_class = "GzipMagic"


class GzipMethod(ArchiveLedgerError):
    failure_class = "GzipMethod"


class GzipReservedFlags(ArchiveLedgerError):
    failure_class = "GzipReservedFlags"


class GzipOptionalFieldLimit(ArchiveLedgerError):
    failure_class = "GzipOptionalFieldLimit"


class GzipExtraField(ArchiveLedgerError):
    failure_class = "GzipExtraField"


class GzipHeaderCrc(ArchiveLedgerError):
    failure_class = "GzipHeaderCrc"


class GzipDeflate(ArchiveLedgerError):
    failure_class = "GzipDeflate"


class GzipTrailerCrc(ArchiveLedgerError):
    failure_class = "GzipTrailerCrc"


class GzipTrailerSize(ArchiveLedgerError):
    failure_class = "GzipTrailerSize"


class GzipMemberCount(ArchiveLedgerError):
    failure_class = "GzipMemberCount"


class GzipTrailingData(ArchiveLedgerError):
    failure_class = "GzipTrailingData"


class CompressionRatioLimit(ArchiveLedgerError):
    failure_class = "CompressionRatioLimit"


class UncompressedTarLimit(ArchiveLedgerError):
    failure_class = "UncompressedTarLimit"


class TarPartialBlock(ArchiveLedgerError):
    failure_class = "TarPartialBlock"


class TarMagic(ArchiveLedgerError):
    failure_class = "TarMagic"


class TarVersion(ArchiveLedgerError):
    failure_class = "TarVersion"


class TarChecksum(ArchiveLedgerError):
    failure_class = "TarChecksum"


class TarNumericEncoding(ArchiveLedgerError):
    failure_class = "TarNumericEncoding"


class TarHeaderLimit(ArchiveLedgerError):
    failure_class = "TarHeaderLimit"


class TarUnsupportedType(ArchiveLedgerError):
    failure_class = "TarUnsupportedType"


class TarExtensionLimit(ArchiveLedgerError):
    failure_class = "TarExtensionLimit"


class TarExtensionPayloadLimit(ArchiveLedgerError):
    failure_class = "TarExtensionPayloadLimit"


class TarPaxGrammar(ArchiveLedgerError):
    failure_class = "TarPaxGrammar"


class TarPaxKeyword(ArchiveLedgerError):
    failure_class = "TarPaxKeyword"


class TarExtensionConflict(ArchiveLedgerError):
    failure_class = "TarExtensionConflict"


class TarExtensionOrphan(ArchiveLedgerError):
    failure_class = "TarExtensionOrphan"


class TarPathEncoding(ArchiveLedgerError):
    failure_class = "TarPathEncoding"


class TarPathInvalid(ArchiveLedgerError):
    failure_class = "TarPathInvalid"


class TarDuplicateRawName(ArchiveLedgerError):
    failure_class = "TarDuplicateRawName"


class TarDuplicateEffectiveName(ArchiveLedgerError):
    failure_class = "TarDuplicateEffectiveName"


class TarDuplicateCollisionKey(ArchiveLedgerError):
    failure_class = "TarDuplicateCollisionKey"


class TarFileDirectoryCollision(ArchiveLedgerError):
    failure_class = "TarFileDirectoryCollision"


class TarRegularAncestor(ArchiveLedgerError):
    failure_class = "TarRegularAncestor"


class TarMemberLimit(ArchiveLedgerError):
    failure_class = "TarMemberLimit"


class TarMemberSizeLimit(ArchiveLedgerError):
    failure_class = "TarMemberSizeLimit"


class TarAggregateLimit(ArchiveLedgerError):
    failure_class = "TarAggregateLimit"


class TarPaddingNonzero(ArchiveLedgerError):
    failure_class = "TarPaddingNonzero"


class TarTerminator(ArchiveLedgerError):
    failure_class = "TarTerminator"


class TarTrailingLimit(ArchiveLedgerError):
    failure_class = "TarTrailingLimit"


class CandidateByteLimit(ArchiveLedgerError):
    failure_class = "CandidateByteLimit"


class ProfileMismatch(ArchiveLedgerError):
    failure_class = "ProfileMismatch"


class EmbeddedLeanMismatch(ArchiveLedgerError):
    failure_class = "EmbeddedLeanMismatch"


class OutputCollision(ArchiveLedgerError):
    failure_class = "OutputCollision"


class OutputWrite(ArchiveLedgerError):
    failure_class = "OutputWrite"


class OutputDurability(ArchiveLedgerError):
    failure_class = "OutputDurability"


class OutputPublication(ArchiveLedgerError):
    failure_class = "OutputPublication"


def _raise(error_type: Type[ArchiveLedgerError], diagnostic: str) -> None:
    raise error_type(diagnostic)


def _checkpoint(name: str) -> None:
    hook = _TEST_CHECKPOINT_HOOK
    if hook is not None:
        hook(name)


def canonical_json(value: Any) -> bytes:
    """Return the contract's canonical one-line JSON bytes without LF."""
    _validate_json_value(value, allow_signed=False)
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _raise(OutputWrite, "canonical-json")
    raise AssertionError("unreachable")


def canonical_json_line(value: Any) -> bytes:
    return canonical_json(value) + b"\n"


def _validate_json_value(value: Any, allow_signed: bool) -> None:
    if value is None or isinstance(value, float):
        _raise(OutputWrite, "invalid-json-value")
    if isinstance(value, bool) or isinstance(value, str):
        return
    if isinstance(value, int):
        if value < 0 and not allow_signed:
            _raise(OutputWrite, "negative-json-integer")
        if value > U64_MAX:
            _raise(OutputWrite, "json-integer-overflow")
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item, allow_signed)
        return
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            _raise(OutputWrite, "non-string-json-key")
        for item in value.values():
            _validate_json_value(item, allow_signed)
        return
    _raise(OutputWrite, "unsupported-json-value")


CONTRACT_OBJECT_BYTES = canonical_json(CONTRACT_OBJECT)
CONTRACT_DIGEST = hashlib.sha256(CONTRACT_DOMAIN + CONTRACT_OBJECT_BYTES).hexdigest()
EXPECTED_CONTRACT_DIGEST = "9a85d6b33f31ee3e78d6176da9208753bc5c244c4fecc44ab29efc265b4f7bd1"
if CONTRACT_DIGEST != EXPECTED_CONTRACT_DIGEST:
    raise RuntimeError("contract digest constant mismatch")


def checked_add(value: int, increment: int, limit: int, error_type: Type[ArchiveLedgerError]) -> int:
    """Add nonnegative counters and reject N+1 before use."""
    if value < 0 or increment < 0 or value > U64_MAX - increment:
        _raise(error_type, "counter-overflow")
    result = value + increment
    if result > limit:
        _raise(error_type, "limit")
    return result


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode_ascii_field(raw: bytes, allow_empty: bool, error_type: Type[ArchiveLedgerError]) -> str:
    nul = raw.find(b"\0")
    content = raw if nul < 0 else raw[:nul]
    if nul >= 0 and any(raw[nul:]):
        _raise(error_type, "nonzero-after-nul")
    if not allow_empty and not content:
        _raise(error_type, "empty-field")
    if any(byte < 0x20 or byte > 0x7E for byte in content):
        _raise(error_type, "non-printable-ascii")
    try:
        return content.decode("ascii")
    except UnicodeDecodeError:
        _raise(error_type, "non-ascii")
    raise AssertionError("unreachable")


def parse_octal_field(raw: bytes, digits: int) -> int:
    """Parse an exact canonical ustar octal field."""
    if len(raw) != digits + 1 or raw[-1:] != b"\0":
        _raise(TarNumericEncoding, "octal-shape")
    body = raw[:-1]
    if len(body) != digits or any(byte < 0x30 or byte > 0x37 for byte in body):
        _raise(TarNumericEncoding, "octal-digit")
    value = 0
    for byte in body:
        digit = byte - 0x30
        if value > (U64_MAX - digit) // 8:
            _raise(TarNumericEncoding, "octal-overflow")
        value = value * 8 + digit
    return value


def parse_checksum_field(raw: bytes) -> int:
    if len(raw) != 8 or raw[6:] != b"\0 " or any(byte < 0x30 or byte > 0x37 for byte in raw[:6]):
        _raise(TarNumericEncoding, "checksum-shape")
    return int(raw[:6], 8)


def parse_pax_path(payload: bytes) -> bytes:
    """Parse the sole admitted local PAX record."""
    if not payload or payload[-1:] != b"\n" or b"\0" in payload:
        _raise(TarPaxGrammar, "pax-framing")
    space = payload.find(b" ")
    if space <= 0:
        _raise(TarPaxGrammar, "pax-length")
    length_raw = payload[:space]
    if len(length_raw) > 1 and length_raw[:1] == b"0":
        _raise(TarPaxGrammar, "pax-leading-zero")
    if any(byte < 0x30 or byte > 0x39 for byte in length_raw):
        _raise(TarPaxGrammar, "pax-length-digit")
    declared = int(length_raw, 10)
    if declared != len(payload):
        _raise(TarPaxGrammar, "pax-length-mismatch")
    body = payload[space + 1 : -1]
    if b"=" not in body:
        _raise(TarPaxGrammar, "pax-record")
    key, value = body.split(b"=", 1)
    if key != b"path":
        _raise(TarPaxKeyword, "pax-keyword")
    if not value:
        _raise(TarPaxGrammar, "pax-empty-value")
    if any(byte < 0x20 or byte > 0x7E for byte in value):
        _raise(TarPathEncoding, "pax-path-encoding")
    return value


def parse_gnu_long_name(payload: bytes) -> bytes:
    if not payload or payload[-1:] != b"\0" or b"\0" in payload[:-1]:
        _raise(TarPaxGrammar, "gnu-long-name-framing")
    value = payload[:-1]
    if not value or any(byte < 0x20 or byte > 0x7E for byte in value):
        _raise(TarPathEncoding, "gnu-long-name-encoding")
    return value


def validate_effective_path(raw: bytes, kind: str) -> Tuple[str, str]:
    """Return the exact effective name and its collision key."""
    if not raw or len(raw) > MAX_EFFECTIVE_PATH_BYTES:
        _raise(TarPathInvalid, "path-length")
    if any(byte < 0x20 or byte > 0x7E for byte in raw) or b"\\" in raw:
        _raise(TarPathEncoding, "path-encoding")
    try:
        name = raw.decode("ascii")
    except UnicodeDecodeError:
        _raise(TarPathEncoding, "path-ascii")
    if name.startswith("/") or name.startswith("./") or "//" in name:
        _raise(TarPathInvalid, "path-form")
    if kind == "regular" and name.endswith("/"):
        _raise(TarPathInvalid, "regular-trailing-separator")
    if kind == "directory":
        if name.endswith("//"):
            _raise(TarPathInvalid, "directory-trailing-separator")
        collision_key = name[:-1] if name.endswith("/") else name
    else:
        collision_key = name
    if not collision_key:
        _raise(TarPathInvalid, "root-marker")
    parts = collision_key.split("/")
    if len(parts) > MAX_PATH_COMPONENTS:
        _raise(TarPathInvalid, "component-count")
    for part in parts:
        if not part or part in (".", "..") or len(part.encode("ascii")) > MAX_PATH_COMPONENT_BYTES:
            _raise(TarPathInvalid, "component")
    return name, collision_key


def _canonical_legacy_row(row: Sequence[Any]) -> bytes:
    return json.dumps(list(row), ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def strict_json_object(
    data: bytes,
    expected_keys: Set[str],
    allow_signed: bool = False,
) -> Dict[str, Any]:
    """Parse one canonical JSON object with duplicate and unknown-key rejection."""
    def pairs_hook(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _raise(OutputWrite, "duplicate-json-key")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("ascii"), object_pairs_hook=pairs_hook)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _raise(OutputWrite, "invalid-json")
    if not isinstance(value, dict) or set(value) != expected_keys:
        _raise(OutputWrite, "json-field-set")
    _validate_json_value(value, allow_signed=allow_signed)
    try:
        canonical = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _raise(OutputWrite, "canonical-json")
    if canonical != data:
        _raise(OutputWrite, "noncanonical-json")
    return value


def _failure_line(error: ArchiveLedgerError) -> bytes:
    value = {
        "failure_class": error.failure_class,
        "schema": FAILURE_SCHEMA,
    }
    data = canonical_json_line(value)
    if len(data) > MAX_STATUS_BYTES:
        return b'{"failure_class":"OutputWrite","schema":"hsai-p01b-archive-ledger-failure-v1"}\n'
    return data


class CandidateBudget:
    def __init__(self) -> None:
        self.bytes = 0

    def reserve(self, amount: int) -> None:
        self.bytes = checked_add(self.bytes, amount, MAX_TOTAL_CANDIDATE_BYTES, CandidateByteLimit)


def write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        try:
            written = os.write(fd, view)
        except OSError:
            _raise(OutputWrite, "write")
        if written <= 0:
            _raise(OutputWrite, "short-write")
        view = view[written:]


def _write_atomic_terminal_line(fd: int, data: bytes) -> None:
    if not data or len(data) > 16384:
        _raise(OutputWrite, "terminal-line-size")
    try:
        descriptor = os.fstat(fd)
        pipe_buf = os.fpathconf(fd, "PC_PIPE_BUF")
    except (OSError, ValueError):
        _raise(OutputWrite, "terminal-pipe")
    if not stat.S_ISFIFO(descriptor.st_mode) or len(data) > pipe_buf:
        _raise(OutputWrite, "terminal-atomicity")
    try:
        written = os.write(fd, data)
    except OSError:
        _raise(OutputWrite, "terminal-write")
    if written != len(data):
        _raise(OutputWrite, "terminal-short-write")


def _close_descriptor(
    fd: int,
    error_type: Type[ArchiveLedgerError],
    diagnostic: str,
) -> None:
    try:
        os.close(fd)
    except OSError:
        _raise(error_type, diagnostic)


def _canonical_json_chunks(value: Dict[str, Any], allow_signed: bool) -> Iterable[bytes]:
    _validate_json_value(value, allow_signed=allow_signed)
    encoder = json.JSONEncoder(
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    try:
        for chunk in encoder.iterencode(value):
            yield chunk.encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _raise(OutputWrite, "canonical-json")
    yield b"\n"


class CanonicalWriter:
    """Bounded canonical JSON or JSONL writer with streaming digest."""

    def __init__(self, fd: int, byte_limit: int, budget: CandidateBudget) -> None:
        self.fd = fd
        self.byte_limit = byte_limit
        self.budget = budget
        self.bytes = 0
        self.rows = 0
        self.digest = hashlib.sha256()

    def write_object(self, value: Dict[str, Any], allow_signed: bool = False) -> None:
        for data in _canonical_json_chunks(value, allow_signed):
            self.bytes = checked_add(self.bytes, len(data), self.byte_limit, CandidateByteLimit)
            self.budget.reserve(len(data))
            write_all(self.fd, data)
            self.digest.update(data)
        self.rows += 1

    @property
    def sha256(self) -> str:
        return self.digest.hexdigest()


class MemoryWriter:
    """Pure synthetic-test sink implementing the CanonicalWriter interface."""

    def __init__(self, byte_limit: int, budget: Optional[CandidateBudget] = None) -> None:
        self.byte_limit = byte_limit
        self.budget = budget
        self.data = bytearray()
        self.rows = 0

    def write_object(self, value: Dict[str, Any], allow_signed: bool = False) -> None:
        for encoded in _canonical_json_chunks(value, allow_signed):
            if len(self.data) + len(encoded) > self.byte_limit:
                _raise(CandidateByteLimit, "memory-writer-limit")
            if self.budget is not None:
                self.budget.reserve(len(encoded))
            self.data.extend(encoded)
        self.rows += 1

    @property
    def bytes(self) -> int:
        return len(self.data)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(bytes(self.data)).hexdigest()


class PrependReader:
    """Bounded descriptor reader with an explicit pushback prefix."""

    def __init__(self, fd: int) -> None:
        self.fd = fd
        self.prefix = bytearray()
        self.offset = 0
        self.raw_digest = hashlib.sha256()

    def read_some(self, limit: int = READ_CHUNK_BYTES) -> bytes:
        if self.prefix:
            size = min(limit, len(self.prefix))
            data = bytes(self.prefix[:size])
            del self.prefix[:size]
            return data
        try:
            data = os.read(self.fd, limit)
        except OSError:
            _raise(InputOpen, "archive-read")
        self.raw_digest.update(data)
        self.offset += len(data)
        return data

    def read_exact(self, size: int, error_type: Type[ArchiveLedgerError]) -> bytes:
        chunks: List[bytes] = []
        remaining = size
        while remaining:
            chunk = self.read_some(min(READ_CHUNK_BYTES, remaining))
            if not chunk:
                _raise(error_type, "truncated")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def unread(self, data: bytes) -> None:
        if data:
            self.prefix = bytearray(data) + self.prefix


def _read_c_string(
    reader: PrependReader,
    limit: int,
    total: int,
) -> Tuple[bytes, bytes, int]:
    value = bytearray()
    raw = bytearray()
    while True:
        byte = reader.read_exact(1, GzipOptionalFieldLimit)
        if byte == b"\0":
            raw.extend(byte)
            break
        if len(value) >= limit:
            _raise(GzipOptionalFieldLimit, "optional-string")
        total = checked_add(total, 1, MAX_GZIP_OPTIONAL_BYTES_TOTAL, GzipOptionalFieldLimit)
        raw.extend(byte)
        value.extend(byte)
    return bytes(value), bytes(raw), total


def _header_fields(header: bytes) -> Dict[str, Any]:
    if len(header) != BLOCK_BYTES:
        _raise(TarPartialBlock, "header-size")
    if header[257:263] != b"ustar\0":
        _raise(TarMagic, "ustar-magic")
    if header[263:265] != b"00":
        _raise(TarVersion, "ustar-version")
    if header[500:512] != b"\0" * 12:
        _raise(TarUnsupportedType, "header-padding")

    parsed_checksum = parse_checksum_field(header[148:156])
    checksum_header = header[:148] + (b" " * 8) + header[156:]
    if sum(checksum_header) != parsed_checksum:
        _raise(TarChecksum, "unsigned-posix-checksum")

    name = _decode_ascii_field(header[0:100], allow_empty=False, error_type=TarPathEncoding)
    linkname = _decode_ascii_field(header[157:257], allow_empty=True, error_type=TarPathEncoding)
    _decode_ascii_field(header[265:297], allow_empty=True, error_type=TarPathEncoding)
    _decode_ascii_field(header[297:329], allow_empty=True, error_type=TarPathEncoding)
    prefix = _decode_ascii_field(header[345:500], allow_empty=True, error_type=TarPathEncoding)
    if linkname:
        _raise(TarUnsupportedType, "linkname")
    if prefix and (prefix.startswith("/") or prefix.endswith("/") or name.startswith("/") or name.endswith("/")):
        _raise(TarPathInvalid, "ustar-prefix-join")

    member_flag = header[156:157]
    member_types = {
        b"\0": "regular",
        b"0": "regular",
        b"5": "directory",
        b"x": "pax_path",
        b"L": "gnu_long_name",
    }
    if member_flag not in member_types:
        _raise(TarUnsupportedType, "typeflag")

    values = {
        "mode": parse_octal_field(header[100:108], 7),
        "uid": parse_octal_field(header[108:116], 7),
        "gid": parse_octal_field(header[116:124], 7),
        "size": parse_octal_field(header[124:136], 11),
        "mtime": parse_octal_field(header[136:148], 11),
        "checksum": parsed_checksum,
        "devmajor": parse_octal_field(header[329:337], 7),
        "devminor": parse_octal_field(header[337:345], 7),
    }
    if values["devmajor"] != 0 or values["devminor"] != 0:
        _raise(TarUnsupportedType, "device-number")
    if member_types[member_flag] == "directory" and values["size"] != 0:
        _raise(TarUnsupportedType, "directory-size")
    if values["size"] > MAX_MEMBER_BYTES:
        _raise(TarMemberSizeLimit, "member-size")

    raw_base = (prefix + "/" + name) if prefix else name
    return {
        "base_name": name,
        "prefix": prefix,
        "raw_base": raw_base,
        "member_type": member_types[member_flag],
        "values": values,
        "header": header,
    }


class TarLedgerParser:
    """Incremental strict-ustar parser that never materializes file payloads."""

    def __init__(self, header_writer: Any, inventory_writer: Any, require_profile: bool = True) -> None:
        self.header_writer = header_writer
        self.inventory_writer = inventory_writer
        self.require_profile = require_profile
        self.buffer = bytearray()
        self.position = 0
        self.uncompressed_bytes = 0
        self.tar_digest = hashlib.sha256()
        self.mode = "header"
        self.zero_blocks = 0
        self.first_zero_index = 0
        self.first_zero_offset = 0
        self.trailing_offset = 0
        self.trailing_bytes = 0
        self.trailing_digest = hashlib.sha256()
        self.physical_headers = 0
        self.logical_members = 0
        self.extension_headers = 0
        self.extension_payload_bytes_total = 0
        self.regular_members = 0
        self.directory_members = 0
        self.root_count = 0
        self.aggregate_regular_bytes = 0
        self.largest_member_bytes = 0
        self.pending_extension: Optional[Tuple[bytes, int]] = None
        self.current: Optional[Dict[str, Any]] = None
        self.current_remaining = 0
        self.current_padding_remaining = 0
        self.current_content_digest = hashlib.sha256()
        self.current_padding_digest = hashlib.sha256()
        self.current_payload = bytearray()
        self.raw_names: Set[str] = set()
        self.effective_names: Set[str] = set()
        self.collision_kinds: Dict[str, str] = {}
        self.legacy_rows: List[Sequence[Any]] = []
        self.top_level: Set[str] = set()
        self.embedded_lean_bytes = 0
        self.embedded_lean_sha256 = EMPTY_SHA256

        self.header_writer.write_object(
            {
                "schema": "hsai-p01b-gzip-tar-header-ledger-v1",
                "row_kind": "ledger_header",
                "row_index": 0,
                "contract_digest": CONTRACT_DIGEST,
            }
        )
        self.inventory_writer.write_object(
            {
                "schema": "hsai-p01b-ordered-logical-member-inventory-v1",
                "row_kind": "ledger_header",
                "row_index": 0,
                "contract_digest": CONTRACT_DIGEST,
            }
        )

    def feed(self, data: bytes) -> None:
        if not data:
            return
        self.uncompressed_bytes = checked_add(
            self.uncompressed_bytes, len(data), MAX_UNCOMPRESSED_TAR_BYTES, UncompressedTarLimit
        )
        self.tar_digest.update(data)
        self.buffer.extend(data)
        self._drain()

    def _consume(self, size: int) -> bytes:
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        self.position += size
        return data

    def _drain(self) -> None:
        while True:
            if self.mode == "header":
                if len(self.buffer) < BLOCK_BYTES:
                    return
                offset = self.position
                block_index = offset // BLOCK_BYTES
                header = self._consume(BLOCK_BYTES)
                if header == b"\0" * BLOCK_BYTES:
                    if self.pending_extension is not None:
                        _raise(TarExtensionOrphan, "extension-before-terminator")
                    self.zero_blocks += 1
                    if self.zero_blocks == 1:
                        self.first_zero_index = block_index
                        self.first_zero_offset = offset
                    elif self.zero_blocks == 2:
                        self.header_writer.write_object(
                            {
                                "schema": "hsai-p01b-tar-terminator-v1",
                                "row_kind": "tar_terminator",
                                "row_index": self.header_writer.rows,
                                "first_zero_block_index": self.first_zero_index,
                                "first_zero_byte_offset": self.first_zero_offset,
                                "first_zero_sha256": ZERO_BLOCK_SHA256,
                                "second_zero_block_index": block_index,
                                "second_zero_byte_offset": offset,
                                "second_zero_sha256": ZERO_BLOCK_SHA256,
                            }
                        )
                        self.trailing_offset = self.position
                        self.mode = "trailing"
                    else:
                        _raise(TarTerminator, "terminator-count")
                    continue
                if self.zero_blocks:
                    _raise(TarTerminator, "member-after-zero")
                self._start_header(header, offset, block_index)
                continue

            if self.mode == "data":
                if not self.buffer:
                    return
                amount = min(len(self.buffer), self.current_remaining)
                chunk = self._consume(amount)
                self.current_remaining -= amount
                self.current_content_digest.update(chunk)
                if self.current is not None and self.current["member_type"] in ("pax_path", "gnu_long_name"):
                    self.current_payload.extend(chunk)
                if self.current_remaining == 0:
                    self.mode = "padding"
                continue

            if self.mode == "padding":
                if self.current_padding_remaining and not self.buffer:
                    return
                amount = min(len(self.buffer), self.current_padding_remaining)
                if amount:
                    padding = self._consume(amount)
                    if any(padding):
                        _raise(TarPaddingNonzero, "member-padding")
                    self.current_padding_digest.update(padding)
                    self.current_padding_remaining -= amount
                if self.current_padding_remaining == 0:
                    self._complete_current()
                    self.mode = "header"
                continue

            if self.mode == "trailing":
                if not self.buffer:
                    return
                checked_add(
                    self.trailing_bytes,
                    len(self.buffer),
                    MAX_TRAILING_ZERO_BYTES,
                    TarTrailingLimit,
                )
                chunk = self._consume(len(self.buffer))
                if any(chunk):
                    _raise(TarTerminator, "nonzero-trailing-data")
                self.trailing_bytes += len(chunk)
                self.trailing_digest.update(chunk)
                continue
            raise AssertionError("unknown TAR parser mode")

    def _start_header(self, header: bytes, offset: int, block_index: int) -> None:
        self.physical_headers = checked_add(
            self.physical_headers, 1, MAX_PHYSICAL_TAR_HEADERS, TarHeaderLimit
        )
        parsed = _header_fields(header)
        member_type = parsed["member_type"]
        if member_type in ("pax_path", "gnu_long_name"):
            if self.pending_extension is not None:
                _raise(TarExtensionConflict, "stacked-extension")
            self.extension_headers = checked_add(
                self.extension_headers, 1, MAX_EXTENSION_HEADERS, TarExtensionLimit
            )
            size = parsed["values"]["size"]
            if size > MAX_EXTENSION_PAYLOAD_BYTES:
                _raise(TarExtensionPayloadLimit, "extension-payload")
            self.extension_payload_bytes_total = checked_add(
                self.extension_payload_bytes_total,
                size,
                MAX_EXTENSION_PAYLOAD_BYTES_TOTAL,
                TarExtensionPayloadLimit,
            )
        else:
            checked_add(self.logical_members, 1, MAX_LOGICAL_MEMBERS, TarMemberLimit)
            if member_type == "regular":
                aggregate = checked_add(
                    self.aggregate_regular_bytes,
                    parsed["values"]["size"],
                    MAX_AGGREGATE_REGULAR_BYTES,
                    TarAggregateLimit,
                )
                if aggregate > MAX_TOTAL_EXTRACTION_OUTPUT_BYTES:
                    _raise(TarAggregateLimit, "total-extraction-output")

        parsed["physical_header_index"] = self.physical_headers - 1
        parsed["uncompressed_block_index"] = block_index
        parsed["uncompressed_byte_offset"] = offset
        parsed["data_offset"] = offset + BLOCK_BYTES
        self.current = parsed
        size = parsed["values"]["size"]
        self.current_remaining = size
        self.current_padding_remaining = (-size) % BLOCK_BYTES
        self.current_content_digest = hashlib.sha256()
        self.current_padding_digest = hashlib.sha256()
        self.current_payload = bytearray()
        self.mode = "data" if size else "padding"

    def _header_row(self, extension_payload: bytes) -> Dict[str, Any]:
        if self.current is None:
            raise AssertionError("no current header")
        header = self.current["header"]
        values = self.current["values"]
        member_type = self.current["member_type"]
        is_extension = member_type in ("pax_path", "gnu_long_name")
        return {
            "schema": "hsai-p01b-tar-header-v1",
            "row_kind": "tar_header",
            "row_index": self.header_writer.rows,
            "physical_header_index": self.current["physical_header_index"],
            "uncompressed_block_index": self.current["uncompressed_block_index"],
            "uncompressed_byte_offset": self.current["uncompressed_byte_offset"],
            "raw_header_hex": header.hex(),
            "raw_header_sha256": sha256_hex(header),
            "raw_name_hex": header[0:100].hex(),
            "raw_mode_hex": header[100:108].hex(),
            "raw_uid_hex": header[108:116].hex(),
            "raw_gid_hex": header[116:124].hex(),
            "raw_size_hex": header[124:136].hex(),
            "raw_mtime_hex": header[136:148].hex(),
            "raw_checksum_hex": header[148:156].hex(),
            "raw_typeflag_hex": header[156:157].hex(),
            "raw_linkname_hex": header[157:257].hex(),
            "raw_magic_hex": header[257:263].hex(),
            "raw_version_hex": header[263:265].hex(),
            "raw_uname_hex": header[265:297].hex(),
            "raw_gname_hex": header[297:329].hex(),
            "raw_devmajor_hex": header[329:337].hex(),
            "raw_devminor_hex": header[337:345].hex(),
            "raw_prefix_hex": header[345:500].hex(),
            "raw_padding_hex": header[500:512].hex(),
            "base_name": self.current["base_name"],
            "prefix": self.current["prefix"],
            "parsed_mode": values["mode"],
            "parsed_uid": values["uid"],
            "parsed_gid": values["gid"],
            "parsed_size": values["size"],
            "parsed_mtime": values["mtime"],
            "parsed_checksum": values["checksum"],
            "parsed_devmajor": values["devmajor"],
            "parsed_devminor": values["devminor"],
            "checksum_variant": "unsigned-posix-v1",
            "member_type": member_type,
            "extension_payload_present": is_extension,
            "extension_payload_bytes": len(extension_payload) if is_extension else 0,
            "extension_payload_hex": extension_payload.hex() if is_extension else "",
            "extension_payload_sha256": sha256_hex(extension_payload) if is_extension else EMPTY_SHA256,
            "applies_to_archive_index_present": is_extension,
            "applies_to_archive_index": self.logical_members if is_extension else 0,
            "data_offset": self.current["data_offset"],
            "data_bytes": values["size"] if member_type != "directory" else 0,
            "data_padding_bytes": (-values["size"]) % BLOCK_BYTES,
            "data_padding_sha256": self.current_padding_digest.hexdigest(),
        }

    def _complete_current(self) -> None:
        if self.current is None:
            raise AssertionError("no current member")
        member_type = self.current["member_type"]
        payload = bytes(self.current_payload)
        header_row = self._header_row(payload)

        if member_type in ("pax_path", "gnu_long_name"):
            override = parse_pax_path(payload) if member_type == "pax_path" else parse_gnu_long_name(payload)
            if len(override) > MAX_EFFECTIVE_PATH_BYTES:
                _raise(TarPathInvalid, "extension-path-length")
            self.pending_extension = (override, self.current["physical_header_index"])
            self.header_writer.write_object(header_row)
            self.current = None
            return

        self.logical_members = checked_add(self.logical_members, 1, MAX_LOGICAL_MEMBERS, TarMemberLimit)
        kind = member_type
        raw_base = self.current["raw_base"]
        if raw_base in self.raw_names:
            _raise(TarDuplicateRawName, "raw-name")
        self.raw_names.add(raw_base)
        extension_indices: List[int] = []
        if self.pending_extension is None:
            effective_raw = raw_base.encode("ascii")
        else:
            effective_raw, extension_index = self.pending_extension
            extension_indices = [extension_index]
            self.pending_extension = None
        effective_name, collision_key = validate_effective_path(effective_raw, kind)
        if effective_name in self.effective_names:
            _raise(TarDuplicateEffectiveName, "effective-name")
        self.effective_names.add(effective_name)
        previous_kind = self.collision_kinds.get(collision_key)
        if previous_kind is not None:
            if previous_kind != kind:
                _raise(TarFileDirectoryCollision, "kind-collision")
            _raise(TarDuplicateCollisionKey, "collision-key")
        parts = collision_key.split("/")
        for index in range(1, len(parts)):
            ancestor = "/".join(parts[:index])
            if self.collision_kinds.get(ancestor) == "regular":
                _raise(TarRegularAncestor, "regular-ancestor")
        if kind == "regular":
            prefix = collision_key + "/"
            if any(existing.startswith(prefix) for existing in self.collision_kinds):
                _raise(TarRegularAncestor, "regular-becomes-ancestor")
        self.collision_kinds[collision_key] = kind

        size = self.current["values"]["size"]
        if kind == "regular":
            self.regular_members += 1
            self.aggregate_regular_bytes = checked_add(
                self.aggregate_regular_bytes, size, MAX_AGGREGATE_REGULAR_BYTES, TarAggregateLimit
            )
            if self.aggregate_regular_bytes > MAX_TOTAL_EXTRACTION_OUTPUT_BYTES:
                _raise(TarAggregateLimit, "total-extraction-output")
            self.largest_member_bytes = max(self.largest_member_bytes, size)
        else:
            self.directory_members += 1
        if collision_key == ".":
            self.root_count += 1
        else:
            self.top_level.add(collision_key.split("/", 1)[0])

        content_sha256 = self.current_content_digest.hexdigest()
        if collision_key == EMBEDDED_LEAN_PATH:
            self.embedded_lean_bytes = size
            self.embedded_lean_sha256 = content_sha256

        archive_index = self.logical_members - 1
        self.header_writer.write_object(header_row)
        self.inventory_writer.write_object(
            {
                "schema": "hsai-p01b-archive-logical-member-v1",
                "row_kind": "logical_member",
                "row_index": archive_index + 1,
                "archive_index": archive_index,
                "physical_header_index": self.current["physical_header_index"],
                "extension_header_indices": extension_indices,
                "raw_name_hex": self.current["header"][0:100].hex(),
                "effective_raw_name": effective_name,
                "collision_key": collision_key,
                "kind": kind,
                "member_size": size,
                "content_sha256": content_sha256,
                "data_offset": self.current["data_offset"],
                "data_padding_bytes": (-size) % BLOCK_BYTES,
            }
        )
        self.legacy_rows.append([archive_index, effective_name, collision_key, kind, size])
        self.current = None

    def finish(self) -> Dict[str, Any]:
        self._drain()
        if self.buffer:
            _raise(TarPartialBlock, "partial-block")
        if self.mode in ("data", "padding"):
            _raise(TarPartialBlock, "truncated-member")
        if self.pending_extension is not None:
            _raise(TarExtensionOrphan, "orphan-extension")
        if self.zero_blocks != 2 or self.mode != "trailing":
            _raise(TarTerminator, "missing-terminator")
        if self.trailing_bytes % BLOCK_BYTES != 0:
            _raise(TarPartialBlock, "partial-trailing-block")

        self.header_writer.write_object(
            {
                "schema": "hsai-p01b-tar-trailing-padding-v1",
                "row_kind": "tar_trailing_padding",
                "row_index": self.header_writer.rows,
                "uncompressed_byte_offset": self.trailing_offset,
                "padding_bytes": self.trailing_bytes,
                "padding_sha256": self.trailing_digest.hexdigest(),
            }
        )

        legacy_digest = hashlib.sha256()
        for row in sorted(self.legacy_rows):
            legacy_digest.update(_canonical_legacy_row(row))
        observed = {
            "physical_tar_headers": self.physical_headers,
            "logical_members": self.logical_members,
            "root_count": self.root_count,
            "regular_members": self.regular_members,
            "directory_members": self.directory_members,
            "extension_headers": self.extension_headers,
            "uncompressed_tar_bytes": self.uncompressed_bytes,
            "aggregate_regular_bytes": self.aggregate_regular_bytes,
            "largest_member_bytes": self.largest_member_bytes,
            "trailing_zero_bytes": self.trailing_bytes,
            "top_level": sorted(self.top_level),
            "legacy_inventory_sha256": legacy_digest.hexdigest(),
            "embedded_lean_bytes": self.embedded_lean_bytes,
            "embedded_lean_sha256": self.embedded_lean_sha256,
            "uncompressed_tar_sha256": self.tar_digest.hexdigest(),
        }
        if self.require_profile:
            require_pinned_profile(observed)
        return observed


def require_pinned_profile(observed: Dict[str, Any]) -> None:
    expected = {
        "logical_members": EXPECTED_LOGICAL_MEMBERS,
        "root_count": EXPECTED_ROOT_COUNT,
        "regular_members": EXPECTED_REGULAR_MEMBERS,
        "directory_members": EXPECTED_DIRECTORY_MEMBERS,
        "top_level": EXPECTED_TOP_LEVEL,
        "legacy_inventory_sha256": EXPECTED_LEGACY_INVENTORY_SHA256,
    }
    for key, value in expected.items():
        if observed.get(key) != value:
            _raise(ProfileMismatch, "profile-" + key)
    if (
        observed.get("embedded_lean_bytes") != EXPECTED_EMBEDDED_LEAN_BYTES
        or observed.get("embedded_lean_sha256") != EXPECTED_EMBEDDED_LEAN_SHA256
    ):
        _raise(EmbeddedLeanMismatch, "embedded-lean")


class BytesReader:
    """Pure in-memory reader for deterministic synthetic tests."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.index = 0
        self.prefix = bytearray()
        self.offset = 0
        self.raw_digest = hashlib.sha256()

    def read_some(self, limit: int = READ_CHUNK_BYTES) -> bytes:
        if self.prefix:
            size = min(limit, len(self.prefix))
            value = bytes(self.prefix[:size])
            del self.prefix[:size]
            return value
        value = self.data[self.index : self.index + limit]
        self.index += len(value)
        self.offset += len(value)
        self.raw_digest.update(value)
        return value

    def read_exact(self, size: int, error_type: Type[ArchiveLedgerError]) -> bytes:
        chunks: List[bytes] = []
        remaining = size
        while remaining:
            chunk = self.read_some(min(READ_CHUNK_BYTES, remaining))
            if not chunk:
                _raise(error_type, "truncated")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def unread(self, data: bytes) -> None:
        if data:
            self.prefix = bytearray(data) + self.prefix


def _validate_gzip_extra(data: bytes) -> None:
    position = 0
    while position < len(data):
        if len(data) - position < 4:
            _raise(GzipExtraField, "extra-subfield-header")
        subfield_length = struct.unpack("<H", data[position + 2 : position + 4])[0]
        position += 4
        if subfield_length > len(data) - position:
            _raise(GzipExtraField, "extra-subfield-length")
        position += subfield_length
    if position != len(data):
        _raise(GzipExtraField, "extra-framing")


def parse_gzip_tar_reader(
    reader: Any,
    header_writer: Any,
    inventory_writer: Any,
    compressed_bytes: int,
    require_profile: bool = True,
) -> Dict[str, Any]:
    """Directly parse one bounded RFC 1952 member into strict TAR ledgers."""
    fixed_header = reader.read_exact(10, GzipMagic)
    if fixed_header[0:2] != b"\x1f\x8b":
        _raise(GzipMagic, "magic")
    if fixed_header[2] != 8:
        _raise(GzipMethod, "method")
    flg = fixed_header[3]
    if flg & 0xE0:
        _raise(GzipReservedFlags, "reserved-flags")

    header_crc_material = bytearray(fixed_header)
    optional_total = 0
    fextra_present = bool(flg & 0x04)
    fextra_xlen_hex = ""
    fextra = b""
    if fextra_present:
        xlen_raw = reader.read_exact(2, GzipOptionalFieldLimit)
        header_crc_material.extend(xlen_raw)
        xlen = struct.unpack("<H", xlen_raw)[0]
        if xlen > MAX_GZIP_EXTRA_BYTES:
            _raise(GzipOptionalFieldLimit, "extra-length")
        optional_total = checked_add(
            optional_total, xlen, MAX_GZIP_OPTIONAL_BYTES_TOTAL, GzipOptionalFieldLimit
        )
        fextra = reader.read_exact(xlen, GzipExtraField)
        header_crc_material.extend(fextra)
        fextra_xlen_hex = xlen_raw.hex()
        _validate_gzip_extra(fextra)

    fname_present = bool(flg & 0x08)
    fname = b""
    if fname_present:
        fname, raw_fname, optional_total = _read_c_string(
            reader, MAX_GZIP_FILENAME_BYTES, optional_total
        )
        header_crc_material.extend(raw_fname)

    fcomment_present = bool(flg & 0x10)
    fcomment = b""
    if fcomment_present:
        fcomment, raw_comment, optional_total = _read_c_string(
            reader, MAX_GZIP_COMMENT_BYTES, optional_total
        )
        header_crc_material.extend(raw_comment)

    fhcrc_present = bool(flg & 0x02)
    fhcrc_hex = ""
    fhcrc16 = 0
    if fhcrc_present:
        fhcrc_raw = reader.read_exact(2, GzipHeaderCrc)
        fhcrc_hex = fhcrc_raw.hex()
        fhcrc16 = struct.unpack("<H", fhcrc_raw)[0]
        if (zlib.crc32(bytes(header_crc_material)) & 0xFFFF) != fhcrc16:
            _raise(GzipHeaderCrc, "header-crc")

    deflate_offset = len(header_crc_material) + (2 if fhcrc_present else 0)
    decompressor = zlib.decompressobj(wbits=-15)
    deflate_digest = hashlib.sha256()
    deflate_bytes = 0
    output_crc = 0
    output_bytes = 0
    tar_parser = TarLedgerParser(header_writer, inventory_writer, require_profile=require_profile)
    pending = b""

    while not decompressor.eof:
        if not pending:
            pending = reader.read_some(READ_CHUNK_BYTES)
            if not pending:
                _raise(GzipDeflate, "truncated-deflate")
        try:
            remaining_output = MAX_UNCOMPRESSED_TAR_BYTES - output_bytes
            ratio_remaining = compressed_bytes * MAX_COMPRESSION_RATIO - output_bytes
            maximum_output = min(READ_CHUNK_BYTES, remaining_output + 1, ratio_remaining + 1)
            if maximum_output <= 0:
                _raise(CompressionRatioLimit, "compression-ratio")
            output = decompressor.decompress(pending, maximum_output)
        except zlib.error:
            _raise(GzipDeflate, "invalid-deflate")
        unused = decompressor.unused_data if decompressor.eof else b""
        unconsumed = decompressor.unconsumed_tail
        consumed = len(pending) - len(unconsumed) - len(unused)
        if consumed < 0 or (consumed == 0 and not output and not decompressor.eof):
            _raise(GzipDeflate, "deflate-no-progress")
        if consumed:
            deflate_digest.update(pending[:consumed])
            deflate_bytes = checked_add(deflate_bytes, consumed, compressed_bytes, GzipDeflate)
        if output:
            if output_bytes + len(output) > compressed_bytes * MAX_COMPRESSION_RATIO:
                _raise(CompressionRatioLimit, "compression-ratio")
            output_bytes = checked_add(
                output_bytes, len(output), MAX_UNCOMPRESSED_TAR_BYTES, UncompressedTarLimit
            )
            output_crc = zlib.crc32(output, output_crc)
            tar_parser.feed(output)
        if decompressor.eof:
            reader.unread(unused)
            pending = b""
        else:
            pending = unconsumed

    trailer_offset = deflate_offset + deflate_bytes
    trailer = reader.read_exact(8, GzipTrailerCrc)
    trailer_crc32, trailer_isize = struct.unpack("<II", trailer)
    if trailer_crc32 != (output_crc & 0xFFFFFFFF):
        _raise(GzipTrailerCrc, "trailer-crc")
    if trailer_isize != (output_bytes & 0xFFFFFFFF):
        _raise(GzipTrailerSize, "trailer-isize")

    trailing = reader.read_some(READ_CHUNK_BYTES)
    if trailing:
        if trailing.startswith(b"\x1f\x8b"):
            _raise(GzipMemberCount, "second-member")
        _raise(GzipTrailingData, "bytes-after-trailer")

    observed = tar_parser.finish()
    compressed_end = trailer_offset + len(trailer)
    if compressed_end != compressed_bytes:
        _raise(GzipTrailingData, "compressed-length-accounting")

    gzip_row = {
        "schema": "hsai-p01b-gzip-member-v1",
        "row_kind": "gzip_member",
        "row_index": header_writer.rows,
        "member_index": 0,
        "compressed_start": 0,
        "compressed_end": compressed_end,
        "fixed_header_hex": fixed_header.hex(),
        "id1": 31,
        "id2": 139,
        "cm": 8,
        "flg": flg,
        "mtime": struct.unpack("<I", fixed_header[4:8])[0],
        "xfl": fixed_header[8],
        "os": fixed_header[9],
        "fextra_present": fextra_present,
        "fextra_xlen_hex": fextra_xlen_hex,
        "fextra_bytes": len(fextra),
        "fextra_hex": fextra.hex(),
        "fextra_sha256": sha256_hex(fextra),
        "fname_present": fname_present,
        "fname_bytes": len(fname),
        "fname_hex": fname.hex(),
        "fname_sha256": sha256_hex(fname),
        "fcomment_present": fcomment_present,
        "fcomment_bytes": len(fcomment),
        "fcomment_hex": fcomment.hex(),
        "fcomment_sha256": sha256_hex(fcomment),
        "fhcrc_present": fhcrc_present,
        "fhcrc_hex": fhcrc_hex,
        "fhcrc16": fhcrc16,
        "deflate_offset": deflate_offset,
        "deflate_bytes": deflate_bytes,
        "deflate_sha256": deflate_digest.hexdigest(),
        "trailer_offset": trailer_offset,
        "trailer_hex": trailer.hex(),
        "trailer_crc32": trailer_crc32,
        "trailer_isize": trailer_isize,
        "uncompressed_bytes": output_bytes,
        "raw_member_sha256": reader.raw_digest.hexdigest(),
        "uncompressed_tar_sha256": observed["uncompressed_tar_sha256"],
    }
    header_writer.write_object(gzip_row)
    observed["gzip_members"] = 1
    observed["gzip_row"] = gzip_row
    return observed


def parse_gzip_tar_bytes(data: bytes, require_profile: bool = False) -> Tuple[Dict[str, Any], bytes, bytes]:
    """Pure synthetic-test entrypoint; production uses retained descriptors."""
    budget = CandidateBudget()
    header_writer = MemoryWriter(MAX_HEADER_LEDGER_BYTES, budget)
    inventory_writer = MemoryWriter(MAX_INVENTORY_LEDGER_BYTES, budget)
    observed = parse_gzip_tar_reader(
        BytesReader(data),
        header_writer,
        inventory_writer,
        len(data),
        require_profile=require_profile,
    )
    return observed, bytes(header_writer.data), bytes(inventory_writer.data)


MANIFEST_KEYS = {
    "schema",
    "asset_id",
    "url",
    "release_id",
    "github_asset_id",
    "filename",
    "tag_commit",
    "expected_compressed_bytes",
    "expected_archive_sha256",
    "release_immutable",
    "contract_digest",
    "parser_source_sha256",
    "python_version",
    "zlib_version",
    "archive_device",
    "archive_inode",
    "archive_mode",
    "archive_owner_uid",
    "archive_link_count",
    "archive_byte_length",
    "archive_modified_seconds",
    "archive_modified_nanoseconds",
    "archive_changed_seconds",
    "archive_changed_nanoseconds",
    "archive_sha256",
    "gzip_members",
    "physical_tar_headers",
    "logical_members",
    "root_count",
    "regular_members",
    "directory_members",
    "extension_headers",
    "uncompressed_tar_bytes",
    "aggregate_regular_bytes",
    "largest_member_bytes",
    "trailing_zero_bytes",
    "top_level",
    "legacy_inventory_sha256",
    "embedded_lean_bytes",
    "embedded_lean_sha256",
    "header_ledger_bytes",
    "header_ledger_sha256",
    "inventory_ledger_bytes",
    "inventory_ledger_sha256",
    "candidate_only",
    "accepted",
    "phase_797_authorized",
    "materialization_authorized",
    "capture_authorized",
    "accepted_evidence_authorized",
}

STATUS_KEYS = {
    "schema",
    "decision",
    "declared_files",
    "manifest_bytes",
    "manifest_sha256",
    "header_ledger_bytes",
    "header_ledger_sha256",
    "inventory_ledger_bytes",
    "inventory_ledger_sha256",
    "candidate_only",
    "accepted",
    "phase_797_authorized",
    "materialization_authorized",
    "capture_authorized",
    "accepted_evidence_authorized",
}

LEDGER_HEADER_KEYS = {"schema", "row_kind", "row_index", "contract_digest"}
TAR_TERMINATOR_KEYS = {
    "schema",
    "row_kind",
    "row_index",
    "first_zero_block_index",
    "first_zero_byte_offset",
    "first_zero_sha256",
    "second_zero_block_index",
    "second_zero_byte_offset",
    "second_zero_sha256",
}
TAR_TRAILING_KEYS = {
    "schema",
    "row_kind",
    "row_index",
    "uncompressed_byte_offset",
    "padding_bytes",
    "padding_sha256",
}
TAR_HEADER_KEYS = {
    "schema", "row_kind", "row_index", "physical_header_index",
    "uncompressed_block_index", "uncompressed_byte_offset", "raw_header_hex",
    "raw_header_sha256", "raw_name_hex", "raw_mode_hex", "raw_uid_hex",
    "raw_gid_hex", "raw_size_hex", "raw_mtime_hex", "raw_checksum_hex",
    "raw_typeflag_hex", "raw_linkname_hex", "raw_magic_hex", "raw_version_hex",
    "raw_uname_hex", "raw_gname_hex", "raw_devmajor_hex", "raw_devminor_hex",
    "raw_prefix_hex", "raw_padding_hex", "base_name", "prefix", "parsed_mode",
    "parsed_uid", "parsed_gid", "parsed_size", "parsed_mtime", "parsed_checksum",
    "parsed_devmajor", "parsed_devminor", "checksum_variant", "member_type",
    "extension_payload_present", "extension_payload_bytes", "extension_payload_hex",
    "extension_payload_sha256", "applies_to_archive_index_present",
    "applies_to_archive_index", "data_offset", "data_bytes", "data_padding_bytes",
    "data_padding_sha256",
}
GZIP_MEMBER_KEYS = {
    "schema", "row_kind", "row_index", "member_index", "compressed_start",
    "compressed_end", "fixed_header_hex", "id1", "id2", "cm", "flg", "mtime",
    "xfl", "os", "fextra_present", "fextra_xlen_hex", "fextra_bytes", "fextra_hex",
    "fextra_sha256", "fname_present", "fname_bytes", "fname_hex", "fname_sha256",
    "fcomment_present", "fcomment_bytes", "fcomment_hex", "fcomment_sha256",
    "fhcrc_present", "fhcrc_hex", "fhcrc16", "deflate_offset", "deflate_bytes",
    "deflate_sha256", "trailer_offset", "trailer_hex", "trailer_crc32",
    "trailer_isize", "uncompressed_bytes", "raw_member_sha256",
    "uncompressed_tar_sha256",
}
INVENTORY_MEMBER_KEYS = {
    "schema", "row_kind", "row_index", "archive_index", "physical_header_index",
    "extension_header_indices", "raw_name_hex", "effective_raw_name", "collision_key",
    "kind", "member_size", "content_sha256", "data_offset", "data_padding_bytes",
}
LEDGER_U64_FIELDS = {
    "row_index", "physical_header_index", "uncompressed_block_index",
    "uncompressed_byte_offset", "parsed_mode", "parsed_uid", "parsed_gid",
    "parsed_size", "parsed_mtime", "parsed_checksum", "parsed_devmajor",
    "parsed_devminor", "extension_payload_bytes", "applies_to_archive_index",
    "data_offset", "data_bytes", "data_padding_bytes", "first_zero_block_index",
    "first_zero_byte_offset", "second_zero_block_index", "second_zero_byte_offset",
    "padding_bytes", "member_index", "compressed_start", "compressed_end", "id1",
    "id2", "cm", "flg", "mtime", "xfl", "os", "fextra_bytes", "fname_bytes",
    "fcomment_bytes", "fhcrc16", "deflate_offset", "deflate_bytes", "trailer_offset",
    "trailer_crc32", "trailer_isize", "uncompressed_bytes", "archive_index",
    "member_size",
}


def _canonical_json_line_signed(value: Dict[str, Any]) -> bytes:
    _validate_json_value(value, allow_signed=True)
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii") + b"\n"
    except (TypeError, ValueError, UnicodeError):
        _raise(OutputWrite, "canonical-json")
    raise AssertionError("unreachable")


def _canonical_absolute_path(value: Any, error_type: Type[ArchiveLedgerError]) -> str:
    try:
        path = os.fspath(value)
    except TypeError:
        _raise(error_type, "path-type")
    if not isinstance(path, str) or not path or "\0" in path or not path.startswith("/"):
        _raise(error_type, "absolute-path")
    if path != "/" and path.endswith("/"):
        _raise(error_type, "trailing-separator")
    if "//" in path:
        _raise(error_type, "repeated-separator")
    components = path.split("/")[1:]
    if any(component in ("", ".", "..") for component in components):
        _raise(error_type, "path-component")
    if os.path.normpath(path) != path:
        _raise(error_type, "noncanonical-path")
    return path


def _strictly_beneath(path: str, root: str) -> bool:
    try:
        return path != root and os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def _paths_overlap(left: str, right: str) -> bool:
    try:
        common = os.path.commonpath([left, right])
    except ValueError:
        return False
    return common == left or common == right


def _identity_tuple(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_uid,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


class AcceptedPaths:
    """Retained descriptor graph for one input and one candidate parent."""

    def __init__(self) -> None:
        self.fds: List[int] = []
        self.links: List[Tuple[int, str, int, Tuple[int, ...]]] = []
        self.archive_fd = -1
        self.archive_stat: Optional[os.stat_result] = None
        self.candidate_parent_fd = -1
        self.candidate_parent = ""

    def keep(self, fd: int) -> int:
        self.fds.append(fd)
        return fd

    def close(self) -> None:
        while self.fds:
            fd = self.fds.pop()
            try:
                os.close(fd)
            except OSError:
                pass

    def verify_unchanged(self, allow_candidate_parent_metadata_change: bool = False) -> None:
        for parent_fd, name, child_fd, accepted in self.links:
            try:
                entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                opened = os.fstat(child_fd)
            except OSError:
                _raise(InputIdentityDrift, "descriptor-link")
            entry_identity = _identity_tuple(entry)
            opened_identity = _identity_tuple(opened)
            if allow_candidate_parent_metadata_change and child_fd == self.candidate_parent_fd:
                if entry_identity != opened_identity or entry_identity[:4] != accepted[:4]:
                    _raise(InputIdentityDrift, "candidate-parent-identity")
            elif entry_identity != accepted or opened_identity != accepted:
                _raise(InputIdentityDrift, "descriptor-identity")
        if self.archive_fd >= 0 and self.archive_stat is not None:
            try:
                current = os.fstat(self.archive_fd)
            except OSError:
                _raise(InputIdentityDrift, "archive-fstat")
            if _identity_tuple(current) != _identity_tuple(self.archive_stat):
                _raise(InputIdentityDrift, "archive-identity")


def _open_directory_component(
    accepted: AcceptedPaths,
    parent_fd: int,
    name: str,
    error_type: Type[ArchiveLedgerError],
) -> int:
    try:
        _checkpoint("directory-before-stat:" + name)
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _checkpoint("directory-after-stat:" + name)
    except OSError:
        _raise(error_type, "directory-stat")
    if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
        _raise(error_type, "directory-type")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        _checkpoint("directory-before-open:" + name)
        child_fd = os.open(name, flags, dir_fd=parent_fd)
        accepted.keep(child_fd)
        _checkpoint("directory-after-open:" + name)
    except OSError:
        _raise(error_type, "directory-open")
    try:
        after = os.fstat(child_fd)
        _checkpoint("directory-after-fstat:" + name)
    except OSError:
        _raise(error_type, "directory-fstat")
    if _identity_tuple(before) != _identity_tuple(after):
        _raise(InputIdentityDrift, "directory-race")
    accepted.links.append((parent_fd, name, child_fd, _identity_tuple(after)))
    return child_fd


def _open_absolute_directory(
    accepted: AcceptedPaths,
    path: str,
    error_type: Type[ArchiveLedgerError],
) -> int:
    try:
        root_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    except OSError:
        _raise(error_type, "filesystem-root-open")
    accepted.keep(root_fd)
    current = root_fd
    for component in path.split("/")[1:]:
        current = _open_directory_component(accepted, current, component, error_type)
    return current


def _walk_relative_directory(
    accepted: AcceptedPaths,
    root_fd: int,
    relative: str,
    error_type: Type[ArchiveLedgerError],
) -> int:
    current = root_fd
    for component in relative.split("/") if relative else []:
        current = _open_directory_component(accepted, current, component, error_type)
    return current


def _accept_paths(
    download_root_value: Any,
    archive_value: Any,
    attempt_root_value: Any,
    candidate_parent_value: Any,
    require_private_parent: bool = True,
) -> AcceptedPaths:
    download_root = _canonical_absolute_path(download_root_value, InvalidInputPath)
    archive = _canonical_absolute_path(archive_value, InvalidInputPath)
    attempt_root = _canonical_absolute_path(attempt_root_value, InvalidInputPath)
    candidate_parent = _canonical_absolute_path(candidate_parent_value, InvalidOutputPath)
    if not _strictly_beneath(archive, download_root):
        _raise(InvalidInputPath, "archive-root")
    if not _strictly_beneath(candidate_parent, attempt_root):
        _raise(InvalidOutputPath, "candidate-root")
    if _paths_overlap(download_root, attempt_root):
        _raise(InputOverlap, "root-overlap")

    accepted = AcceptedPaths()
    try:
        download_fd = _open_absolute_directory(accepted, download_root, InputOpen)
        attempt_fd = _open_absolute_directory(accepted, attempt_root, InputOpen)
        candidate_relative = os.path.relpath(candidate_parent, attempt_root)
        candidate_fd = _walk_relative_directory(
            accepted, attempt_fd, candidate_relative, InvalidOutputPath
        )
        try:
            candidate_stat = os.fstat(candidate_fd)
        except OSError:
            _raise(InvalidOutputPath, "candidate-parent-fstat")
        if require_private_parent and stat.S_IMODE(candidate_stat.st_mode) != 0o700:
            _raise(InvalidOutputPath, "candidate-parent-mode")

        archive_relative = os.path.relpath(archive, download_root)
        components = archive_relative.split("/")
        archive_parent_fd = _walk_relative_directory(
            accepted, download_fd, "/".join(components[:-1]), InputOpen
        )
        terminal = components[-1]
        try:
            _checkpoint("archive-before-stat")
            before = os.stat(terminal, dir_fd=archive_parent_fd, follow_symlinks=False)
            _checkpoint("archive-after-stat")
        except OSError:
            _raise(InputOpen, "archive-stat")
        if stat.S_ISLNK(before.st_mode):
            _raise(InputOpen, "archive-symlink")
        try:
            _checkpoint("archive-before-open")
            archive_fd = os.open(
                terminal,
                os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=archive_parent_fd,
            )
            accepted.keep(archive_fd)
            _checkpoint("archive-after-open")
        except OSError:
            _raise(InputOpen, "archive-open")
        try:
            after = os.fstat(archive_fd)
        except OSError:
            _raise(InputOpen, "archive-fstat")
        _checkpoint("archive-after-fstat")
        if not stat.S_ISREG(after.st_mode):
            _raise(InputNotRegular, "archive-type")
        if _identity_tuple(before) != _identity_tuple(after):
            _raise(InputIdentityDrift, "archive-open-race")
        accepted.links.append((archive_parent_fd, terminal, archive_fd, _identity_tuple(after)))
        accepted.archive_fd = archive_fd
        accepted.archive_stat = after
        accepted.candidate_parent_fd = candidate_fd
        accepted.candidate_parent = candidate_parent
        accepted.verify_unchanged()
        return accepted
    except Exception:
        accepted.close()
        raise


def validate_input_paths_for_test(
    download_root: Any,
    archive: Any,
    attempt_root: Any,
    candidate_parent: Any,
) -> Dict[str, Any]:
    """Hermetic descriptor acceptance injection; it does not apply asset pins."""
    accepted = _accept_paths(download_root, archive, attempt_root, candidate_parent)
    try:
        accepted.verify_unchanged()
        archive_stat = accepted.archive_stat
        if archive_stat is None:
            raise AssertionError("missing archive stat")
        return {
            "archive_device": archive_stat.st_dev,
            "archive_inode": archive_stat.st_ino,
            "archive_byte_length": archive_stat.st_size,
        }
    finally:
        accepted.close()


def _read_fd_all(fd: int, byte_limit: int) -> bytes:
    chunks: List[bytes] = []
    total = 0
    while True:
        try:
            chunk = os.read(fd, min(READ_CHUNK_BYTES, byte_limit + 1 - total))
        except OSError:
            _raise(OutputPublication, "artifact-read")
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > byte_limit:
            _raise(OutputPublication, "artifact-size")
        chunks.append(chunk)


def _read_named_regular(directory_fd: int, name: str, byte_limit: int) -> bytes:
    try:
        before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except OSError:
        _raise(OutputPublication, "artifact-stat")
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        _raise(OutputPublication, "artifact-type")
    if stat.S_IMODE(before.st_mode) != 0o600:
        _raise(OutputPublication, "artifact-mode")
    try:
        fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory_fd)
    except OSError:
        _raise(OutputPublication, "artifact-open")
    try:
        try:
            after = os.fstat(fd)
        except OSError:
            _raise(OutputPublication, "artifact-fstat")
        if _identity_tuple(before) != _identity_tuple(after):
            _raise(OutputPublication, "artifact-race")
        data = _read_fd_all(fd, byte_limit)
        if len(data) != after.st_size:
            _raise(OutputPublication, "artifact-short-read")
        return data
    finally:
        _close_descriptor(fd, OutputPublication, "artifact-close")


def _strict_json_line(
    data: bytes,
    expected_keys: Set[str],
    allow_signed: bool = False,
) -> Dict[str, Any]:
    if not data.endswith(b"\n") or data.count(b"\n") != 1:
        _raise(OutputPublication, "json-line-framing")
    try:
        value = strict_json_object(data[:-1], expected_keys, allow_signed=allow_signed)
    except OutputWrite as error:
        _raise(OutputPublication, error.diagnostic)
    return value


def _strict_jsonl(data: bytes, inventory: bool) -> List[Dict[str, Any]]:
    if not data or not data.endswith(b"\n"):
        _raise(OutputPublication, "jsonl-framing")
    rows: List[Dict[str, Any]] = []
    for index, line in enumerate(data.splitlines()):
        try:
            provisional = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _raise(OutputPublication, "jsonl-decode")
        if not isinstance(provisional, dict):
            _raise(OutputPublication, "jsonl-object")
        kind = provisional.get("row_kind")
        if index == 0:
            keys = LEDGER_HEADER_KEYS
        elif inventory:
            keys = INVENTORY_MEMBER_KEYS
        elif kind == "tar_header":
            keys = TAR_HEADER_KEYS
        elif kind == "tar_terminator":
            keys = TAR_TERMINATOR_KEYS
        elif kind == "tar_trailing_padding":
            keys = TAR_TRAILING_KEYS
        elif kind == "gzip_member":
            keys = GZIP_MEMBER_KEYS
        else:
            _raise(OutputPublication, "jsonl-row-kind")
        try:
            row = strict_json_object(line, keys)
        except OutputWrite as error:
            _raise(OutputPublication, error.diagnostic)
        if row.get("row_index") != index:
            _raise(OutputPublication, "jsonl-row-index")
        rows.append(row)
    expected_schema = (
        "hsai-p01b-ordered-logical-member-inventory-v1"
        if inventory
        else "hsai-p01b-gzip-tar-header-ledger-v1"
    )
    if rows[0] != {
        "schema": expected_schema,
        "row_kind": "ledger_header",
        "row_index": 0,
        "contract_digest": CONTRACT_DIGEST,
    }:
        _raise(OutputPublication, "ledger-header")
    if inventory:
        for archive_index, row in enumerate(rows[1:]):
            if row.get("row_kind") != "logical_member" or row.get("archive_index") != archive_index:
                _raise(OutputPublication, "inventory-order")
    else:
        kinds = [row.get("row_kind") for row in rows]
        if len(rows) < 4 or kinds[-3:] != ["tar_terminator", "tar_trailing_padding", "gzip_member"]:
            _raise(OutputPublication, "header-ledger-order")
        if any(kind != "tar_header" for kind in kinds[1:-3]):
            _raise(OutputPublication, "header-ledger-order")
    return rows


def _require_u64(value: Any, diagnostic: str) -> int:
    if type(value) is not int or value < 0 or value > U64_MAX:
        _raise(OutputPublication, diagnostic)
    return value


def _require_i64(value: Any, diagnostic: str) -> int:
    if type(value) is not int or value < -(1 << 63) or value > (1 << 63) - 1:
        _raise(OutputPublication, diagnostic)
    return value


def _require_bool(value: Any, diagnostic: str) -> bool:
    if type(value) is not bool:
        _raise(OutputPublication, diagnostic)
    return value


def _require_ascii(value: Any, diagnostic: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not allow_empty):
        _raise(OutputPublication, diagnostic)
    if any(ord(character) < 0x20 or ord(character) > 0x7E for character in value):
        _raise(OutputPublication, diagnostic)
    return value


def _require_hex(value: Any, diagnostic: str, length: Optional[int] = None) -> str:
    if not isinstance(value, str) or len(value) % 2 or (length is not None and len(value) != length):
        _raise(OutputPublication, diagnostic)
    if any(character not in "0123456789abcdef" for character in value):
        _raise(OutputPublication, diagnostic)
    return value


def _require_sha256(value: Any, diagnostic: str) -> str:
    return _require_hex(value, diagnostic, 64)


def _validate_manifest_types(manifest: Dict[str, Any]) -> None:
    signed_fields = {"archive_modified_seconds", "archive_changed_seconds"}
    bool_fields = {
        "release_immutable", "candidate_only", "accepted", "phase_797_authorized",
        "materialization_authorized", "capture_authorized", "accepted_evidence_authorized",
    }
    list_fields = {"top_level"}
    string_fields = {
        "schema", "asset_id", "url", "filename", "tag_commit",
        "expected_archive_sha256", "contract_digest", "parser_source_sha256",
        "python_version", "zlib_version", "archive_sha256", "legacy_inventory_sha256",
        "embedded_lean_sha256", "header_ledger_sha256", "inventory_ledger_sha256",
    }
    u64_fields = MANIFEST_KEYS - signed_fields - bool_fields - list_fields - string_fields
    for key in signed_fields:
        _require_i64(manifest[key], "manifest-signed-integer")
    for key in bool_fields:
        _require_bool(manifest[key], "manifest-bool")
    for key in string_fields:
        _require_ascii(manifest[key], "manifest-ascii", allow_empty=False)
    for key in u64_fields:
        _require_u64(manifest[key], "manifest-u64")
    for key in (
        "expected_archive_sha256", "contract_digest", "parser_source_sha256", "archive_sha256",
        "legacy_inventory_sha256", "embedded_lean_sha256", "header_ledger_sha256",
        "inventory_ledger_sha256",
    ):
        _require_sha256(manifest[key], "manifest-sha256")
    _require_hex(manifest["tag_commit"], "manifest-tag-commit", 40)
    for key in ("archive_modified_nanoseconds", "archive_changed_nanoseconds"):
        if _require_u64(manifest[key], "manifest-nanoseconds") > 999_999_999:
            _raise(OutputPublication, "manifest-nanoseconds")
    top_level = manifest["top_level"]
    if not isinstance(top_level, list) or top_level != sorted(set(top_level)):
        _raise(OutputPublication, "manifest-top-level")
    for item in top_level:
        _require_ascii(item, "manifest-top-level")
    if manifest["expected_compressed_bytes"] != manifest["archive_byte_length"]:
        _raise(OutputPublication, "manifest-expected-length")
    if manifest["expected_archive_sha256"] != manifest["archive_sha256"]:
        _raise(OutputPublication, "manifest-expected-digest")
    if manifest["parser_source_sha256"] != _parser_source_sha256():
        _raise(OutputPublication, "manifest-parser-source")


def _validate_status_types(status: Dict[str, Any]) -> None:
    if status["schema"] != "hsai-p01b-archive-ledger-capture-status-v1":
        _raise(OutputPublication, "status-schema")
    if status["decision"] != "candidate_generated" or status["declared_files"] != DECLARED_FILES:
        _raise(OutputPublication, "status-decision")
    for key in (
        "manifest_bytes", "header_ledger_bytes", "inventory_ledger_bytes",
    ):
        _require_u64(status[key], "status-u64")
    for key in ("manifest_sha256", "header_ledger_sha256", "inventory_ledger_sha256"):
        _require_sha256(status[key], "status-sha256")
    for key in (
        "candidate_only", "accepted", "phase_797_authorized", "materialization_authorized",
        "capture_authorized", "accepted_evidence_authorized",
    ):
        _require_bool(status[key], "status-bool")


def _validate_ledger_rows(rows: List[Dict[str, Any]], inventory: bool) -> None:
    for row in rows:
        for key, value in row.items():
            if key in LEDGER_U64_FIELDS:
                _require_u64(value, "ledger-u64")
            elif key.endswith("_present"):
                _require_bool(value, "ledger-bool")
            elif key.endswith("_sha256") or key in {
                "contract_digest", "first_zero_sha256", "second_zero_sha256",
            }:
                _require_sha256(value, "ledger-sha256")
            elif key.endswith("_hex"):
                _require_hex(value, "ledger-hex")
    if inventory:
        for row in rows[1:]:
            if row["schema"] != "hsai-p01b-archive-logical-member-v1":
                _raise(OutputPublication, "inventory-schema")
            if row["kind"] not in ("regular", "directory"):
                _raise(OutputPublication, "inventory-kind")
            _require_ascii(row["effective_raw_name"], "inventory-name")
            _require_ascii(row["collision_key"], "inventory-collision-key")
            _require_hex(row["raw_name_hex"], "inventory-raw-name", 200)
            indices = row["extension_header_indices"]
            if not isinstance(indices, list) or len(indices) > 1:
                _raise(OutputPublication, "inventory-extension-indices")
            for value in indices:
                _require_u64(value, "inventory-extension-index")
        return

    physical_index = 0
    extension_payload_total = 0
    for row in rows[1:-3]:
        if row["schema"] != "hsai-p01b-tar-header-v1" or row["physical_header_index"] != physical_index:
            _raise(OutputPublication, "tar-header-index")
        physical_index += 1
        _require_hex(row["raw_header_hex"], "tar-raw-header", 1024)
        raw_header = bytes.fromhex(row["raw_header_hex"])
        if sha256_hex(raw_header) != row["raw_header_sha256"]:
            _raise(OutputPublication, "tar-header-digest")
        expected_hex_slices = {
            "raw_name_hex": (0, 100), "raw_mode_hex": (100, 108),
            "raw_uid_hex": (108, 116), "raw_gid_hex": (116, 124),
            "raw_size_hex": (124, 136), "raw_mtime_hex": (136, 148),
            "raw_checksum_hex": (148, 156), "raw_typeflag_hex": (156, 157),
            "raw_linkname_hex": (157, 257), "raw_magic_hex": (257, 263),
            "raw_version_hex": (263, 265), "raw_uname_hex": (265, 297),
            "raw_gname_hex": (297, 329), "raw_devmajor_hex": (329, 337),
            "raw_devminor_hex": (337, 345), "raw_prefix_hex": (345, 500),
            "raw_padding_hex": (500, 512),
        }
        for key, (start, end) in expected_hex_slices.items():
            _require_hex(row[key], "tar-field-hex", (end - start) * 2)
            if row[key] != raw_header[start:end].hex():
                _raise(OutputPublication, "tar-field-binding")
        try:
            parsed = _header_fields(raw_header)
        except ArchiveLedgerError as error:
            _raise(OutputPublication, "tar-header-" + error.failure_class)
        parsed_values = parsed["values"]
        expected_values = {
            "base_name": parsed["base_name"], "prefix": parsed["prefix"],
            "member_type": parsed["member_type"], "parsed_mode": parsed_values["mode"],
            "parsed_uid": parsed_values["uid"], "parsed_gid": parsed_values["gid"],
            "parsed_size": parsed_values["size"], "parsed_mtime": parsed_values["mtime"],
            "parsed_checksum": parsed_values["checksum"],
            "parsed_devmajor": parsed_values["devmajor"],
            "parsed_devminor": parsed_values["devminor"],
        }
        for key, value in expected_values.items():
            if row[key] != value:
                _raise(OutputPublication, "tar-parsed-binding")
        if row["member_type"] not in ("regular", "directory", "pax_path", "gnu_long_name"):
            _raise(OutputPublication, "tar-member-type")
        if row["parsed_size"] > MAX_MEMBER_BYTES:
            _raise(OutputPublication, "tar-member-size-limit")
        if row["checksum_variant"] != "unsigned-posix-v1":
            _raise(OutputPublication, "tar-checksum-variant")
        is_extension = row["member_type"] in ("pax_path", "gnu_long_name")
        if row["extension_payload_present"] is not is_extension:
            _raise(OutputPublication, "tar-extension-presence")
        if row["applies_to_archive_index_present"] is not is_extension:
            _raise(OutputPublication, "tar-extension-index-presence")
        if row["data_bytes"] != (0 if row["member_type"] == "directory" else row["parsed_size"]):
            _raise(OutputPublication, "tar-data-bytes")
        if row["data_padding_bytes"] != (-row["parsed_size"]) % BLOCK_BYTES:
            _raise(OutputPublication, "tar-padding-bytes")
        expected_padding_digest = sha256_hex(b"\0" * row["data_padding_bytes"])
        if row["data_padding_sha256"] != expected_padding_digest:
            _raise(OutputPublication, "tar-padding-digest")
        if len(row["extension_payload_hex"]) > MAX_EXTENSION_PAYLOAD_BYTES * 2:
            _raise(OutputPublication, "tar-extension-payload-limit")
        payload = bytes.fromhex(row["extension_payload_hex"])
        if is_extension:
            if row["extension_payload_bytes"] != len(payload) or row["extension_payload_sha256"] != sha256_hex(payload):
                _raise(OutputPublication, "tar-extension-binding")
            extension_payload_total = checked_add(
                extension_payload_total,
                len(payload),
                MAX_EXTENSION_PAYLOAD_BYTES_TOTAL,
                OutputPublication,
            )
        elif (
            row["extension_payload_bytes"] != 0
            or row["extension_payload_hex"] != ""
            or row["extension_payload_sha256"] != EMPTY_SHA256
            or row["applies_to_archive_index"] != 0
        ):
            _raise(OutputPublication, "tar-extension-absence")
    terminator, trailing, gzip_row = rows[-3:]
    if terminator["schema"] != "hsai-p01b-tar-terminator-v1":
        _raise(OutputPublication, "terminator-schema")
    if trailing["schema"] != "hsai-p01b-tar-trailing-padding-v1":
        _raise(OutputPublication, "trailing-schema")
    physical_rows = rows[1:-3]
    expected_terminator_offset = 0
    if physical_rows:
        last = physical_rows[-1]
        expected_terminator_offset = (
            last["data_offset"] + last["data_bytes"] + last["data_padding_bytes"]
        )
    if (
        terminator["first_zero_byte_offset"] != expected_terminator_offset
        or terminator["first_zero_block_index"] * BLOCK_BYTES != expected_terminator_offset
        or terminator["second_zero_byte_offset"] != expected_terminator_offset + BLOCK_BYTES
        or terminator["second_zero_block_index"] * BLOCK_BYTES != expected_terminator_offset + BLOCK_BYTES
        or terminator["first_zero_sha256"] != ZERO_BLOCK_SHA256
        or terminator["second_zero_sha256"] != ZERO_BLOCK_SHA256
    ):
        _raise(OutputPublication, "terminator-binding")
    if trailing["uncompressed_byte_offset"] != expected_terminator_offset + (2 * BLOCK_BYTES):
        _raise(OutputPublication, "trailing-offset")
    if trailing["padding_bytes"] > MAX_TRAILING_ZERO_BYTES:
        _raise(OutputPublication, "trailing-zero-limit")
    if trailing["padding_sha256"] != sha256_hex(b"\0" * trailing["padding_bytes"]):
        _raise(OutputPublication, "trailing-digest")
    if gzip_row["schema"] != "hsai-p01b-gzip-member-v1":
        _raise(OutputPublication, "gzip-schema")
    _require_hex(gzip_row["fixed_header_hex"], "gzip-fixed-header", 20)
    _require_hex(gzip_row["trailer_hex"], "gzip-trailer", 16)
    if gzip_row["member_index"] != 0 or gzip_row["compressed_start"] != 0:
        _raise(OutputPublication, "gzip-index")
    if (gzip_row["id1"], gzip_row["id2"], gzip_row["cm"]) != (31, 139, 8):
        _raise(OutputPublication, "gzip-fixed-values")
    fixed_header = bytes.fromhex(gzip_row["fixed_header_hex"])
    if fixed_header[:3] != b"\x1f\x8b\x08" or fixed_header[3] != gzip_row["flg"]:
        _raise(OutputPublication, "gzip-fixed-header-binding")
    if gzip_row["flg"] > 0x1F or gzip_row["flg"] & 0xE0:
        _raise(OutputPublication, "gzip-reserved-flags")
    if struct.unpack("<I", fixed_header[4:8])[0] != gzip_row["mtime"]:
        _raise(OutputPublication, "gzip-mtime-binding")
    if fixed_header[8] != gzip_row["xfl"] or fixed_header[9] != gzip_row["os"]:
        _raise(OutputPublication, "gzip-platform-binding")
    optional_fields = (
        ("fextra", 0x04), ("fname", 0x08), ("fcomment", 0x10),
    )
    optional_payloads: Dict[str, bytes] = {}
    for prefix, flag in optional_fields:
        present = bool(gzip_row["flg"] & flag)
        if gzip_row[prefix + "_present"] is not present:
            _raise(OutputPublication, "gzip-option-presence")
        option_limit = {
            "fextra": MAX_GZIP_EXTRA_BYTES,
            "fname": MAX_GZIP_FILENAME_BYTES,
            "fcomment": MAX_GZIP_COMMENT_BYTES,
        }[prefix]
        if len(gzip_row[prefix + "_hex"]) > option_limit * 2:
            _raise(OutputPublication, "gzip-option-limit")
        payload = bytes.fromhex(gzip_row[prefix + "_hex"])
        optional_payloads[prefix] = payload
        if gzip_row[prefix + "_bytes"] != len(payload) or gzip_row[prefix + "_sha256"] != sha256_hex(payload):
            _raise(OutputPublication, "gzip-option-binding")
        if not present and payload:
            _raise(OutputPublication, "gzip-option-absence")
    header_crc_material = bytearray(fixed_header)
    optional_total = 0
    if gzip_row["fextra_present"]:
        if len(gzip_row["fextra_xlen_hex"]) != 4:
            _raise(OutputPublication, "gzip-extra-length")
        xlen_raw = bytes.fromhex(gzip_row["fextra_xlen_hex"])
        fextra = optional_payloads["fextra"]
        if (
            len(xlen_raw) != 2
            or struct.unpack("<H", xlen_raw)[0] != len(fextra)
            or len(fextra) > MAX_GZIP_EXTRA_BYTES
        ):
            _raise(OutputPublication, "gzip-extra-length")
        optional_total = checked_add(
            optional_total,
            len(fextra),
            MAX_GZIP_OPTIONAL_BYTES_TOTAL,
            OutputPublication,
        )
        try:
            _validate_gzip_extra(fextra)
        except ArchiveLedgerError as error:
            _raise(OutputPublication, "gzip-extra-" + error.failure_class)
        header_crc_material.extend(xlen_raw)
        header_crc_material.extend(fextra)
    elif gzip_row["fextra_xlen_hex"] != "":
        _raise(OutputPublication, "gzip-extra-absence")
    for prefix, limit in (
        ("fname", MAX_GZIP_FILENAME_BYTES),
        ("fcomment", MAX_GZIP_COMMENT_BYTES),
    ):
        if gzip_row[prefix + "_present"]:
            payload = optional_payloads[prefix]
            if len(payload) > limit or b"\0" in payload:
                _raise(OutputPublication, "gzip-option-string")
            optional_total = checked_add(
                optional_total,
                len(payload),
                MAX_GZIP_OPTIONAL_BYTES_TOTAL,
                OutputPublication,
            )
            header_crc_material.extend(payload)
            header_crc_material.extend(b"\0")
    if gzip_row["fhcrc_present"] is not bool(gzip_row["flg"] & 0x02):
        _raise(OutputPublication, "gzip-hcrc-presence")
    if gzip_row["fhcrc_present"]:
        if len(gzip_row["fhcrc_hex"]) != 4:
            _raise(OutputPublication, "gzip-hcrc-binding")
        raw_hcrc = bytes.fromhex(gzip_row["fhcrc_hex"])
        if (
            len(raw_hcrc) != 2
            or struct.unpack("<H", raw_hcrc)[0] != gzip_row["fhcrc16"]
            or (zlib.crc32(bytes(header_crc_material)) & 0xFFFF) != gzip_row["fhcrc16"]
        ):
            _raise(OutputPublication, "gzip-hcrc-binding")
    elif gzip_row["fhcrc_hex"] != "" or gzip_row["fhcrc16"] != 0:
        _raise(OutputPublication, "gzip-hcrc-absence")
    if gzip_row["deflate_offset"] != len(header_crc_material) + (
        2 if gzip_row["fhcrc_present"] else 0
    ):
        _raise(OutputPublication, "gzip-deflate-offset")
    if gzip_row["trailer_offset"] != gzip_row["deflate_offset"] + gzip_row["deflate_bytes"]:
        _raise(OutputPublication, "gzip-deflate-range")
    if gzip_row["compressed_end"] != gzip_row["trailer_offset"] + 8:
        _raise(OutputPublication, "gzip-member-range")
    trailer_crc, trailer_size = struct.unpack("<II", bytes.fromhex(gzip_row["trailer_hex"]))
    if trailer_crc != gzip_row["trailer_crc32"] or trailer_size != gzip_row["trailer_isize"]:
        _raise(OutputPublication, "gzip-trailer-binding")
    if gzip_row["trailer_isize"] != gzip_row["uncompressed_bytes"] % (1 << 32):
        _raise(OutputPublication, "gzip-isize-binding")
    if gzip_row["uncompressed_bytes"] != trailing["uncompressed_byte_offset"] + trailing["padding_bytes"]:
        _raise(OutputPublication, "gzip-uncompressed-range")


def _validate_authority_fields(value: Dict[str, Any]) -> None:
    expected = {
        "candidate_only": True,
        "accepted": False,
        "phase_797_authorized": False,
        "materialization_authorized": False,
        "capture_authorized": False,
        "accepted_evidence_authorized": False,
    }
    for key, required in expected.items():
        if value.get(key) is not required:
            _raise(OutputPublication, "authority-ceiling")


def _validate_candidate_fd(
    candidate_fd: int,
    allow_synthetic: bool = False,
) -> Dict[str, Any]:
    try:
        names = sorted(os.listdir(candidate_fd))
    except OSError:
        _raise(OutputPublication, "candidate-list")
    if names != DECLARED_FILES:
        _raise(OutputPublication, "declared-file-set")
    manifest_data = _read_named_regular(candidate_fd, MANIFEST_FILENAME, MAX_MANIFEST_BYTES)
    header_data = _read_named_regular(candidate_fd, HEADER_LEDGER_FILENAME, MAX_HEADER_LEDGER_BYTES)
    inventory_data = _read_named_regular(
        candidate_fd, INVENTORY_LEDGER_FILENAME, MAX_INVENTORY_LEDGER_BYTES
    )
    status_data = _read_named_regular(candidate_fd, STATUS_FILENAME, MAX_STATUS_BYTES)
    manifest = _strict_json_line(manifest_data, MANIFEST_KEYS, allow_signed=True)
    status = _strict_json_line(status_data, STATUS_KEYS)
    header_rows = _strict_jsonl(header_data, inventory=False)
    inventory_rows = _strict_jsonl(inventory_data, inventory=True)
    _validate_manifest_types(manifest)
    _validate_status_types(status)
    _validate_ledger_rows(header_rows, inventory=False)
    _validate_ledger_rows(inventory_rows, inventory=True)
    expected_asset_authority = (
        {
            "asset_id": "synthetic-test-only",
            "url": "synthetic:test-only",
            "release_id": 0,
            "github_asset_id": 0,
            "filename": "synthetic.tar.gz",
            "tag_commit": "0" * 40,
            "expected_compressed_bytes": manifest["archive_byte_length"],
            "expected_archive_sha256": manifest["archive_sha256"],
            "release_immutable": False,
        }
        if allow_synthetic
        else {
            "asset_id": ASSET_ID,
            "url": ASSET_URL,
            "release_id": RELEASE_ID,
            "github_asset_id": GITHUB_ASSET_ID,
            "filename": ARCHIVE_FILENAME,
            "tag_commit": TAG_COMMIT,
            "expected_compressed_bytes": EXPECTED_COMPRESSED_BYTES,
            "expected_archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "release_immutable": RELEASE_IMMUTABLE,
        }
    )
    for key, expected in expected_asset_authority.items():
        if manifest.get(key) != expected:
            _raise(OutputPublication, "manifest-asset-authority")
    authority = {
        "candidate_only": True,
        "accepted": False,
        "phase_797_authorized": False,
        "materialization_authorized": False,
        "capture_authorized": False,
        "accepted_evidence_authorized": False,
    }
    _validate_authority_fields(manifest)
    _validate_authority_fields(status)
    expected_status = {
        "schema": "hsai-p01b-archive-ledger-capture-status-v1",
        "decision": "candidate_generated",
        "declared_files": DECLARED_FILES,
        "manifest_bytes": len(manifest_data),
        "manifest_sha256": sha256_hex(manifest_data),
        "header_ledger_bytes": len(header_data),
        "header_ledger_sha256": sha256_hex(header_data),
        "inventory_ledger_bytes": len(inventory_data),
        "inventory_ledger_sha256": sha256_hex(inventory_data),
        **authority,
    }
    if status != expected_status:
        _raise(OutputPublication, "status-binding")
    if manifest.get("schema") != "hsai-p01b-archive-source-manifest-v1":
        _raise(OutputPublication, "manifest-schema")
    if manifest.get("contract_digest") != CONTRACT_DIGEST:
        _raise(OutputPublication, "manifest-contract")
    if manifest.get("header_ledger_bytes") != len(header_data) or manifest.get(
        "header_ledger_sha256"
    ) != sha256_hex(header_data):
        _raise(OutputPublication, "manifest-header-binding")
    if manifest.get("inventory_ledger_bytes") != len(inventory_data) or manifest.get(
        "inventory_ledger_sha256"
    ) != sha256_hex(inventory_data):
        _raise(OutputPublication, "manifest-inventory-binding")
    if manifest.get("gzip_members") != 1:
        _raise(OutputPublication, "manifest-gzip-count")
    if manifest.get("physical_tar_headers") != len(header_rows) - 4:
        _raise(OutputPublication, "manifest-header-count")
    if manifest.get("logical_members") != len(inventory_rows) - 1:
        _raise(OutputPublication, "manifest-member-count")
    gzip_row = header_rows[-1]
    physical_rows = header_rows[1:-3]
    members = inventory_rows[1:]
    if len(physical_rows) > MAX_PHYSICAL_TAR_HEADERS:
        _raise(OutputPublication, "physical-header-limit")
    if len(members) > MAX_LOGICAL_MEMBERS:
        _raise(OutputPublication, "logical-member-limit")
    extension_header_count = sum(
        row["member_type"] in ("pax_path", "gnu_long_name")
        for row in physical_rows
    )
    if extension_header_count > MAX_EXTENSION_HEADERS:
        _raise(OutputPublication, "extension-header-limit")
    if gzip_row["uncompressed_bytes"] > MAX_UNCOMPRESSED_TAR_BYTES:
        _raise(OutputPublication, "uncompressed-tar-limit")
    if header_rows[-2]["padding_bytes"] > MAX_TRAILING_ZERO_BYTES:
        _raise(OutputPublication, "trailing-zero-limit")
    if (
        manifest["archive_byte_length"] == 0
        or gzip_row["uncompressed_bytes"]
        > manifest["archive_byte_length"] * MAX_COMPRESSION_RATIO
    ):
        _raise(OutputPublication, "compression-ratio-limit")
    regular_members = 0
    directory_members = 0
    aggregate_regular_bytes = 0
    largest_member_bytes = 0
    top_level: Set[str] = set()
    legacy_rows: List[Sequence[Any]] = []
    embedded_lean_bytes = 0
    embedded_lean_sha256 = EMPTY_SHA256
    raw_names: Set[str] = set()
    effective_names: Set[str] = set()
    collision_kinds: Dict[str, str] = {}
    used_logical_headers: Set[int] = set()
    used_extension_headers: Set[int] = set()
    for member in members:
        physical_index = member["physical_header_index"]
        if physical_index >= len(physical_rows):
            _raise(OutputPublication, "inventory-physical-index")
        physical = physical_rows[physical_index]
        if physical_index in used_logical_headers:
            _raise(OutputPublication, "inventory-duplicate-physical-index")
        used_logical_headers.add(physical_index)
        if physical["member_type"] not in ("regular", "directory"):
            _raise(OutputPublication, "inventory-physical-type")
        if (
            member["raw_name_hex"] != physical["raw_name_hex"]
            or member["kind"] != physical["member_type"]
            or member["member_size"] != physical["parsed_size"]
            or member["data_offset"] != physical["data_offset"]
            or member["data_padding_bytes"] != physical["data_padding_bytes"]
        ):
            _raise(OutputPublication, "inventory-physical-binding")
        extension_indices = member["extension_header_indices"]
        raw_base = (
            physical["prefix"] + "/" + physical["base_name"]
            if physical["prefix"]
            else physical["base_name"]
        )
        if raw_base in raw_names:
            _raise(OutputPublication, "inventory-duplicate-raw-name")
        raw_names.add(raw_base)
        expected_effective_raw = raw_base.encode("ascii")
        if extension_indices:
            extension_index = extension_indices[0]
            if extension_index >= len(physical_rows):
                _raise(OutputPublication, "inventory-extension-index")
            extension = physical_rows[extension_index]
            if (
                extension["member_type"] not in ("pax_path", "gnu_long_name")
                or extension_index + 1 != physical_index
                or extension["applies_to_archive_index"] != member["archive_index"]
            ):
                _raise(OutputPublication, "inventory-extension-binding")
            if extension_index in used_extension_headers:
                _raise(OutputPublication, "inventory-duplicate-extension-index")
            used_extension_headers.add(extension_index)
            extension_payload = bytes.fromhex(extension["extension_payload_hex"])
            try:
                expected_effective_raw = (
                    parse_pax_path(extension_payload)
                    if extension["member_type"] == "pax_path"
                    else parse_gnu_long_name(extension_payload)
                )
            except ArchiveLedgerError as error:
                _raise(OutputPublication, "inventory-extension-" + error.failure_class)
        try:
            effective_name, collision_key = validate_effective_path(
                expected_effective_raw, member["kind"]
            )
        except ArchiveLedgerError as error:
            _raise(OutputPublication, "inventory-path-" + error.failure_class)
        if effective_name != member["effective_raw_name"] or collision_key != member["collision_key"]:
            _raise(OutputPublication, "inventory-path-binding")
        if effective_name in effective_names:
            _raise(OutputPublication, "inventory-duplicate-effective-name")
        effective_names.add(effective_name)
        previous_kind = collision_kinds.get(collision_key)
        if previous_kind is not None:
            if previous_kind != member["kind"]:
                _raise(OutputPublication, "inventory-file-directory-collision")
            _raise(OutputPublication, "inventory-duplicate-collision-key")
        parts = collision_key.split("/")
        for index in range(1, len(parts)):
            if collision_kinds.get("/".join(parts[:index])) == "regular":
                _raise(OutputPublication, "inventory-regular-ancestor")
        if member["kind"] == "regular":
            prefix = collision_key + "/"
            if any(existing.startswith(prefix) for existing in collision_kinds):
                _raise(OutputPublication, "inventory-regular-becomes-ancestor")
        collision_kinds[collision_key] = member["kind"]
        if member["kind"] == "regular":
            regular_members += 1
            if member["member_size"] > MAX_MEMBER_BYTES:
                _raise(OutputPublication, "member-size-limit")
            aggregate_regular_bytes = checked_add(
                aggregate_regular_bytes,
                member["member_size"],
                MAX_AGGREGATE_REGULAR_BYTES,
                OutputPublication,
            )
            if aggregate_regular_bytes > MAX_TOTAL_EXTRACTION_OUTPUT_BYTES:
                _raise(OutputPublication, "total-extraction-output-limit")
            largest_member_bytes = max(largest_member_bytes, member["member_size"])
        else:
            directory_members += 1
            if member["content_sha256"] != EMPTY_SHA256:
                _raise(OutputPublication, "inventory-directory-digest")
        top_level.add(collision_key.split("/", 1)[0])
        legacy_rows.append(
            [member["archive_index"], effective_name, collision_key, member["kind"], member["member_size"]]
        )
        if collision_key == EMBEDDED_LEAN_PATH:
            embedded_lean_bytes = member["member_size"]
            embedded_lean_sha256 = member["content_sha256"]
    expected_logical_headers = {
        index
        for index, row in enumerate(physical_rows)
        if row["member_type"] in ("regular", "directory")
    }
    expected_extension_headers = set(range(len(physical_rows))) - expected_logical_headers
    if used_logical_headers != expected_logical_headers or used_extension_headers != expected_extension_headers:
        _raise(OutputPublication, "inventory-header-coverage")
    legacy_digest = hashlib.sha256()
    for row in sorted(legacy_rows):
        legacy_digest.update(_canonical_legacy_row(row))
    observed_bindings = {
        "regular_members": regular_members,
        "directory_members": directory_members,
        "extension_headers": extension_header_count,
        "uncompressed_tar_bytes": gzip_row["uncompressed_bytes"],
        "aggregate_regular_bytes": aggregate_regular_bytes,
        "largest_member_bytes": largest_member_bytes,
        "trailing_zero_bytes": header_rows[-2]["padding_bytes"],
        "top_level": sorted(top_level),
        "legacy_inventory_sha256": legacy_digest.hexdigest(),
        "embedded_lean_bytes": embedded_lean_bytes,
        "embedded_lean_sha256": embedded_lean_sha256,
        "root_count": 0,
    }
    for key, expected in observed_bindings.items():
        if manifest.get(key) != expected:
            _raise(OutputPublication, "manifest-observed-binding")
    if not allow_synthetic:
        try:
            require_pinned_profile(manifest)
        except ArchiveLedgerError as error:
            _raise(OutputPublication, "manifest-profile-" + error.failure_class)
    if gzip_row["compressed_end"] != manifest["archive_byte_length"]:
        _raise(OutputPublication, "gzip-compressed-length")
    if gzip_row["raw_member_sha256"] != manifest["archive_sha256"]:
        _raise(OutputPublication, "gzip-archive-digest")
    return status


def validate_published_candidate_for_test(candidate: Any) -> Dict[str, Any]:
    path = _canonical_absolute_path(candidate, InvalidOutputPath)
    accepted = AcceptedPaths()
    try:
        candidate_fd = _open_absolute_directory(accepted, path, OutputPublication)
        try:
            candidate_stat = os.fstat(candidate_fd)
        except OSError:
            _raise(OutputPublication, "candidate-fstat")
        if stat.S_IMODE(candidate_stat.st_mode) != 0o700:
            _raise(OutputPublication, "candidate-mode")
        accepted.verify_unchanged()
        return _validate_candidate_fd(candidate_fd, allow_synthetic=True)
    finally:
        accepted.close()


def _create_exclusive_file(directory_fd: int, name: str, data: bytes) -> None:
    _checkpoint("before-create:" + name)
    try:
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
    except OSError:
        try:
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError:
            _raise(OutputWrite, "artifact-create")
        _raise(OutputCollision, "artifact-exists")
    try:
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            _raise(OutputWrite, "artifact-chmod")
        _checkpoint("after-create:" + name)
        _checkpoint("before-write:" + name)
        write_all(fd, data)
        _checkpoint("after-write:" + name)
        try:
            _checkpoint("before-fsync:" + name)
            os.fsync(fd)
            _checkpoint("after-fsync:" + name)
        except OSError:
            _raise(OutputDurability, "artifact-fsync")
    finally:
        _close_descriptor(fd, OutputDurability, "artifact-close")


def _fsync_directory(fd: int, label: str) -> None:
    try:
        _checkpoint("before-directory-fsync:" + label)
        os.fsync(fd)
        _checkpoint("after-directory-fsync:" + label)
    except OSError:
        _raise(OutputDurability, "directory-fsync")


def _verify_candidate_directory_identity(
    parent_fd: int,
    candidate_fd: int,
    accepted_stable_identity: Tuple[int, ...],
) -> None:
    try:
        entry = os.stat(CANDIDATE_DIRECTORY, dir_fd=parent_fd, follow_symlinks=False)
        opened = os.fstat(candidate_fd)
    except OSError:
        _raise(OutputPublication, "candidate-identity-stat")
    entry_identity = _identity_tuple(entry)
    opened_identity = _identity_tuple(opened)
    if (
        not stat.S_ISDIR(entry.st_mode)
        or stat.S_ISLNK(entry.st_mode)
        or entry_identity != opened_identity
        or _candidate_stable_identity(entry) != accepted_stable_identity
    ):
        _raise(OutputPublication, "candidate-identity-drift")


def _candidate_stable_identity(value: os.stat_result) -> Tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_gid)


def _cleanup_candidate(
    parent_fd: int,
    candidate_fd: int,
    accepted_stable_identity: Tuple[int, ...],
) -> None:
    _verify_candidate_directory_identity(parent_fd, candidate_fd, accepted_stable_identity)
    failed = False
    try:
        names = os.listdir(candidate_fd)
    except OSError:
        names = []
        failed = True
    for name in names:
        try:
            os.unlink(name, dir_fd=candidate_fd)
        except OSError:
            failed = True
    try:
        os.rmdir(CANDIDATE_DIRECTORY, dir_fd=parent_fd)
    except OSError:
        failed = True
    if failed:
        _raise(OutputPublication, "cleanup")


def _parser_source_sha256() -> str:
    try:
        fd = os.open(__file__, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError:
        _raise(OutputWrite, "parser-source-open")
    digest = hashlib.sha256()
    try:
        while True:
            try:
                data = os.read(fd, READ_CHUNK_BYTES)
            except OSError:
                _raise(OutputWrite, "parser-source-read")
            if not data:
                return digest.hexdigest()
            digest.update(data)
    finally:
        _close_descriptor(fd, OutputWrite, "parser-source-close")


def _split_timestamp_ns(value: int) -> Tuple[int, int]:
    seconds, nanoseconds = divmod(value, 1_000_000_000)
    return seconds, nanoseconds


def _stat_timestamp_ns(value: os.stat_result, nanosecond_name: str, second_name: str) -> int:
    nanoseconds = getattr(value, nanosecond_name, None)
    if nanoseconds is not None:
        return int(nanoseconds)
    return int(getattr(value, second_name)) * 1_000_000_000


def _build_manifest(
    observed: Dict[str, Any],
    header_data: bytes,
    inventory_data: bytes,
    archive_stat: os.stat_result,
    archive_digest: str,
    synthetic: bool,
) -> bytes:
    modified_seconds, modified_nanoseconds = _split_timestamp_ns(
        _stat_timestamp_ns(archive_stat, "st_mtime_ns", "st_mtime")
    )
    changed_seconds, changed_nanoseconds = _split_timestamp_ns(
        _stat_timestamp_ns(archive_stat, "st_ctime_ns", "st_ctime")
    )
    asset_id = "synthetic-test-only" if synthetic else ASSET_ID
    url = "synthetic:test-only" if synthetic else ASSET_URL
    manifest = {
        "schema": "hsai-p01b-archive-source-manifest-v1",
        "asset_id": asset_id,
        "url": url,
        "release_id": 0 if synthetic else RELEASE_ID,
        "github_asset_id": 0 if synthetic else GITHUB_ASSET_ID,
        "filename": "synthetic.tar.gz" if synthetic else ARCHIVE_FILENAME,
        "tag_commit": "0" * 40 if synthetic else TAG_COMMIT,
        "expected_compressed_bytes": archive_stat.st_size if synthetic else EXPECTED_COMPRESSED_BYTES,
        "expected_archive_sha256": archive_digest if synthetic else EXPECTED_ARCHIVE_SHA256,
        "release_immutable": False if synthetic else RELEASE_IMMUTABLE,
        "contract_digest": CONTRACT_DIGEST,
        "parser_source_sha256": _parser_source_sha256(),
        "python_version": sys.version.split()[0],
        "zlib_version": zlib.ZLIB_VERSION,
        "archive_device": archive_stat.st_dev,
        "archive_inode": archive_stat.st_ino,
        "archive_mode": archive_stat.st_mode,
        "archive_owner_uid": archive_stat.st_uid,
        "archive_link_count": archive_stat.st_nlink,
        "archive_byte_length": archive_stat.st_size,
        "archive_modified_seconds": modified_seconds,
        "archive_modified_nanoseconds": modified_nanoseconds,
        "archive_changed_seconds": changed_seconds,
        "archive_changed_nanoseconds": changed_nanoseconds,
        "archive_sha256": archive_digest,
        "gzip_members": observed["gzip_members"],
        "physical_tar_headers": observed["physical_tar_headers"],
        "logical_members": observed["logical_members"],
        "root_count": observed["root_count"],
        "regular_members": observed["regular_members"],
        "directory_members": observed["directory_members"],
        "extension_headers": observed["extension_headers"],
        "uncompressed_tar_bytes": observed["uncompressed_tar_bytes"],
        "aggregate_regular_bytes": observed["aggregate_regular_bytes"],
        "largest_member_bytes": observed["largest_member_bytes"],
        "trailing_zero_bytes": observed["trailing_zero_bytes"],
        "top_level": observed["top_level"],
        "legacy_inventory_sha256": observed["legacy_inventory_sha256"],
        "embedded_lean_bytes": observed["embedded_lean_bytes"],
        "embedded_lean_sha256": observed["embedded_lean_sha256"],
        "header_ledger_bytes": len(header_data),
        "header_ledger_sha256": sha256_hex(header_data),
        "inventory_ledger_bytes": len(inventory_data),
        "inventory_ledger_sha256": sha256_hex(inventory_data),
        "candidate_only": True,
        "accepted": False,
        "phase_797_authorized": False,
        "materialization_authorized": False,
        "capture_authorized": False,
        "accepted_evidence_authorized": False,
    }
    if set(manifest) != MANIFEST_KEYS:
        raise AssertionError("manifest field-set mismatch")
    data = _canonical_json_line_signed(manifest)
    if len(data) > MAX_MANIFEST_BYTES:
        _raise(CandidateByteLimit, "manifest")
    return data


def _build_status(manifest_data: bytes, header_data: bytes, inventory_data: bytes) -> bytes:
    status = {
        "schema": "hsai-p01b-archive-ledger-capture-status-v1",
        "decision": "candidate_generated",
        "declared_files": DECLARED_FILES,
        "manifest_bytes": len(manifest_data),
        "manifest_sha256": sha256_hex(manifest_data),
        "header_ledger_bytes": len(header_data),
        "header_ledger_sha256": sha256_hex(header_data),
        "inventory_ledger_bytes": len(inventory_data),
        "inventory_ledger_sha256": sha256_hex(inventory_data),
        "candidate_only": True,
        "accepted": False,
        "phase_797_authorized": False,
        "materialization_authorized": False,
        "capture_authorized": False,
        "accepted_evidence_authorized": False,
    }
    data = canonical_json_line(status)
    if len(data) > MAX_STATUS_BYTES:
        _raise(CandidateByteLimit, "status")
    return data


def _publish_candidate_bytes(
    parent_fd: int,
    candidate_parent: str,
    manifest_data: bytes,
    header_data: bytes,
    inventory_data: bytes,
    before_mutation_check: Optional[Any] = None,
    precommit_check: Optional[Any] = None,
    allow_synthetic_validation: bool = False,
) -> str:
    total = len(manifest_data) + len(header_data) + len(inventory_data)
    if total > MAX_TOTAL_CANDIDATE_BYTES:
        _raise(CandidateByteLimit, "candidate")
    candidate_fd = -1
    candidate_stable_identity: Tuple[int, ...] = ()
    created = False
    try:
        if before_mutation_check is not None:
            before_mutation_check()
        try:
            _checkpoint("before-candidate-mkdir")
            os.mkdir(CANDIDATE_DIRECTORY, 0o700, dir_fd=parent_fd)
            created = True
            _checkpoint("after-candidate-mkdir")
        except OSError:
            try:
                os.stat(CANDIDATE_DIRECTORY, dir_fd=parent_fd, follow_symlinks=False)
            except OSError:
                _raise(OutputWrite, "candidate-create")
            _raise(OutputCollision, "candidate-exists")
        try:
            candidate_fd = os.open(
                CANDIDATE_DIRECTORY,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=parent_fd,
            )
            os.fchmod(candidate_fd, 0o700)
            candidate_stable_identity = _candidate_stable_identity(os.fstat(candidate_fd))
        except OSError:
            _raise(OutputWrite, "candidate-open")
        _verify_candidate_directory_identity(
            parent_fd, candidate_fd, candidate_stable_identity
        )
        _create_exclusive_file(candidate_fd, HEADER_LEDGER_FILENAME, header_data)
        _create_exclusive_file(candidate_fd, INVENTORY_LEDGER_FILENAME, inventory_data)
        _strict_jsonl(_read_named_regular(candidate_fd, HEADER_LEDGER_FILENAME, MAX_HEADER_LEDGER_BYTES), False)
        _strict_jsonl(
            _read_named_regular(candidate_fd, INVENTORY_LEDGER_FILENAME, MAX_INVENTORY_LEDGER_BYTES), True
        )
        _create_exclusive_file(candidate_fd, MANIFEST_FILENAME, manifest_data)
        status_data = _build_status(manifest_data, header_data, inventory_data)
        if total + len(status_data) > MAX_TOTAL_CANDIDATE_BYTES:
            _raise(CandidateByteLimit, "candidate")
        _create_exclusive_file(candidate_fd, PENDING_STATUS_FILENAME, status_data)
        _fsync_directory(candidate_fd, "candidate-before-status-link")
        try:
            _checkpoint("before-status-link")
            if precommit_check is not None:
                precommit_check()
            _verify_candidate_directory_identity(
                parent_fd, candidate_fd, candidate_stable_identity
            )
            os.link(
                PENDING_STATUS_FILENAME,
                STATUS_FILENAME,
                src_dir_fd=candidate_fd,
                dst_dir_fd=candidate_fd,
                follow_symlinks=False,
            )
            _checkpoint("after-status-link")
        except OSError:
            _raise(OutputPublication, "status-link")
        _fsync_directory(candidate_fd, "candidate-after-status-link")
        _verify_candidate_directory_identity(
            parent_fd, candidate_fd, candidate_stable_identity
        )
        try:
            _checkpoint("before-pending-unlink")
            os.unlink(PENDING_STATUS_FILENAME, dir_fd=candidate_fd)
            _checkpoint("after-pending-unlink")
        except OSError:
            _raise(OutputPublication, "pending-unlink")
        _fsync_directory(candidate_fd, "candidate-after-pending-unlink")
        _fsync_directory(parent_fd, "parent-after-publication")
        _verify_candidate_directory_identity(
            parent_fd, candidate_fd, candidate_stable_identity
        )
        validated = _validate_candidate_fd(
            candidate_fd,
            allow_synthetic=allow_synthetic_validation,
        )
        if validated.get("decision") != "candidate_generated":
            _raise(OutputPublication, "candidate-decision")
        _verify_candidate_directory_identity(
            parent_fd, candidate_fd, candidate_stable_identity
        )
        created = False
        return os.path.join(candidate_parent, CANDIDATE_DIRECTORY)
    except Exception:
        if created:
            if candidate_fd >= 0:
                _cleanup_candidate(
                    parent_fd, candidate_fd, candidate_stable_identity
                )
            else:
                try:
                    os.rmdir(CANDIDATE_DIRECTORY, dir_fd=parent_fd)
                except OSError:
                    _raise(OutputPublication, "cleanup")
        raise
    finally:
        if candidate_fd >= 0:
            try:
                os.close(candidate_fd)
            except OSError:
                pass


def publish_synthetic_candidate_for_test(data: bytes, candidate_parent: Any) -> str:
    """Publish a test-owned candidate; this entrypoint is never asset authority."""
    parent = _canonical_absolute_path(candidate_parent, InvalidOutputPath)
    accepted = AcceptedPaths()
    try:
        parent_fd = _open_absolute_directory(accepted, parent, InvalidOutputPath)
        try:
            parent_stat = os.fstat(parent_fd)
        except OSError:
            _raise(InvalidOutputPath, "candidate-parent-fstat")
        if stat.S_IMODE(parent_stat.st_mode) != 0o700:
            _raise(InvalidOutputPath, "candidate-parent-mode")
        observed, header_data, inventory_data = parse_gzip_tar_bytes(data, require_profile=False)
        synthetic_stat = os.stat_result((stat.S_IFREG | 0o600, 0, 0, 1, os.getuid(), 1, len(data), 0, 0, 0))
        manifest_data = _build_manifest(
            observed,
            header_data,
            inventory_data,
            synthetic_stat,
            sha256_hex(data),
            synthetic=True,
        )
        return _publish_candidate_bytes(
            parent_fd,
            parent,
            manifest_data,
            header_data,
            inventory_data,
            allow_synthetic_validation=True,
        )
    finally:
        accepted.close()


def _hash_descriptor(fd: int) -> Tuple[int, str]:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
    except OSError:
        _raise(InputOpen, "archive-seek")
    digest = hashlib.sha256()
    total = 0
    while True:
        try:
            data = os.read(fd, READ_CHUNK_BYTES)
        except OSError:
            _raise(InputOpen, "archive-read")
        if not data:
            return total, digest.hexdigest()
        total = checked_add(total, len(data), EXPECTED_COMPRESSED_BYTES + 1, InputLengthMismatch)
        digest.update(data)


def _duplicate_descriptor(fd: int) -> int:
    try:
        return os.dup(fd)
    except OSError:
        _raise(InputOpen, "archive-dup")
    raise AssertionError("unreachable")


def _apply_process_limits() -> None:
    requested = [
        (resource.RLIMIT_CPU, CPU_SECONDS),
        (resource.RLIMIT_FSIZE, MAX_HEADER_LEDGER_BYTES),
        (resource.RLIMIT_NOFILE, MAX_OPEN_FILE_DESCRIPTORS),
    ]
    for limit, value in requested:
        try:
            _, hard = resource.getrlimit(limit)
            target = value if hard == resource.RLIM_INFINITY else min(value, hard)
            resource.setrlimit(limit, (target, target))
            soft_after, _ = resource.getrlimit(limit)
        except (OSError, ValueError):
            _raise(ResourceLimitUnavailable, "setrlimit")
        if soft_after > value:
            _raise(ResourceLimitUnavailable, "setrlimit-ceiling")


def inspect_archive(
    download_root: Any,
    archive: Any,
    attempt_root: Any,
    candidate_parent: Any,
) -> Dict[str, Any]:
    accepted = _accept_paths(download_root, archive, attempt_root, candidate_parent)
    try:
        archive_stat = accepted.archive_stat
        if archive_stat is None:
            raise AssertionError("missing archive stat")
        if archive_stat.st_size != EXPECTED_COMPRESSED_BYTES:
            _raise(InputLengthMismatch, "archive-length")
        hash_fd = _duplicate_descriptor(accepted.archive_fd)
        try:
            length, archive_digest = _hash_descriptor(hash_fd)
        finally:
            _close_descriptor(hash_fd, InputOpen, "archive-hash-close")
        if length != EXPECTED_COMPRESSED_BYTES:
            _raise(InputLengthMismatch, "archive-length")
        if archive_digest != EXPECTED_ARCHIVE_SHA256:
            _raise(InputDigestMismatch, "archive-sha256")
        accepted.verify_unchanged()
        parse_fd = _duplicate_descriptor(accepted.archive_fd)
        try:
            try:
                os.lseek(parse_fd, 0, os.SEEK_SET)
            except OSError:
                _raise(InputOpen, "archive-seek")
            budget = CandidateBudget()
            header_writer = MemoryWriter(MAX_HEADER_LEDGER_BYTES, budget)
            inventory_writer = MemoryWriter(MAX_INVENTORY_LEDGER_BYTES, budget)
            observed = parse_gzip_tar_reader(
                PrependReader(parse_fd),
                header_writer,
                inventory_writer,
                EXPECTED_COMPRESSED_BYTES,
                require_profile=True,
            )
        finally:
            _close_descriptor(parse_fd, InputOpen, "archive-parse-close")
        accepted.verify_unchanged()
        header_data = bytes(header_writer.data)
        inventory_data = bytes(inventory_writer.data)
        manifest_data = _build_manifest(
            observed,
            header_data,
            inventory_data,
            archive_stat,
            archive_digest,
            synthetic=False,
        )
        def precommit_check() -> None:
            accepted.verify_unchanged(allow_candidate_parent_metadata_change=True)
            verify_fd = _duplicate_descriptor(accepted.archive_fd)
            try:
                verify_length, verify_digest = _hash_descriptor(verify_fd)
            finally:
                _close_descriptor(verify_fd, InputOpen, "archive-verify-close")
            accepted.verify_unchanged(allow_candidate_parent_metadata_change=True)
            if verify_length != EXPECTED_COMPRESSED_BYTES:
                _raise(InputLengthMismatch, "archive-length-drift")
            if verify_digest != archive_digest:
                _raise(InputDigestMismatch, "archive-digest-drift")

        _publish_candidate_bytes(
            accepted.candidate_parent_fd,
            accepted.candidate_parent,
            manifest_data,
            header_data,
            inventory_data,
            before_mutation_check=accepted.verify_unchanged,
            precommit_check=precommit_check,
        )
        return _strict_json_line(
            _build_status(manifest_data, header_data, inventory_data),
            STATUS_KEYS,
        )
    finally:
        accepted.close()


def _parse_cli(argv: Sequence[str]) -> Tuple[str, str, str, str]:
    if len(argv) != 9 or argv[0] != "inspect" or list(argv[1::2]) != [
        "--download-root", "--archive", "--attempt-root", "--candidate-parent"
    ]:
        _raise(InvalidCli, "argv")
    return argv[2], argv[4], argv[6], argv[8]


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        os.close(0)
    except OSError:
        pass
    try:
        _apply_process_limits()
        download_root, archive, attempt_root, candidate_parent = _parse_cli(
            sys.argv[1:] if argv is None else argv
        )
        status_value = inspect_archive(download_root, archive, attempt_root, candidate_parent)
    except ArchiveLedgerError as error:
        try:
            _write_atomic_terminal_line(2, _failure_line(error))
        except ArchiveLedgerError:
            pass
        return 1
    try:
        _write_atomic_terminal_line(1, canonical_json_line(status_value))
        return 0
    except ArchiveLedgerError as error:
        try:
            _write_atomic_terminal_line(2, _failure_line(error))
        except ArchiveLedgerError:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
