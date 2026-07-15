"""Focused in-memory tests for the P01B container command contract."""

import ast
from dataclasses import replace
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import unittest


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "p01b_container_contract.py"
SPEC = importlib.util.spec_from_file_location("p01b_container_contract", CONTRACT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load P01B container contract")
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

HEX_1 = "1" * 64
HEX_2 = "2" * 64
HEX_3 = "3" * 64
HEX_4 = "4" * 64
CONTAINER_ID = "c" * 64
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
STDOUT_SHA256 = hashlib.sha256(b"stdout").hexdigest()
STDERR_SHA256 = hashlib.sha256(b"stderr").hexdigest()


class ContainerContractTests(unittest.TestCase):
    def setUp(self):
        self.root = contract.AuthorizationRoot(
            authorization_id="authorization-01",
            action_sha256=HEX_1,
            policy_sha256=HEX_2,
            evidence_bundle_sha256=HEX_3,
            admission_decision_sha256=HEX_4,
        )
        self.bindings = contract.PlaceholderBindings(
            attempt_id="attempt-01",
            authorization_root_sha256=self.root.digest,
            docker_executable=contract.DOCKER_EXECUTABLE,
            docker_executable_sha256=contract.DOCKER_EXECUTABLE_SHA256,
            empty_docker_config_abs="/contract/empty-docker-config",
            docker_host_uri=contract.DOCKER_HOST_URI,
            seccomp_profile_abs="/contract/seccomp.json",
            seccomp_profile_sha256=contract.SECCOMP_PROFILE_SHA256,
            clean_corpus_root_abs="/contract/corpus",
            corpus_sha256=contract.CORPUS_SHA256,
            source_manifest_sha256=contract.SOURCE_MANIFEST_SHA256,
            test_id_sha256=contract.TEST_ID_SHA256,
            attempt_tmpdir_abs="/contract/tmp/attempt-01",
            platform_manifest_reference="python@sha256:" + "a" * 64,
            image_config_digest=contract.IMAGE_CONFIG_DIGEST,
            workload_profile="focused",
        )
        self.plan = contract.build_container_command_plan(self.root, self.bindings)

    def command_template(self, role):
        return next(command for command in self.plan.commands if command.role == role)

    def receipt(self, state, outcome="exit", exit_code=0, signal=None, **changes):
        role = state.next_role
        self.assertIsNotNone(role)
        command = contract.next_container_command(self.plan, state)
        if command is None:
            command = self.command_template(role)
            if state.container_id is not None:
                argv = tuple(
                    state.container_id if item == contract.CREATED_CONTAINER_ID else item
                    for item in command.argv
                )
                command = replace(command, argv=argv)

        if outcome == "not_run":
            exit_code = None
            signal = None
            started = ended = duration = 0
            stdout_bytes = stderr_bytes = 0
            stdout_sha256 = stderr_sha256 = EMPTY_SHA256
            observed = False
            container_id = None
        else:
            if outcome == "signal":
                exit_code = None
                signal = 9 if signal is None else signal
            elif outcome != "exit":
                exit_code = None
                signal = None
            started = 10_000 + len(state.completed_receipt_sha256) * 100
            ended = started + 25
            duration = 25
            stdout_bytes = len(b"stdout")
            stderr_bytes = len(b"stderr")
            stdout_sha256 = STDOUT_SHA256
            stderr_sha256 = STDERR_SHA256
            observed = True
            if role == "create":
                container_id = CONTAINER_ID if outcome == "exit" and exit_code == 0 else None
            else:
                container_id = state.container_id

        values = {
            "plan_sha256": self.plan.digest,
            "authorization_root_sha256": self.plan.authorization_root_sha256,
            "ordinal": len(state.completed_receipt_sha256),
            "role": role,
            "argv": command.argv,
            "environment": command.environment,
            "cwd": command.cwd,
            "docker_executable_sha256": self.plan.docker_executable_sha256,
            "started_monotonic_ns": started,
            "ended_monotonic_ns": ended,
            "duration_ns": duration,
            "outcome": outcome,
            "exit_code": exit_code,
            "signal": signal,
            "stdout_bytes": stdout_bytes,
            "stdout_sha256": stdout_sha256,
            "stdout_cap": command.stdout_cap,
            "stdout_truncated": outcome == "stdout_limit",
            "stderr_bytes": stderr_bytes,
            "stderr_sha256": stderr_sha256,
            "stderr_cap": command.stderr_cap,
            "stderr_truncated": outcome == "stderr_limit",
            "container_id": container_id,
            "previous_receipt_sha256": state.previous_receipt_sha256,
            "observation_class": "synthetic_fixture",
            "container_action_observed": observed,
            "accepted_evidence_created": False,
            "level2_plus_created": False,
            "authority_granted": False,
        }
        values.update(changes)
        return contract.CommandReceipt(**values)

    def advance(self, state, outcome="exit", exit_code=0, signal=None, **changes):
        receipt = self.receipt(
            state,
            outcome=outcome,
            exit_code=exit_code,
            signal=signal,
            **changes,
        )
        return contract.advance_attempt_state(self.plan, state, receipt), receipt

    def advance_successfully_to(self, role):
        state = contract.AttemptState.initial(self.plan)
        receipts = []
        while state.next_role != role:
            state, receipt = self.advance(state)
            receipts.append(receipt)
        return state, receipts

    def assert_rejected(self, receipt, state):
        with self.assertRaises(contract.ContainerContractError):
            contract.validate_command_receipt(receipt, self.plan, state)

    def test_authorization_bindings_and_plan_are_exact_and_deterministic(self):
        expected_host_environment = (
            ("HOME", "/nonexistent"),
            ("LANG", "C"),
            ("LC_ALL", "C"),
            ("PATH", "/usr/bin:/bin"),
            ("TMPDIR", "/contract/tmp/attempt-01"),
            ("TZ", "UTC"),
        )
        expected_prefix = (
            "/Applications/Docker.app/Contents/Resources/bin/docker",
            "--config",
            "/contract/empty-docker-config",
            "--host",
            "unix:///Users/shaanp/.docker/run/docker.sock",
            "--log-level",
            "error",
        )
        expected_create = expected_prefix + (
            "container",
            "create",
            "--pull=never",
            "--platform=linux/arm64/v8",
            "--name=hsai-p01b-attempt-01",
            "--hostname=hsai-p01b",
            "--runtime=runc",
            "--network=none",
            "--ipc=none",
            "--cgroupns=private",
            "--user=65532:65532",
            "--read-only",
            "--privileged=false",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--security-opt=seccomp=/contract/seccomp.json",
            "--memory=536870912",
            "--memory-swap=536870912",
            "--memory-swappiness=0",
            "--oom-kill-disable=false",
            "--pids-limit=16",
            "--cpu-period=100000",
            "--cpu-quota=100000",
            "--ulimit=cpu=900:900",
            "--ulimit=fsize=67108864:67108864",
            "--ulimit=nofile=32:32",
            "--ulimit=core=0:0",
            "--tmpfs=/work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700",
            "--shm-size=1048576",
            "--log-driver=none",
            "--restart=no",
            "--no-healthcheck",
            "--mount=type=bind,src=/contract/corpus,dst=/input,readonly,bind-propagation=rprivate",
            "--workdir=/input",
            "--entrypoint=/usr/bin/env",
            "python@sha256:" + "a" * 64,
            "-i",
            "HOME=/nonexistent",
            "LANG=C.UTF-8",
            "LC_ALL=C.UTF-8",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "PYTHONHASHSEED=0",
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONNOUSERSITE=1",
            "TMPDIR=/work",
            "TZ=UTC",
            "/usr/local/bin/python3",
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tools/hsai-formal-preflight/tests",
            "-p",
            "test_p01b_archive_ledger.py",
        )
        placeholder = contract.CREATED_CONTAINER_ID
        expected_commands = (
            (0, "create", expected_create, "always"),
            (
                1,
                "inspect-prestart",
                expected_prefix + ("container", "inspect", "--format={{json .}}", placeholder),
                "after-create",
            ),
            (
                2,
                "start-attach",
                expected_prefix + ("container", "start", "--attach", placeholder),
                "after-prestart-inspect",
            ),
            (
                3,
                "kill",
                expected_prefix + ("container", "kill", "--signal=KILL", placeholder),
                "on-bounded-start-failure",
            ),
            (4, "wait", expected_prefix + ("container", "wait", placeholder), "after-start"),
            (
                5,
                "inspect-terminal",
                expected_prefix + ("container", "inspect", "--format={{json .}}", placeholder),
                "after-start",
            ),
            (6, "remove", expected_prefix + ("container", "rm", placeholder), "after-create"),
        )

        self.assertEqual(
            self.root.digest,
            "c793e85c49b59f53b045855f08418cc413e1ef1a67d54b78f634dd80d0ae5f90",
        )
        self.assertEqual(
            self.bindings.digest,
            "acefc04944f2c21d0aabd909010181c52475d9458077b9d0926b4e621ee3de9f",
        )
        self.assertEqual(
            self.plan.digest,
            "78c8d9f620734e1800f66ec9d03d31a508ec416f757218c26e8b223e64c044f9",
        )
        self.assertEqual(self.bindings.host_environment, expected_host_environment)
        self.assertEqual(
            tuple(
                (command.template_ordinal, command.role, command.argv, command.activation)
                for command in self.plan.commands
            ),
            expected_commands,
        )
        for command in self.plan.commands:
            self.assertEqual(command.environment, expected_host_environment)
            self.assertEqual(command.cwd, "/")
            self.assertEqual((command.stdout_cap, command.stderr_cap), (16384, 16384))
        rebuilt = contract.build_container_command_plan(self.root, self.bindings)
        self.assertEqual(rebuilt, self.plan)
        self.assertEqual(contract.canonical_json_bytes(rebuilt), contract.canonical_json_bytes(self.plan))

    def test_root_and_unsafe_placeholder_bindings_are_rejected(self):
        invalid_roots = (
            replace(self.root, authorization_id="A"),
            replace(self.root, action_sha256="A" * 64),
            replace(self.root, schema="wrong"),
        )
        for candidate in invalid_roots:
            with self.subTest(root=candidate):
                with self.assertRaises(contract.ContainerContractError):
                    contract.validate_authorization_root(candidate)

        invalid_bindings = (
            replace(self.bindings, attempt_id="unsafe/id"),
            replace(self.bindings, docker_executable="/usr/bin/docker"),
            replace(self.bindings, docker_executable_sha256="0" * 64),
            replace(self.bindings, empty_docker_config_abs="relative/config"),
            replace(self.bindings, empty_docker_config_abs="/contract/../config"),
            replace(self.bindings, clean_corpus_root_abs="//contract/corpus"),
            replace(self.bindings, attempt_tmpdir_abs=self.bindings.clean_corpus_root_abs),
            replace(self.bindings, docker_host_uri="unix:///tmp/docker.sock"),
            replace(self.bindings, seccomp_profile_sha256="0" * 64),
            replace(self.bindings, corpus_sha256="0" * 64),
            replace(self.bindings, source_manifest_sha256="0" * 64),
            replace(self.bindings, test_id_sha256="0" * 64),
            replace(self.bindings, platform_manifest_reference="sha256:" + "a" * 64),
            replace(self.bindings, image_config_digest="sha256:" + "0" * 64),
            replace(self.bindings, workload_profile="arbitrary"),
            replace(self.bindings, schema="wrong"),
        )
        for candidate in invalid_bindings:
            with self.subTest(bindings=candidate):
                with self.assertRaises(contract.ContainerContractError):
                    contract.validate_placeholder_bindings(candidate)

        mismatched = replace(self.bindings, authorization_root_sha256="f" * 64)
        with self.assertRaises(contract.ContainerContractError):
            contract.build_container_command_plan(self.root, mismatched)

    def test_plan_tamper_is_rejected(self):
        commands = self.plan.commands
        command_tampers = (
            (replace(commands[0], argv=commands[0].argv + ("extra",)),) + commands[1:],
            (replace(commands[0], environment=commands[0].environment + (("USER", "root"),)),)
            + commands[1:],
            (replace(commands[0], cwd="/tmp"),) + commands[1:],
            (replace(commands[0], stdout_cap=1),) + commands[1:],
            (replace(commands[0], activation="sometimes"),) + commands[1:],
            (replace(commands[0], template_ordinal=7),) + commands[1:],
            (commands[1], commands[0]) + commands[2:],
        )
        plan_tampers = (
            replace(self.plan, schema="wrong"),
            replace(self.plan, attempt_id="other-attempt"),
            replace(self.plan, authorization_root_sha256="f" * 64),
            replace(self.plan, bindings_sha256="f" * 64),
            replace(self.plan, docker_executable_sha256="f" * 64),
            replace(self.plan, platform_manifest_reference="other@sha256:" + "a" * 64),
            replace(self.plan, image_config_digest="sha256:" + "f" * 64),
            replace(self.plan, seccomp_profile_sha256="f" * 64),
            replace(self.plan, corpus_sha256="f" * 64),
            replace(self.plan, source_manifest_sha256="f" * 64),
            replace(self.plan, test_id_sha256="f" * 64),
        ) + tuple(replace(self.plan, commands=tamper) for tamper in command_tampers)
        for candidate in plan_tampers:
            with self.subTest(plan=candidate):
                with self.assertRaises(contract.ContainerContractError):
                    contract.validate_container_command_plan(candidate, self.root, self.bindings)

    def test_receipt_parser_accepts_only_strict_canonical_ascii_json(self):
        state = contract.AttemptState.initial(self.plan)
        receipt = self.receipt(state)
        raw = contract.canonical_json_bytes(receipt.to_dict())
        self.assertEqual(contract.parse_command_receipt(raw), receipt)
        self.assertEqual(raw, raw.strip())
        self.assertTrue(raw.isascii())

        missing = receipt.to_dict()
        del missing["role"]
        unknown = receipt.to_dict()
        unknown["unknown"] = False
        bool_ordinal = receipt.to_dict()
        bool_ordinal["ordinal"] = True
        duplicate = raw[:-1] + b',"schema":"hsai-p01b-container-command-receipt-v1"}'
        nonfinite = raw.replace(b'"duration_ns":25', b'"duration_ns":NaN', 1)
        attacks = (
            b"{",
            b"\xff",
            b" " + raw,
            duplicate,
            nonfinite,
            contract.canonical_json_bytes(missing),
            contract.canonical_json_bytes(unknown),
            contract.canonical_json_bytes(bool_ordinal),
            b"{" + b" " * contract.MAX_RECEIPT_BYTES,
        )
        for attack in attacks:
            with self.subTest(attack=attack[:80]):
                with self.assertRaises(contract.ContainerContractError):
                    contract.parse_command_receipt(attack)

        unsorted = json.dumps(receipt.to_dict(), separators=(",", ":")).encode("ascii")
        self.assertNotEqual(unsorted, raw)
        with self.assertRaises(contract.ContainerContractError):
            contract.parse_command_receipt(unsorted)

    def test_receipt_binding_context_time_stream_and_authority_drift_are_rejected(self):
        state = contract.AttemptState.initial(self.plan)
        valid = self.receipt(state)
        drifted = (
            replace(valid, authorization_root_sha256="f" * 64),
            replace(valid, plan_sha256="f" * 64),
            replace(valid, argv=valid.argv + ("extra",)),
            replace(valid, environment=replace_environment(valid.environment, "LANG", "en_US")),
            replace(valid, cwd="/tmp"),
            replace(valid, role="inspect-prestart"),
            replace(valid, ordinal=1),
            replace(valid, started_monotonic_ns=valid.ended_monotonic_ns + 1, duration_ns=0),
            replace(valid, duration_ns=valid.duration_ns + 1),
            replace(valid, signal=9),
            replace(valid, stdout_bytes=valid.stdout_cap + 1),
            replace(valid, stdout_sha256="F" * 64),
            replace(valid, stdout_truncated=True),
            replace(valid, stdout_cap=valid.stdout_cap + 1),
            replace(valid, stderr_cap=valid.stderr_cap + 1),
            replace(valid, docker_executable_sha256="f" * 64),
            replace(valid, previous_receipt_sha256="e" * 64),
            replace(valid, observation_class="accepted"),
            replace(valid, container_action_observed=False),
            replace(valid, accepted_evidence_created=True),
            replace(valid, level2_plus_created=True),
            replace(valid, authority_granted=True),
        )
        for candidate in drifted:
            with self.subTest(receipt=candidate):
                self.assert_rejected(candidate, state)

        after_create, _ = self.advance(state)
        inspect_receipt = self.receipt(after_create)
        self.assert_rejected(replace(inspect_receipt, container_id="d" * 64), after_create)
        self.assert_rejected(replace(inspect_receipt, previous_receipt_sha256=None), after_create)

        invalid_signal = replace(
            inspect_receipt,
            outcome="signal",
            exit_code=1,
            signal=9,
        )
        self.assert_rejected(invalid_signal, after_create)

    def test_not_run_receipt_cannot_fabricate_observations(self):
        state = contract.AttemptState.initial(self.plan)
        state, _ = self.advance(state, exit_code=1)
        valid = self.receipt(state, outcome="not_run")
        contract.validate_command_receipt(valid, self.plan, state)
        attacks = (
            replace(valid, container_action_observed=True),
            replace(valid, started_monotonic_ns=1),
            replace(valid, stdout_bytes=1),
            replace(valid, stdout_sha256=STDOUT_SHA256),
            replace(valid, container_id=CONTAINER_ID),
            replace(valid, exit_code=0),
        )
        for attack in attacks:
            with self.subTest(receipt=attack):
                self.assert_rejected(attack, state)

    def test_create_failure_marks_every_later_role_not_run_without_removal(self):
        state = contract.AttemptState.initial(self.plan)
        state, create = self.advance(state, exit_code=125)
        receipts = [create]
        while state.status not in contract.TERMINAL_STATUSES:
            self.assertIsNone(contract.next_container_command(self.plan, state))
            state, receipt = self.advance(state, outcome="not_run")
            receipts.append(receipt)

        self.assertEqual(
            tuple(receipt.role for receipt in receipts),
            ("create", "inspect-prestart", "start-attach", "kill", "wait", "inspect-terminal", "remove"),
        )
        self.assertTrue(all(receipt.outcome == "not_run" for receipt in receipts[1:]))
        self.assertFalse(receipts[-1].container_action_observed)
        self.assertIsNone(receipts[-1].container_id)
        self.assertEqual(state.status, "cleanup_not_applicable_no_container_created")
        self.assertEqual(contract.validate_receipt_chain(self.plan, receipts), state)

    def test_prestart_inspection_failure_skips_execution_then_removes(self):
        state = contract.AttemptState.initial(self.plan)
        receipts = []
        state, receipt = self.advance(state)
        receipts.append(receipt)
        state, receipt = self.advance(state, exit_code=1)
        receipts.append(receipt)
        for role in ("start-attach", "kill", "wait", "inspect-terminal"):
            self.assertEqual(state.next_role, role)
            self.assertIsNone(contract.next_container_command(self.plan, state))
            state, receipt = self.advance(state, outcome="not_run")
            receipts.append(receipt)

        remove = contract.next_container_command(self.plan, state)
        self.assertIsNotNone(remove)
        self.assertEqual(remove.role, "remove")
        self.assertEqual(remove.argv[-1], CONTAINER_ID)
        state, receipt = self.advance(state)
        receipts.append(receipt)
        self.assertEqual(state.status, "failed")
        self.assertEqual(receipts[-1].role, "remove")
        self.assertEqual(receipts[-1].outcome, "exit")
        self.assertEqual(contract.validate_receipt_chain(self.plan, receipts), state)

    def test_normal_success_has_no_kill_and_resolves_every_placeholder(self):
        state = contract.AttemptState.initial(self.plan)
        receipts = []
        while state.status not in contract.TERMINAL_STATUSES:
            command = contract.next_container_command(self.plan, state)
            self.assertIsNotNone(command)
            self.assertFalse(any("${" in item for item in command.argv))
            state, receipt = self.advance(state)
            receipts.append(receipt)

        self.assertEqual(
            tuple(receipt.role for receipt in receipts),
            ("create", "inspect-prestart", "start-attach", "wait", "inspect-terminal", "remove"),
        )
        self.assertEqual(state.status, "succeeded")
        self.assertFalse(state.bounded_start_failure)
        self.assertEqual(contract.validate_receipt_chain(self.plan, receipts), state)

    def test_bounded_start_failure_requires_kill_before_wait(self):
        state, receipts = self.advance_successfully_to("start-attach")
        state, bounded = self.advance(state, outcome="timeout")
        receipts.append(bounded)
        self.assertEqual(state.next_role, "kill")
        self.assertTrue(state.container_started)
        self.assertTrue(state.bounded_start_failure)

        kill = self.receipt(state)
        illegal_wait = replace(kill, role="wait")
        self.assert_rejected(illegal_wait, state)
        state = contract.advance_attempt_state(self.plan, state, kill)
        receipts.append(kill)
        self.assertEqual(state.next_role, "wait")
        while state.status not in contract.TERMINAL_STATUSES:
            state, receipt = self.advance(state)
            receipts.append(receipt)
        self.assertEqual(
            tuple(receipt.role for receipt in receipts),
            ("create", "inspect-prestart", "start-attach", "kill", "wait", "inspect-terminal", "remove"),
        )
        self.assertEqual(state.status, "failed")

    def test_kill_without_started_bounded_container_is_rejected(self):
        state, _ = self.advance_successfully_to("start-attach")
        illegal_state = replace(state, next_role="kill")
        receipt = self.receipt(illegal_state)
        self.assert_rejected(receipt, illegal_state)

        started_only = replace(illegal_state, container_started=True)
        receipt = self.receipt(started_only)
        self.assert_rejected(receipt, started_only)

    def test_wait_or_terminal_inspection_failure_still_removes(self):
        for failing_role in ("wait", "inspect-terminal"):
            with self.subTest(failing_role=failing_role):
                state, receipts = self.advance_successfully_to(failing_role)
                state, failed = self.advance(state, exit_code=1)
                receipts.append(failed)
                while state.next_role != "remove":
                    state, receipt = self.advance(state)
                    receipts.append(receipt)
                self.assertEqual(state.next_role, "remove")
                self.assertNotIn("kill", tuple(receipt.role for receipt in receipts))
                state, removed = self.advance(state)
                receipts.append(removed)
                self.assertEqual(removed.role, "remove")
                self.assertEqual(state.status, "failed")
                self.assertEqual(contract.validate_receipt_chain(self.plan, receipts), state)

    def test_cleanup_failure_is_terminal_and_rejects_later_transition(self):
        state, receipts = self.advance_successfully_to("remove")
        state, failed_remove = self.advance(state, exit_code=1)
        receipts.append(failed_remove)
        self.assertEqual(state.status, "cleanup_failed")
        self.assertIsNone(state.next_role)
        with self.assertRaises(contract.ContainerContractError):
            contract.next_container_command(self.plan, state)
        with self.assertRaises(contract.ContainerContractError):
            contract.advance_attempt_state(self.plan, state, failed_remove)
        self.assertEqual(contract.validate_receipt_chain(self.plan, receipts), state)

    def test_successful_cleanup_is_terminal_and_rejects_later_transition(self):
        state, receipts = self.advance_successfully_to("remove")
        state, removed = self.advance(state)
        receipts.append(removed)
        self.assertEqual(state.status, "succeeded")
        with self.assertRaises(contract.ContainerContractError):
            contract.advance_attempt_state(self.plan, state, removed)
        self.assertEqual(contract.validate_receipt_chain(self.plan, receipts), state)

    def test_source_has_no_execution_io_network_environment_or_cli_surface(self):
        source = inspect.getsource(contract)
        tree = ast.parse(source)
        imported_roots = set()
        forbidden_calls = {"__import__", "compile", "eval", "exec", "input", "open", "print"}
        forbidden_attributes = {
            "connect",
            "environ",
            "getenv",
            "popen",
            "read_bytes",
            "read_text",
            "run",
            "system",
            "urlopen",
            "write_bytes",
            "write_text",
        }
        function_names = set()
        main_guards = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_roots.add((node.module or "").split(".", 1)[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.add(node.name)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, forbidden_calls)
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr.lower(), forbidden_attributes)
            elif isinstance(node, ast.If):
                rendered = ast.dump(node.test, include_attributes=False)
                if "__main__" in rendered or "__name__" in rendered:
                    main_guards.append(rendered)

        self.assertEqual(imported_roots, {"dataclasses", "hashlib", "json", "re", "typing"})
        self.assertFalse({"cli", "main", "run", "execute"} & function_names)
        self.assertEqual(main_guards, [])
        self.assertNotIn("__main__", source)


def replace_environment(environment, key, value):
    return tuple((name, value if name == key else original) for name, original in environment)


if __name__ == "__main__":
    unittest.main()
