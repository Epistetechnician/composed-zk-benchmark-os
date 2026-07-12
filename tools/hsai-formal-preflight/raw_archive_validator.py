#!/usr/bin/python3
"""Fail-closed archive validation for the bounded HSAI Aeneas lane."""

import argparse
import gzip
import hashlib
import json
import os
import stat
import sys
import tarfile
import tempfile


SCHEMA = "hsai-raw-archive-validation-v1"
SELF_TEST_SCHEMA = "hsai-raw-archive-self-test-v1"
BLOCK = 512
ALLOWED_TYPES = (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
MAIN_PROFILE = {
    "logical_members": 2471,
    "root_count": 0,
    "regular_members": 2305,
    "directory_members": 166,
    "top_level": ["aeneas", "backends", "charon", "charon-driver", "libs", "rust-toolchain"],
    "inventory_sha256": "26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e",
}
LEAN_PROFILE = {
    "logical_members": 2125,
    "root_count": 1,
    "regular_members": 2021,
    "directory_members": 104,
    "top_level": ["ir", "lib"],
    "inventory_sha256": "8242938ad079bf2ee9359b29f8c7a257c88b27d4efac8d67ba167b6730999ff4",
}
EMBEDDED_LEAN = "backends/lean/.lake/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz"


class ValidationError(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class RawAwareTarInfo(tarfile.TarInfo):
    @classmethod
    def frombuf(cls, buf, encoding, errors):
        if len(buf) == BLOCK:
            raw_name = buf[0:100]
            raw_type = buf[156:157]
            raw_prefix = buf[345:500]
        else:
            raw_name = raw_type = raw_prefix = None
        value = super().frombuf(buf, encoding, errors)
        value.hsai_raw_name = raw_name
        value.hsai_raw_type = raw_type
        value.hsai_raw_prefix = raw_prefix
        return value


def canonical_json(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def fail(code, detail):
    raise ValidationError(code, detail)


def decode_field(raw, label):
    if raw is None:
        fail("missing_raw_metadata", label)
    try:
        return raw.split(b"\0", 1)[0].decode("utf-8", "strict")
    except UnicodeDecodeError:
        fail("invalid_utf8", label)


def parse_octal(raw, label):
    stripped = raw.rstrip(b"\0 ").lstrip(b" ")
    if not stripped:
        return 0
    if stripped[:1] == b"\x80":
        fail("unsupported_numeric_encoding", label)
    try:
        return int(stripped, 8)
    except ValueError:
        fail("malformed_numeric_field", label)


def header_checksum(header):
    stored = parse_octal(header[148:156], "checksum")
    unsigned = sum(header[:148]) + (8 * 32) + sum(header[156:])
    signed = sum(byte if byte < 128 else byte - 256 for byte in header[:148]) + (8 * 32) + sum(
        byte if byte < 128 else byte - 256 for byte in header[156:]
    )
    if stored not in (unsigned, signed):
        fail("invalid_checksum", "tar header checksum mismatch")


def parse_pax(payload):
    result = {}
    pos = 0
    while pos < len(payload):
        space = payload.find(b" ", pos)
        if space < 0 or space == pos:
            fail("invalid_pax_length", "missing PAX record length")
        try:
            length = int(payload[pos:space])
        except ValueError:
            fail("invalid_pax_length", "nondecimal PAX record length")
        end = pos + length
        if length <= space - pos + 3 or end > len(payload) or payload[end - 1 : end] != b"\n":
            fail("invalid_pax_length", "PAX record length is inconsistent")
        body = payload[space + 1 : end - 1]
        if b"=" not in body:
            fail("invalid_pax_record", "PAX record has no equals sign")
        key_raw, value_raw = body.split(b"=", 1)
        try:
            key = key_raw.decode("utf-8", "strict")
            value = value_raw.decode("utf-8", "strict")
        except UnicodeDecodeError:
            fail("invalid_utf8", "PAX record")
        if key in result:
            fail("duplicate_pax_key", key)
        result[key] = value
        pos = end
    if pos != len(payload):
        fail("unconsumed_pax_payload", "PAX payload was not consumed exactly")
    return result


def normalize_name(raw_name, member_type, size):
    if raw_name in (".", "./"):
        if member_type != tarfile.DIRTYPE or size != 0:
            fail("invalid_root_marker", raw_name)
        return ".", True
    if not raw_name:
        fail("empty_name", "logical member name is empty")
    if raw_name.startswith("/"):
        fail("absolute_path", raw_name)
    if raw_name.startswith("./"):
        raw_name = raw_name[2:]
        if raw_name.startswith("./"):
            fail("repeated_leading_dot", raw_name)
    if raw_name.endswith("/"):
        if member_type != tarfile.DIRTYPE or raw_name.endswith("//"):
            fail("invalid_trailing_separator", raw_name)
        raw_name = raw_name[:-1]
    parts = raw_name.split("/")
    if any(part == "" for part in parts):
        fail("repeated_separator", raw_name)
    if any(part == "." for part in parts):
        fail("internal_dot", raw_name)
    if any(part == ".." for part in parts):
        fail("parent_component", raw_name)
    return "/".join(parts), False


def read_exact(handle, size, label):
    chunks = []
    remaining = size
    while remaining:
        chunk = handle.read(min(1024 * 1024, remaining))
        if not chunk:
            fail("truncated_archive", label)
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def skip_exact(handle, size, label):
    remaining = size
    while remaining:
        chunk = handle.read(min(1024 * 1024, remaining))
        if not chunk:
            fail("truncated_archive", label)
        remaining -= len(chunk)


def scan_raw_archive(fileobj):
    rows = []
    kinds = {}
    raw_names = set()
    collision_keys = set()
    pending_name = None
    embedded = None
    zero_blocks = 0
    archive_index = 0
    with gzip.GzipFile(fileobj=fileobj, mode="rb") as stream:
        while True:
            header = stream.read(BLOCK)
            if not header:
                break
            if len(header) != BLOCK:
                fail("truncated_header", "partial tar header")
            if header == b"\0" * BLOCK:
                zero_blocks += 1
                if zero_blocks == 2:
                    trailing = stream.read()
                    if trailing.strip(b"\0"):
                        fail("trailing_archive_data", "nonzero data after terminator")
                    break
                continue
            if zero_blocks:
                fail("single_zero_block", "member follows a zero block")
            header_checksum(header)
            name = decode_field(header[0:100], "name")
            prefix = decode_field(header[345:500], "prefix")
            if prefix:
                name = prefix + "/" + name
            member_type = header[156:157]
            size = parse_octal(header[124:136], "size")
            padded = ((size + BLOCK - 1) // BLOCK) * BLOCK

            if member_type in (tarfile.XGLTYPE, tarfile.SOLARIS_XHDTYPE):
                fail("global_or_solaris_pax", name)
            if member_type == tarfile.XHDTYPE:
                payload = read_exact(stream, size, "PAX payload")
                skip_exact(stream, padded - size, "PAX padding")
                pax = parse_pax(payload)
                if any(key.startswith("GNU.sparse.") for key in pax):
                    fail("pax_sparse", name)
                path = pax.get("path")
                sparse_name = pax.get("GNU.sparse.name")
                if path is not None and sparse_name is not None:
                    fail("conflicting_path_extension", name)
                if pending_name is not None:
                    fail("conflicting_path_extension", name)
                pending_name = path if path is not None else sparse_name
                continue
            if member_type == tarfile.GNUTYPE_LONGNAME:
                payload = read_exact(stream, size, "GNU long-name payload")
                skip_exact(stream, padded - size, "GNU long-name padding")
                if pending_name is not None:
                    fail("conflicting_path_extension", name)
                if not payload.endswith(b"\0") or payload.rstrip(b"\0") + b"\0" != payload:
                    fail("malformed_gnu_long_name", name)
                try:
                    pending_name = payload[:-1].decode("utf-8", "strict")
                except UnicodeDecodeError:
                    fail("invalid_utf8", "GNU long name")
                continue
            if member_type in (tarfile.GNUTYPE_LONGLINK, tarfile.GNUTYPE_SPARSE):
                fail("unsupported_extension", repr(member_type))
            if member_type not in ALLOWED_TYPES:
                fail("unsupported_member_type", repr(member_type))
            if member_type == tarfile.AREGTYPE and name.endswith("/"):
                fail("old_v7_directory_conversion", name)

            effective_name = pending_name if pending_name is not None else name
            pending_name = None
            collision_key, is_root = normalize_name(effective_name, member_type, size)
            if effective_name in raw_names:
                fail("duplicate_raw_name", effective_name)
            if collision_key in collision_keys:
                fail("duplicate_collision_key", collision_key)
            raw_names.add(effective_name)
            collision_keys.add(collision_key)
            kind = "directory" if member_type == tarfile.DIRTYPE else "regular"
            kinds[collision_key] = kind
            rows.append([archive_index, effective_name, collision_key, kind, size])
            archive_index += 1

            if kind == "regular" and collision_key == EMBEDDED_LEAN:
                embedded = read_exact(stream, size, "embedded Lean asset")
            else:
                skip_exact(stream, size, "member data")
            skip_exact(stream, padded - size, "member padding")

    if pending_name is not None:
        fail("orphan_path_extension", pending_name)
    if zero_blocks < 2:
        fail("missing_terminator", "archive lacks two zero blocks")
    for _, _, key, _, _ in rows:
        if key == ".":
            continue
        parts = key.split("/")
        for index in range(1, len(parts)):
            ancestor = "/".join(parts[:index])
            if ancestor in kinds and kinds[ancestor] != "directory":
                fail("regular_file_ancestor", ancestor)
    return rows, embedded


def structural_inventory(rows):
    records = []
    for row in sorted(rows):
        records.append(json.dumps(row, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n")
    return hashlib.sha256(b"".join(records)).hexdigest()


def descriptor_identity(fd):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        fail("not_regular_file", "archive input is not regular")
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, digest.hexdigest())


def tarfile_cross_check(fd, expected_count):
    os.lseek(fd, 0, os.SEEK_SET)
    with os.fdopen(os.dup(fd), "rb", closefd=True) as source:
        with tarfile.open(
            fileobj=source,
            mode="r:gz",
            encoding="utf-8",
            errors="strict",
            ignore_zeros=False,
            tarinfo=RawAwareTarInfo,
        ) as archive:
            members = archive.getmembers()
    if len(members) != expected_count:
        fail("tarfile_member_count_mismatch", str(len(members)))
    for member in members:
        if not hasattr(member, "hsai_raw_name"):
            fail("missing_raw_metadata", member.name)
        if member.type not in ALLOWED_TYPES or member.sparse is not None:
            fail("tarfile_unsupported_semantics", member.name)


def profile_summary(rows):
    roots = sum(1 for row in rows if row[2] == ".")
    regular = sum(1 for row in rows if row[3] == "regular")
    directory = sum(1 for row in rows if row[3] == "directory")
    top = sorted({row[2].split("/", 1)[0] for row in rows if row[2] != "."})
    return {
        "logical_members": len(rows),
        "root_count": roots,
        "regular_members": regular,
        "directory_members": directory,
        "top_level": top,
        "inventory_sha256": structural_inventory(rows),
    }


def require_profile(observed, expected):
    if observed != expected:
        fail("profile_mismatch", canonical_json({"expected": expected, "observed": observed}))


def validate_one(path, profile):
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        before = descriptor_identity(fd)
        with os.fdopen(os.dup(fd), "rb", closefd=True) as source:
            rows, embedded = scan_raw_archive(source)
        observed = profile_summary(rows)
        require_profile(observed, profile)
        tarfile_cross_check(fd, profile["logical_members"])
        after = descriptor_identity(fd)
        if before != after:
            fail("descriptor_drift", path)
        return observed, embedded, {"bytes": before[2], "sha256": before[4]}
    finally:
        os.close(fd)


def validate_archives(main_path, lean_path):
    main, embedded, main_identity = validate_one(main_path, MAIN_PROFILE)
    lean, _, lean_identity = validate_one(lean_path, LEAN_PROFILE)
    if embedded is None:
        fail("embedded_asset_missing", EMBEDDED_LEAN)
    with open(lean_path, "rb") as source:
        separate = source.read()
    if embedded != separate:
        fail("embedded_asset_mismatch", EMBEDDED_LEAN)
    return {
        "schema": SCHEMA,
        "embedded_lean_equal": True,
        "lean": dict(lean, **lean_identity),
        "main": dict(main, **main_identity),
    }


def build_header(name, member_type=tarfile.REGTYPE, size=0, prefix=""):
    info = tarfile.TarInfo(name=name)
    info.type = member_type
    info.size = size
    header = info.tobuf(format=tarfile.USTAR_FORMAT, encoding="utf-8", errors="strict")
    if prefix:
        mutable = bytearray(header)
        encoded = prefix.encode("utf-8")
        mutable[345 : 345 + len(encoded)] = encoded
        mutable[148:156] = b"        "
        checksum = sum(mutable)
        mutable[148:156] = ("%06o\0 " % checksum).encode("ascii")
        header = bytes(mutable)
    return header


def make_archive(headers_and_payloads):
    raw = bytearray()
    for header, payload in headers_and_payloads:
        raw.extend(header)
        raw.extend(payload)
        raw.extend(b"\0" * ((-len(payload)) % BLOCK))
    raw.extend(b"\0" * (2 * BLOCK))
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as target:
        path = target.name
    with gzip.open(path, "wb") as compressed:
        compressed.write(bytes(raw))
    return path


def expect_scan(case_id, headers, should_pass, expected_code=None):
    path = make_archive(headers)
    try:
        with open(path, "rb") as source:
            try:
                scan_raw_archive(source)
                observed = "pass"
            except ValidationError as error:
                observed = error.code
        if should_pass and observed != "pass":
            fail("self_test_failed", case_id + ":" + observed)
        if not should_pass and observed != expected_code:
            fail("self_test_failed", case_id + ":" + observed)
    finally:
        os.unlink(path)


def pax_record(key, value):
    body = (key + "=" + value + "\n").encode("utf-8")
    length = len(body) + 2
    while True:
        record = str(length).encode("ascii") + b" " + body
        if len(record) == length:
            return record
        length = len(record)


def run_self_test():
    cases = []

    def add(case_id, action):
        action()
        cases.append(case_id)

    safe = [
        (build_header("dir", tarfile.DIRTYPE), b""),
        (build_header("dir/file"), b""),
        (build_header("legacy", tarfile.AREGTYPE), b""),
        (build_header("file", prefix="prefix"), b""),
    ]
    add("01-safe-members-and-ustar-prefix", lambda: expect_scan("01", safe, True))
    add("02-root-dot", lambda: expect_scan("02", [(build_header(".", tarfile.DIRTYPE), b"")], True))
    add("03-root-dot-slash", lambda: expect_scan("03", [(build_header("./", tarfile.DIRTYPE), b"")], True))
    invalid_names = [
        ("04-absolute", "/a", "absolute_path"),
        ("05-parent", "a/../b", "parent_component"),
        ("06-empty", "", "empty_name"),
        ("07-internal-dot", "a/./b", "internal_dot"),
        ("08-repeated-leading", "././a", "repeated_leading_dot"),
        ("09-repeated-separator", "a//b", "repeated_separator"),
        ("10-regular-trailing", "a/", "invalid_trailing_separator"),
    ]
    for case_id, name, code in invalid_names:
        add(case_id, lambda c=case_id, n=name, x=code: expect_scan(c, [(build_header(n), b"")], False, x))
    add("11-duplicate-raw", lambda: expect_scan("11", [(build_header("a"), b""), (build_header("a"), b"")], False, "duplicate_raw_name"))
    add("12-duplicate-key", lambda: expect_scan("12", [(build_header("./a"), b""), (build_header("a"), b"")], False, "duplicate_collision_key"))
    add("13-file-ancestor", lambda: expect_scan("13", [(build_header("a"), b""), (build_header("a/b"), b"")], False, "regular_file_ancestor"))
    unsupported = [
        ("14-symlink", tarfile.SYMTYPE),
        ("15-hardlink", tarfile.LNKTYPE),
        ("16-character", tarfile.CHRTYPE),
        ("17-block", tarfile.BLKTYPE),
        ("18-fifo", tarfile.FIFOTYPE),
        ("19-contiguous", tarfile.CONTTYPE),
        ("20-gnu-sparse", tarfile.GNUTYPE_SPARSE),
        ("21-unknown", b"Z"),
    ]
    for case_id, kind in unsupported:
        expected = "unsupported_extension" if kind == tarfile.GNUTYPE_SPARSE else "unsupported_member_type"
        add(case_id, lambda c=case_id, k=kind, x=expected: expect_scan(c, [(build_header("a", k), b"")], False, x))
    sparse = pax_record("GNU.sparse.map", "0,1")
    add("22-pax-sparse", lambda: expect_scan("22", [(build_header("pax", tarfile.XHDTYPE, len(sparse)), sparse), (build_header("a"), b"")], False, "pax_sparse"))
    def root_marker_rejections():
        expect_scan("23-type", [(build_header("."), b"")], False, "invalid_root_marker")
        expect_scan("23-size", [(build_header(".", tarfile.DIRTYPE, 1), b"x")], False, "invalid_root_marker")

    add("23-root-type-or-size", root_marker_rejections)

    def expect_profile_mismatch(case_id, observed, expected):
        try:
            require_profile(observed, expected)
        except ValidationError as error:
            if error.code == "profile_mismatch":
                return
            raise
        fail("self_test_failed", case_id + ":profile accepted")

    root_observed = profile_summary([[0, "./", ".", "directory", 0]])
    root_expected = dict(root_observed, root_count=0)
    add("24-root-count-drift", lambda: expect_profile_mismatch("24", root_observed, root_expected))
    top_observed = profile_summary([[0, "x", "x", "regular", 0]])
    top_expected = dict(top_observed, top_level=["expected"])
    add("25-top-level-drift", lambda: expect_profile_mismatch("25", top_observed, top_expected))
    count_observed = profile_summary([])
    count_expected = dict(count_observed, logical_members=1)
    add("26-count-drift", lambda: expect_profile_mismatch("26", count_observed, count_expected))
    pax = pax_record("path", "long/path")
    add("27-valid-pax-path", lambda: expect_scan("27", [(build_header("pax", tarfile.XHDTYPE, len(pax)), pax), (build_header("short"), b"")], True))
    long_payload = b"long/name\0"
    add("28-valid-gnu-long-name", lambda: expect_scan("28", [(build_header("long", tarfile.GNUTYPE_LONGNAME, len(long_payload)), long_payload), (build_header("short"), b"")], True))
    duplicate_pax = pax_record("path", "a") + pax_record("path", "b")
    add("29-duplicate-pax-key", lambda: expect_scan("29", [(build_header("pax", tarfile.XHDTYPE, len(duplicate_pax)), duplicate_pax), (build_header("short"), b"")], False, "duplicate_pax_key"))
    bad_utf8 = b"\xff\0"
    add("30-invalid-utf8", lambda: expect_scan("30", [(build_header("long", tarfile.GNUTYPE_LONGNAME, len(bad_utf8)), bad_utf8), (build_header("short"), b"")], False, "invalid_utf8"))
    def malformed_variants():
        bad_header = bytearray(build_header("a"))
        bad_header[0] ^= 1
        expect_scan("31-checksum", [(bytes(bad_header), b"")], False, "invalid_checksum")
        invalid_pax = b"99 path=a\n"
        expect_scan(
            "31-pax",
            [(build_header("pax", tarfile.XHDTYPE, len(invalid_pax)), invalid_pax)],
            False,
            "invalid_pax_length",
        )

    add("31-malformed-header-or-pax", malformed_variants)
    if len(cases) != 31:
        fail("self_test_count_mismatch", str(len(cases)))
    return {"schema": SELF_TEST_SCHEMA, "cases": cases, "failed": 0, "passed": len(cases)}


def main(argv=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("self-test", allow_abbrev=False)
    validate = subparsers.add_parser("validate", allow_abbrev=False)
    validate.add_argument("--main", required=True)
    validate.add_argument("--lean", required=True)
    args = parser.parse_args(argv)
    try:
        result = run_self_test() if args.command == "self-test" else validate_archives(args.main, args.lean)
    except ValidationError as error:
        sys.stderr.write(canonical_json({"code": error.code, "detail": error.detail, "schema": "hsai-raw-archive-error-v1"}) + "\n")
        return 1
    sys.stdout.write(canonical_json(result) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
