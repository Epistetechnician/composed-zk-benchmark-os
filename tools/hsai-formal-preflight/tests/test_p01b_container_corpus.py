import ast
import copy
import contextlib
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).parents[3]
CHECKER_PATH = ROOT / "tools/hsai-formal-preflight/p01b_container_corpus.py"
SPEC = importlib.util.spec_from_file_location("p01b_container_corpus", CHECKER_PATH)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

IMPLEMENTATION_PATHS = [
    "tools/hsai-formal-preflight/p01b_container_corpus.py",
    "tools/hsai-formal-preflight/p01b_container_seccomp.json",
    "tools/hsai-formal-preflight/p01b_container_seccomp_license.txt",
    "tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json",
    "tools/hsai-formal-preflight/p01b_container_test_corpus.json",
    "tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py",
]

EXPECTED_CHECKER_SHA256 = "f788f0d97fc3ca26b32d23ffaa83d43edf4b6c04189aa0ebca2c3c877cd94598"
EXPECTED_CORPUS_BYTES = 27079
EXPECTED_CORPUS_SHA256 = "6f719e8a113464334b368e6470126b8339c5ed66f115ebced4c724555405b064"
EXPECTED_PROFILE_BYTES = 13470
EXPECTED_PROFILE_SHA256 = "536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74"
EXPECTED_LICENSE_BYTES = 11358
EXPECTED_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
EXPECTED_PROVENANCE_BYTES = 1116
EXPECTED_PROVENANCE_SHA256 = "e4e20cd2de3830961c669cd99233e3490320143462b23027726e7f02d95c337b"
EXPECTED_SOURCE_COMMIT = "53442464ec851be46dd1e47b44b0918a14e9cf4a"
EXPECTED_SOURCE_TREE = "571e9aa4011a60b2af8e8069812aa71ca31b5641"
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "adebe965254ffa43e3c2579262dc365486c27eadb492d1fe55eaf73cf3eb00b6"
)
EXPECTED_FOCUSED_ID_ARRAY_SHA256 = (
    "43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543"
)
EXPECTED_FULL_ID_ARRAY_SHA256 = (
    "87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8"
)
EXPECTED_TEST_ID_DIGEST = (
    "1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726"
)
EXPECTED_CONTAINER_ENVIRONMENT = {
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
EXPECTED_FOCUSED_SUITE_FILES = [
    "tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py"
]
EXPECTED_FULL_SUITE_FILES = [
    "tools/hsai-formal-preflight/tests/test_bounded_runner.py",
    "tools/hsai-formal-preflight/tests/test_execution_state_machine.py",
    "tools/hsai-formal-preflight/tests/test_fixture_validator.py",
    "tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py",
    "tools/hsai-formal-preflight/tests/test_raw_archive_validator.py",
]
EXPECTED_FOCUSED_ARGV = [
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
EXPECTED_FULL_ARGV = [
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
EXPECTED_PROVENANCE_LINE = (
    '{"license":{"bytes":11358,"destination_path":"tools/hsai-formal-preflight/'
    'p01b_container_seccomp_license.txt","sha256":"cfc7749b96f63bd31c3c42b5c471bf'
    '756814053e847c10f3eb003417bc523d30","source_path":"LICENSE"},'
    '"notice_paths_absent":["NOTICE","NOTICE.md"],"peeled_commit":"836ae4d37ef2ec'
    '995c77c99fc55f5b5f3af3a897","profile":{"bytes":13470,"destination_path":'
    '"tools/hsai-formal-preflight/p01b_container_seccomp.json","sha256":"536529b665'
    'dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74","source_path":'
    '"seccomp/default.json"},"repository":"https://github.com/moby/profiles","schema":'
    '"hsai-p01b-container-seccomp-provenance-v1","tag":"seccomp/v0.2.3",'
    '"tag_object":"f1a0fd6b5a369fca061b041539129661ed337ef5","verification":'
    '{"license_http_status":200,"ls_remote_output":"f1a0fd6b5a369fca061b041539129661'
    'ed337ef5\\trefs/tags/seccomp/v0.2.3\\n836ae4d37ef2ec995c77c99fc55f5b5f3af3a'
    '897\\trefs/tags/seccomp/v0.2.3^{}\\n","ls_remote_output_bytes":135,'
    '"ls_remote_output_sha256":"ef8d86358f2d2869ea6637304dd3942a4480eafba20122b895'
    '022d01f8b55dc9","notice_http_status":{"NOTICE":404,"NOTICE.md":404},'
    '"profile_http_status":200}}'
)

SCHEMA_GOLDENS = (
    (
        b"hsai:p01b-container-corpus-schema:v1\0",
        567,
        "3494d76c1e9b0cd29ac00218b7aac06f55213fae9fca862d19c740eebb0adac2",
    ),
    (
        b"hsai:p01b-container-provenance-schema:v1\0",
        360,
        "31f43727cb321bc0943019bc0a6d48c36900047a64e0cf2db2b62d1ebab8260f",
    ),
    (
        b"hsai:p01b-container-corpus-profile-audit-schema:v1\0",
        1268,
        "544da1c5356c622e56960059b68f31e46bb521673ce76e3c8ae140c6ce84b305",
    ),
)


def raw_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_document():
    return json.loads((ROOT / checker.CORPUS_PATH).read_text(encoding="ascii"))


def source_payloads(document):
    return {entry["path"]: (ROOT / entry["path"]).read_bytes() for entry in document["source_files"]}


def tree_manifest(root):
    records = []
    selected = [root / "docs/796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md"]
    selected.extend((root / "tools/hsai-formal-preflight").rglob("*"))
    for path in sorted(selected, key=lambda value: value.as_posix()):
        status = path.lstat()
        relative = path.relative_to(root).as_posix()
        if stat.S_ISREG(status.st_mode):
            identity = ("file", stat.S_IMODE(status.st_mode), status.st_size, raw_sha256(path))
        elif stat.S_ISDIR(status.st_mode):
            identity = ("directory", stat.S_IMODE(status.st_mode))
        elif stat.S_ISLNK(status.st_mode):
            identity = ("symlink", os.readlink(path))
        else:
            identity = ("other", stat.S_IFMT(status.st_mode), stat.S_IMODE(status.st_mode))
        records.append((relative, identity))
    return records


def write_fixed_json(root, raw):
    destination = root / checker.CORPUS_PATH
    destination.parent.mkdir(parents=True)
    destination.write_bytes(raw)
    destination.chmod(0o644)


class ContainerCorpusTests(unittest.TestCase):
    def assert_validation_error(self, callback, message):
        with self.assertRaises(checker.ValidationError) as captured:
            callback()
        self.assertIn(message, str(captured.exception))

    def test_repository_bundle_validates_with_exact_bounded_summary(self):
        summary = checker.validate_repository(ROOT)
        self.assertEqual(
            summary,
            {
                "focused_test_count": 68,
                "full_test_count": 151,
                "profile_sha256": EXPECTED_PROFILE_SHA256,
                "schema": checker.VALIDATION_SCHEMA,
                "source_file_count": 11,
                "test_id_digest": EXPECTED_TEST_ID_DIGEST,
            },
        )

    def test_corpus_is_canonical_and_binds_checker_and_source_manifest(self):
        raw = (ROOT / checker.CORPUS_PATH).read_bytes()
        document = corpus_document()
        self.assertEqual(raw, checker.canonical_json_bytes(document))
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (EXPECTED_CORPUS_BYTES, EXPECTED_CORPUS_SHA256))
        self.assertEqual(raw_sha256(CHECKER_PATH), EXPECTED_CHECKER_SHA256)
        self.assertEqual(document["checker_source_sha256"], EXPECTED_CHECKER_SHA256)
        manifest = checker.compact_json_bytes(document["source_files"])
        self.assertEqual(
            hashlib.sha256(checker.SOURCE_MANIFEST_DOMAIN + manifest).hexdigest(),
            checker.SOURCE_MANIFEST_SHA256,
        )
        self.assertEqual(document["source_commit"], EXPECTED_SOURCE_COMMIT)
        self.assertEqual(document["source_tree"], EXPECTED_SOURCE_TREE)
        self.assertEqual(document["source_manifest_sha256"], EXPECTED_SOURCE_MANIFEST_SHA256)
        self.assertEqual(checker.SOURCE_COMMIT, EXPECTED_SOURCE_COMMIT)
        self.assertEqual(checker.SOURCE_TREE, EXPECTED_SOURCE_TREE)
        self.assertEqual(checker.SOURCE_MANIFEST_SHA256, EXPECTED_SOURCE_MANIFEST_SHA256)

    def test_all_three_boundary_schema_descriptors_match_independent_golden_hashes(self):
        boundary = (
            ROOT / "docs/796a3l2-phase-hsai-p01b-linux-container-implementation-boundary.md"
        ).read_text(encoding="ascii")
        blocks = [value.encode("ascii") for value in re.findall(r"```json\n(.*?)\n```", boundary, re.S)]
        for domain, expected_bytes, expected_digest in SCHEMA_GOLDENS:
            with self.subTest(domain=domain):
                matches = [value for value in blocks if len(value) == expected_bytes]
                self.assertEqual(len(matches), 1)
                self.assertEqual(
                    hashlib.sha256(domain + matches[0]).hexdigest(), expected_digest
                )

    def test_loader_and_ast_reconstruct_exact_ordered_ids_without_running_tests(self):
        document = corpus_document()
        payloads = source_payloads(document)
        original_run = unittest.TestCase.run

        def fail_if_run(*_args, **_kwargs):
            raise AssertionError("discovery executed a test")

        unittest.TestCase.run = fail_if_run
        try:
            focused_loader = checker.static_loader_ids(
                payloads, checker.FOCUSED_SUITE_FILES
            )
            full_loader = checker.static_loader_ids(payloads, checker.FULL_SUITE_FILES)
        finally:
            unittest.TestCase.run = original_run

        focused_ast = checker.ast_ids(payloads, checker.FOCUSED_SUITE_FILES)
        full_ast = checker.ast_ids(payloads, checker.FULL_SUITE_FILES)
        self.assertEqual(focused_loader, focused_ast)
        self.assertEqual(full_loader, full_ast)
        self.assertEqual(focused_loader, document["focused"]["ids"])
        self.assertEqual(full_loader, document["full"]["ids"])
        self.assertEqual((len(focused_loader), len(full_loader)), (68, 151))
        self.assertNotIn(IMPLEMENTATION_PATHS[-1], checker.FULL_SUITE_FILES)

    def test_id_arrays_and_combined_domain_digest_are_exact(self):
        document = corpus_document()
        focused = checker.compact_json_bytes(document["focused"]["ids"])
        full = checker.compact_json_bytes(document["full"]["ids"])
        self.assertEqual(hashlib.sha256(focused).hexdigest(), EXPECTED_FOCUSED_ID_ARRAY_SHA256)
        self.assertEqual(hashlib.sha256(full).hexdigest(), EXPECTED_FULL_ID_ARRAY_SHA256)
        self.assertEqual(checker.FOCUSED_ID_ARRAY_SHA256, EXPECTED_FOCUSED_ID_ARRAY_SHA256)
        self.assertEqual(checker.FULL_ID_ARRAY_SHA256, EXPECTED_FULL_ID_ARRAY_SHA256)
        combined = {
            "focused": document["focused"]["ids"],
            "full": document["full"]["ids"],
            "schema": "hsai-p01b-test-corpus-v1",
        }
        self.assertEqual(
            hashlib.sha256(checker.TEST_ID_DOMAIN + checker.compact_json_bytes(combined)).hexdigest(),
            EXPECTED_TEST_ID_DIGEST,
        )
        self.assertEqual(checker.TEST_ID_DIGEST, EXPECTED_TEST_ID_DIGEST)

    def test_exact_argv_environment_working_directory_and_suite_files(self):
        document = corpus_document()
        self.assertEqual(document["container_environment"], EXPECTED_CONTAINER_ENVIRONMENT)
        self.assertEqual(checker.CONTAINER_ENVIRONMENT, EXPECTED_CONTAINER_ENVIRONMENT)
        self.assertEqual(document["working_directory"], "/input")
        self.assertEqual(document["focused"]["argv"], EXPECTED_FOCUSED_ARGV)
        self.assertEqual(document["full"]["argv"], EXPECTED_FULL_ARGV)
        self.assertEqual(document["focused"]["suite_files"], EXPECTED_FOCUSED_SUITE_FILES)
        self.assertEqual(document["full"]["suite_files"], EXPECTED_FULL_SUITE_FILES)
        self.assertEqual(checker.FOCUSED_ARGV, EXPECTED_FOCUSED_ARGV)
        self.assertEqual(checker.FULL_ARGV, EXPECTED_FULL_ARGV)
        self.assertEqual(checker.FOCUSED_SUITE_FILES, EXPECTED_FOCUSED_SUITE_FILES)
        self.assertEqual(checker.FULL_SUITE_FILES, EXPECTED_FULL_SUITE_FILES)

    def test_source_files_have_exact_bytes_mode_and_digest(self):
        document = corpus_document()
        for entry in document["source_files"]:
            with self.subTest(path=entry["path"]):
                path = ROOT / entry["path"]
                status = path.stat()
                self.assertTrue(stat.S_ISREG(status.st_mode))
                self.assertEqual(stat.S_IMODE(status.st_mode), 0o644)
                self.assertEqual(path.stat().st_size, entry["bytes"])
                self.assertEqual(raw_sha256(path), entry["sha256"])

    def test_profile_license_and_provenance_identities_are_exact(self):
        profile = ROOT / checker.PROFILE_PATH
        license_path = ROOT / checker.LICENSE_PATH
        provenance_raw = (ROOT / checker.PROVENANCE_PATH).read_bytes()
        provenance = json.loads(provenance_raw.decode("ascii"))
        self.assertEqual(
            (profile.stat().st_size, raw_sha256(profile)),
            (EXPECTED_PROFILE_BYTES, EXPECTED_PROFILE_SHA256),
        )
        self.assertEqual(
            (license_path.stat().st_size, raw_sha256(license_path)),
            (EXPECTED_LICENSE_BYTES, EXPECTED_LICENSE_SHA256),
        )
        self.assertEqual(
            (len(provenance_raw), hashlib.sha256(provenance_raw).hexdigest()),
            (EXPECTED_PROVENANCE_BYTES, EXPECTED_PROVENANCE_SHA256),
        )
        self.assertEqual(provenance_raw, EXPECTED_PROVENANCE_LINE.encode("ascii") + b"\n")
        self.assertEqual(provenance_raw, checker.canonical_json_bytes(provenance))
        self.assertEqual(provenance, checker.EXPECTED_PROVENANCE)
        remote = provenance["verification"]["ls_remote_output"].encode("ascii")
        self.assertEqual((len(remote), hashlib.sha256(remote).hexdigest()), (135, checker.LS_REMOTE_OUTPUT_SHA256))

    def test_provenance_mutations_fail_closed(self):
        mutations = (
            ("tag", lambda value: value.update(tag="seccomp/latest")),
            ("peeled", lambda value: value.update(peeled_commit="0" * 40)),
            ("profile", lambda value: value["profile"].update(bytes=13471)),
            ("license", lambda value: value["license"].update(sha256="0" * 64)),
            (
                "remote",
                lambda value: value["verification"].update(ls_remote_output="truncated\n"),
            ),
            (
                "notice",
                lambda value: value["verification"]["notice_http_status"].update(NOTICE=200),
            ),
        )
        for name, mutate in mutations:
            with self.subTest(name=name):
                document = copy.deepcopy(checker.EXPECTED_PROVENANCE)
                mutate(document)
                self.assert_validation_error(
                    lambda document=document: checker.validate_provenance(document),
                    "pinned record",
                )

    def test_corpus_shape_type_path_and_digest_mutations_fail_closed(self):
        mutations = (
            ("extra", lambda value: value.update(unexpected=True), "keys differ"),
            ("missing", lambda value: value.pop("source_tree"), "keys differ"),
            (
                "boolean size",
                lambda value: value["source_files"][0].update(bytes=True),
                "bounded integer",
            ),
            (
                "mode",
                lambda value: value["source_files"][0].update(mode="100755"),
                "mode differs",
            ),
            (
                "traversal",
                lambda value: value["source_files"][0].update(path="../escape"),
                "canonical relative path",
            ),
            (
                "manifest",
                lambda value: value["source_files"][0].update(sha256="0" * 64),
                "source manifest digest differs",
            ),
            (
                "checker",
                lambda value: value.update(checker_source_sha256="0" * 64),
                "checker source digest differs",
            ),
        )
        for name, mutate, message in mutations:
            with self.subTest(name=name):
                document = corpus_document()
                mutate(document)
                self.assert_validation_error(
                    lambda document=document: checker.validate_document(document, ROOT),
                    message,
                )

    def test_suite_count_argv_duplicate_and_order_mutations_fail_closed(self):
        mutations = (
            (
                "count",
                lambda value: value["focused"].update(count=67),
                "count differs",
            ),
            (
                "argv",
                lambda value: value["full"].update(argv=["/bin/true"]),
                "argv differs",
            ),
            (
                "duplicate",
                lambda value: value["focused"]["ids"].append(value["focused"]["ids"][-1]),
                "ordered and unique",
            ),
            (
                "order",
                lambda value: value["full"]["ids"].reverse(),
                "ordered and unique",
            ),
        )
        for name, mutate, message in mutations:
            with self.subTest(name=name):
                document = corpus_document()
                mutate(document)
                self.assert_validation_error(
                    lambda document=document: checker.validate_document(document, ROOT),
                    message,
                )

    def test_loader_rejects_duplicate_noncanonical_and_nonascii_json(self):
        canonical = (ROOT / checker.CORPUS_PATH).read_bytes()
        duplicate = canonical.replace(
            b'"working_directory":"/input"',
            b'"working_directory":"/input","working_directory":"/input"',
        )
        pretty = (json.dumps(corpus_document(), indent=2) + "\n").encode("ascii")
        for name, raw, message in (
            ("duplicate", duplicate, "duplicate JSON key"),
            ("pretty", pretty, "not canonical JSON"),
            ("nonascii", b'{"x":"\xff"}\n', "ASCII JSON"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                write_fixed_json(root, raw)
                self.assert_validation_error(
                    lambda root=root: checker.load_canonical_json(root, checker.CORPUS_PATH),
                    message,
                )

    def test_source_symlink_and_nonregular_paths_are_rejected(self):
        first_path = pathlib.PurePosixPath(corpus_document()["source_files"][0]["path"])
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            destination = root.joinpath(*first_path.parts)
            destination.parent.mkdir(parents=True)
            destination.symlink_to(ROOT / first_path)
            self.assert_validation_error(
                lambda: checker.validate_source_files(corpus_document(), root),
                "symlinked",
            )
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            destination = root.joinpath(*first_path.parts)
            destination.mkdir(parents=True)
            self.assert_validation_error(
                lambda: checker.validate_source_files(corpus_document(), root),
                "not regular",
            )

    def test_root_intermediate_alias_fifo_and_mode_attacks_are_rejected(self):
        aliases = ("", ".", "../escape", "/absolute", "a\\b", "a/../b", "a//b")
        for value in aliases:
            with self.subTest(alias=value):
                self.assert_validation_error(
                    lambda value=value: checker.validate_relative_path(value, "candidate"),
                    "canonical relative path",
                )

        with tempfile.TemporaryDirectory() as directory:
            real_root = pathlib.Path(directory) / "real"
            real_root.mkdir()
            root_link = pathlib.Path(directory) / "root-link"
            root_link.symlink_to(real_root, target_is_directory=True)
            self.assert_validation_error(
                lambda: checker.read_regular_file(root_link, "x", 1),
                "root must not be a symlink",
            )

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "real").mkdir()
            (root / "alias").symlink_to(root / "real", target_is_directory=True)
            self.assert_validation_error(
                lambda: checker.read_regular_file(root, "alias/file", 1),
                "ancestor rejected",
            )

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            fifo = root / "fifo"
            os.mkfifo(fifo, 0o644)
            self.assert_validation_error(
                lambda: checker.read_regular_file(root, "fifo", 1), "not regular"
            )
            wrong_mode = root / "wrong-mode"
            wrong_mode.write_bytes(b"x")
            wrong_mode.chmod(0o600)
            self.assert_validation_error(
                lambda: checker.read_regular_file(root, "wrong-mode", 1),
                "mode differs",
            )

    def test_descriptor_relative_reader_uses_nofollow_and_dir_fds(self):
        original_open = checker.os.open
        calls = []

        def recording_open(path, flags, *args, **kwargs):
            calls.append((path, flags, kwargs.get("dir_fd")))
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(checker.os, "open", side_effect=recording_open):
            checker.read_regular_file(ROOT, checker.PROFILE_PATH, checker.PROFILE_BYTES)
        self.assertGreater(len(calls), 2)
        self.assertIsNone(calls[0][2])
        for path, flags, directory_descriptor in calls[1:]:
            self.assertFalse(pathlib.PurePath(path).is_absolute())
            self.assertIsNotNone(directory_descriptor)
            if getattr(os, "O_NOFOLLOW", 0):
                self.assertTrue(flags & os.O_NOFOLLOW)

    def test_static_loader_does_not_mutate_process_state_or_import_modules(self):
        payloads = source_payloads(corpus_document())
        before_path = list(sys.path)
        before_dont_write = sys.dont_write_bytecode
        before_modules = {name: id(module) for name, module in sys.modules.items()}
        checker.static_loader_ids(payloads, checker.FULL_SUITE_FILES)
        self.assertEqual(sys.path, before_path)
        self.assertEqual(sys.dont_write_bytecode, before_dont_write)
        self.assertEqual(
            {name: id(module) for name, module in sys.modules.items()}, before_modules
        )

    def test_static_loader_never_discovers_imports_or_executes_source(self):
        suite_file = "tools/hsai-formal-preflight/tests/test_shadow.py"
        payloads = {
            suite_file: (
                b"import unmanifested_local_shadow\n\n"
                b"class ShadowTests(unittest.TestCase):\n"
                b"    def test_static_only(self):\n"
                b"        raise AssertionError('must never execute')\n"
            )
        }
        with mock.patch.object(
            unittest.TestLoader,
            "discover",
            side_effect=AssertionError("pathname discovery must not run"),
        ), mock.patch(
            "builtins.__import__",
            side_effect=AssertionError("source imports must not run"),
        ):
            identifiers = checker.static_loader_ids(payloads, [suite_file])
        self.assertEqual(identifiers, ["test_shadow.ShadowTests.test_static_only"])

    def test_checker_source_has_no_forbidden_authority_or_write_surface(self):
        tree = ast.parse(CHECKER_PATH.read_text(encoding="ascii"))
        imported = set()
        calls = set()
        attributes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
        self.assertTrue(imported <= {"ast", "hashlib", "json", "os", "pathlib", "stat", "sys", "typing", "unittest"})
        self.assertTrue(imported.isdisjoint({"subprocess", "socket", "urllib", "http", "ssl", "requests", "docker", "importlib"}))
        self.assertTrue(calls.isdisjoint({"__import__", "eval", "exec", "system", "popen", "spawn", "fork"}))
        self.assertTrue(
            calls.isdisjoint(
                {
                    "write",
                    "write_bytes",
                    "write_text",
                    "mkdir",
                    "makedirs",
                    "unlink",
                    "remove",
                    "rename",
                    "replace",
                    "chmod",
                    "chown",
                }
            )
        )
        self.assertTrue(attributes.isdisjoint({"environ", "getenv", "putenv"}))

    def test_validation_does_not_mutate_repository_files(self):
        before = tree_manifest(ROOT)
        checker.validate_repository(ROOT)
        self.assertEqual(tree_manifest(ROOT), before)

    def test_runtime_traps_deny_environment_and_filesystem_mutation(self):
        class DeniedEnvironment(dict):
            def _deny(self, *_args, **_kwargs):
                raise AssertionError("environment access")

            __contains__ = _deny
            __getitem__ = _deny
            __iter__ = _deny
            copy = _deny
            get = _deny
            items = _deny
            keys = _deny
            values = _deny

        def deny_mutation(*_args, **_kwargs):
            raise AssertionError("filesystem or process mutation")

        mutation_names = (
            "chmod",
            "chown",
            "fork",
            "link",
            "makedirs",
            "mkdir",
            "popen",
            "putenv",
            "remove",
            "rename",
            "replace",
            "rmdir",
            "spawnv",
            "spawnve",
            "symlink",
            "system",
            "truncate",
            "unlink",
            "write",
        )
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(checker.os, "environ", DeniedEnvironment()))
            for name in mutation_names:
                if hasattr(checker.os, name):
                    stack.enter_context(
                        mock.patch.object(checker.os, name, side_effect=deny_mutation)
                    )
            checker.validate_repository(ROOT)

    def test_validation_succeeds_from_test_owned_nonwritable_directory_tree(self):
        document = corpus_document()
        paths = [entry["path"] for entry in document["source_files"]]
        paths.extend(
            [
                checker.CHECKER_PATH,
                checker.CORPUS_PATH,
                checker.PROFILE_PATH,
                checker.LICENSE_PATH,
                checker.PROVENANCE_PATH,
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for relative in paths:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
                destination.chmod(0o644)
            directories = sorted(
                (path for path in root.rglob("*") if path.is_dir()),
                key=lambda value: len(value.parts),
                reverse=True,
            )
            for path in directories:
                path.chmod(0o555)
            root.chmod(0o555)
            try:
                summary = checker.validate_repository(root)
                self.assertEqual(summary["full_test_count"], 151)
            finally:
                root.chmod(0o755)
                for path in directories:
                    path.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
