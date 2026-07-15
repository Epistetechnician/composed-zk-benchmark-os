import ast
import hashlib
import importlib.util
import json
import os
import pathlib
import stat
import struct
import tempfile
import unittest
import zlib


MODULE_PATH = pathlib.Path(__file__).parents[1] / "p01b_archive_ledger.py"
BOUNDARY_PATH = (
    pathlib.Path(__file__).parents[3]
    / "docs"
    / "796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md"
)

BOUNDARY_DOCUMENT_SHA256 = (
    "2b52a3b24d94b565434dc341d808fe7ee3ad44757ea5ff8365f8dc88aefe1ba0"
)
CONTRACT_DIGEST = "9a85d6b33f31ee3e78d6176da9208753bc5c244c4fecc44ab29efc265b4f7bd1"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
ZERO_BLOCK_SHA256 = hashlib.sha256(bytes(512)).hexdigest()
SAFE_ARCHIVE_BYTES = 114
SAFE_ARCHIVE_SHA256 = "5258325ce4930a7e5718376ee77c3f89f02f9da02bd1f4f4a9e6174777f27bbb"
SAFE_HEADER_LEDGER_BYTES = 8524
SAFE_HEADER_LEDGER_SHA256 = "493ccd92f233a8188aa3a29c296874ee7ee27a791eb3016b0a8fa08535fba45b"
SAFE_INVENTORY_LEDGER_BYTES = 1389
SAFE_INVENTORY_LEDGER_SHA256 = "18d8764192ec41596bfd19f97696fde1bd69d7545e5f38718184aecbc247cadb"

LIMITS = {
    "READ_CHUNK_BYTES": 65536,
    "GZIP_MEMBERS": 1,
    "MAX_GZIP_FILENAME_BYTES": 4096,
    "MAX_GZIP_COMMENT_BYTES": 4096,
    "MAX_GZIP_EXTRA_BYTES": 65535,
    "MAX_GZIP_OPTIONAL_BYTES_TOTAL": 73727,
    "MAX_COMPRESSION_RATIO": 72,
    "MAX_UNCOMPRESSED_TAR_BYTES": 8589934592,
    "MAX_PHYSICAL_TAR_HEADERS": 8192,
    "MAX_LOGICAL_MEMBERS": 4096,
    "MAX_EXTENSION_HEADERS": 512,
    "MAX_EXTENSION_PAYLOAD_BYTES": 65536,
    "MAX_EXTENSION_PAYLOAD_BYTES_TOTAL": 4194304,
    "MAX_MEMBER_BYTES": 1073741824,
    "MAX_AGGREGATE_REGULAR_BYTES": 6442450944,
    "MAX_TOTAL_EXTRACTION_OUTPUT_BYTES": 6442450944,
    "MAX_EFFECTIVE_PATH_BYTES": 1024,
    "MAX_PATH_COMPONENT_BYTES": 255,
    "MAX_PATH_COMPONENTS": 128,
    "MAX_TRAILING_ZERO_BYTES": 1048576,
    "MAX_HEADER_LEDGER_BYTES": 67108864,
    "MAX_INVENTORY_LEDGER_BYTES": 16777216,
    "MAX_MANIFEST_BYTES": 1048576,
    "MAX_STATUS_BYTES": 65536,
    "MAX_TOTAL_CANDIDATE_BYTES": 85000192,
}

FAILURE_CLASSES = {
    "InvalidCli",
    "InvalidInputPath",
    "InvalidOutputPath",
    "InputOverlap",
    "InputOpen",
    "InputNotRegular",
    "InputIdentityDrift",
    "InputLengthMismatch",
    "InputDigestMismatch",
    "ResourceLimitUnavailable",
    "GzipMagic",
    "GzipMethod",
    "GzipReservedFlags",
    "GzipOptionalFieldLimit",
    "GzipExtraField",
    "GzipHeaderCrc",
    "GzipDeflate",
    "GzipTrailerCrc",
    "GzipTrailerSize",
    "GzipMemberCount",
    "GzipTrailingData",
    "CompressionRatioLimit",
    "UncompressedTarLimit",
    "TarPartialBlock",
    "TarMagic",
    "TarVersion",
    "TarChecksum",
    "TarNumericEncoding",
    "TarHeaderLimit",
    "TarUnsupportedType",
    "TarExtensionLimit",
    "TarExtensionPayloadLimit",
    "TarPaxGrammar",
    "TarPaxKeyword",
    "TarExtensionConflict",
    "TarExtensionOrphan",
    "TarPathEncoding",
    "TarPathInvalid",
    "TarDuplicateRawName",
    "TarDuplicateEffectiveName",
    "TarDuplicateCollisionKey",
    "TarFileDirectoryCollision",
    "TarRegularAncestor",
    "TarMemberLimit",
    "TarMemberSizeLimit",
    "TarAggregateLimit",
    "TarPaddingNonzero",
    "TarTerminator",
    "TarTrailingLimit",
    "CandidateByteLimit",
    "ProfileMismatch",
    "EmbeddedLeanMismatch",
    "OutputCollision",
    "OutputWrite",
    "OutputDurability",
    "OutputPublication",
}

LEDGER_HEADER_FIELDS = {"schema", "row_kind", "row_index", "contract_digest"}
TAR_TERMINATOR_FIELDS = {
    "schema", "row_kind", "row_index", "first_zero_block_index",
    "first_zero_byte_offset", "first_zero_sha256", "second_zero_block_index",
    "second_zero_byte_offset", "second_zero_sha256",
}
TAR_TRAILING_FIELDS = {
    "schema", "row_kind", "row_index", "uncompressed_byte_offset",
    "padding_bytes", "padding_sha256",
}
TAR_HEADER_FIELDS = {
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
GZIP_MEMBER_FIELDS = {
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
INVENTORY_MEMBER_FIELDS = {
    "schema", "row_kind", "row_index", "archive_index", "physical_header_index",
    "extension_header_indices", "raw_name_hex", "effective_raw_name", "collision_key",
    "kind", "member_size", "content_sha256", "data_offset", "data_padding_bytes",
}
MANIFEST_FIELDS = {
    "schema", "asset_id", "url", "release_id", "github_asset_id", "filename",
    "tag_commit", "expected_compressed_bytes", "expected_archive_sha256",
    "release_immutable", "contract_digest", "parser_source_sha256", "python_version",
    "zlib_version", "archive_device", "archive_inode", "archive_mode",
    "archive_owner_uid", "archive_link_count", "archive_byte_length",
    "archive_modified_seconds", "archive_modified_nanoseconds",
    "archive_changed_seconds", "archive_changed_nanoseconds", "archive_sha256",
    "gzip_members", "physical_tar_headers", "logical_members", "root_count",
    "regular_members", "directory_members", "extension_headers",
    "uncompressed_tar_bytes", "aggregate_regular_bytes", "largest_member_bytes",
    "trailing_zero_bytes", "top_level", "legacy_inventory_sha256",
    "embedded_lean_bytes", "embedded_lean_sha256", "header_ledger_bytes",
    "header_ledger_sha256", "inventory_ledger_bytes", "inventory_ledger_sha256",
    "candidate_only", "accepted", "phase_797_authorized",
    "materialization_authorized", "capture_authorized", "accepted_evidence_authorized",
}
STATUS_FIELDS = {
    "schema", "decision", "declared_files", "manifest_bytes", "manifest_sha256",
    "header_ledger_bytes", "header_ledger_sha256", "inventory_ledger_bytes",
    "inventory_ledger_sha256", "candidate_only", "accepted",
    "phase_797_authorized", "materialization_authorized", "capture_authorized",
    "accepted_evidence_authorized",
}

LEDGER_INTEGER_FIELDS = {
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

AUTHORITY_FIELDS = {
    "candidate_only": True,
    "accepted": False,
    "phase_797_authorized": False,
    "materialization_authorized": False,
    "capture_authorized": False,
    "accepted_evidence_authorized": False,
}

DECLARED_ARTIFACTS = [
    "archive-ledger-capture-status-v1.json",
    "archive-source-manifest-v1.json",
    "gzip-tar-header-ledger-v1.jsonl",
    "ordered-logical-member-inventory-v1.jsonl",
]

PINNED_ASSET_AUTHORITY = {
    "asset_id": "aeneas-main-nightly-2026-07-10-c2015b8",
    "url": (
        "https://github.com/AeneasVerif/aeneas/releases/download/"
        "nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz"
    ),
    "release_id": 351909376,
    "github_asset_id": 472143319,
    "filename": "aeneas-macos-aarch64.tar.gz",
    "tag_commit": "c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d",
    "expected_compressed_bytes": 123234656,
    "expected_archive_sha256": "fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45",
    "release_immutable": False,
}

PINNED_PROFILE = {
    "gzip_members": 1,
    "logical_members": 2471,
    "root_count": 0,
    "regular_members": 2305,
    "directory_members": 166,
    "top_level": ["aeneas", "backends", "charon", "charon-driver", "libs", "rust-toolchain"],
    "legacy_inventory_sha256": "26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e",
    "embedded_lean_bytes": 50447755,
    "embedded_lean_sha256": "f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59",
}


def canonical_json_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def expected_contract_object():
    return {
        "boundary_document_sha256": BOUNDARY_DOCUMENT_SHA256,
        "candidate_artifact_schemas": [
            "hsai-p01b-archive-ledger-capture-status-v1",
            "hsai-p01b-archive-source-manifest-v1",
            "hsai-p01b-gzip-tar-header-ledger-v1",
            "hsai-p01b-ordered-logical-member-inventory-v1",
        ],
        "failure_taxonomy_schema": "hsai-p01b-archive-ledger-failure-v1",
        "grammar_profile": "hsai-p01b-single-gzip-strict-ustar-v1",
        "limits": LIMITS,
        "schema": "hsai-p01b-archive-ledger-contract-v1",
    }


def load_module():
    if not MODULE_PATH.is_file():
        raise AssertionError("Phase 796-A1 helper is absent: {}".format(MODULE_PATH))
    spec = importlib.util.spec_from_file_location("p01b_archive_ledger", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_octal(value, width):
    encoded = format(value, "0{}o".format(width - 1)).encode("ascii")
    if len(encoded) != width - 1:
        raise ValueError("octal value does not fit")
    return encoded + b"\0"


def exact_checksum(value):
    encoded = format(value, "06o").encode("ascii")
    if len(encoded) != 6:
        raise ValueError("checksum does not fit")
    return encoded + b"\0 "


def string_field(value, width):
    raw = value if isinstance(value, bytes) else value.encode("ascii")
    if len(raw) > width:
        raise ValueError("string field does not fit")
    return raw + bytes(width - len(raw))


def ustar_header(
    name,
    *,
    member_type=b"0",
    size=0,
    prefix=b"",
    mode=0o644,
    uid=0,
    gid=0,
    mtime=0,
    linkname=b"",
    uname=b"",
    gname=b"",
    devmajor=0,
    devminor=0,
):
    header = bytearray(512)
    header[0:100] = string_field(name, 100)
    header[100:108] = exact_octal(mode, 8)
    header[108:116] = exact_octal(uid, 8)
    header[116:124] = exact_octal(gid, 8)
    header[124:136] = exact_octal(size, 12)
    header[136:148] = exact_octal(mtime, 12)
    header[148:156] = b"        "
    header[156:157] = member_type
    header[157:257] = string_field(linkname, 100)
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    header[265:297] = string_field(uname, 32)
    header[297:329] = string_field(gname, 32)
    header[329:337] = exact_octal(devmajor, 8)
    header[337:345] = exact_octal(devminor, 8)
    header[345:500] = string_field(prefix, 155)
    header[500:512] = bytes(12)
    header[148:156] = exact_checksum(sum(header))
    return bytes(header)


def tar_member(name, payload=b"", *, member_type=b"0", prefix=b""):
    size = 0 if member_type == b"5" else len(payload)
    header = ustar_header(
        name,
        member_type=member_type,
        size=size,
        prefix=prefix,
    )
    padding = bytes((-len(payload)) % 512) if size else b""
    return header + payload + padding


def tar_stream(*members, trailing_zero_bytes=0, terminator_blocks=2):
    return b"".join(members) + bytes(512 * terminator_blocks + trailing_zero_bytes)


def pax_key_value_record(key, value):
    payload = key + b"=" + value + b"\n"
    length = len(payload) + 2
    while True:
        record = str(length).encode("ascii") + b" " + payload
        if len(record) == length:
            return record
        length = len(record)


def pax_record(path):
    return pax_key_value_record(b"path", path)


def gzip_member(
    payload,
    *,
    extra=None,
    filename=None,
    comment=None,
    header_crc=False,
    mtime=0,
    xfl=0,
    os_byte=255,
):
    flags = 0
    if header_crc:
        flags |= 0x02
    if extra is not None:
        flags |= 0x04
    if filename is not None:
        flags |= 0x08
    if comment is not None:
        flags |= 0x10
    header = bytearray(b"\x1f\x8b\x08" + bytes([flags]))
    header.extend(struct.pack("<I", mtime))
    header.extend(bytes([xfl, os_byte]))
    if extra is not None:
        header.extend(struct.pack("<H", len(extra)))
        header.extend(extra)
    if filename is not None:
        header.extend(filename + b"\0")
    if comment is not None:
        header.extend(comment + b"\0")
    if header_crc:
        header.extend(struct.pack("<H", zlib.crc32(header) & 0xFFFF))
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(payload) + compressor.flush()
    trailer = struct.pack("<II", zlib.crc32(payload) & 0xFFFFFFFF, len(payload) & 0xFFFFFFFF)
    return bytes(header) + compressed + trailer


def safe_archive(*, content=b"payload", trailing_zero_bytes=0):
    tar = tar_stream(
        tar_member(b"dir/", member_type=b"5"),
        tar_member(b"file.txt", content, prefix=b"dir"),
        trailing_zero_bytes=trailing_zero_bytes,
    )
    return gzip_member(tar)


def normalize_result(result):
    if isinstance(result, dict):
        return result
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if hasattr(result, "__dict__"):
        return dict(result.__dict__)
    raise AssertionError("synthetic parser result is not inspectable")


def decode_jsonl(data):
    return [json.loads(line) for line in data.splitlines()]


def independent_json_object(data, expected_keys=None):
    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    value = json.loads(data.decode("ascii"), object_pairs_hook=pairs_hook)
    if not isinstance(value, dict):
        raise ValueError("object required")
    if expected_keys is not None and set(value) != set(expected_keys):
        raise ValueError("field set")
    return value


def independent_exact_integer(case, value, *, signed=False):
    case.assertIs(type(value), int)
    if signed:
        case.assertGreaterEqual(value, -(1 << 63))
        case.assertLessEqual(value, (1 << 63) - 1)
    else:
        case.assertGreaterEqual(value, 0)
        case.assertLessEqual(value, (1 << 64) - 1)


def independent_ascii(case, value):
    case.assertIs(type(value), str)
    value.encode("ascii")


def independent_hex(case, value, exact_characters=None):
    independent_ascii(case, value)
    if exact_characters is not None:
        case.assertEqual(len(value), exact_characters)
    case.assertEqual(len(value) % 2, 0)
    case.assertTrue(set(value) <= set("0123456789abcdef"))
    bytes.fromhex(value)


def independent_sha256(case, value):
    independent_hex(case, value, 64)


def independent_validate_ledger_rows(case, header_rows, inventory_rows):
    header_schemas = {
        "ledger_header": (LEDGER_HEADER_FIELDS, "hsai-p01b-gzip-tar-header-ledger-v1"),
        "tar_header": (TAR_HEADER_FIELDS, "hsai-p01b-tar-header-v1"),
        "tar_terminator": (TAR_TERMINATOR_FIELDS, "hsai-p01b-tar-terminator-v1"),
        "tar_trailing_padding": (
            TAR_TRAILING_FIELDS,
            "hsai-p01b-tar-trailing-padding-v1",
        ),
        "gzip_member": (GZIP_MEMBER_FIELDS, "hsai-p01b-gzip-member-v1"),
    }
    for rows, inventory in ((header_rows, False), (inventory_rows, True)):
        case.assertGreater(len(rows), 0)
        for index, row in enumerate(rows):
            case.assertIs(type(row), dict)
            kind = row["row_kind"]
            if inventory:
                expected_fields = LEDGER_HEADER_FIELDS if index == 0 else INVENTORY_MEMBER_FIELDS
                expected_schema = (
                    "hsai-p01b-ordered-logical-member-inventory-v1"
                    if index == 0
                    else "hsai-p01b-archive-logical-member-v1"
                )
                expected_kind = "ledger_header" if index == 0 else "logical_member"
                case.assertEqual(kind, expected_kind)
            else:
                expected_fields, expected_schema = header_schemas[kind]
            case.assertEqual(set(row), expected_fields)
            case.assertEqual(row["schema"], expected_schema)
            case.assertEqual(row["row_index"], index)
            for key, value in row.items():
                if key in LEDGER_INTEGER_FIELDS:
                    independent_exact_integer(case, value)
                elif key.endswith("_present"):
                    case.assertIs(type(value), bool)
                elif key == "extension_header_indices":
                    case.assertIs(type(value), list)
                    for item in value:
                        independent_exact_integer(case, item)
                else:
                    independent_ascii(case, value)
                if key.endswith("_hex"):
                    independent_hex(case, value)
                if key.endswith("_sha256") or key == "contract_digest":
                    independent_sha256(case, value)

    case.assertEqual(header_rows[0]["contract_digest"], CONTRACT_DIGEST)
    case.assertEqual(inventory_rows[0]["contract_digest"], CONTRACT_DIGEST)
    physical = header_rows[1:-3]
    terminator, trailing, gzip_row = header_rows[-3:]
    case.assertEqual([row["physical_header_index"] for row in physical], list(range(len(physical))))
    case.assertEqual(gzip_row["member_index"], 0)
    case.assertEqual((gzip_row["id1"], gzip_row["id2"], gzip_row["cm"]), (31, 139, 8))
    case.assertEqual(gzip_row["flg"] & 0xE0, 0)
    case.assertEqual(gzip_row["compressed_start"], 0)
    case.assertEqual(gzip_row["trailer_offset"], gzip_row["deflate_offset"] + gzip_row["deflate_bytes"])
    case.assertEqual(gzip_row["compressed_end"], gzip_row["trailer_offset"] + 8)
    case.assertEqual(gzip_row["trailer_isize"], gzip_row["uncompressed_bytes"] % (1 << 32))
    case.assertEqual(terminator["second_zero_byte_offset"], terminator["first_zero_byte_offset"] + 512)
    case.assertEqual(trailing["uncompressed_byte_offset"], terminator["second_zero_byte_offset"] + 512)
    case.assertEqual(terminator["first_zero_sha256"], ZERO_BLOCK_SHA256)
    case.assertEqual(terminator["second_zero_sha256"], ZERO_BLOCK_SHA256)
    case.assertEqual(trailing["padding_sha256"], hashlib.sha256(bytes(trailing["padding_bytes"])).hexdigest())

    logical = inventory_rows[1:]
    case.assertEqual([row["archive_index"] for row in logical], list(range(len(logical))))
    for row in logical:
        case.assertIn(row["kind"], {"regular", "directory"})
        case.assertLess(row["physical_header_index"], len(physical))
        source = physical[row["physical_header_index"]]
        case.assertEqual(row["raw_name_hex"], source["raw_name_hex"])
        case.assertEqual(row["member_size"], source["parsed_size"])
        case.assertEqual(row["data_offset"], source["data_offset"])
        case.assertEqual(row["data_padding_bytes"], source["data_padding_bytes"])
        if row["kind"] == "directory":
            case.assertEqual(row["content_sha256"], EMPTY_SHA256)


def independent_validate_candidate(case, candidate):
    candidate = pathlib.Path(candidate)
    manifest_data = (candidate / "archive-source-manifest-v1.json").read_bytes()
    status_data = (candidate / "archive-ledger-capture-status-v1.json").read_bytes()
    header_data = (candidate / "gzip-tar-header-ledger-v1.jsonl").read_bytes()
    inventory_data = (candidate / "ordered-logical-member-inventory-v1.jsonl").read_bytes()
    case.assertTrue(manifest_data.endswith(b"\n"))
    case.assertTrue(status_data.endswith(b"\n"))
    manifest = independent_json_object(manifest_data[:-1], MANIFEST_FIELDS)
    status = independent_json_object(status_data[:-1], STATUS_FIELDS)
    header_rows = [
        independent_json_object(line)
        for line in header_data.splitlines()
    ]
    inventory_rows = [
        independent_json_object(line)
        for line in inventory_data.splitlines()
    ]

    manifest_bool_fields = set(AUTHORITY_FIELDS) | {"release_immutable"}
    manifest_list_fields = {"top_level"}
    manifest_string_fields = {
        "schema", "asset_id", "url", "filename", "tag_commit",
        "expected_archive_sha256", "contract_digest", "parser_source_sha256",
        "python_version", "zlib_version", "archive_sha256", "legacy_inventory_sha256",
        "embedded_lean_sha256", "header_ledger_sha256", "inventory_ledger_sha256",
    }
    signed_fields = {"archive_modified_seconds", "archive_changed_seconds"}
    for key, value in manifest.items():
        if key in manifest_bool_fields:
            case.assertIs(type(value), bool)
        elif key in manifest_list_fields:
            case.assertIs(type(value), list)
            case.assertEqual(value, sorted(set(value)))
            for item in value:
                independent_ascii(case, item)
        elif key in manifest_string_fields:
            independent_ascii(case, value)
        else:
            independent_exact_integer(case, value, signed=key in signed_fields)
    for key in (
        "expected_archive_sha256", "contract_digest", "parser_source_sha256",
        "archive_sha256", "legacy_inventory_sha256", "embedded_lean_sha256",
        "header_ledger_sha256", "inventory_ledger_sha256",
    ):
        independent_sha256(case, manifest[key])
    independent_hex(case, manifest["tag_commit"], 40)
    case.assertEqual(manifest["schema"], "hsai-p01b-archive-source-manifest-v1")
    case.assertEqual(manifest["contract_digest"], CONTRACT_DIGEST)
    case.assertEqual(manifest["expected_compressed_bytes"], manifest["archive_byte_length"])
    case.assertEqual(manifest["expected_archive_sha256"], manifest["archive_sha256"])
    case.assertLess(manifest["archive_modified_nanoseconds"], 1_000_000_000)
    case.assertLess(manifest["archive_changed_nanoseconds"], 1_000_000_000)
    for key, expected in AUTHORITY_FIELDS.items():
        case.assertIs(manifest[key], expected)

    case.assertEqual(status["schema"], "hsai-p01b-archive-ledger-capture-status-v1")
    case.assertEqual(status["decision"], "candidate_generated")
    case.assertEqual(status["declared_files"], DECLARED_ARTIFACTS)
    for key in ("manifest_bytes", "header_ledger_bytes", "inventory_ledger_bytes"):
        independent_exact_integer(case, status[key])
    for key in ("manifest_sha256", "header_ledger_sha256", "inventory_ledger_sha256"):
        independent_sha256(case, status[key])
    for key, expected in AUTHORITY_FIELDS.items():
        case.assertIs(status[key], expected)
    for prefix, data in (
        ("manifest", manifest_data),
        ("header_ledger", header_data),
        ("inventory_ledger", inventory_data),
    ):
        case.assertEqual(status[prefix + "_bytes"], len(data))
        case.assertEqual(status[prefix + "_sha256"], hashlib.sha256(data).hexdigest())
    case.assertEqual(manifest["header_ledger_bytes"], len(header_data))
    case.assertEqual(manifest["header_ledger_sha256"], hashlib.sha256(header_data).hexdigest())
    case.assertEqual(manifest["inventory_ledger_bytes"], len(inventory_data))
    case.assertEqual(manifest["inventory_ledger_sha256"], hashlib.sha256(inventory_data).hexdigest())
    independent_validate_ledger_rows(case, header_rows, inventory_rows)
    case.assertEqual(manifest["physical_tar_headers"], len(header_rows) - 4)
    case.assertEqual(manifest["logical_members"], len(inventory_rows) - 1)
    case.assertEqual(manifest["gzip_members"], 1)


class Phase796A1TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def failure_code(self, error):
        for name in ("code", "failure_class", "kind"):
            value = getattr(error, name, None)
            if isinstance(value, str):
                return value
        return None

    def assert_failure(self, expected, callback):
        try:
            callback()
        except Exception as error:  # The concrete closed-taxonomy type is implementation-owned.
            self.assertEqual(self.failure_code(error), expected, repr(error))
        else:
            self.fail("expected {}".format(expected))

    def parse(self, raw, *, limits=None):
        parser = getattr(self.module, "parse_synthetic_archive_for_test", None)
        if callable(parser):
            return normalize_result(parser(raw, limits=limits))
        parser = getattr(self.module, "parse_gzip_tar_bytes", None)
        self.assertTrue(callable(parser), "helper must expose a hermetic byte parser")
        changed = {}
        try:
            for name, value in (limits or {}).items():
                if hasattr(self.module, name):
                    changed[name] = getattr(self.module, name)
                    setattr(self.module, name, value)
            observed, header_ledger, inventory_ledger = parser(raw, require_profile=False)
        finally:
            for name, value in changed.items():
                setattr(self.module, name, value)
        return {
            "observed": observed,
            "header_rows": decode_jsonl(header_ledger),
            "inventory_rows": decode_jsonl(inventory_ledger),
        }

    def limits(self, **overrides):
        result = dict(LIMITS)
        result.update(overrides)
        return result


class ContractAndSourceTests(Phase796A1TestCase):
    def test_committed_boundary_and_contract_digest_golden_vectors(self):
        self.assertEqual(hashlib.sha256(BOUNDARY_PATH.read_bytes()).hexdigest(), BOUNDARY_DOCUMENT_SHA256)
        expected = expected_contract_object()
        expected_bytes = canonical_json_bytes(expected)
        expected_digest = hashlib.sha256(
            b"hsai:p01b-archive-ledger-contract:v1\0" + expected_bytes
        ).hexdigest()
        self.assertEqual(expected_digest, CONTRACT_DIGEST)
        self.assertEqual(self.module.BOUNDARY_DOCUMENT_SHA256, BOUNDARY_DOCUMENT_SHA256)
        self.assertEqual(self.module.CONTRACT_OBJECT, expected)
        self.assertEqual(self.module.CONTRACT_OBJECT_BYTES, expected_bytes)
        self.assertEqual(self.module.CONTRACT_DIGEST, CONTRACT_DIGEST)

    def test_fixed_limits_and_closed_failure_taxonomy_are_exact(self):
        self.assertEqual(self.module.LIMITS, LIMITS)
        self.assertEqual(self.module.LEDGER_HEADER_KEYS, LEDGER_HEADER_FIELDS)
        self.assertEqual(self.module.TAR_HEADER_KEYS, TAR_HEADER_FIELDS)
        self.assertEqual(self.module.TAR_TERMINATOR_KEYS, TAR_TERMINATOR_FIELDS)
        self.assertEqual(self.module.TAR_TRAILING_KEYS, TAR_TRAILING_FIELDS)
        self.assertEqual(self.module.GZIP_MEMBER_KEYS, GZIP_MEMBER_FIELDS)
        self.assertEqual(self.module.INVENTORY_MEMBER_KEYS, INVENTORY_MEMBER_FIELDS)
        self.assertEqual(self.module.MANIFEST_KEYS, MANIFEST_FIELDS)
        self.assertEqual(self.module.STATUS_KEYS, STATUS_FIELDS)
        actual = {
            value.failure_class
            for value in vars(self.module).values()
            if isinstance(value, type)
            and issubclass(value, self.module.ArchiveLedgerError)
            and value is not self.module.ArchiveLedgerError
        }
        self.assertEqual(actual, FAILURE_CLASSES)
        self.assertEqual(len(FAILURE_CLASSES), 56)

    def test_pinned_asset_and_profile_constants_are_literal_boundary_values(self):
        actual_asset = {
            "asset_id": self.module.ASSET_ID,
            "url": self.module.ASSET_URL,
            "release_id": self.module.RELEASE_ID,
            "github_asset_id": self.module.GITHUB_ASSET_ID,
            "filename": self.module.ARCHIVE_FILENAME,
            "tag_commit": self.module.TAG_COMMIT,
            "expected_compressed_bytes": self.module.EXPECTED_COMPRESSED_BYTES,
            "expected_archive_sha256": self.module.EXPECTED_ARCHIVE_SHA256,
            "release_immutable": self.module.RELEASE_IMMUTABLE,
        }
        actual_profile = {
            "gzip_members": self.module.GZIP_MEMBERS,
            "logical_members": self.module.EXPECTED_LOGICAL_MEMBERS,
            "root_count": self.module.EXPECTED_ROOT_COUNT,
            "regular_members": self.module.EXPECTED_REGULAR_MEMBERS,
            "directory_members": self.module.EXPECTED_DIRECTORY_MEMBERS,
            "top_level": self.module.EXPECTED_TOP_LEVEL,
            "legacy_inventory_sha256": self.module.EXPECTED_LEGACY_INVENTORY_SHA256,
            "embedded_lean_bytes": self.module.EXPECTED_EMBEDDED_LEAN_BYTES,
            "embedded_lean_sha256": self.module.EXPECTED_EMBEDDED_LEAN_SHA256,
        }
        self.assertEqual(actual_asset, PINNED_ASSET_AUTHORITY)
        self.assertEqual(actual_profile, PINNED_PROFILE)

    def test_canonical_json_is_ascii_sorted_compact_and_total(self):
        encoded = self.module.canonical_json({"z": "\u00e9", "a": [2, 1]})
        self.assertEqual(encoded, b'{"a":[2,1],"z":"\\u00e9"}')
        for forbidden in (None, 1.0, float("nan"), float("inf"), -float("inf")):
            with self.subTest(forbidden=repr(forbidden)):
                self.assert_failure(
                    "OutputWrite",
                    lambda value=forbidden: self.module.canonical_json({"v": value}),
                )

    def test_independent_json_parser_rejects_duplicates_and_helper_rejects_unknowns(self):
        with self.assertRaises(ValueError):
            independent_json_object(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError):
            independent_json_object(b'{"a":1,"b":2}', {"a"})
        self.assert_failure(
            "OutputWrite",
            lambda: self.module.strict_json_object(b'{"a":1,"a":2}', {"a"}),
        )
        self.assert_failure(
            "OutputWrite",
            lambda: self.module.strict_json_object(b'{"a":1,"b":2}', {"a"}),
        )

    def test_helper_source_has_no_forbidden_dependency_or_ambient_surface(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_modules = {
            "gzip",
            "tarfile",
            "subprocess",
            "socket",
            "ssl",
            "http",
            "urllib",
            "requests",
            "importlib",
            "pkgutil",
        }
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(
            imported,
            {"hashlib", "json", "os", "resource", "stat", "struct", "sys", "typing", "zlib"},
        )
        self.assertEqual(imported & forbidden_modules, set())

        forbidden_calls = {
            ("os", "system"),
            ("os", "popen"),
            ("os", "getenv"),
            ("os", "putenv"),
            ("os", "spawnl"),
            ("os", "spawnv"),
            ("os", "execv"),
            ("os", "execve"),
        }
        observed_calls = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if isinstance(node.func.value, ast.Name):
                observed_calls.add((node.func.value.id, node.func.attr))
        self.assertEqual(observed_calls & forbidden_calls, set())
        self.assertNotIn("environ", {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)})
        forbidden_names = {"__import__", "eval", "exec", "compile"}
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertEqual(called_names & forbidden_names, set())
        write_open_functions = set()
        for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if not isinstance(node.func.value, ast.Name) or (node.func.value.id, node.func.attr) != ("os", "open"):
                    continue
                rendered = ast.dump(node)
                if "O_WRONLY" in rendered or "O_CREAT" in rendered:
                    write_open_functions.add(function.name)
        self.assertEqual(write_open_functions, {"_create_exclusive_file"})
        mutation_owners = {}
        for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                    mutation_owners.setdefault(node.func.attr, set()).add(function.name)
        self.assertEqual(
            mutation_owners.get("write"),
            {"write_all", "_write_atomic_terminal_line"},
        )
        self.assertEqual(mutation_owners.get("mkdir"), {"_publish_candidate_bytes"})
        self.assertEqual(mutation_owners.get("link"), {"_publish_candidate_bytes"})
        self.assertEqual(
            mutation_owners.get("unlink"), {"_cleanup_candidate", "_publish_candidate_bytes"}
        )
        self.assertEqual(
            mutation_owners.get("rmdir"), {"_cleanup_candidate", "_publish_candidate_bytes"}
        )
        self.assertEqual(
            mutation_owners.get("fchmod"), {"_create_exclusive_file", "_publish_candidate_bytes"}
        )
        for forbidden in (
            "remove", "rename", "replace", "chdir", "fork", "forkpty", "execv", "execve",
            "spawnl", "spawnv", "system", "popen", "getenv", "putenv", "unsetenv",
        ):
            self.assertNotIn(forbidden, mutation_owners)


class GzipAndTarParsingTests(Phase796A1TestCase):
    def test_safe_archive_parses_canonical_rows_and_content_digest(self):
        result = self.parse(safe_archive())
        inventory = result["inventory_rows"]
        headers = result["header_rows"]
        self.assertEqual(inventory[0]["row_kind"], "ledger_header")
        self.assertEqual([row["row_index"] for row in inventory], list(range(len(inventory))))
        self.assertEqual([row["archive_index"] for row in inventory[1:]], [0, 1])
        self.assertEqual(inventory[1]["kind"], "directory")
        self.assertEqual(inventory[1]["content_sha256"], EMPTY_SHA256)
        self.assertEqual(inventory[2]["effective_raw_name"], "dir/file.txt")
        self.assertEqual(inventory[2]["content_sha256"], hashlib.sha256(b"payload").hexdigest())
        self.assertEqual(headers[0]["row_kind"], "ledger_header")
        self.assertEqual(headers[-3]["row_kind"], "tar_terminator")
        self.assertEqual(headers[-2]["row_kind"], "tar_trailing_padding")
        self.assertEqual(headers[-1]["row_kind"], "gzip_member")
        self.assertEqual(headers[-3]["first_zero_sha256"], ZERO_BLOCK_SHA256)
        self.assertEqual(headers[-1]["uncompressed_tar_sha256"], hashlib.sha256(
            tar_stream(tar_member(b"dir/", member_type=b"5"), tar_member(b"file.txt", b"payload", prefix=b"dir"))
        ).hexdigest())

    def test_gzip_optional_fields_and_header_crc_are_bound(self):
        extra = b"AB\x04\x00data"
        raw = gzip_member(
            tar_stream(tar_member(b"a", b"x")),
            extra=extra,
            filename=b"archive.tar",
            comment=b"fixture",
            header_crc=True,
            mtime=7,
            xfl=2,
            os_byte=3,
        )
        row = self.parse(raw)["header_rows"][-1]
        self.assertTrue(row["fextra_present"])
        self.assertEqual(row["fextra_hex"], extra.hex())
        self.assertTrue(row["fname_present"])
        self.assertEqual(row["fname_hex"], b"archive.tar".hex())
        self.assertTrue(row["fcomment_present"])
        self.assertEqual(row["fcomment_hex"], b"fixture".hex())
        self.assertTrue(row["fhcrc_present"])

    def test_pax_and_gnu_long_name_extensions_apply_once(self):
        pax_name = b"pax/renamed.txt"
        gnu_name = b"gnu/" + b"a" * 90 + b".txt"
        raw = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(pax_name), member_type=b"x"),
                tar_member(b"ignored", b"pax"),
                tar_member(b"LongLink", gnu_name + b"\0", member_type=b"L"),
                tar_member(b"ignored2", b"gnu"),
            )
        )
        result = self.parse(raw)
        inventory = result["inventory_rows"][1:]
        self.assertEqual([row["effective_raw_name"] for row in inventory], [pax_name.decode(), gnu_name.decode()])
        self.assertEqual([row["extension_header_indices"] for row in inventory], [[0], [2]])

    def test_pax_path_value_may_contain_equals(self):
        raw = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(b"dir/a=b"), member_type=b"x"),
                tar_member(b"ignored", b"payload"),
            )
        )
        inventory = self.parse(raw)["inventory_rows"]
        self.assertEqual(inventory[1]["effective_raw_name"], "dir/a=b")

    def test_complete_ledger_bytes_are_deterministic_and_schemas_are_exact(self):
        raw = safe_archive()
        first = self.module.parse_gzip_tar_bytes(raw, require_profile=False)
        second = self.module.parse_gzip_tar_bytes(raw, require_profile=False)
        self.assertEqual(first, second)
        _, header_data, inventory_data = first
        self.assertEqual(len(raw), SAFE_ARCHIVE_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SAFE_ARCHIVE_SHA256)
        self.assertEqual(len(header_data), SAFE_HEADER_LEDGER_BYTES)
        self.assertEqual(hashlib.sha256(header_data).hexdigest(), SAFE_HEADER_LEDGER_SHA256)
        self.assertEqual(len(inventory_data), SAFE_INVENTORY_LEDGER_BYTES)
        self.assertEqual(hashlib.sha256(inventory_data).hexdigest(), SAFE_INVENTORY_LEDGER_SHA256)
        headers = decode_jsonl(header_data)
        inventory = decode_jsonl(inventory_data)
        expected_header_keys = {
            "ledger_header": LEDGER_HEADER_FIELDS,
            "tar_header": TAR_HEADER_FIELDS,
            "tar_terminator": TAR_TERMINATOR_FIELDS,
            "tar_trailing_padding": TAR_TRAILING_FIELDS,
            "gzip_member": GZIP_MEMBER_FIELDS,
        }
        for row in headers:
            self.assertEqual(set(row), expected_header_keys[row["row_kind"]])
        for line, row in zip(header_data.splitlines(), headers):
            self.assertEqual(
                independent_json_object(line, expected_header_keys[row["row_kind"]]), row
            )
        self.assertEqual(set(inventory[0]), LEDGER_HEADER_FIELDS)
        for row in inventory[1:]:
            self.assertEqual(set(row), INVENTORY_MEMBER_FIELDS)
        for line, row in zip(inventory_data.splitlines(), inventory):
            expected = LEDGER_HEADER_FIELDS if row["row_kind"] == "ledger_header" else INVENTORY_MEMBER_FIELDS
            self.assertEqual(independent_json_object(line, expected), row)
        gzip_row = headers[-1]
        for prefix in ("fextra", "fname", "fcomment"):
            self.assertFalse(gzip_row[prefix + "_present"])
            self.assertEqual(gzip_row[prefix + "_bytes"], 0)
            self.assertEqual(gzip_row[prefix + "_hex"], "")
            self.assertEqual(gzip_row[prefix + "_sha256"], EMPTY_SHA256)
        self.assertFalse(gzip_row["fhcrc_present"])
        self.assertEqual(gzip_row["fhcrc_hex"], "")
        self.assertEqual(gzip_row["fhcrc16"], 0)

    def test_every_ledger_u64_and_bool_field_rejects_python_bool_integer_aliasing(self):
        raw = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(b"renamed"), member_type=b"x"),
                tar_member(b"ignored", b"x"),
            ),
            extra=b"AB\0\0",
            filename=b"name",
            comment=b"comment",
            header_crc=True,
        )
        _, header_data, inventory_data = self.module.parse_gzip_tar_bytes(raw, require_profile=False)
        groups = [
            (decode_jsonl(header_data), False),
            (decode_jsonl(inventory_data), True),
        ]
        observed_u64 = set()
        observed_bool = set()
        for rows, inventory in groups:
            for row_index, row in enumerate(rows):
                for key in row:
                    if key in self.module.LEDGER_U64_FIELDS:
                        observed_u64.add(key)
                        changed = json.loads(json.dumps(rows))
                        changed[row_index][key] = False
                        with self.subTest(kind="u64", field=key):
                            self.assert_failure(
                                "OutputPublication",
                                lambda changed=changed, inventory=inventory: self.module._validate_ledger_rows(
                                    changed, inventory
                                ),
                            )
                    if key.endswith("_present"):
                        observed_bool.add(key)
                        changed = json.loads(json.dumps(rows))
                        changed[row_index][key] = 1
                        with self.subTest(kind="bool", field=key):
                            self.assert_failure(
                                "OutputPublication",
                                lambda changed=changed, inventory=inventory: self.module._validate_ledger_rows(
                                    changed, inventory
                                ),
                            )
        self.assertEqual(observed_u64, self.module.LEDGER_U64_FIELDS)
        self.assertEqual(
            observed_bool,
            {
                "extension_payload_present", "applies_to_archive_index_present",
                "fextra_present", "fname_present", "fcomment_present", "fhcrc_present",
            },
        )

    def test_every_emitted_ledger_field_rejects_an_incompatible_json_type(self):
        raw = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(b"renamed"), member_type=b"x"),
                tar_member(b"ignored", b"x"),
            ),
            extra=b"AB\0\0",
            filename=b"name",
            comment=b"comment",
            header_crc=True,
        )
        _, header_data, inventory_data = self.module.parse_gzip_tar_bytes(raw, require_profile=False)
        groups = [
            (
                decode_jsonl(header_data),
                False,
                LEDGER_HEADER_FIELDS | TAR_HEADER_FIELDS | TAR_TERMINATOR_FIELDS
                | TAR_TRAILING_FIELDS | GZIP_MEMBER_FIELDS,
            ),
            (decode_jsonl(inventory_data), True, LEDGER_HEADER_FIELDS | INVENTORY_MEMBER_FIELDS),
        ]
        for rows, inventory, expected_fields in groups:
            observed_fields = set()
            for row_index, row in enumerate(rows):
                for key, value in row.items():
                    observed_fields.add(key)
                    changed = json.loads(json.dumps(rows))
                    if isinstance(value, bool):
                        replacement = 1
                    elif isinstance(value, int):
                        replacement = False
                    elif isinstance(value, str):
                        replacement = []
                    elif isinstance(value, list):
                        replacement = "not-an-array"
                    else:
                        self.fail("unhandled emitted JSON type")
                    changed[row_index][key] = replacement
                    data = b"".join(canonical_json_bytes(item) + b"\n" for item in changed)

                    def validate(data=data, inventory=inventory):
                        parsed = self.module._strict_jsonl(data, inventory)
                        self.module._validate_ledger_rows(parsed, inventory)

                    with self.subTest(inventory=inventory, field=key):
                        self.assert_failure("OutputPublication", validate)
            self.assertEqual(observed_fields, expected_fields)

    def test_gzip_failure_classes_are_stable(self):
        valid = safe_archive()
        cases = []
        cases.append(("GzipMagic", b"\x00" + valid[1:]))
        cases.append(("GzipMethod", valid[:2] + b"\x00" + valid[3:]))
        cases.append(("GzipReservedFlags", valid[:3] + b"\x20" + valid[4:]))
        bad_extra = gzip_member(tar_stream(tar_member(b"a", b"x")), extra=b"AB\x05\x00x")
        cases.append(("GzipExtraField", bad_extra))
        with_hcrc = bytearray(gzip_member(tar_stream(tar_member(b"a", b"x")), header_crc=True))
        with_hcrc[10] ^= 1
        cases.append(("GzipHeaderCrc", bytes(with_hcrc)))
        malformed_deflate = bytearray(valid)
        malformed_deflate[10:13] = b"\x07\x00\x00"
        cases.append(("GzipDeflate", bytes(malformed_deflate)))
        bad_crc = bytearray(valid)
        bad_crc[-8] ^= 1
        cases.append(("GzipTrailerCrc", bytes(bad_crc)))
        bad_size = bytearray(valid)
        bad_size[-4] ^= 1
        cases.append(("GzipTrailerSize", bytes(bad_size)))
        cases.append(("GzipMemberCount", valid + valid))
        cases.append(("GzipTrailingData", valid + b"\0"))
        cases.append(("GzipTrailingData", valid + b"garbage"))
        for code, raw in cases:
            with self.subTest(code=code):
                self.assert_failure(code, lambda raw=raw: self.parse(raw))

    def test_gzip_truncation_matrix_fails_closed(self):
        valid = safe_archive()
        cases = [
            ("empty", b"", "GzipMagic"),
            ("fixed-header", valid[:9], "GzipMagic"),
            ("deflate", valid[:-9], "GzipDeflate"),
            ("trailer", valid[:-1], "GzipTrailerCrc"),
        ]
        extra = gzip_member(tar_stream(tar_member(b"a")), extra=b"AB\0\0")
        cases.append(("extra-xlen", extra[:11], "GzipOptionalFieldLimit"))
        cases.append(("extra-payload", extra[:13], "GzipExtraField"))
        header_crc = gzip_member(tar_stream(tar_member(b"a")), header_crc=True)
        cases.append(("header-crc", header_crc[:11], "GzipHeaderCrc"))
        fixed_suffix = struct.pack("<I", 0) + b"\0\xff"
        cases.append(("filename-nul", b"\x1f\x8b\x08\x08" + fixed_suffix + b"name", "GzipOptionalFieldLimit"))
        cases.append(("comment-nul", b"\x1f\x8b\x08\x10" + fixed_suffix + b"comment", "GzipOptionalFieldLimit"))
        for name, raw, failure in cases:
            with self.subTest(name=name):
                self.assert_failure(failure, lambda raw=raw: self.parse(raw))

    def test_tar_header_and_stream_failure_classes_are_stable(self):
        base_header = bytearray(ustar_header(b"a", size=1))
        cases = []
        bad_magic = bytearray(base_header)
        bad_magic[257:263] = b"bad!!!"
        cases.append(("TarMagic", tar_stream(bytes(bad_magic) + b"x" + bytes(511))))
        bad_version = bytearray(base_header)
        bad_version[263:265] = b"01"
        bad_version[148:156] = b"        "
        bad_version[148:156] = exact_checksum(sum(bad_version))
        cases.append(("TarVersion", tar_stream(bytes(bad_version) + b"x" + bytes(511))))
        bad_checksum = bytearray(base_header)
        bad_checksum[148:156] = b"000000\0 "
        cases.append(("TarChecksum", tar_stream(bytes(bad_checksum) + b"x" + bytes(511))))
        bad_numeric = bytearray(base_header)
        bad_numeric[124] = 0x80
        bad_numeric[148:156] = b"        "
        bad_numeric[148:156] = exact_checksum(sum(bad_numeric))
        cases.append(("TarNumericEncoding", tar_stream(bytes(bad_numeric) + b"x" + bytes(511))))
        cases.append(("TarUnsupportedType", tar_stream(tar_member(b"a", member_type=b"2"))))
        nonzero_padding = bytearray(tar_stream(tar_member(b"a", b"x")))
        nonzero_padding[513] = 1
        cases.append(("TarPaddingNonzero", bytes(nonzero_padding)))
        cases.append(("TarTerminator", gzip_member(tar_stream(tar_member(b"a", b"x"), terminator_blocks=1))))
        cases.append(("TarPartialBlock", gzip_member(tar_stream(tar_member(b"a", b"x"))[:-1])))
        for code, tar in cases:
            raw = tar if tar.startswith(b"\x1f\x8b") else gzip_member(tar)
            with self.subTest(code=code):
                self.assert_failure(code, lambda raw=raw: self.parse(raw))

    def test_signed_checksum_numeric_shapes_and_rejected_tar_families(self):
        signed_header = bytearray(ustar_header(b"a"))
        signed_header[265] = 0xFF
        signed_header[148:156] = b"        "
        signed_sum = sum(byte if byte < 128 else byte - 256 for byte in signed_header)
        signed_header[148:156] = exact_checksum(signed_sum)
        self.assert_failure(
            "TarChecksum",
            lambda: self.parse(gzip_member(tar_stream(bytes(signed_header)))),
        )

        for label, replacement in (
            ("leading-space", b" 000000\0"),
            ("trailing-space", b"0000000 "),
            ("missing-nul", b"00000000"),
            ("sign", b"+000000\0"),
            ("non-octal", b"0000008\0"),
            ("extra-nul", b"000000\0\0"),
        ):
            header = bytearray(ustar_header(b"a"))
            header[100:108] = replacement
            header[148:156] = b"        "
            header[148:156] = exact_checksum(sum(header))
            with self.subTest(numeric=label):
                self.assert_failure(
                    "TarNumericEncoding",
                    lambda header=bytes(header): self.parse(gzip_member(tar_stream(header))),
                )

        rejected_flags = [
            b"1", b"2", b"3", b"4", b"6", b"7", b"g", b"K", b"S", b"V",
            b"M", b"D", b"N", b"A", b"E", b"I",
        ]
        for member_type in rejected_flags:
            with self.subTest(member_type=member_type):
                raw = gzip_member(tar_stream(tar_member(b"a", member_type=member_type)))
                self.assert_failure("TarUnsupportedType", lambda raw=raw: self.parse(raw))

    def test_string_field_device_directory_and_header_padding_rules(self):
        cases = []
        for label, start, width in (
            ("name", 0, 100), ("uname", 265, 32), ("gname", 297, 32), ("prefix", 345, 155),
        ):
            header = bytearray(ustar_header(b"a"))
            header[start : start + width] = b"a\0b" + bytes(width - 3)
            header[148:156] = b"        "
            header[148:156] = exact_checksum(sum(header))
            cases.append((label, bytes(header), "TarPathEncoding"))

        link_header = bytearray(ustar_header(b"a", linkname=b"target"))
        cases.append(("linkname", bytes(link_header), "TarUnsupportedType"))
        for label, name, prefix in (
            ("prefix-leading", b"name", b"/prefix"),
            ("prefix-trailing", b"name", b"prefix/"),
            ("name-leading", b"/name", b"prefix"),
            ("name-trailing", b"name/", b"prefix"),
        ):
            cases.append((label, ustar_header(name, prefix=prefix), "TarPathInvalid"))
        cases.append(("device-number", ustar_header(b"a", devmajor=1), "TarUnsupportedType"))
        cases.append(("directory-size", ustar_header(b"a/", member_type=b"5", size=1), "TarUnsupportedType"))
        padding_header = bytearray(ustar_header(b"a"))
        padding_header[500] = 1
        padding_header[148:156] = b"        "
        padding_header[148:156] = exact_checksum(sum(padding_header))
        cases.append(("header-padding", bytes(padding_header), "TarUnsupportedType"))
        for label, header, failure in cases:
            with self.subTest(label=label):
                self.assert_failure(
                    failure,
                    lambda header=header: self.parse(gzip_member(tar_stream(header))),
                )

    def test_malformed_gnu_long_name_forms_are_rejected(self):
        cases = [
            (b"", "TarPaxGrammar"),
            (b"name", "TarPaxGrammar"),
            (b"a\0b\0", "TarPaxGrammar"),
            (b"\xff\0", "TarPathEncoding"),
            (b"a\n\0", "TarPathEncoding"),
        ]
        for payload, failure in cases:
            raw = gzip_member(
                tar_stream(
                    tar_member(b"LongLink", payload, member_type=b"L"),
                    tar_member(b"ignored"),
                )
            )
            with self.subTest(payload=payload):
                self.assert_failure(failure, lambda raw=raw: self.parse(raw))

    def test_member_after_zero_and_nonzero_trailing_data_fail(self):
        member_after_zero = (
            tar_member(b"a") + bytes(512) + tar_member(b"b") + bytes(1024)
        )
        nonzero_trailing = tar_stream(tar_member(b"a")) + b"\x01" + bytes(511)
        self.assert_failure(
            "TarTerminator",
            lambda: self.parse(gzip_member(member_after_zero)),
        )
        self.assert_failure(
            "TarTerminator",
            lambda: self.parse(gzip_member(nonzero_trailing)),
        )

    def test_extension_failures_are_stable(self):
        malformed_length = b"99 path=a\n"
        unknown_key = pax_key_value_record(b"size", b"1")
        cases = [
            (
                "TarPaxGrammar",
                tar_stream(tar_member(b"PaxHeader", malformed_length, member_type=b"x"), tar_member(b"a")),
            ),
            (
                "TarPaxKeyword",
                tar_stream(tar_member(b"PaxHeader", unknown_key, member_type=b"x"), tar_member(b"a")),
            ),
            (
                "TarExtensionConflict",
                tar_stream(
                    tar_member(b"PaxHeader", pax_record(b"a"), member_type=b"x"),
                    tar_member(b"LongLink", b"b\0", member_type=b"L"),
                    tar_member(b"ignored"),
                ),
            ),
            (
                "TarExtensionOrphan",
                tar_stream(tar_member(b"PaxHeader", pax_record(b"a"), member_type=b"x")),
            ),
            (
                "TarPaxGrammar",
                tar_stream(tar_member(b"LongLink", b"a\0junk", member_type=b"L"), tar_member(b"ignored")),
            ),
        ]
        for code, tar in cases:
            with self.subTest(code=code):
                self.assert_failure(code, lambda tar=tar: self.parse(gzip_member(tar)))

    def test_pax_grammar_rejects_all_noncanonical_record_forms(self):
        payloads = [
            (b"09 path=a\n", "TarPaxGrammar"),
            (b"+9 path=a\n", "TarPaxGrammar"),
            (b"9path=a\n", "TarPaxGrammar"),
            (b"9 path=\n", "TarPaxGrammar"),
            (b"9 =value\n", "TarPaxKeyword"),
            (b"9 path=a\0", "TarPaxGrammar"),
            (pax_record(b"a") + pax_record(b"b"), "TarPaxGrammar"),
            (b"10 path=\xff\n", "TarPathEncoding"),
        ]
        for payload, failure in payloads:
            raw = gzip_member(
                tar_stream(
                    tar_member(b"PaxHeader", payload, member_type=b"x"),
                    tar_member(b"ignored"),
                )
            )
            with self.subTest(payload=payload):
                self.assert_failure(failure, lambda raw=raw: self.parse(raw))

        for keyword in (b"size", b"GNU.sparse.size", b"vendor.key"):
            payload = pax_key_value_record(keyword, b"1")
            raw = gzip_member(
                tar_stream(
                    tar_member(b"PaxHeader", payload, member_type=b"x"),
                    tar_member(b"ignored"),
                )
            )
            with self.subTest(keyword=keyword):
                self.assert_failure("TarPaxKeyword", lambda raw=raw: self.parse(raw))

    def test_embedded_identity_and_legacy_inventory_order_are_bound(self):
        first_payload = b"lean-bytes"
        first = gzip_member(
            tar_stream(
                tar_member(self.module.EMBEDDED_LEAN_PATH.encode("ascii"), first_payload),
                tar_member(b"other", b"x"),
            )
        )
        second = gzip_member(
            tar_stream(
                tar_member(b"other", b"x"),
                tar_member(self.module.EMBEDDED_LEAN_PATH.encode("ascii"), first_payload),
            )
        )
        changed = gzip_member(
            tar_stream(
                tar_member(self.module.EMBEDDED_LEAN_PATH.encode("ascii"), b"LEAN-BYTES"),
                tar_member(b"other", b"x"),
            )
        )
        first_observed = self.parse(first)["observed"]
        second_observed = self.parse(second)["observed"]
        changed_observed = self.parse(changed)["observed"]
        self.assertEqual(first_observed["embedded_lean_bytes"], len(first_payload))
        self.assertEqual(
            first_observed["embedded_lean_sha256"], hashlib.sha256(first_payload).hexdigest()
        )
        self.assertNotEqual(
            first_observed["legacy_inventory_sha256"],
            second_observed["legacy_inventory_sha256"],
        )
        self.assertEqual(first_observed["embedded_lean_bytes"], changed_observed["embedded_lean_bytes"])
        self.assertNotEqual(
            first_observed["embedded_lean_sha256"], changed_observed["embedded_lean_sha256"]
        )

    def test_path_aliases_and_collisions_fail_closed(self):
        invalid_names = [
            (b"/absolute", "TarPathInvalid"),
            (b"./leading", "TarPathInvalid"),
            (b"a//b", "TarPathInvalid"),
            (b"a/./b", "TarPathInvalid"),
            (b"a/../b", "TarPathInvalid"),
            (b"a\\b", "TarPathEncoding"),
            (b"control\x1f", "TarPathEncoding"),
            (b"trailing/", "TarPathInvalid"),
        ]
        for name, failure in invalid_names:
            with self.subTest(name=name):
                raw = gzip_member(tar_stream(tar_member(name, b"x")))
                self.assert_failure(failure, lambda raw=raw: self.parse(raw))

        collision_cases = [
            ("TarDuplicateRawName", [tar_member(b"a"), tar_member(b"a")]),
            ("TarFileDirectoryCollision", [tar_member(b"a"), tar_member(b"a/", member_type=b"5")]),
            ("TarRegularAncestor", [tar_member(b"a", b"x"), tar_member(b"a/b", b"y")]),
            ("TarRegularAncestor", [tar_member(b"a/b", b"y"), tar_member(b"a", b"x")]),
        ]
        for code, members in collision_cases:
            with self.subTest(code=code):
                raw = gzip_member(tar_stream(*members))
                self.assert_failure(code, lambda raw=raw: self.parse(raw))


class BoundaryLimitTests(Phase796A1TestCase):
    def assert_limit_boundary(self, accepted, rejected, limit_name, limit_value, failure):
        limits = self.limits(**{limit_name: limit_value})
        self.parse(accepted, limits=limits)
        self.assert_failure(failure, lambda: self.parse(rejected, limits=limits))

    def test_gzip_optional_name_comment_and_extra_n_n_plus_one(self):
        tar = tar_stream(tar_member(b"a"))
        self.assert_limit_boundary(
            gzip_member(tar, filename=b"abc"),
            gzip_member(tar, filename=b"abcd"),
            "MAX_GZIP_FILENAME_BYTES",
            3,
            "GzipOptionalFieldLimit",
        )
        self.assert_limit_boundary(
            gzip_member(tar, comment=b"abc"),
            gzip_member(tar, comment=b"abcd"),
            "MAX_GZIP_COMMENT_BYTES",
            3,
            "GzipOptionalFieldLimit",
        )
        extra_four = b"AB\0\0"
        extra_five = b"AB\x01\0x"
        self.assert_limit_boundary(
            gzip_member(tar, extra=extra_four),
            gzip_member(tar, extra=extra_five),
            "MAX_GZIP_EXTRA_BYTES",
            4,
            "GzipOptionalFieldLimit",
        )

    def test_tar_header_member_extension_and_trailing_n_n_plus_one(self):
        one = gzip_member(tar_stream(tar_member(b"a")))
        two = gzip_member(tar_stream(tar_member(b"a"), tar_member(b"b")))
        self.assert_limit_boundary(one, two, "MAX_PHYSICAL_TAR_HEADERS", 1, "TarHeaderLimit")
        self.assert_limit_boundary(one, two, "MAX_LOGICAL_MEMBERS", 1, "TarMemberLimit")

        one_ext = gzip_member(
            tar_stream(tar_member(b"PaxHeader", pax_record(b"a"), member_type=b"x"), tar_member(b"ignored"))
        )
        two_ext = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(b"a"), member_type=b"x"),
                tar_member(b"ignored"),
                tar_member(b"PaxHeader2", pax_record(b"b"), member_type=b"x"),
                tar_member(b"ignored2"),
            )
        )
        self.assert_limit_boundary(one_ext, two_ext, "MAX_EXTENSION_HEADERS", 1, "TarExtensionLimit")
        self.assert_limit_boundary(
            gzip_member(tar_stream(tar_member(b"a"), trailing_zero_bytes=512)),
            gzip_member(tar_stream(tar_member(b"a"), trailing_zero_bytes=1024)),
            "MAX_TRAILING_ZERO_BYTES",
            512,
            "TarTrailingLimit",
        )

    def test_member_and_aggregate_bytes_n_n_plus_one(self):
        one_byte = gzip_member(tar_stream(tar_member(b"a", b"x")))
        two_bytes = gzip_member(tar_stream(tar_member(b"a", b"xy")))
        self.assert_limit_boundary(one_byte, two_bytes, "MAX_MEMBER_BYTES", 1, "TarMemberSizeLimit")
        self.assert_limit_boundary(one_byte, two_bytes, "MAX_AGGREGATE_REGULAR_BYTES", 1, "TarAggregateLimit")
        self.assert_limit_boundary(one_byte, two_bytes, "MAX_TOTAL_EXTRACTION_OUTPUT_BYTES", 1, "TarAggregateLimit")

    def test_path_component_count_and_length_n_n_plus_one(self):
        accepted = gzip_member(tar_stream(tar_member(b"abc", b"x")))
        too_long = gzip_member(tar_stream(tar_member(b"abcd", b"x")))
        self.assert_limit_boundary(accepted, too_long, "MAX_PATH_COMPONENT_BYTES", 3, "TarPathInvalid")
        self.assert_limit_boundary(accepted, too_long, "MAX_EFFECTIVE_PATH_BYTES", 3, "TarPathInvalid")
        one_component = gzip_member(tar_stream(tar_member(b"a", b"x")))
        two_components = gzip_member(tar_stream(tar_member(b"a/b", b"x")))
        self.assert_limit_boundary(one_component, two_components, "MAX_PATH_COMPONENTS", 1, "TarPathInvalid")

    def test_uncompressed_compression_and_extension_payload_limits(self):
        tar = tar_stream(tar_member(b"a", b"x"))
        raw = gzip_member(tar)
        self.parse(raw, limits=self.limits(MAX_UNCOMPRESSED_TAR_BYTES=len(tar)))
        self.assert_failure(
            "UncompressedTarLimit",
            lambda: self.parse(raw, limits=self.limits(MAX_UNCOMPRESSED_TAR_BYTES=len(tar) - 1)),
        )
        ratio = (len(tar) + len(raw) - 1) // len(raw)
        self.parse(raw, limits=self.limits(MAX_COMPRESSION_RATIO=ratio))
        self.assert_failure(
            "CompressionRatioLimit",
            lambda: self.parse(raw, limits=self.limits(MAX_COMPRESSION_RATIO=ratio - 1)),
        )

        payload = pax_record(b"a")
        extension = gzip_member(
            tar_stream(tar_member(b"PaxHeader", payload, member_type=b"x"), tar_member(b"ignored"))
        )
        self.parse(extension, limits=self.limits(MAX_EXTENSION_PAYLOAD_BYTES=len(payload)))
        self.assert_failure(
            "TarExtensionPayloadLimit",
            lambda: self.parse(
                extension,
                limits=self.limits(MAX_EXTENSION_PAYLOAD_BYTES=len(payload) - 1),
            ),
        )
        second_payload = pax_record(b"b")
        two_extensions = gzip_member(
            tar_stream(
                tar_member(b"Pax1", payload, member_type=b"x"),
                tar_member(b"ignored1"),
                tar_member(b"Pax2", second_payload, member_type=b"x"),
                tar_member(b"ignored2"),
            )
        )
        total = len(payload) + len(second_payload)
        self.parse(two_extensions, limits=self.limits(MAX_EXTENSION_PAYLOAD_BYTES_TOTAL=total))
        self.assert_failure(
            "TarExtensionPayloadLimit",
            lambda: self.parse(
                two_extensions,
                limits=self.limits(MAX_EXTENSION_PAYLOAD_BYTES_TOTAL=total - 1),
            ),
        )

    def test_optional_total_and_ledger_byte_limits(self):
        tar = tar_stream(tar_member(b"a", b"x"))
        raw = gzip_member(tar, filename=b"ab", comment=b"cd")
        self.parse(raw, limits=self.limits(MAX_GZIP_OPTIONAL_BYTES_TOTAL=4))
        self.assert_failure(
            "GzipOptionalFieldLimit",
            lambda: self.parse(raw, limits=self.limits(MAX_GZIP_OPTIONAL_BYTES_TOTAL=3)),
        )

        plain = gzip_member(tar)
        _, header_data, inventory_data = self.module.parse_gzip_tar_bytes(plain, require_profile=False)
        self.parse(plain, limits=self.limits(MAX_HEADER_LEDGER_BYTES=len(header_data)))
        self.assert_failure(
            "CandidateByteLimit",
            lambda: self.parse(
                plain,
                limits=self.limits(MAX_HEADER_LEDGER_BYTES=len(header_data) - 1),
            ),
        )
        self.parse(plain, limits=self.limits(MAX_INVENTORY_LEDGER_BYTES=len(inventory_data)))
        self.assert_failure(
            "CandidateByteLimit",
            lambda: self.parse(
                plain,
                limits=self.limits(MAX_INVENTORY_LEDGER_BYTES=len(inventory_data) - 1),
            ),
        )

    def test_reader_chunk_bound_and_second_member_limit(self):
        reader = self.module.BytesReader(b"x" * (LIMITS["READ_CHUNK_BYTES"] + 1))
        self.assertEqual(len(reader.read_some()), LIMITS["READ_CHUNK_BYTES"])
        self.assertEqual(len(reader.read_some()), 1)
        valid = safe_archive()
        self.assert_failure("GzipMemberCount", lambda: self.parse(valid + valid))


class ClosedTaxonomyBehaviorTests(Phase796A1TestCase):
    def test_cli_profile_embedded_and_checked_arithmetic_failures(self):
        valid_argv = [
            "inspect", "--download-root", "/d", "--archive", "/d/a",
            "--attempt-root", "/t", "--candidate-parent", "/t/phase-796a",
        ]
        self.assertEqual(self.module._parse_cli(valid_argv), ("/d", "/d/a", "/t", "/t/phase-796a"))
        invalid_argv = [valid_argv[:-1], valid_argv + ["extra"]]
        for index in (0, 1, 3, 5, 7):
            changed = list(valid_argv)
            changed[index] = "invalid-token"
            invalid_argv.append(changed)
        invalid_argv.extend(
            (
                ["inspect", "--download", "/d", "--archive", "/d/a", "--attempt-root", "/t",
                 "--candidate-parent", "/t/phase-796a"],
                ["inspect", "--archive", "/d/a", "--download-root", "/d", "--attempt-root", "/t",
                 "--candidate-parent", "/t/phase-796a"],
                ["inspect", "--download-root", "/d", "--download-root", "/d/a", "--attempt-root", "/t",
                 "--candidate-parent", "/t/phase-796a"],
            )
        )
        for argv in invalid_argv:
            self.assert_failure("InvalidCli", lambda argv=argv: self.module._parse_cli(argv))
        self.assert_failure(
            "ProfileMismatch",
            lambda: self.module.parse_gzip_tar_bytes(safe_archive(), require_profile=True),
        )
        profile = dict(PINNED_PROFILE)
        profile["embedded_lean_sha256"] = "0" * 64
        self.assert_failure("EmbeddedLeanMismatch", lambda: self.module.require_pinned_profile(profile))
        self.assert_failure(
            "TarMemberLimit",
            lambda: self.module.checked_add(1, 1, 1, self.module.TarMemberLimit),
        )
        self.assert_failure(
            "TarMemberLimit",
            lambda: self.module.checked_add(self.module.U64_MAX, 1, self.module.U64_MAX, self.module.TarMemberLimit),
        )

    def test_duplicate_effective_and_collision_key_are_distinct(self):
        duplicate_effective = gzip_member(
            tar_stream(
                tar_member(b"Pax1", pax_record(b"same"), member_type=b"x"),
                tar_member(b"raw1"),
                tar_member(b"Pax2", pax_record(b"same"), member_type=b"x"),
                tar_member(b"raw2"),
            )
        )
        self.assert_failure("TarDuplicateEffectiveName", lambda: self.parse(duplicate_effective))
        duplicate_collision = gzip_member(
            tar_stream(tar_member(b"a/", member_type=b"5"), tar_member(b"a", member_type=b"5"))
        )
        self.assert_failure("TarDuplicateCollisionKey", lambda: self.parse(duplicate_collision))

    def test_resource_limit_unavailability_is_closed(self):
        original = self.module.resource.setrlimit
        try:
            def reject(*_args):
                raise ValueError("injected")
            self.module.resource.setrlimit = reject
            self.assert_failure("ResourceLimitUnavailable", self.module._apply_process_limits)
        finally:
            self.module.resource.setrlimit = original

    def test_resource_limits_are_exact_clamped_and_postchecked(self):
        original_get = self.module.resource.getrlimit
        original_set = self.module.resource.setrlimit
        policies = {
            self.module.resource.RLIMIT_CPU: self.module.CPU_SECONDS,
            self.module.resource.RLIMIT_FSIZE: self.module.MAX_HEADER_LEDGER_BYTES,
            self.module.resource.RLIMIT_NOFILE: self.module.MAX_OPEN_FILE_DESCRIPTORS,
        }
        try:
            current = {}
            calls = []

            def get_unlimited(limit):
                return current.get(limit, (0, self.module.resource.RLIM_INFINITY))

            def set_recorded(limit, pair):
                calls.append((limit, pair))
                current[limit] = pair

            self.module.resource.getrlimit = get_unlimited
            self.module.resource.setrlimit = set_recorded
            self.module._apply_process_limits()
            self.assertEqual(calls, [(limit, (value, value)) for limit, value in policies.items()])

            finite_hard = {
                self.module.resource.RLIMIT_CPU: self.module.CPU_SECONDS - 1,
                self.module.resource.RLIMIT_FSIZE: self.module.MAX_HEADER_LEDGER_BYTES - 1,
                self.module.resource.RLIMIT_NOFILE: self.module.MAX_OPEN_FILE_DESCRIPTORS - 1,
            }
            current = {}
            calls = []

            def get_finite(limit):
                return current.get(limit, (0, finite_hard[limit]))

            self.module.resource.getrlimit = get_finite
            self.module._apply_process_limits()
            self.assertEqual(
                calls,
                [(limit, (finite_hard[limit], finite_hard[limit])) for limit in policies],
            )

            for offending, policy in policies.items():
                current = {}

                def get_drifted(limit, offending=offending, policy=policy):
                    if limit in current:
                        value = current[limit]
                        if limit == offending:
                            return (policy + 1, value[1])
                        return value
                    return (0, self.module.resource.RLIM_INFINITY)

                self.module.resource.getrlimit = get_drifted
                with self.subTest(limit=offending):
                    self.assert_failure(
                        "ResourceLimitUnavailable", self.module._apply_process_limits
                    )
        finally:
            self.module.resource.getrlimit = original_get
            self.module.resource.setrlimit = original_set

    def test_main_owns_stdin_stdout_stderr_and_canonical_exit_contract(self):
        original_limits = self.module._apply_process_limits
        original_inspect = self.module.inspect_archive

        def read_pipe(fd):
            chunks = []
            while True:
                data = os.read(fd, 4096)
                if not data:
                    return b"".join(chunks)
                chunks.append(data)

        def invoke(argv, inspect, write_override=None):
            saved = [os.dup(fd) for fd in (0, 1, 2)]
            stdin_read, stdin_write = os.pipe()
            stdout_read, stdout_write = os.pipe()
            stderr_read, stderr_write = os.pipe()
            original_write = self.module.os.write
            stdin_closed = []

            def limits():
                try:
                    os.fstat(0)
                except OSError:
                    stdin_closed.append(True)
                else:
                    self.fail("stdin remained open before process setup")

            try:
                os.dup2(stdin_read, 0)
                os.dup2(stdout_write, 1)
                os.dup2(stderr_write, 2)
                os.close(stdin_read)
                os.close(stdout_write)
                os.close(stderr_write)
                self.module._apply_process_limits = limits
                self.module.inspect_archive = inspect
                if write_override is not None:
                    self.module.os.write = lambda fd, data: write_override(
                        fd, data, original_write
                    )
                code = self.module.main(argv)
            finally:
                self.module.os.write = original_write
                for target, source in enumerate(saved):
                    os.dup2(source, target)
                    os.close(source)
                os.close(stdin_write)
                self.module._apply_process_limits = original_limits
                self.module.inspect_archive = original_inspect
            stdout = read_pipe(stdout_read)
            stderr = read_pipe(stderr_read)
            os.close(stdout_read)
            os.close(stderr_read)
            return code, stdout, stderr, stdin_closed

        expected_status = {
            "accepted": False,
            "candidate_only": True,
            "decision": "candidate_generated",
        }

        def inspect_success(*args):
            self.assertEqual(args, ("/d", "/d/a", "/t", "/t/phase-796a"))
            with self.assertRaises(OSError):
                os.fstat(0)
            return expected_status

        valid = [
            "inspect", "--download-root", "/d", "--archive", "/d/a",
            "--attempt-root", "/t", "--candidate-parent", "/t/phase-796a",
        ]
        code, stdout, stderr, stdin_closed = invoke(valid, inspect_success)
        self.assertEqual(code, 0)
        self.assertEqual(stdout, canonical_json_bytes(expected_status) + b"\n")
        self.assertEqual(stderr, b"")
        self.assertEqual(stdin_closed, [True])

        code, stdout, stderr, stdin_closed = invoke(
            ["invalid"], lambda *_args: self.fail("unreachable")
        )
        self.assertEqual(code, 1)
        self.assertEqual(stdout, b"")
        self.assertEqual(
            stderr,
            b'{"failure_class":"InvalidCli","schema":"hsai-p01b-archive-ledger-failure-v1"}\n',
        )
        self.assertLessEqual(len(stderr), 16384)
        self.assertEqual(stdin_closed, [True])

        def failed_stdout(fd, data, real_write):
            if fd == 1:
                raise OSError("injected stdout failure")
            return real_write(fd, data)

        def short_stdout_without_write(fd, data, real_write):
            if fd == 1:
                return len(data) - 1
            return real_write(fd, data)

        for name, override in (
            ("failed", failed_stdout),
            ("short", short_stdout_without_write),
        ):
            code, stdout, stderr, stdin_closed = invoke(
                valid, inspect_success, write_override=override
            )
            with self.subTest(stdout_write=name):
                self.assertEqual(code, 1)
                self.assertEqual(stdout, b"")
                self.assertEqual(
                    stderr,
                    b'{"failure_class":"OutputWrite","schema":"hsai-p01b-archive-ledger-failure-v1"}\n',
                )
                self.assertEqual(stdin_closed, [True])


class DescriptorAndPublicationTests(Phase796A1TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        # macOS exposes /var through a symlink; use its canonical target so the
        # production no-symlink-ancestor contract remains testable.
        self.root = pathlib.Path(os.path.realpath(self.temporary.name))
        self.download = self.root / "download"
        self.attempt = self.root / "attempt"
        self.candidate_parent = self.attempt / "phase-796a"
        self.download.mkdir(mode=0o700)
        self.attempt.mkdir(mode=0o700)
        self.candidate_parent.mkdir(mode=0o700)

    def tearDown(self):
        self.temporary.cleanup()

    def validate_paths(self, download_root, archive, attempt_root, candidate_parent):
        validator = getattr(self.module, "validate_input_paths_for_test", None)
        self.assertTrue(
            callable(validator),
            "helper must expose validate_input_paths_for_test for descriptor/root tests",
        )
        return validator(download_root, archive, attempt_root, candidate_parent)

    def test_root_overlap_and_noncanonical_paths_are_rejected(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        archive.write_bytes(b"fixture")
        self.assert_failure(
            "InputOverlap",
            lambda: self.validate_paths(self.root, archive, self.root, self.root / "phase-796a"),
        )
        self.assert_failure(
            "InvalidInputPath",
            lambda: self.validate_paths(
                str(self.download) + "/",
                archive,
                self.attempt,
                self.candidate_parent,
            ),
        )
        self.assert_failure(
            "InvalidOutputPath",
            lambda: self.validate_paths(
                self.download,
                archive,
                self.attempt,
                str(self.candidate_parent) + "/",
            ),
        )

    def test_symlink_and_nonregular_archive_are_rejected(self):
        real = self.download / "real"
        real.write_bytes(b"fixture")
        symlink = self.download / "aeneas-macos-aarch64.tar.gz"
        symlink.symlink_to(real.name)
        self.assert_failure(
            "InputOpen",
            lambda: self.validate_paths(self.download, symlink, self.attempt, self.candidate_parent),
        )
        symlink.unlink()
        symlink.mkdir()
        self.assert_failure(
            "InputNotRegular",
            lambda: self.validate_paths(self.download, symlink, self.attempt, self.candidate_parent),
        )

    def test_publication_uses_final_status_as_commit_marker(self):
        publisher = getattr(self.module, "publish_synthetic_candidate_for_test", None)
        validator = getattr(self.module, "validate_published_candidate_for_test", None)
        self.assertTrue(callable(publisher), "helper must expose synthetic publication injection")
        self.assertTrue(callable(validator), "helper must expose independent candidate validation")
        candidate = pathlib.Path(publisher(safe_archive(), self.candidate_parent))
        expected_names = {
            "archive-source-manifest-v1.json",
            "gzip-tar-header-ledger-v1.jsonl",
            "ordered-logical-member-inventory-v1.jsonl",
            "archive-ledger-capture-status-v1.json",
        }
        self.assertEqual({path.name for path in candidate.iterdir()}, expected_names)
        self.assertFalse((candidate / ".archive-ledger-capture-status-v1.pending").exists())
        for path in candidate.iterdir():
            self.assertTrue(stat.S_ISREG(path.stat().st_mode))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        manifest = json.loads((candidate / "archive-source-manifest-v1.json").read_text(encoding="ascii"))
        status = json.loads((candidate / "archive-ledger-capture-status-v1.json").read_text(encoding="ascii"))
        self.assertEqual(set(manifest), MANIFEST_FIELDS)
        self.assertEqual(set(status), STATUS_FIELDS)
        self.assertEqual(
            independent_json_object(
                (candidate / "archive-source-manifest-v1.json").read_bytes().rstrip(b"\n"),
                MANIFEST_FIELDS,
            ),
            manifest,
        )
        self.assertEqual(
            independent_json_object(
                (candidate / "archive-ledger-capture-status-v1.json").read_bytes().rstrip(b"\n"),
                STATUS_FIELDS,
            ),
            status,
        )
        independent_validate_candidate(self, candidate)
        validated = normalize_result(validator(candidate))
        self.assertEqual(validated["decision"], "candidate_generated")
        for key, expected in AUTHORITY_FIELDS.items():
            self.assertIs(validated[key], expected)

        (candidate / "archive-ledger-capture-status-v1.json").unlink()
        self.assert_failure("OutputPublication", lambda: validator(candidate))

    def test_preexisting_candidate_is_never_overwritten(self):
        publisher = getattr(self.module, "publish_synthetic_candidate_for_test", None)
        self.assertTrue(callable(publisher), "helper must expose synthetic publication injection")
        existing = self.candidate_parent / "archive-ledger-candidate"
        existing.mkdir(mode=0o700)
        marker = existing / "owned"
        marker.write_bytes(b"unchanged")
        self.assert_failure(
            "OutputCollision",
            lambda: publisher(safe_archive(), self.candidate_parent),
        )
        self.assertEqual(marker.read_bytes(), b"unchanged")

    def fresh_parent(self, name):
        parent = self.attempt / name
        parent.mkdir(mode=0o700)
        return parent

    def rebind_ledger(self, candidate, filename, data):
        candidate = pathlib.Path(candidate)
        (candidate / filename).write_bytes(data)
        manifest_path = candidate / "archive-source-manifest-v1.json"
        status_path = candidate / "archive-ledger-capture-status-v1.json"
        prefix = "header_ledger" if filename.startswith("gzip-tar") else "inventory_ledger"
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        manifest[prefix + "_bytes"] = len(data)
        manifest[prefix + "_sha256"] = hashlib.sha256(data).hexdigest()
        manifest_data = canonical_json_bytes(manifest) + b"\n"
        manifest_path.write_bytes(manifest_data)
        status = json.loads(status_path.read_text(encoding="ascii"))
        status[prefix + "_bytes"] = len(data)
        status[prefix + "_sha256"] = hashlib.sha256(data).hexdigest()
        status["manifest_bytes"] = len(manifest_data)
        status["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
        status_path.write_bytes(canonical_json_bytes(status) + b"\n")

    def rebind_manifest(self, candidate, updates):
        candidate = pathlib.Path(candidate)
        manifest_path = candidate / "archive-source-manifest-v1.json"
        status_path = candidate / "archive-ledger-capture-status-v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        manifest.update(updates)
        manifest_data = canonical_json_bytes(manifest) + b"\n"
        manifest_path.write_bytes(manifest_data)
        status = json.loads(status_path.read_text(encoding="ascii"))
        status["manifest_bytes"] = len(manifest_data)
        status["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
        status_path.write_bytes(canonical_json_bytes(status) + b"\n")

    def test_ancestor_symlink_and_retained_identity_drift_are_rejected(self):
        real = self.download / "real-directory"
        real.mkdir()
        archive = real / "aeneas-macos-aarch64.tar.gz"
        archive.write_bytes(b"fixture")
        alias = self.download / "alias"
        alias.symlink_to(real.name)
        self.assert_failure(
            "InputOpen",
            lambda: self.validate_paths(
                self.download,
                alias / archive.name,
                self.attempt,
                self.candidate_parent,
            ),
        )

        direct = self.download / "aeneas-macos-aarch64.tar.gz"
        direct.write_bytes(b"fixture")
        accepted = self.module._accept_paths(
            self.download, direct, self.attempt, self.candidate_parent
        )
        try:
            direct.write_bytes(b"changed-content")
            self.assert_failure("InputIdentityDrift", accepted.verify_unchanged)
        finally:
            accepted.close()

    def test_directory_and_terminal_replacement_checkpoints_fail_closed(self):
        race = self.download / "race"
        race.mkdir()
        archive = race / "aeneas-macos-aarch64.tar.gz"
        archive.write_bytes(b"fixture")
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        moved = self.download / "race-original"
        try:
            def replace_directory(name):
                if name == "directory-after-stat:race":
                    race.rename(moved)
                    race.mkdir()
                    (race / archive.name).write_bytes(b"fixture")
            self.module._TEST_CHECKPOINT_HOOK = replace_directory
            self.assert_failure(
                "InputIdentityDrift",
                lambda: self.validate_paths(
                    self.download, archive, self.attempt, self.candidate_parent
                ),
            )
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook
            if race.exists():
                for child in race.iterdir():
                    child.unlink()
                race.rmdir()
            if moved.exists():
                moved.rename(race)

        original_hook = self.module._TEST_CHECKPOINT_HOOK
        replacement = race / "replacement"
        try:
            def replace_terminal(name):
                if name == "archive-after-stat":
                    archive.rename(replacement)
                    archive.write_bytes(b"fixture")
            self.module._TEST_CHECKPOINT_HOOK = replace_terminal
            self.assert_failure(
                "InputIdentityDrift",
                lambda: self.validate_paths(
                    self.download, archive, self.attempt, self.candidate_parent
                ),
            )
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook
            if archive.exists():
                archive.unlink()
            if replacement.exists():
                replacement.rename(archive)

    def test_every_directory_and_archive_acceptance_checkpoint_has_defined_replacement_behavior(self):
        directory_stages = (
            "before-stat", "after-stat", "before-open", "after-open", "after-fstat"
        )
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        try:
            for index, stage in enumerate(directory_stages):
                name = "race-checkpoint-{}".format(index)
                current = self.download / name
                moved = self.download / (name + "-original")
                current.mkdir()
                archive = current / "aeneas-macos-aarch64.tar.gz"
                archive.write_bytes(b"fixture")

                def replace_directory(checkpoint, target="directory-{}:{}".format(stage, name)):
                    if checkpoint == target:
                        current.rename(moved)
                        current.mkdir()
                        (current / archive.name).write_bytes(b"fixture")

                self.module._TEST_CHECKPOINT_HOOK = replace_directory
                with self.subTest(kind="directory", stage=stage):
                    def callback(archive=archive):
                        return self.validate_paths(
                            self.download, archive, self.attempt, self.candidate_parent
                        )
                    self.assert_failure("InputIdentityDrift", callback)

            for index, stage in enumerate(directory_stages):
                archive = self.download / "archive-checkpoint-{}.tar.gz".format(index)
                moved = self.download / "archive-checkpoint-{}.original".format(index)
                archive.write_bytes(b"fixture")

                def replace_archive(checkpoint, target="archive-{}".format(stage)):
                    if checkpoint == target:
                        archive.rename(moved)
                        archive.write_bytes(b"fixture")

                self.module._TEST_CHECKPOINT_HOOK = replace_archive
                with self.subTest(kind="archive", stage=stage):
                    def callback(archive=archive):
                        return self.validate_paths(
                            self.download, archive, self.attempt, self.candidate_parent
                        )
                    self.assert_failure("InputIdentityDrift", callback)
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook

    def test_candidate_parent_replacement_before_commit_marker_is_rejected(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        raw = safe_archive()
        archive.write_bytes(raw)
        accepted = self.module._accept_paths(
            self.download, archive, self.attempt, self.candidate_parent
        )
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        moved_parent = self.attempt / "phase-796a-original"
        try:
            observed, header_data, inventory_data = self.module.parse_gzip_tar_bytes(
                raw, require_profile=False
            )
            manifest_data = self.module._build_manifest(
                observed,
                header_data,
                inventory_data,
                accepted.archive_stat,
                hashlib.sha256(raw).hexdigest(),
                synthetic=True,
            )

            def replace_parent(name):
                if name == "before-status-link":
                    self.candidate_parent.rename(moved_parent)
                    self.candidate_parent.mkdir(mode=0o700)

            def precommit():
                accepted.verify_unchanged(allow_candidate_parent_metadata_change=True)

            self.module._TEST_CHECKPOINT_HOOK = replace_parent
            self.assert_failure(
                "InputIdentityDrift",
                lambda: self.module._publish_candidate_bytes(
                    accepted.candidate_parent_fd,
                    accepted.candidate_parent,
                    manifest_data,
                    header_data,
                    inventory_data,
                    before_mutation_check=accepted.verify_unchanged,
                    precommit_check=precommit,
                ),
            )
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook
            accepted.close()

    def test_candidate_directory_replacement_is_rejected_before_commit_and_cleanup(self):
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        for index, checkpoint in enumerate(
            ("before-status-link", "after-write:gzip-tar-header-ledger-v1.jsonl")
        ):
            parent = self.fresh_parent("candidate-replacement-{}".format(index))
            candidate = parent / "archive-ledger-candidate"
            moved = parent / "archive-ledger-candidate-original"

            def replace_candidate(name, checkpoint=checkpoint):
                if name == checkpoint:
                    candidate.rename(moved)
                    candidate.mkdir(mode=0o700)
                    if checkpoint.startswith("after-write"):
                        raise self.module.OutputWrite("injected-after-replacement")

            try:
                self.module._TEST_CHECKPOINT_HOOK = replace_candidate
                with self.subTest(checkpoint=checkpoint):
                    self.assert_failure(
                        "OutputPublication",
                        lambda parent=parent: self.module.publish_synthetic_candidate_for_test(
                            safe_archive(), parent
                        ),
                    )
                    self.assertTrue(moved.is_dir())
            finally:
                self.module._TEST_CHECKPOINT_HOOK = original_hook

    def test_retained_root_metadata_drift_and_all_root_overlap_orders_fail(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        archive.write_bytes(b"fixture")
        accepted = self.module._accept_paths(
            self.download, archive, self.attempt, self.candidate_parent
        )
        original_mode = stat.S_IMODE(self.download.stat().st_mode)
        try:
            self.download.chmod(0o755)
            self.assert_failure("InputIdentityDrift", accepted.verify_unchanged)
        finally:
            self.download.chmod(original_mode)
            accepted.close()

        nested_attempt = self.download / "nested-attempt"
        nested_candidate = nested_attempt / "phase-796a"
        self.assert_failure(
            "InputOverlap",
            lambda: self.module._accept_paths(
                self.download, archive, nested_attempt, nested_candidate
            ),
        )
        outer_attempt = self.root
        self.assert_failure(
            "InputOverlap",
            lambda: self.module._accept_paths(
                self.download, archive, outer_attempt, self.candidate_parent
            ),
        )

    def test_production_entry_rejects_length_then_digest_before_publication(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        raw = safe_archive()
        archive.write_bytes(raw)
        self.assert_failure(
            "InputLengthMismatch",
            lambda: self.module.inspect_archive(
                self.download, archive, self.attempt, self.candidate_parent
            ),
        )
        original_length = self.module.EXPECTED_COMPRESSED_BYTES
        try:
            self.module.EXPECTED_COMPRESSED_BYTES = len(raw)
            self.assert_failure(
                "InputDigestMismatch",
                lambda: self.module.inspect_archive(
                    self.download, archive, self.attempt, self.candidate_parent
                ),
            )
        finally:
            self.module.EXPECTED_COMPRESSED_BYTES = original_length
        self.assertFalse((self.candidate_parent / "archive-ledger-candidate").exists())

    def test_production_entry_rechecks_retained_archive_immediately_before_status_link(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        raw = safe_archive()
        archive.write_bytes(raw)
        observed, _, _ = self.module.parse_gzip_tar_bytes(raw, require_profile=False)
        names = [
            "EXPECTED_COMPRESSED_BYTES", "EXPECTED_ARCHIVE_SHA256", "EXPECTED_LOGICAL_MEMBERS",
            "EXPECTED_ROOT_COUNT", "EXPECTED_REGULAR_MEMBERS", "EXPECTED_DIRECTORY_MEMBERS",
            "EXPECTED_TOP_LEVEL", "EXPECTED_LEGACY_INVENTORY_SHA256",
            "EXPECTED_EMBEDDED_LEAN_BYTES", "EXPECTED_EMBEDDED_LEAN_SHA256",
        ]
        original = {name: getattr(self.module, name) for name in names}
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        try:
            self.module.EXPECTED_COMPRESSED_BYTES = len(raw)
            self.module.EXPECTED_ARCHIVE_SHA256 = hashlib.sha256(raw).hexdigest()
            self.module.EXPECTED_LOGICAL_MEMBERS = observed["logical_members"]
            self.module.EXPECTED_ROOT_COUNT = observed["root_count"]
            self.module.EXPECTED_REGULAR_MEMBERS = observed["regular_members"]
            self.module.EXPECTED_DIRECTORY_MEMBERS = observed["directory_members"]
            self.module.EXPECTED_TOP_LEVEL = observed["top_level"]
            self.module.EXPECTED_LEGACY_INVENTORY_SHA256 = observed["legacy_inventory_sha256"]
            self.module.EXPECTED_EMBEDDED_LEAN_BYTES = observed["embedded_lean_bytes"]
            self.module.EXPECTED_EMBEDDED_LEAN_SHA256 = observed["embedded_lean_sha256"]

            success_parent = self.fresh_parent("production-shape-success")
            status_value = self.module.inspect_archive(
                self.download, archive, self.attempt, success_parent
            )
            self.assertEqual(status_value["decision"], "candidate_generated")

            def mutate_before_link(name):
                if name == "before-status-link":
                    archive.write_bytes(b"X" * len(raw))

            self.module._TEST_CHECKPOINT_HOOK = mutate_before_link
            self.assert_failure(
                "InputIdentityDrift",
                lambda: self.module.inspect_archive(
                    self.download, archive, self.attempt, self.candidate_parent
                ),
            )
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook
            for name, value in original.items():
                setattr(self.module, name, value)
        self.assertFalse((self.candidate_parent / "archive-ledger-candidate").exists())

    def test_descriptor_duplication_failure_maps_to_closed_taxonomy(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        raw = safe_archive()
        archive.write_bytes(raw)
        original_length = self.module.EXPECTED_COMPRESSED_BYTES
        original_dup = self.module.os.dup
        try:
            self.module.EXPECTED_COMPRESSED_BYTES = len(raw)
            self.module.os.dup = lambda _fd: (_ for _ in ()).throw(OSError("injected"))
            self.assert_failure(
                "InputOpen",
                lambda: self.module.inspect_archive(
                    self.download, archive, self.attempt, self.candidate_parent
                ),
            )
        finally:
            self.module.EXPECTED_COMPRESSED_BYTES = original_length
            self.module.os.dup = original_dup

    def test_descriptor_close_failure_maps_to_closed_taxonomy(self):
        archive = self.download / "aeneas-macos-aarch64.tar.gz"
        raw = safe_archive()
        archive.write_bytes(raw)
        original_length = self.module.EXPECTED_COMPRESSED_BYTES
        original_close = self.module.os.close
        try:
            self.module.EXPECTED_COMPRESSED_BYTES = len(raw)
            self.module.os.close = lambda _fd: (_ for _ in ()).throw(OSError("injected"))
            self.assert_failure(
                "InputOpen",
                lambda: self.module.inspect_archive(
                    self.download, archive, self.attempt, self.candidate_parent
                ),
            )
        finally:
            self.module.EXPECTED_COMPRESSED_BYTES = original_length
            self.module.os.close = original_close

    def test_candidate_validator_rejects_tamper_pending_and_undeclared_files(self):
        publisher = self.module.publish_synthetic_candidate_for_test
        validator = self.module.validate_published_candidate_for_test

        parent = self.fresh_parent("tamper-status")
        candidate = pathlib.Path(publisher(safe_archive(), parent))
        status_path = candidate / "archive-ledger-capture-status-v1.json"
        status = json.loads(status_path.read_text(encoding="ascii"))
        status["unknown"] = 1
        status_path.write_bytes(canonical_json_bytes(status) + b"\n")
        self.assert_failure("OutputPublication", lambda: validator(candidate))

        parent = self.fresh_parent("extra-file")
        candidate = pathlib.Path(publisher(safe_archive(), parent))
        (candidate / "undeclared").write_bytes(b"x")
        self.assert_failure("OutputPublication", lambda: validator(candidate))

        parent = self.fresh_parent("pending-only")
        candidate = pathlib.Path(publisher(safe_archive(), parent))
        final_status = candidate / "archive-ledger-capture-status-v1.json"
        final_status.rename(candidate / ".archive-ledger-capture-status-v1.pending")
        self.assert_failure("OutputPublication", lambda: validator(candidate))

        parent = self.fresh_parent("wrong-mode")
        candidate = pathlib.Path(publisher(safe_archive(), parent))
        (candidate / "archive-source-manifest-v1.json").chmod(0o644)
        self.assert_failure("OutputPublication", lambda: validator(candidate))

    def test_each_declared_artifact_rejects_stat_open_replacement_races(self):
        original_open = self.module.os.open
        targets = list(DECLARED_ARTIFACTS)
        for index, target in enumerate(targets):
            for replacement in ("regular", "symlink"):
                parent = self.fresh_parent(
                    "artifact-race-{}-{}".format(index, replacement)
                )
                candidate = pathlib.Path(
                    self.module.publish_synthetic_candidate_for_test(
                        safe_archive(), parent
                    )
                )
                swapped = {"done": False}

                def replace_before_open(path, flags, *args, **kwargs):
                    if path == target and kwargs.get("dir_fd") is not None and not swapped["done"]:
                        swapped["done"] = True
                        directory_fd = kwargs["dir_fd"]
                        original_name = target + ".original"
                        os.rename(
                            target,
                            original_name,
                            src_dir_fd=directory_fd,
                            dst_dir_fd=directory_fd,
                        )
                        if replacement == "symlink":
                            os.symlink(original_name, target, dir_fd=directory_fd)
                        else:
                            replacement_fd = original_open(
                                target,
                                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                                0o600,
                                dir_fd=directory_fd,
                            )
                            try:
                                os.write(replacement_fd, b"replacement")
                            finally:
                                os.close(replacement_fd)
                    return original_open(path, flags, *args, **kwargs)

                try:
                    self.module.os.open = replace_before_open
                    with self.subTest(target=target, replacement=replacement):
                        self.assert_failure(
                            "OutputPublication",
                            lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                                candidate
                            ),
                        )
                        self.assertTrue(swapped["done"])
                finally:
                    self.module.os.open = original_open

    def test_candidate_validator_rejects_semantic_tamper_with_rebound_digests(self):
        parent = self.fresh_parent("semantic-tamper")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        header_path = candidate / "gzip-tar-header-ledger-v1.jsonl"
        manifest_path = candidate / "archive-source-manifest-v1.json"
        status_path = candidate / "archive-ledger-capture-status-v1.json"

        header_rows = decode_jsonl(header_path.read_bytes())
        header_rows[1]["raw_name_hex"] = "00" * 100
        header_data = b"".join(canonical_json_bytes(row) + b"\n" for row in header_rows)
        header_path.write_bytes(header_data)

        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        manifest["header_ledger_bytes"] = len(header_data)
        manifest["header_ledger_sha256"] = hashlib.sha256(header_data).hexdigest()
        manifest_data = canonical_json_bytes(manifest) + b"\n"
        manifest_path.write_bytes(manifest_data)

        status = json.loads(status_path.read_text(encoding="ascii"))
        status["header_ledger_bytes"] = len(header_data)
        status["header_ledger_sha256"] = hashlib.sha256(header_data).hexdigest()
        status["manifest_bytes"] = len(manifest_data)
        status["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
        status_path.write_bytes(canonical_json_bytes(status) + b"\n")
        self.assert_failure(
            "OutputPublication",
            lambda: self.module.validate_published_candidate_for_test(candidate),
        )

    def test_every_manifest_and_status_authority_field_is_fixed(self):
        for artifact in ("manifest", "status"):
            for index, (field, required) in enumerate(AUTHORITY_FIELDS.items()):
                parent = self.fresh_parent(
                    "authority-{}-{}".format(artifact, index)
                )
                candidate = pathlib.Path(
                    self.module.publish_synthetic_candidate_for_test(
                        safe_archive(), parent
                    )
                )
                manifest_path = candidate / "archive-source-manifest-v1.json"
                status_path = candidate / "archive-ledger-capture-status-v1.json"
                if artifact == "manifest":
                    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
                    manifest[field] = not required
                    manifest_data = canonical_json_bytes(manifest) + b"\n"
                    manifest_path.write_bytes(manifest_data)
                    status = json.loads(status_path.read_text(encoding="ascii"))
                    status["manifest_bytes"] = len(manifest_data)
                    status["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
                    status_path.write_bytes(canonical_json_bytes(status) + b"\n")
                else:
                    status = json.loads(status_path.read_text(encoding="ascii"))
                    status[field] = not required
                    status_path.write_bytes(canonical_json_bytes(status) + b"\n")
                with self.subTest(artifact=artifact, field=field):
                    self.assert_failure(
                        "OutputPublication",
                        lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                            candidate
                        ),
                    )

    def test_manifest_asset_authority_and_production_profile_are_reconstructed(self):
        replacements = {
            "asset_id": "replacement-asset",
            "url": "synthetic:replacement",
            "release_id": 1,
            "github_asset_id": 1,
            "filename": "replacement.tar.gz",
            "tag_commit": "1" * 40,
            "expected_compressed_bytes": 1,
            "expected_archive_sha256": "1" * 64,
            "release_immutable": True,
        }
        for index, (field, replacement) in enumerate(replacements.items()):
            parent = self.fresh_parent("asset-authority-{}".format(index))
            candidate = pathlib.Path(
                self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
            )
            updates = {field: replacement}
            if field == "expected_compressed_bytes":
                updates["archive_byte_length"] = replacement
            elif field == "expected_archive_sha256":
                updates["archive_sha256"] = replacement
            self.rebind_manifest(candidate, updates)
            with self.subTest(field=field):
                self.assert_failure(
                    "OutputPublication",
                    lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                        candidate
                    ),
                )

        parent = self.fresh_parent("production-profile-reconstruction")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        self.rebind_manifest(
            candidate,
            {
                **PINNED_ASSET_AUTHORITY,
                "archive_byte_length": PINNED_ASSET_AUTHORITY["expected_compressed_bytes"],
                "archive_sha256": PINNED_ASSET_AUTHORITY["expected_archive_sha256"],
            },
        )
        candidate_fd = os.open(
            candidate,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
        )
        try:
            try:
                self.module._validate_candidate_fd(candidate_fd)
            except self.module.OutputPublication as error:
                self.assertEqual(error.diagnostic, "manifest-profile-ProfileMismatch")
            else:
                self.fail("production profile mismatch was accepted")
        finally:
            os.close(candidate_fd)

    def test_candidate_reconstructs_complete_optional_gzip_header(self):
        raw = gzip_member(
            tar_stream(tar_member(b"a", b"x")),
            extra=b"AB\0\0",
            filename=b"name",
            comment=b"comment",
            header_crc=True,
        )

        def mutate(name, callback):
            parent = self.fresh_parent("gzip-reconstruction-" + name)
            candidate = pathlib.Path(
                self.module.publish_synthetic_candidate_for_test(raw, parent)
            )
            header_path = candidate / "gzip-tar-header-ledger-v1.jsonl"
            rows = decode_jsonl(header_path.read_bytes())
            callback(rows[-1])
            data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
            self.rebind_ledger(candidate, "gzip-tar-header-ledger-v1.jsonl", data)
            self.assert_failure(
                "OutputPublication",
                lambda: self.module.validate_published_candidate_for_test(candidate),
            )

        def malformed_extra(row):
            payload = b"AB\x01\0"
            row["fextra_hex"] = payload.hex()
            row["fextra_bytes"] = len(payload)
            row["fextra_sha256"] = hashlib.sha256(payload).hexdigest()

        def nul_filename(row):
            payload = b"a\0"
            row["fname_hex"] = payload.hex()
            row["fname_bytes"] = len(payload)
            row["fname_sha256"] = hashlib.sha256(payload).hexdigest()

        def oversized_comment(row):
            payload = b"c" * (self.module.MAX_GZIP_COMMENT_BYTES + 1)
            row["fcomment_hex"] = payload.hex()
            row["fcomment_bytes"] = len(payload)
            row["fcomment_sha256"] = hashlib.sha256(payload).hexdigest()

        def wrong_hcrc(row):
            row["fhcrc16"] = (row["fhcrc16"] + 1) & 0xFFFF
            row["fhcrc_hex"] = struct.pack("<H", row["fhcrc16"]).hex()

        mutate("extra", malformed_extra)
        mutate("extra-xlen-width", lambda row: row.__setitem__(
            "fextra_xlen_hex", "00" * 3
        ))
        mutate("filename", nul_filename)
        mutate("comment", oversized_comment)
        mutate("hcrc", wrong_hcrc)
        mutate("hcrc-width", lambda row: row.__setitem__(
            "fhcrc_hex", "00" * 3
        ))
        mutate("deflate-offset", lambda row: row.__setitem__(
            "deflate_offset", row["deflate_offset"] + 1
        ))

        parent = self.fresh_parent("gzip-reconstruction-aggregate")
        candidate = self.module.publish_synthetic_candidate_for_test(raw, parent)
        original_total = self.module.MAX_GZIP_OPTIONAL_BYTES_TOTAL
        try:
            self.module.MAX_GZIP_OPTIONAL_BYTES_TOTAL = len(b"AB\0\0namecomment") - 1
            self.assert_failure(
                "OutputPublication",
                lambda: self.module.validate_published_candidate_for_test(candidate),
            )
        finally:
            self.module.MAX_GZIP_OPTIONAL_BYTES_TOTAL = original_total

    def test_fixed_width_hex_and_trailing_limits_precede_decode_and_hash(self):
        raw = gzip_member(
            tar_stream(tar_member(b"a", b"x")),
            extra=b"AB\0\0",
            header_crc=True,
        )
        builtin_bytes = bytes
        for index, field in enumerate(("fextra_xlen_hex", "fhcrc_hex")):
            parent = self.fresh_parent("predecode-{}".format(index))
            candidate = pathlib.Path(
                self.module.publish_synthetic_candidate_for_test(raw, parent)
            )
            header_path = candidate / "gzip-tar-header-ledger-v1.jsonl"
            rows = decode_jsonl(header_path.read_bytes())
            guarded_value = "00" * 3
            rows[-1][field] = guarded_value
            data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
            self.rebind_ledger(candidate, "gzip-tar-header-ledger-v1.jsonl", data)
            decoded = []

            class GuardedBytes:
                def __call__(self, *args, **kwargs):
                    return builtin_bytes(*args, **kwargs)

                def fromhex(self, value):
                    if value == guarded_value:
                        decoded.append(value)
                        raise AssertionError("fixed-width field decoded before rejection")
                    return builtin_bytes.fromhex(value)

            self.module.bytes = GuardedBytes()
            try:
                with self.subTest(field=field):
                    self.assert_failure(
                        "OutputPublication",
                        lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                            candidate
                        ),
                    )
                    self.assertEqual(decoded, [])
            finally:
                del self.module.bytes

        parent = self.fresh_parent("prehash-trailing")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        header_path = candidate / "gzip-tar-header-ledger-v1.jsonl"
        rows = decode_jsonl(header_path.read_bytes())
        guarded_size = self.module.MAX_TRAILING_ZERO_BYTES + 1
        rows[-2]["padding_bytes"] = guarded_size
        rows[-2]["padding_sha256"] = "0" * 64
        data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
        self.rebind_ledger(candidate, "gzip-tar-header-ledger-v1.jsonl", data)
        original_sha256_hex = self.module.sha256_hex
        hashed = []

        def guarded_sha256_hex(value):
            if len(value) == guarded_size:
                hashed.append(len(value))
                raise AssertionError("trailing padding hashed before rejection")
            return original_sha256_hex(value)

        self.module.sha256_hex = guarded_sha256_hex
        try:
            self.assert_failure(
                "OutputPublication",
                lambda: self.module.validate_published_candidate_for_test(candidate),
            )
            self.assertEqual(hashed, [])
        finally:
            self.module.sha256_hex = original_sha256_hex

    def test_candidate_reapplies_every_reconstructed_size_limit(self):
        safe_parent = self.fresh_parent("candidate-limit-safe")
        safe_candidate = self.module.publish_synthetic_candidate_for_test(
            safe_archive(), safe_parent
        )
        safe_observed = self.parse(safe_archive())["observed"]
        extended_raw = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(b"renamed"), member_type=b"x"),
                tar_member(b"ignored", b"x"),
            )
        )
        extended_parent = self.fresh_parent("candidate-limit-extended")
        extended_candidate = self.module.publish_synthetic_candidate_for_test(
            extended_raw, extended_parent
        )
        trailing_raw = gzip_member(
            tar_stream(tar_member(b"a", b"x"), trailing_zero_bytes=512)
        )
        trailing_parent = self.fresh_parent("candidate-limit-trailing")
        trailing_candidate = self.module.publish_synthetic_candidate_for_test(
            trailing_raw, trailing_parent
        )
        cases = (
            ("MAX_PHYSICAL_TAR_HEADERS", 1, safe_candidate),
            ("MAX_LOGICAL_MEMBERS", 1, safe_candidate),
            ("MAX_MEMBER_BYTES", len(b"payload") - 1, safe_candidate),
            ("MAX_AGGREGATE_REGULAR_BYTES", len(b"payload") - 1, safe_candidate),
            ("MAX_TOTAL_EXTRACTION_OUTPUT_BYTES", len(b"payload") - 1, safe_candidate),
            (
                "MAX_UNCOMPRESSED_TAR_BYTES",
                safe_observed["uncompressed_tar_bytes"] - 1,
                safe_candidate,
            ),
            ("MAX_EXTENSION_HEADERS", 0, extended_candidate),
            ("MAX_EXTENSION_PAYLOAD_BYTES", 0, extended_candidate),
            ("MAX_EXTENSION_PAYLOAD_BYTES_TOTAL", 0, extended_candidate),
            ("MAX_TRAILING_ZERO_BYTES", 511, trailing_candidate),
            (
                "MAX_COMPRESSION_RATIO",
                (safe_observed["uncompressed_tar_bytes"] - 1) // len(safe_archive()),
                safe_candidate,
            ),
        )
        for limit_name, rejected_limit, candidate in cases:
            original = getattr(self.module, limit_name)
            try:
                setattr(self.module, limit_name, rejected_limit)
                with self.subTest(limit=limit_name):
                    self.assert_failure(
                        "OutputPublication",
                        lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                            candidate
                        ),
                    )
            finally:
                setattr(self.module, limit_name, original)

        rebound_parent = self.fresh_parent("candidate-limit-rebound-trailing")
        rebound_candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(
                safe_archive(), rebound_parent
            )
        )
        header_path = rebound_candidate / "gzip-tar-header-ledger-v1.jsonl"
        rows = decode_jsonl(header_path.read_bytes())
        rows[-2]["padding_bytes"] = 1 << 63
        rows[-2]["padding_sha256"] = "0" * 64
        rebound_data = b"".join(
            canonical_json_bytes(row) + b"\n" for row in rows
        )
        self.rebind_ledger(
            rebound_candidate,
            "gzip-tar-header-ledger-v1.jsonl",
            rebound_data,
        )
        self.assert_failure(
            "OutputPublication",
            lambda: self.module.validate_published_candidate_for_test(
                rebound_candidate
            ),
        )

    def test_rebound_numeric_ranges_and_nested_indices_fail_closed(self):
        manifest_cases = (
            ({"archive_device": -1}, False),
            ({"archive_device": (1 << 64)}, False),
            ({"archive_modified_seconds": -(1 << 63)}, True),
            ({"archive_changed_seconds": (1 << 63) - 1}, True),
            ({"archive_modified_seconds": -(1 << 63) - 1}, False),
            ({"archive_changed_seconds": (1 << 63)}, False),
            ({"archive_modified_nanoseconds": 999_999_999}, True),
            ({"archive_changed_nanoseconds": 1_000_000_000}, False),
        )
        for index, (updates, accepted) in enumerate(manifest_cases):
            parent = self.fresh_parent("manifest-range-{}".format(index))
            candidate = pathlib.Path(
                self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
            )
            self.rebind_manifest(candidate, updates)
            with self.subTest(manifest=updates):
                if accepted:
                    self.module.validate_published_candidate_for_test(candidate)
                else:
                    self.assert_failure(
                        "OutputPublication",
                        lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                            candidate
                        ),
                    )

        for index, value in enumerate((-1, 1 << 64)):
            parent = self.fresh_parent("status-range-{}".format(index))
            candidate = pathlib.Path(
                self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
            )
            status_path = candidate / "archive-ledger-capture-status-v1.json"
            status = json.loads(status_path.read_text(encoding="ascii"))
            status["manifest_bytes"] = value
            status_path.write_bytes(canonical_json_bytes(status) + b"\n")
            self.assert_failure(
                "OutputPublication",
                lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                    candidate
                ),
            )

        extended = gzip_member(
            tar_stream(
                tar_member(b"PaxHeader", pax_record(b"renamed"), member_type=b"x"),
                tar_member(b"ignored", b"x"),
            )
        )
        for index, value in enumerate((False, -1, 1 << 64)):
            parent = self.fresh_parent("nested-index-{}".format(index))
            candidate = pathlib.Path(
                self.module.publish_synthetic_candidate_for_test(extended, parent)
            )
            inventory_path = candidate / "ordered-logical-member-inventory-v1.jsonl"
            rows = decode_jsonl(inventory_path.read_bytes())
            rows[1]["extension_header_indices"] = [value]
            data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
            self.rebind_ledger(
                candidate,
                "ordered-logical-member-inventory-v1.jsonl",
                data,
            )
            self.assert_failure(
                "OutputPublication",
                lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                    candidate
                ),
            )

    def test_candidate_validator_rejects_boolean_u64_with_rebound_digests(self):
        parent = self.fresh_parent("boolean-u64")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        inventory_path = candidate / "ordered-logical-member-inventory-v1.jsonl"
        manifest_path = candidate / "archive-source-manifest-v1.json"
        status_path = candidate / "archive-ledger-capture-status-v1.json"
        rows = decode_jsonl(inventory_path.read_bytes())
        rows[0]["row_index"] = False
        inventory_data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
        inventory_path.write_bytes(inventory_data)
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        manifest["inventory_ledger_bytes"] = len(inventory_data)
        manifest["inventory_ledger_sha256"] = hashlib.sha256(inventory_data).hexdigest()
        manifest_data = canonical_json_bytes(manifest) + b"\n"
        manifest_path.write_bytes(manifest_data)
        status = json.loads(status_path.read_text(encoding="ascii"))
        status["inventory_ledger_bytes"] = len(inventory_data)
        status["inventory_ledger_sha256"] = hashlib.sha256(inventory_data).hexdigest()
        status["manifest_bytes"] = len(manifest_data)
        status["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
        status_path.write_bytes(canonical_json_bytes(status) + b"\n")
        self.assert_failure(
            "OutputPublication",
            lambda: self.module.validate_published_candidate_for_test(candidate),
        )

    def test_candidate_validator_rejects_reserved_gzip_flags_and_invented_logical_names(self):
        parent = self.fresh_parent("reserved-gzip")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        header_path = candidate / "gzip-tar-header-ledger-v1.jsonl"
        rows = decode_jsonl(header_path.read_bytes())
        fixed = bytearray.fromhex(rows[-1]["fixed_header_hex"])
        fixed[3] = 0x20
        rows[-1]["fixed_header_hex"] = fixed.hex()
        rows[-1]["flg"] = 0x20
        header_data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
        self.rebind_ledger(candidate, "gzip-tar-header-ledger-v1.jsonl", header_data)
        self.assert_failure(
            "OutputPublication",
            lambda: self.module.validate_published_candidate_for_test(candidate),
        )

        parent = self.fresh_parent("invented-logical-name")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        inventory_path = candidate / "ordered-logical-member-inventory-v1.jsonl"
        rows = decode_jsonl(inventory_path.read_bytes())
        rows[2]["effective_raw_name"] = "invented.txt"
        rows[2]["collision_key"] = "invented.txt"
        inventory_data = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
        self.rebind_ledger(
            candidate, "ordered-logical-member-inventory-v1.jsonl", inventory_data
        )
        self.assert_failure(
            "OutputPublication",
            lambda: self.module.validate_published_candidate_for_test(candidate),
        )

    def test_manifest_allows_only_the_two_signed_timestamp_seconds(self):
        parent = self.fresh_parent("signed-seconds")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        manifest_path = candidate / "archive-source-manifest-v1.json"
        status_path = candidate / "archive-ledger-capture-status-v1.json"

        def rewrite_manifest(field, value):
            manifest = json.loads(manifest_path.read_text(encoding="ascii"))
            manifest[field] = value
            manifest_data = canonical_json_bytes(manifest) + b"\n"
            manifest_path.write_bytes(manifest_data)
            status = json.loads(status_path.read_text(encoding="ascii"))
            status["manifest_bytes"] = len(manifest_data)
            status["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
            status_path.write_bytes(canonical_json_bytes(status) + b"\n")

        rewrite_manifest("archive_modified_seconds", -1)
        self.module.validate_published_candidate_for_test(candidate)
        rewrite_manifest("archive_device", -1)
        self.assert_failure(
            "OutputPublication",
            lambda: self.module.validate_published_candidate_for_test(candidate),
        )

    def test_every_manifest_and_status_field_rejects_an_incompatible_json_type(self):
        parent = self.fresh_parent("artifact-types")
        candidate = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
        )
        manifest = json.loads(
            (candidate / "archive-source-manifest-v1.json").read_text(encoding="ascii")
        )
        status = json.loads(
            (candidate / "archive-ledger-capture-status-v1.json").read_text(encoding="ascii")
        )

        for key, value in manifest.items():
            changed = dict(manifest)
            if isinstance(value, bool):
                changed[key] = 0
            elif isinstance(value, int):
                changed[key] = False
            elif isinstance(value, str):
                changed[key] = []
            elif isinstance(value, list):
                changed[key] = "not-an-array"
            else:
                self.fail("unhandled manifest JSON type")
            with self.subTest(artifact="manifest", field=key):
                self.assert_failure(
                    "OutputPublication",
                    lambda changed=changed: self.module._validate_manifest_types(changed),
                )

        for key, value in status.items():
            changed = dict(status)
            if isinstance(value, bool):
                changed[key] = 0
            elif isinstance(value, int):
                changed[key] = False
            elif isinstance(value, str):
                changed[key] = []
            elif isinstance(value, list):
                changed[key] = "not-an-array"
            else:
                self.fail("unhandled status JSON type")
            with self.subTest(artifact="status", field=key):
                self.assert_failure(
                    "OutputPublication",
                    lambda changed=changed: self.module._validate_status_types(changed),
                )

    def test_publication_checkpoint_failures_roll_back_without_commit_marker(self):
        checkpoints = ["before-candidate-mkdir", "after-candidate-mkdir"]
        for filename in (
            "gzip-tar-header-ledger-v1.jsonl",
            "ordered-logical-member-inventory-v1.jsonl",
            "archive-source-manifest-v1.json",
            ".archive-ledger-capture-status-v1.pending",
        ):
            checkpoints.extend(
                stage + ":" + filename
                for stage in (
                    "before-create", "after-create", "before-write", "after-write",
                    "before-fsync", "after-fsync",
                )
            )
        for label in (
            "candidate-before-status-link", "candidate-after-status-link",
            "candidate-after-pending-unlink", "parent-after-publication",
        ):
            checkpoints.extend(
                ("before-directory-fsync:" + label, "after-directory-fsync:" + label)
            )
        checkpoints.extend(
            ("before-status-link", "after-status-link", "before-pending-unlink", "after-pending-unlink")
        )
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        try:
            for index, checkpoint in enumerate(checkpoints):
                parent = self.fresh_parent("checkpoint-{}".format(index))

                def reject(name, target=checkpoint):
                    if name == target:
                        raise self.module.OutputWrite("injected-checkpoint")

                self.module._TEST_CHECKPOINT_HOOK = reject
                with self.subTest(checkpoint=checkpoint):
                    self.assert_failure(
                        "OutputWrite",
                        lambda parent=parent: self.module.publish_synthetic_candidate_for_test(
                            safe_archive(), parent
                        ),
                    )
                    self.assertFalse((parent / "archive-ledger-candidate").exists())
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook

    def test_crash_states_preserve_exact_commit_marker_semantics(self):
        class SimulatedCrash(BaseException):
            pass

        original_hook = self.module._TEST_CHECKPOINT_HOOK
        status_name = "archive-ledger-capture-status-v1.json"
        pending_name = ".archive-ledger-capture-status-v1.pending"

        def crash_at(checkpoint, parent_name):
            parent = self.fresh_parent(parent_name)

            def crash(name):
                if name == checkpoint:
                    raise SimulatedCrash(checkpoint)

            self.module._TEST_CHECKPOINT_HOOK = crash
            with self.assertRaises(SimulatedCrash):
                self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
            return parent / "archive-ledger-candidate"

        try:
            pre_link_checkpoints = ["before-candidate-mkdir", "after-candidate-mkdir"]
            for filename in (
                "gzip-tar-header-ledger-v1.jsonl",
                "ordered-logical-member-inventory-v1.jsonl",
                "archive-source-manifest-v1.json",
                pending_name,
            ):
                pre_link_checkpoints.extend(
                    stage + ":" + filename
                    for stage in (
                        "before-create", "after-create", "before-write", "after-write",
                        "before-fsync", "after-fsync",
                    )
                )
            pre_link_checkpoints.extend(
                (
                    "before-directory-fsync:candidate-before-status-link",
                    "after-directory-fsync:candidate-before-status-link",
                    "before-status-link",
                )
            )
            for index, checkpoint in enumerate(pre_link_checkpoints):
                candidate = crash_at(checkpoint, "crash-pre-link-{}".format(index))
                with self.subTest(crash_state="pre-link", checkpoint=checkpoint):
                    self.assertFalse((candidate / status_name).exists())
                    self.assert_failure(
                        "OutputPublication",
                        lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                            candidate
                        ),
                    )

            linked_checkpoints = (
                "after-status-link",
                "before-directory-fsync:candidate-after-status-link",
                "after-directory-fsync:candidate-after-status-link",
                "before-pending-unlink",
            )
            linked_candidates = []
            for index, checkpoint in enumerate(linked_checkpoints):
                candidate = crash_at(checkpoint, "crash-linked-{}".format(index))
                linked_candidates.append(candidate)
                with self.subTest(crash_state="linked-pending", checkpoint=checkpoint):
                    self.assertTrue((candidate / status_name).is_file())
                    self.assertTrue((candidate / pending_name).is_file())
                    self.assert_failure(
                        "OutputPublication",
                        lambda candidate=candidate: self.module.validate_published_candidate_for_test(
                            candidate
                        ),
                    )

            linked = linked_candidates[-1]
            pending_stat = os.stat(linked / pending_name, follow_symlinks=False)
            status_stat = os.stat(linked / status_name, follow_symlinks=False)
            self.assertEqual((pending_stat.st_dev, pending_stat.st_ino),
                             (status_stat.st_dev, status_stat.st_ino))
            status = independent_json_object(
                (linked / status_name).read_bytes().rstrip(b"\n"), STATUS_FIELDS
            )
            for filename, prefix in (
                ("archive-source-manifest-v1.json", "manifest"),
                ("gzip-tar-header-ledger-v1.jsonl", "header_ledger"),
                ("ordered-logical-member-inventory-v1.jsonl", "inventory_ledger"),
            ):
                data = (linked / filename).read_bytes()
                self.assertEqual(len(data), status[prefix + "_bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 status[prefix + "_sha256"])
            committed_checkpoints = (
                "after-pending-unlink",
                "before-directory-fsync:candidate-after-pending-unlink",
                "after-directory-fsync:candidate-after-pending-unlink",
                "before-directory-fsync:parent-after-publication",
                "after-directory-fsync:parent-after-publication",
            )
            for index, checkpoint in enumerate(committed_checkpoints):
                candidate = crash_at(checkpoint, "crash-committed-{}".format(index))
                with self.subTest(crash_state="final-only", checkpoint=checkpoint):
                    self.assertTrue((candidate / status_name).is_file())
                    self.assertFalse((candidate / pending_name).exists())
                    independent_validate_candidate(self, candidate)
                    self.module.validate_published_candidate_for_test(candidate)
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook

    def test_partial_zero_progress_write_link_conflict_and_cleanup_failure(self):
        original_write = self.module.os.write
        parent = self.fresh_parent("partial-write")
        try:
            def partial_write(fd, data):
                amount = max(1, len(data) // 2)
                return original_write(fd, data[:amount])
            self.module.os.write = partial_write
            candidate = self.module.publish_synthetic_candidate_for_test(safe_archive(), parent)
            self.module.validate_published_candidate_for_test(candidate)
        finally:
            self.module.os.write = original_write

        for name, replacement in (
            ("zero-progress", lambda _fd, _data: 0),
            ("enospc", lambda _fd, _data: (_ for _ in ()).throw(OSError(28, "No space left"))),
        ):
            parent = self.fresh_parent(name)
            try:
                self.module.os.write = replacement
                self.assert_failure(
                    "OutputWrite",
                    lambda parent=parent: self.module.publish_synthetic_candidate_for_test(
                        safe_archive(), parent
                    ),
                )
            finally:
                self.module.os.write = original_write
            self.assertFalse((parent / "archive-ledger-candidate").exists())

        partial_error_parent = self.fresh_parent("partial-then-error")
        calls = {"count": 0}
        try:
            def partial_then_error(fd, data):
                calls["count"] += 1
                if calls["count"] == 1:
                    return original_write(fd, data[:1])
                raise OSError(28, "No space left")
            self.module.os.write = partial_then_error
            self.assert_failure(
                "OutputWrite",
                lambda: self.module.publish_synthetic_candidate_for_test(
                    safe_archive(), partial_error_parent
                ),
            )
        finally:
            self.module.os.write = original_write
        self.assertFalse((partial_error_parent / "archive-ledger-candidate").exists())

        conflict_parent = self.fresh_parent("status-link-conflict")
        original_hook = self.module._TEST_CHECKPOINT_HOOK
        try:
            def create_conflict(name):
                if name == "before-status-link":
                    conflict = conflict_parent / "archive-ledger-candidate" / "archive-ledger-capture-status-v1.json"
                    conflict.write_bytes(b"conflict")
                    conflict.chmod(0o600)
            self.module._TEST_CHECKPOINT_HOOK = create_conflict
            self.assert_failure(
                "OutputPublication",
                lambda: self.module.publish_synthetic_candidate_for_test(
                    safe_archive(), conflict_parent
                ),
            )
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook
        self.assertFalse((conflict_parent / "archive-ledger-candidate").exists())

        cleanup_parent = self.fresh_parent("cleanup-failure")
        original_unlink = self.module.os.unlink
        try:
            def stop_after_write(name):
                if name == "after-write:gzip-tar-header-ledger-v1.jsonl":
                    raise self.module.OutputWrite("injected")
            def reject_unlink(*_args, **_kwargs):
                raise OSError("injected")
            self.module._TEST_CHECKPOINT_HOOK = stop_after_write
            self.module.os.unlink = reject_unlink
            self.assert_failure(
                "OutputPublication",
                lambda: self.module.publish_synthetic_candidate_for_test(
                    safe_archive(), cleanup_parent
                ),
            )
        finally:
            self.module._TEST_CHECKPOINT_HOOK = original_hook
            self.module.os.unlink = original_unlink

    def test_publication_durability_and_candidate_byte_limits_fail_closed(self):
        original_fsync = self.module.os.fsync
        parent = self.fresh_parent("durability")
        try:
            def reject_fsync(_fd):
                raise OSError("injected")
            self.module.os.fsync = reject_fsync
            self.assert_failure(
                "OutputDurability",
                lambda: self.module.publish_synthetic_candidate_for_test(safe_archive(), parent),
            )
        finally:
            self.module.os.fsync = original_fsync
        self.assertFalse((parent / "archive-ledger-candidate").exists())

        baseline_parent = self.fresh_parent("limit-baseline")
        baseline = pathlib.Path(
            self.module.publish_synthetic_candidate_for_test(safe_archive(), baseline_parent)
        )
        exact_limits = {
            "MAX_MANIFEST_BYTES": (baseline / "archive-source-manifest-v1.json").stat().st_size,
            "MAX_STATUS_BYTES": (baseline / "archive-ledger-capture-status-v1.json").stat().st_size,
            "MAX_TOTAL_CANDIDATE_BYTES": sum(path.stat().st_size for path in baseline.iterdir()),
        }
        for index, (limit_name, exact) in enumerate(exact_limits.items()):
            original = getattr(self.module, limit_name)
            try:
                accepted_parent = self.fresh_parent("limit-accepted-{}".format(index))
                setattr(self.module, limit_name, exact)
                self.module.publish_synthetic_candidate_for_test(safe_archive(), accepted_parent)

                rejected_parent = self.fresh_parent("limit-rejected-{}".format(index))
                setattr(self.module, limit_name, exact - 1)
                self.assert_failure(
                    "CandidateByteLimit",
                    lambda parent=rejected_parent: self.module.publish_synthetic_candidate_for_test(
                        safe_archive(), parent
                    ),
                )
                self.assertFalse((rejected_parent / "archive-ledger-candidate").exists())
            finally:
                setattr(self.module, limit_name, original)


class FixtureBuilderTests(unittest.TestCase):
    def test_fixture_builders_are_deterministic_and_do_not_touch_network(self):
        self.assertEqual(safe_archive(), safe_archive())
        header = ustar_header(b"a", size=1)
        stored = int(header[148:154], 8)
        checksum_view = bytearray(header)
        checksum_view[148:156] = b"        "
        self.assertEqual(stored, sum(checksum_view))
        raw = gzip_member(tar_stream(tar_member(b"a", b"x")))
        self.assertEqual(raw[:3], b"\x1f\x8b\x08")
        self.assertNotIn(b"https://", raw)


if __name__ == "__main__":
    unittest.main()
