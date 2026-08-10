#!/usr/bin/python3
"""Read-only validator for the Phase 796-A3L3 P01B corpus and profile."""

import ast
import hashlib
import json
import os
import pathlib
import stat
import unittest
from typing import Any, Dict, Iterable, List, Sequence, Tuple


CORPUS_SCHEMA = "hsai-p01b-container-test-corpus-v1"
PROVENANCE_SCHEMA = "hsai-p01b-container-seccomp-provenance-v1"
VALIDATION_SCHEMA = "hsai-p01b-container-corpus-validation-v1"
SOURCE_COMMIT = "53442464ec851be46dd1e47b44b0918a14e9cf4a"
SOURCE_TREE = "571e9aa4011a60b2af8e8069812aa71ca31b5641"
SOURCE_MANIFEST_DOMAIN = b"hsai:p01b-container-corpus-source-manifest:v1\0"
SOURCE_MANIFEST_SHA256 = (
    "adebe965254ffa43e3c2579262dc365486c27eadb492d1fe55eaf73cf3eb00b6"
)
TEST_ID_DOMAIN = b"hsai:p01b-test-corpus:v1\0"
TEST_ID_DIGEST = "1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726"
FOCUSED_ID_ARRAY_SHA256 = (
    "43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543"
)
FULL_ID_ARRAY_SHA256 = (
    "87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8"
)

CHECKER_PATH = "tools/hsai-formal-preflight/p01b_container_corpus.py"
CORPUS_PATH = "tools/hsai-formal-preflight/p01b_container_test_corpus.json"
PROFILE_PATH = "tools/hsai-formal-preflight/p01b_container_seccomp.json"
LICENSE_PATH = "tools/hsai-formal-preflight/p01b_container_seccomp_license.txt"
PROVENANCE_PATH = "tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json"

PROFILE_BYTES = 13470
PROFILE_SHA256 = "536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74"
LICENSE_BYTES = 11358
LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
LS_REMOTE_OUTPUT = (
    "f1a0fd6b5a369fca061b041539129661ed337ef5\trefs/tags/seccomp/v0.2.3\n"
    "836ae4d37ef2ec995c77c99fc55f5b5f3af3a897\trefs/tags/seccomp/v0.2.3^{}\n"
)
LS_REMOTE_OUTPUT_SHA256 = (
    "ef8d86358f2d2869ea6637304dd3942a4480eafba20122b895022d01f8b55dc9"
)

CONTAINER_ENVIRONMENT = {
    "HOME": "/nonexistent",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "TMPDIR": "/work",
    "TZ": "UTC",
}
FOCUSED_SUITE_FILES = [
    "tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py"
]
FULL_SUITE_FILES = [
    "tools/hsai-formal-preflight/tests/test_bounded_runner.py",
    "tools/hsai-formal-preflight/tests/test_execution_state_machine.py",
    "tools/hsai-formal-preflight/tests/test_fixture_validator.py",
    "tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py",
    "tools/hsai-formal-preflight/tests/test_raw_archive_validator.py",
]
FOCUSED_ARGV = [
    "/usr/local/bin/python3",
    "-B",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tools/hsai-formal-preflight/tests",
    "-p",
    "test_p01b_archive_ledger.py",
]
FULL_ARGV = [
    "/usr/local/bin/python3",
    "-B",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tools/hsai-formal-preflight/tests",
    "-p",
    "test_*.py",
]

ROOT_KEYS = {
    "checker_source_sha256",
    "container_environment",
    "focused",
    "full",
    "schema",
    "source_commit",
    "source_files",
    "source_manifest_sha256",
    "source_tree",
    "working_directory",
}
SUITE_KEYS = {"argv", "count", "id_array_sha256", "ids", "pattern", "suite_files"}
FILE_KEYS = {"bytes", "mode", "path", "sha256"}
PROVENANCE_ROOT_KEYS = {
    "license",
    "notice_paths_absent",
    "peeled_commit",
    "profile",
    "repository",
    "schema",
    "tag",
    "tag_object",
    "verification",
}
ARTIFACT_KEYS = {"bytes", "destination_path", "source_path", "sha256"}
VERIFICATION_KEYS = {
    "license_http_status",
    "ls_remote_output",
    "ls_remote_output_bytes",
    "ls_remote_output_sha256",
    "notice_http_status",
    "profile_http_status",
}

EXPECTED_PROVENANCE = {
    "license": {
        "bytes": LICENSE_BYTES,
        "destination_path": LICENSE_PATH,
        "sha256": LICENSE_SHA256,
        "source_path": "LICENSE",
    },
    "notice_paths_absent": ["NOTICE", "NOTICE.md"],
    "peeled_commit": "836ae4d37ef2ec995c77c99fc55f5b5f3af3a897",
    "profile": {
        "bytes": PROFILE_BYTES,
        "destination_path": PROFILE_PATH,
        "sha256": PROFILE_SHA256,
        "source_path": "seccomp/default.json",
    },
    "repository": "https://github.com/moby/profiles",
    "schema": PROVENANCE_SCHEMA,
    "tag": "seccomp/v0.2.3",
    "tag_object": "f1a0fd6b5a369fca061b041539129661ed337ef5",
    "verification": {
        "license_http_status": 200,
        "ls_remote_output": LS_REMOTE_OUTPUT,
        "ls_remote_output_bytes": 135,
        "ls_remote_output_sha256": LS_REMOTE_OUTPUT_SHA256,
        "notice_http_status": {"NOTICE": 404, "NOTICE.md": 404},
        "profile_http_status": 200,
    },
}

MAX_JSON_BYTES = 128 * 1024
MAX_SOURCE_BYTES = 256 * 1024
MAX_CHECKER_BYTES = 128 * 1024


class ValidationError(Exception):
    """A bounded corpus or profile validation failure."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")


def compact_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reject_duplicate_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key")
        result[key] = value
    return result


def require_exact_keys(value: Any, expected: set, label: str) -> None:
    if not isinstance(value, dict):
        raise ValidationError(label + " must be an object")
    actual = set(value)
    if actual != expected:
        raise ValidationError(
            "{0} keys differ: missing={1}, extra={2}".format(
                label, sorted(expected - actual), sorted(actual - expected)
            )
        )


def require_ascii_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.isascii():
        raise ValidationError(label + " must be an ASCII string")
    return value


def require_plain_int(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValidationError(label + " must be a bounded integer")
    return value


def require_sha256(value: Any, label: str) -> str:
    digest = require_ascii_string(value, label)
    if len(digest) != 64 or digest.lower() != digest:
        raise ValidationError(label + " must be lowercase SHA-256")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValidationError(label + " must be lowercase SHA-256")
    return digest


def validate_relative_path(value: Any, label: str) -> str:
    path = require_ascii_string(value, label)
    pure = pathlib.PurePosixPath(path)
    if (
        not path
        or path == "."
        or pure.is_absolute()
        or "\\" in path
        or path != pure.as_posix()
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        raise ValidationError(label + " must be a canonical relative path")
    return path


def _resolved_root(root: pathlib.Path) -> pathlib.Path:
    try:
        if root.is_symlink():
            raise ValidationError("root must not be a symlink")
        resolved = root.resolve(strict=True)
        root_status = resolved.stat()
    except OSError as error:
        raise ValidationError("root cannot be resolved: " + str(error))
    if not stat.S_ISDIR(root_status.st_mode):
        raise ValidationError("root must be a directory")
    return resolved


def read_regular_file(
    root: pathlib.Path, relative: str, maximum: int, expected_mode: int = 0o644
) -> bytes:
    validate_relative_path(relative, "path")
    resolved_root = _resolved_root(root)
    parts = pathlib.PurePosixPath(relative).parts
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        directory_descriptor = os.open(str(resolved_root), directory_flags)
    except OSError as error:
        raise ValidationError("root cannot be opened read-only: " + str(error))
    try:
        for component in parts[:-1]:
            try:
                next_descriptor = os.open(
                    component, directory_flags, dir_fd=directory_descriptor
                )
            except OSError as error:
                raise ValidationError(
                    "path ancestor rejected as missing, replaced, or symlinked: "
                    + relative
                    + ": "
                    + str(error)
                )
            next_status = os.fstat(next_descriptor)
            if not stat.S_ISDIR(next_status.st_mode):
                os.close(next_descriptor)
                raise ValidationError("path ancestor is not a directory: " + relative)
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        try:
            descriptor = os.open(parts[-1], file_flags, dir_fd=directory_descriptor)
        except OSError as error:
            raise ValidationError(
                "path terminal rejected as missing, replaced, or symlinked: "
                + relative
                + ": "
                + str(error)
            )
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise ValidationError("path is not regular: " + relative)
            if stat.S_IMODE(before.st_mode) != expected_mode:
                raise ValidationError("path mode differs: " + relative)
            chunks: List[bytes] = []
            retained = 0
            while retained <= maximum:
                chunk = os.read(descriptor, min(65536, maximum + 1 - retained))
                if not chunk:
                    break
                chunks.append(chunk)
                retained += len(chunk)
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
    finally:
        os.close(directory_descriptor)
    if retained > maximum:
        raise ValidationError("path exceeds byte limit: " + relative)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
        before.st_nlink,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
        after.st_nlink,
    )
    if identity_before != identity_after or retained != before.st_size:
        raise ValidationError("path identity drifted while reading: " + relative)
    return b"".join(chunks)


def load_canonical_json(root: pathlib.Path, relative: str) -> Any:
    raw = read_regular_file(root, relative, MAX_JSON_BYTES)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise ValidationError(relative + " must be ASCII JSON")
    try:
        document = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except ValidationError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError):
        raise ValidationError(relative + " is not valid JSON")
    if raw != canonical_json_bytes(document):
        raise ValidationError(relative + " is not canonical JSON")
    return document


def validate_source_entry(entry: Any, index: int) -> Dict[str, Any]:
    label = "source_files[{0}]".format(index)
    require_exact_keys(entry, FILE_KEYS, label)
    require_plain_int(entry["bytes"], label + ".bytes")
    if entry["mode"] != "100644":
        raise ValidationError(label + ".mode differs")
    validate_relative_path(entry["path"], label + ".path")
    require_sha256(entry["sha256"], label + ".sha256")
    return entry


def validate_source_files(document: Dict[str, Any], root: pathlib.Path) -> Dict[str, bytes]:
    entries = document["source_files"]
    if not isinstance(entries, list) or len(entries) != 11:
        raise ValidationError("source_files must contain exactly eleven entries")
    normalized = [validate_source_entry(entry, index) for index, entry in enumerate(entries)]
    paths = [entry["path"] for entry in normalized]
    if len(paths) != len(set(paths)):
        raise ValidationError("source_files paths must be unique")
    manifest_bytes = compact_json_bytes(normalized)
    if sha256_hex(SOURCE_MANIFEST_DOMAIN + manifest_bytes) != SOURCE_MANIFEST_SHA256:
        raise ValidationError("source manifest digest differs")
    if document["source_manifest_sha256"] != SOURCE_MANIFEST_SHA256:
        raise ValidationError("declared source manifest digest differs")

    payloads: Dict[str, bytes] = {}
    for index, entry in enumerate(normalized):
        raw = read_regular_file(root, entry["path"], MAX_SOURCE_BYTES)
        if len(raw) != entry["bytes"]:
            raise ValidationError("source_files[{0}] byte length differs".format(index))
        if sha256_hex(raw) != entry["sha256"]:
            raise ValidationError("source_files[{0}] digest differs".format(index))
        payloads[entry["path"]] = raw
    return payloads


def _flatten_tests(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            for nested in _flatten_tests(item):
                yield nested
        else:
            yield item


def _static_test_method(_case: unittest.TestCase) -> None:
    pass


def _line_scan_classes(source: bytes, label: str) -> Dict[str, Dict[str, List[str]]]:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("static source scan failed: " + label + ": " + str(error))
    classes: Dict[str, Dict[str, List[str]]] = {}
    current_class = ""
    for line_number, line in enumerate(text.splitlines(), 1):
        indentation = line[: len(line) - len(line.lstrip(" \t"))]
        if "\t" in indentation:
            raise ValidationError(
                "static source scan rejects tab indentation: {0}:{1}".format(
                    label, line_number
                )
            )
        if line.startswith("class "):
            header = line[len("class ") :]
            if not header.endswith(":"):
                raise ValidationError(
                    "static source scan requires one-line class header: {0}:{1}".format(
                        label, line_number
                    )
                )
            declaration = header[:-1]
            if "(" in declaration:
                if not declaration.endswith(")"):
                    raise ValidationError(
                        "static source scan rejects class header: {0}:{1}".format(
                            label, line_number
                        )
                    )
                class_name, raw_bases = declaration[:-1].split("(", 1)
                bases = [base.strip().split(".")[-1] for base in raw_bases.split(",")]
            else:
                class_name = declaration
                bases = []
            class_name = class_name.strip()
            if (
                not class_name
                or not class_name.isascii()
                or not class_name.isidentifier()
                or any(
                    not base or not base.isascii() or not base.isidentifier()
                    for base in bases
                )
            ):
                raise ValidationError(
                    "static source scan rejects class identity: {0}:{1}".format(
                        label, line_number
                    )
                )
            if class_name in classes:
                raise ValidationError("static source scan found duplicate class: " + class_name)
            classes[class_name] = {"bases": bases, "tests": []}
            current_class = class_name
            continue
        if line and not line.startswith((" ", "\t", "#")):
            current_class = ""
            continue
        if not current_class or not line.startswith("    ") or line.startswith("        "):
            continue
        stripped = line.strip()
        prefixes = ("def test", "async def test")
        if not stripped.startswith(prefixes):
            continue
        method_name = stripped.split("def ", 1)[1].split("(", 1)[0]
        if (
            not method_name.startswith("test")
            or not method_name.isascii()
            or not method_name.isidentifier()
        ):
            raise ValidationError(
                "static source scan rejects test identity: {0}:{1}".format(
                    label, line_number
                )
            )
        if method_name in classes[current_class]["tests"]:
            raise ValidationError("static source scan found duplicate test: " + method_name)
        classes[current_class]["tests"].append(method_name)
    return classes


def _static_inherits_test_case(
    name: str, classes: Dict[str, Dict[str, List[str]]], visiting: Sequence[str]
) -> bool:
    if name in visiting:
        raise ValidationError("static class inheritance cycle")
    for base in classes[name]["bases"]:
        if base == "TestCase":
            return True
        if base in classes and _static_inherits_test_case(
            base, classes, list(visiting) + [name]
        ):
            return True
    return False


def _static_effective_tests(
    name: str, classes: Dict[str, Dict[str, List[str]]], visiting: Sequence[str]
) -> List[str]:
    if name in visiting:
        raise ValidationError("static class inheritance cycle")
    methods: Dict[str, None] = {}
    for base in classes[name]["bases"]:
        if base in classes:
            for method in _static_effective_tests(
                base, classes, list(visiting) + [name]
            ):
                methods[method] = None
    for method in classes[name]["tests"]:
        methods[method] = None
    return sorted(methods)


def static_loader_ids(
    source_payloads: Dict[str, bytes], suite_files: Sequence[str]
) -> List[str]:
    identifiers: List[str] = []
    for suite_file in suite_files:
        if suite_file not in source_payloads:
            raise ValidationError("static source scan missing suite file: " + suite_file)
        module_name = pathlib.PurePosixPath(suite_file).stem
        classes = _line_scan_classes(source_payloads[suite_file], suite_file)
        for class_name in sorted(classes):
            if not _static_inherits_test_case(class_name, classes, []):
                continue
            methods = _static_effective_tests(class_name, classes, [])
            attributes: Dict[str, Any] = {"__module__": module_name}
            for method in methods:
                attributes[method] = _static_test_method
            synthetic_class = type(class_name, (unittest.TestCase,), attributes)
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(synthetic_class)
            if loader.errors:
                raise ValidationError("TestLoader static reconstruction failed")
            identifiers.extend(test.id() for test in _flatten_tests(suite))
    identifiers.sort()
    if len(identifiers) != len(set(identifiers)):
        raise ValidationError("TestLoader identifiers are not unique")
    if any(not identifier.isascii() for identifier in identifiers):
        raise ValidationError("TestLoader identifier is not ASCII")
    return identifiers


def _base_name(base: ast.expr) -> str:
    if isinstance(base, ast.Attribute):
        return base.attr
    if isinstance(base, ast.Name):
        return base.id
    return ""


def _inherits_test_case(
    name: str, classes: Dict[str, ast.ClassDef], visiting: Sequence[str]
) -> bool:
    if name in visiting:
        raise ValidationError("AST class inheritance cycle")
    node = classes[name]
    for base in node.bases:
        base_name = _base_name(base)
        if base_name == "TestCase":
            return True
        if base_name in classes and _inherits_test_case(
            base_name, classes, list(visiting) + [name]
        ):
            return True
    return False


def ast_ids(source_payloads: Dict[str, bytes], suite_files: Sequence[str]) -> List[str]:
    identifiers: List[str] = []
    for suite_file in suite_files:
        try:
            text = source_payloads[suite_file].decode("utf-8")
            tree = ast.parse(text, filename=suite_file)
        except (KeyError, UnicodeDecodeError, SyntaxError) as error:
            raise ValidationError("AST reconstruction failed: " + str(error))
        module = pathlib.PurePosixPath(suite_file).stem
        classes = {
            node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
        }
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not _inherits_test_case(
                node.name, classes, []
            ):
                continue
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and member.name.startswith(
                    "test"
                ):
                    identifiers.append("{0}.{1}.{2}".format(module, node.name, member.name))
    identifiers.sort()
    if len(identifiers) != len(set(identifiers)):
        raise ValidationError("AST identifiers are not unique")
    return identifiers


def validate_suite(
    suite: Any,
    label: str,
    expected_pattern: str,
    expected_argv: Sequence[str],
    expected_files: Sequence[str],
    expected_count: int,
    expected_digest: str,
    source_payloads: Dict[str, bytes],
) -> List[str]:
    require_exact_keys(suite, SUITE_KEYS, label)
    if suite["pattern"] != expected_pattern:
        raise ValidationError(label + ".pattern differs")
    if suite["argv"] != list(expected_argv):
        raise ValidationError(label + ".argv differs")
    if suite["suite_files"] != list(expected_files):
        raise ValidationError(label + ".suite_files differs")
    if type(suite["count"]) is not int or suite["count"] != expected_count:
        raise ValidationError(label + ".count differs")
    if suite["id_array_sha256"] != expected_digest:
        raise ValidationError(label + ".id_array_sha256 differs")
    identifiers = suite["ids"]
    if not isinstance(identifiers, list) or any(
        not isinstance(identifier, str) or not identifier.isascii()
        for identifier in identifiers
    ):
        raise ValidationError(label + ".ids must be an ASCII string array")
    if identifiers != sorted(identifiers) or len(identifiers) != len(set(identifiers)):
        raise ValidationError(label + ".ids must be ordered and unique")
    if len(identifiers) != expected_count:
        raise ValidationError(label + ".ids count differs")
    if sha256_hex(compact_json_bytes(identifiers)) != expected_digest:
        raise ValidationError(label + ".ids digest differs")
    loader_ids = static_loader_ids(source_payloads, expected_files)
    syntax_ids = ast_ids(source_payloads, expected_files)
    if identifiers != loader_ids or identifiers != syntax_ids:
        raise ValidationError(label + ".ids differ from independent discovery")
    return identifiers


def validate_provenance(document: Any) -> None:
    require_exact_keys(document, PROVENANCE_ROOT_KEYS, "provenance")
    require_exact_keys(document["license"], ARTIFACT_KEYS, "provenance.license")
    require_exact_keys(document["profile"], ARTIFACT_KEYS, "provenance.profile")
    require_exact_keys(document["verification"], VERIFICATION_KEYS, "provenance.verification")
    if document != EXPECTED_PROVENANCE:
        raise ValidationError("provenance differs from the pinned record")
    remote = document["verification"]["ls_remote_output"].encode("ascii")
    if len(remote) != 135 or sha256_hex(remote) != LS_REMOTE_OUTPUT_SHA256:
        raise ValidationError("provenance ls-remote output differs")


def validate_document(document: Any, root: pathlib.Path) -> Dict[str, Any]:
    require_exact_keys(document, ROOT_KEYS, "corpus")
    if document["schema"] != CORPUS_SCHEMA:
        raise ValidationError("corpus schema differs")
    if document["source_commit"] != SOURCE_COMMIT or document["source_tree"] != SOURCE_TREE:
        raise ValidationError("source commit or tree differs")
    if document["working_directory"] != "/input":
        raise ValidationError("working_directory differs")
    if document["container_environment"] != CONTAINER_ENVIRONMENT:
        raise ValidationError("container_environment differs")
    require_sha256(document["checker_source_sha256"], "checker_source_sha256")

    source_payloads = validate_source_files(document, root)
    checker = read_regular_file(root, CHECKER_PATH, MAX_CHECKER_BYTES)
    if sha256_hex(checker) != document["checker_source_sha256"]:
        raise ValidationError("checker source digest differs")

    focused = validate_suite(
        document["focused"],
        "focused",
        "test_p01b_archive_ledger.py",
        FOCUSED_ARGV,
        FOCUSED_SUITE_FILES,
        68,
        FOCUSED_ID_ARRAY_SHA256,
        source_payloads,
    )
    full = validate_suite(
        document["full"],
        "full",
        "test_*.py",
        FULL_ARGV,
        FULL_SUITE_FILES,
        151,
        FULL_ID_ARRAY_SHA256,
        source_payloads,
    )
    id_payload = {"focused": focused, "full": full, "schema": "hsai-p01b-test-corpus-v1"}
    if sha256_hex(TEST_ID_DOMAIN + compact_json_bytes(id_payload)) != TEST_ID_DIGEST:
        raise ValidationError("combined test ID digest differs")
    return {
        "focused_test_count": len(focused),
        "full_test_count": len(full),
        "source_file_count": len(source_payloads),
        "test_id_digest": TEST_ID_DIGEST,
    }


def validate_repository(root: pathlib.Path) -> Dict[str, Any]:
    resolved_root = _resolved_root(root)
    corpus = load_canonical_json(resolved_root, CORPUS_PATH)
    summary = validate_document(corpus, resolved_root)
    provenance = load_canonical_json(resolved_root, PROVENANCE_PATH)
    validate_provenance(provenance)

    profile = read_regular_file(resolved_root, PROFILE_PATH, PROFILE_BYTES)
    license_bytes = read_regular_file(resolved_root, LICENSE_PATH, LICENSE_BYTES)
    if len(profile) != PROFILE_BYTES or sha256_hex(profile) != PROFILE_SHA256:
        raise ValidationError("seccomp profile identity differs")
    if len(license_bytes) != LICENSE_BYTES or sha256_hex(license_bytes) != LICENSE_SHA256:
        raise ValidationError("seccomp license identity differs")
    try:
        json.loads(profile.decode("ascii"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, ValueError):
        raise ValidationError("seccomp profile is not strict ASCII JSON")

    return {
        "focused_test_count": summary["focused_test_count"],
        "full_test_count": summary["full_test_count"],
        "profile_sha256": PROFILE_SHA256,
        "schema": VALIDATION_SCHEMA,
        "source_file_count": summary["source_file_count"],
        "test_id_digest": summary["test_id_digest"],
    }
