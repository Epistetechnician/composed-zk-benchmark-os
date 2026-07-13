import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "execution_state_machine.py"
RUNNER_PATH = Path(__file__).resolve().parents[1] / "bounded_runner.py"
SPEC = importlib.util.spec_from_file_location("execution_state_machine", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExecutionStateMachineTests(unittest.TestCase):
    def command(self, command_id="check", stage_id="frozen-identities", **changes):
        output_root = "/tmp/hsai-state-machine-{}".format(command_id)
        values = {
            "command_id": command_id,
            "stage_id": stage_id,
            "argv": ("/usr/bin/true",),
            "env": (),
            "network_policy": MODULE.STAGE_BY_ID[stage_id].network_policy,
            "role": "producer",
            "cwd": "/tmp",
            "timeout_seconds": 5.0,
            "stdout_cap": 1024,
            "stderr_cap": 1024,
            "status_path": output_root + ".status",
            "stdout_path": output_root + ".stdout",
            "stderr_path": output_root + ".stderr",
            "expected_reason": "exit",
            "expected_returncode": 0,
            "expected_signal": None,
        }
        values.update(changes)
        return MODULE.CommandSpec(**values)

    def temporary_repo(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        (root / "tracked.txt").write_text("tracked\n", encoding="ascii")
        subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "initial"], check=True)
        return temporary, root

    def test_stage_registry_is_contiguous_and_predecessor_bound(self):
        for ordinal, stage in enumerate(MODULE.STAGES):
            self.assertEqual(stage.ordinal, ordinal)
            expected = None if ordinal == 0 else MODULE.STAGES[ordinal - 1].stage_id
            self.assertEqual(stage.predecessor, expected)

    def test_plan_round_trips_as_canonical_json(self):
        plan = MODULE.ExecutionPlan("phase-test", (self.command(),))
        raw = MODULE.canonical_json_line(plan.to_dict())
        self.assertEqual(MODULE.load_canonical_json(raw), plan.to_dict())

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.load_canonical_json(b'{"a":1,"a":2}\n')

    def test_noncanonical_json_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.load_canonical_json(b'{"a": 1}\n')

    def test_duplicate_command_ids_are_rejected(self):
        command = self.command()
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.ExecutionPlan("phase-test", (command, command)).validate()

    def test_command_stage_order_is_monotonic(self):
        later = self.command("later", "charon-source")
        earlier = self.command("earlier", "frozen-identities")
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.ExecutionPlan("phase-test", (later, earlier)).validate()

    def test_shell_execution_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(argv=("/bin/sh", "-c", "true")).validate()

    def test_exact_phase732_shell_fixtures_are_accepted(self):
        timeout = self.command(
            "timeout-fixture",
            "client-and-fixtures",
            argv=MODULE.EXACT_TIMEOUT_FIXTURE,
            role="exact-process-fixture",
            timeout_seconds=1.0,
            expected_reason="timeout",
            expected_returncode=None,
            expected_signal=15,
        )
        stderr = self.command(
            "stderr-fixture",
            "client-and-fixtures",
            argv=MODULE.EXACT_STDERR_FIXTURE,
            role="exact-process-fixture",
            expected_reason="stderr_limit",
            expected_returncode=None,
            expected_signal=15,
        )
        timeout.validate()
        stderr.validate()

    def test_near_match_phase732_shell_fixture_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(
                "near-fixture",
                "client-and-fixtures",
                argv=("/bin/sh", "-c", "exec /usr/bin/yes y >&2"),
                role="exact-process-fixture",
                expected_reason="stderr_limit",
                expected_returncode=None,
            ).validate()

    def test_relative_executable_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(argv=("git", "status")).validate()

    def test_unknown_environment_key_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(env=(("UNSCOPED", "1"),)).validate()

    def test_network_policy_drift_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(network_policy="acquisition").validate()

    def test_output_collision_is_rejected_within_command(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(status_path="/tmp/a", stdout_path="/tmp/a").validate()

    def test_output_collision_is_rejected_across_plan(self):
        first = self.command("first", status_path="/tmp/shared")
        second = self.command("second", stdout_path="/tmp/shared")
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.ExecutionPlan("phase-test", (first, second)).validate()

    def test_noncanonical_cwd_is_rejected(self):
        with self.assertRaises(MODULE.StateMachineError):
            self.command(cwd="/tmp/../tmp").validate()

    def invoke_adapter(self, producer, **changes):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        command = self.command(
            "adapter",
            argv=tuple(producer),
            cwd=str(root),
            status_path=str(root / "status.json"),
            stdout_path=str(root / "stdout.bin"),
            stderr_path=str(root / "stderr.bin"),
            env=(("LC_ALL", "C"), ("PATH", "/usr/bin:/bin")),
            **changes
        )
        adapter = MODULE.BoundedRunnerAdapter(sys.executable, str(RUNNER_PATH))
        return root, command, adapter(command)

    def test_bounded_adapter_accepts_normal_exit(self):
        root, _, result = self.invoke_adapter(("/bin/echo", "ok"))
        self.assertTrue(result.succeeded)
        self.assertEqual((root / "stdout.bin").read_bytes(), b"ok\n")

    def test_bounded_adapter_accepts_expected_nonzero_exit(self):
        _, _, result = self.invoke_adapter(
            ("/usr/bin/false",), expected_returncode=1
        )
        self.assertTrue(result.succeeded)

    def test_bounded_adapter_accepts_timeout(self):
        _, _, result = self.invoke_adapter(
            ("/bin/sleep", "30"),
            timeout_seconds=0.1,
            expected_reason="timeout",
            expected_returncode=None,
            expected_signal=15,
        )
        self.assertTrue(result.succeeded)

    def test_bounded_adapter_accepts_stdout_limit(self):
        _, _, result = self.invoke_adapter(
            (sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x'*4096)"),
            stdout_cap=64,
            expected_reason="stdout_limit",
            expected_returncode=None,
            expected_signal=15,
        )
        self.assertTrue(result.succeeded)

    def test_bounded_adapter_accepts_stderr_limit(self):
        _, _, result = self.invoke_adapter(
            (sys.executable, "-c", "import sys; sys.stderr.buffer.write(b'x'*4096)"),
            stderr_cap=64,
            expected_reason="stderr_limit",
            expected_returncode=None,
            expected_signal=15,
        )
        self.assertTrue(result.succeeded)

    def test_bounded_adapter_rejects_preexisting_output(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        status_path = root / "status.json"
        status_path.write_text("owned\n", encoding="ascii")
        command = self.command(
            "adapter",
            cwd=str(root),
            status_path=str(status_path),
            stdout_path=str(root / "stdout.bin"),
            stderr_path=str(root / "stderr.bin"),
        )
        result = MODULE.BoundedRunnerAdapter(sys.executable, str(RUNNER_PATH))(command)
        self.assertFalse(result.succeeded)
        self.assertEqual(result.failure_code, "OutputPathAlreadyExists")

    def test_bounded_adapter_replaces_environment(self):
        root, _, result = self.invoke_adapter(
            (
                sys.executable,
                "-c",
                "import os; print(','.join(sorted(os.environ)))",
            )
        )
        self.assertTrue(result.succeeded)
        observed = set((root / "stdout.bin").read_text(encoding="ascii").strip().split(","))
        self.assertEqual(observed - {"__CF_USER_TEXT_ENCODING"}, {"LC_ALL", "PATH"})

    def test_bounded_adapter_rejects_status_argv_drift(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        fake_runner = root / "fake_runner.py"
        fake_runner.write_text(
            "import json,pathlib,sys\n"
            "def value(flag): return sys.argv[sys.argv.index(flag)+1]\n"
            "stdout=pathlib.Path(value('--stdout-path')); stderr=pathlib.Path(value('--stderr-path')); status=pathlib.Path(value('--status-path'))\n"
            "stdout.write_bytes(b''); stderr.write_bytes(b'')\n"
            "document={'argv':['/usr/bin/false'],'elapsed_ms':0,'reason':'exit','returncode':0,'schema':'hsai-bounded-runner-status-v1','signal':None,'stderr_bytes':0,'stderr_cap':1024,'stdout_bytes':0,'stdout_cap':1024}\n"
            "status.write_text(json.dumps(document,separators=(',',':'),sort_keys=True)+'\\n',encoding='ascii')\n",
            encoding="ascii",
        )
        command = self.command(
            "adapter",
            cwd=str(root),
            status_path=str(root / "status.json"),
            stdout_path=str(root / "stdout.bin"),
            stderr_path=str(root / "stderr.bin"),
            env=(("LC_ALL", "C"), ("PATH", "/usr/bin:/bin")),
        )
        result = MODULE.BoundedRunnerAdapter(sys.executable, str(fake_runner))(command)
        self.assertFalse(result.succeeded)
        self.assertEqual(result.failure_code, "BoundedStatusArgvDrift")

    def test_state_rejects_stage_skip(self):
        state = MODULE.AttemptState("phase-test")
        with self.assertRaises(MODULE.StateMachineError):
            state.record_stage("frozen-identities", ())

    def test_state_rejects_stage_replay(self):
        state = MODULE.AttemptState("phase-test")
        state.record_stage("primary-preservation", ())
        with self.assertRaises(MODULE.StateMachineError):
            state.record_stage("primary-preservation", ())

    def test_first_failure_is_terminal(self):
        state = MODULE.AttemptState("phase-test")
        state.record_stage(
            "primary-preservation",
            (MODULE.CommandResult("snapshot", False, "SnapshotMismatch"),),
        )
        self.assertEqual(state.status, "failed")
        self.assertEqual(state.first_failure["command_id"], "snapshot")
        with self.assertRaises(MODULE.StateMachineError):
            state.record_stage("primary-preservation", ())

    def test_all_stages_complete_monotonically(self):
        state = MODULE.AttemptState("phase-test")
        for stage in MODULE.STAGES:
            state.record_stage(stage.stage_id, ())
        self.assertEqual(state.status, "complete")
        self.assertIsNone(state.next_stage)

    def test_execute_stage_preserves_argv_and_completes(self):
        command = self.command("preserve", "primary-preservation")
        plan = MODULE.ExecutionPlan("phase-test", (command,))
        state = MODULE.AttemptState("phase-test")
        observed = []

        def producer(spec):
            observed.append(spec.argv)
            return MODULE.CommandResult(spec.command_id, True)

        MODULE.execute_stage(plan, state, "primary-preservation", producer)
        self.assertEqual(observed, [("/usr/bin/true",)])
        self.assertEqual(state.status, "running")

    def test_execute_stage_stops_after_first_failure(self):
        first = self.command("first", "primary-preservation")
        failed = self.command("failed", "primary-preservation")
        forbidden = self.command("forbidden", "primary-preservation")
        plan = MODULE.ExecutionPlan("phase-test", (first, failed, forbidden))
        state = MODULE.AttemptState("phase-test")
        observed = []

        def producer(spec):
            observed.append(spec.command_id)
            return MODULE.CommandResult(
                spec.command_id,
                spec.command_id != "failed",
                "ExpectedFailure" if spec.command_id == "failed" else None,
            )

        MODULE.execute_stage(plan, state, "primary-preservation", producer)
        self.assertEqual(observed, ["first", "failed"])
        self.assertEqual(state.status, "failed")
        self.assertEqual(state.first_failure["failure_code"], "ExpectedFailure")

    def test_execute_stage_converts_producer_exception_to_terminal_failure(self):
        command = self.command("explode", "primary-preservation")
        plan = MODULE.ExecutionPlan("phase-test", (command,))
        state = MODULE.AttemptState("phase-test")

        def producer(_spec):
            raise RuntimeError("boom")

        MODULE.execute_stage(plan, state, "primary-preservation", producer)
        self.assertEqual(state.status, "failed")
        self.assertEqual(state.first_failure["failure_code"], "ProducerException:RuntimeError")

    def test_execute_stage_rejects_wrong_result_identity(self):
        command = self.command("expected", "primary-preservation")
        plan = MODULE.ExecutionPlan("phase-test", (command,))
        state = MODULE.AttemptState("phase-test")
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.execute_stage(
                plan,
                state,
                "primary-preservation",
                lambda _spec: MODULE.CommandResult("wrong", True),
            )

    def test_clean_primary_snapshot_verifies(self):
        temporary, root = self.temporary_repo()
        self.addCleanup(temporary.cleanup)
        snapshot = MODULE.snapshot_primary(root)
        self.assertEqual(snapshot["files"], {})
        MODULE.verify_primary(root, snapshot)

    def test_dirty_primary_snapshot_records_hash_and_verifies(self):
        temporary, root = self.temporary_repo()
        self.addCleanup(temporary.cleanup)
        (root / "untracked.txt").write_text("owned elsewhere\n", encoding="ascii")
        snapshot = MODULE.snapshot_primary(root)
        self.assertIn("untracked.txt", snapshot["files"])
        MODULE.verify_primary(root, snapshot)

    def test_dirty_primary_mutation_is_detected(self):
        temporary, root = self.temporary_repo()
        self.addCleanup(temporary.cleanup)
        path = root / "untracked.txt"
        path.write_text("before\n", encoding="ascii")
        snapshot = MODULE.snapshot_primary(root)
        path.write_text("after\n", encoding="ascii")
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.verify_primary(root, snapshot)

    def test_rename_status_is_rejected(self):
        temporary, root = self.temporary_repo()
        self.addCleanup(temporary.cleanup)
        subprocess.run(["git", "-C", str(root), "mv", "tracked.txt", "renamed.txt"], check=True)
        with self.assertRaises(MODULE.StateMachineError):
            MODULE.snapshot_primary(root)

    def test_cli_snapshot_and_verification_support_dirty_primary(self):
        temporary, root = self.temporary_repo()
        self.addCleanup(temporary.cleanup)
        (root / "untracked.txt").write_text("dirty\n", encoding="ascii")
        snapshot = subprocess.run(
            [sys.executable, str(MODULE_PATH), "snapshot-v1", "--repo-root", str(root)],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        snapshot_path = root.parent / "snapshot.json"
        snapshot_path.write_bytes(snapshot)
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "verify-snapshot-v1",
                "--repo-root",
                str(root),
                "--snapshot",
                str(snapshot_path),
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        result = json.loads(completed.stdout)
        self.assertTrue(result["verified"])

    def test_complete_operation_plan_is_valid_and_deterministic(self):
        first = MODULE.build_complete_operation_plan()
        second = MODULE.build_complete_operation_plan()
        first.validate()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.sha256(), second.sha256())
        self.assertEqual(
            MODULE.load_canonical_json(MODULE.canonical_json_line(first.to_dict())),
            first.to_dict(),
        )

    def test_complete_operation_plan_covers_every_stage_and_kind(self):
        plan = MODULE.build_complete_operation_plan()
        self.assertEqual(
            {operation.stage_id for operation in plan.operations},
            set(MODULE.STAGE_BY_ID),
        )
        self.assertEqual(
            {operation.kind for operation in plan.operations},
            set(MODULE.OPERATION_KINDS),
        )
        self.assertEqual(
            [operation.predecessor for operation in plan.operations],
            [None] + [operation.operation_id for operation in plan.operations[:-1]],
        )

    def test_complete_operation_plan_is_machine_path_free(self):
        raw = MODULE.canonical_json_line(MODULE.build_complete_operation_plan().to_dict())
        self.assertNotIn(b"/Users/", raw)
        self.assertNotIn(b"/private/", raw)
        self.assertNotIn(b"/var/folders/", raw)

    def test_complete_operation_plan_has_no_hidden_shell_payload(self):
        raw = MODULE.canonical_json_line(MODULE.build_complete_operation_plan().to_dict())
        self.assertNotIn(b"/bin/sh", raw)
        self.assertNotIn(b"/bin/bash", raw)
        self.assertNotIn(b"/bin/zsh", raw)

    def test_complete_operation_plan_network_and_mutation_ownership_match_stages(self):
        plan = MODULE.build_complete_operation_plan()
        for operation in plan.operations:
            stage = MODULE.STAGE_BY_ID[operation.stage_id]
            self.assertEqual(operation.network_policy, stage.network_policy)
            self.assertEqual(operation.mutation_owner, stage.mutation_owner)
            if stage.network_policy == "closed":
                self.assertNotEqual(operation.network_policy, "acquisition")

    def test_loopback_operation_binds_exact_positive_and_sandboxed_negative_probe(self):
        plan = MODULE.build_complete_operation_plan()
        loopback = next(
            operation
            for operation in plan.operations
            if operation.kind == "persistent-loopback-control"
        )
        payload = dict(loopback.payload)
        positive = json.loads(payload["positive_argv"])
        negative = json.loads(payload["sandboxed_negative_argv"])
        self.assertEqual(
            negative,
            ["/usr/bin/sandbox-exec", "-f", "{SANDBOX_PROFILE}"] + positive,
        )

    def test_operation_rejects_unknown_kind(self):
        operation = MODULE.build_complete_operation_plan().operations[0]
        with self.assertRaises(MODULE.StateMachineError):
            replace(operation, kind="unknown").validate()

    def test_operation_rejects_extra_payload_field(self):
        operation = MODULE.build_complete_operation_plan().operations[0]
        with self.assertRaises(MODULE.StateMachineError):
            replace(
                operation,
                payload=operation.payload + (("unexpected", "value"),),
            ).validate()

    def test_operation_rejects_hidden_shell_payload(self):
        operation = MODULE.build_complete_operation_plan().operations[0]
        with self.assertRaises(MODULE.StateMachineError):
            replace(
                operation,
                payload=MODULE._payload(contract_ref="phase753-/bin/sh"),
            ).validate()

    def test_bounded_operation_rejects_command_identity_drift(self):
        operation = next(
            operation
            for operation in MODULE.build_complete_operation_plan().operations
            if operation.kind == "bounded-producer"
        )
        payload = dict(operation.payload)
        payload["command_id"] = "different-command"
        with self.assertRaises(MODULE.StateMachineError):
            replace(operation, payload=tuple(sorted(payload.items()))).validate()

    def test_complete_operation_plan_rejects_duplicate_id(self):
        plan = MODULE.build_complete_operation_plan()
        duplicate = replace(plan.operations[1], operation_id=plan.operations[0].operation_id)
        with self.assertRaises(MODULE.StateMachineError):
            replace(plan, operations=(plan.operations[0], duplicate) + plan.operations[2:]).validate()

    def test_complete_operation_plan_rejects_predecessor_gap(self):
        plan = MODULE.build_complete_operation_plan()
        gap = replace(plan.operations[1], predecessor=None)
        with self.assertRaises(MODULE.StateMachineError):
            replace(plan, operations=(plan.operations[0], gap) + plan.operations[2:]).validate()

    def test_complete_operation_plan_rejects_empty_stage(self):
        plan = MODULE.build_complete_operation_plan()
        operations = tuple(
            operation
            for operation in plan.operations
            if operation.stage_id != "helper-self-tests"
        )
        rebound = tuple(
            replace(operation, predecessor=None if index == 0 else operations[index - 1].operation_id)
            for index, operation in enumerate(operations)
        )
        with self.assertRaises(MODULE.StateMachineError):
            replace(plan, operations=rebound).validate()

    def test_complete_operation_plan_rejects_cleanup_before_end(self):
        plan = MODULE.build_complete_operation_plan()
        early_cleanup = replace(
            plan.operations[0],
            kind="cleanup-and-verify",
            payload=plan.operations[-1].payload,
        )
        with self.assertRaises(MODULE.StateMachineError):
            replace(plan, operations=(early_cleanup,) + plan.operations[1:]).validate()

    def test_all_complete_operations_are_reachable_exactly_once(self):
        plan = MODULE.build_complete_operation_plan()
        state = MODULE.OperationAttemptState(plan)
        observed = []
        while state.next_operation is not None:
            operation = state.next_operation
            observed.append(operation.operation_id)
            state.record(operation.operation_id, True)
        self.assertEqual(observed, [operation.operation_id for operation in plan.operations])
        self.assertEqual(state.status, "complete")
        with self.assertRaises(MODULE.StateMachineError):
            state.record(plan.operations[-1].operation_id, True)

    def test_failure_at_every_noncleanup_operation_routes_directly_to_cleanup(self):
        plan = MODULE.build_complete_operation_plan()
        cleanup = plan.operations[-1]
        for failed_index, failed in enumerate(plan.operations[:-1]):
            with self.subTest(operation_id=failed.operation_id):
                state = MODULE.OperationAttemptState(plan)
                for predecessor in plan.operations[:failed_index]:
                    state.record(predecessor.operation_id, True)
                state.record(failed.operation_id, False, "InjectedFailure")
                self.assertEqual(state.next_operation.operation_id, cleanup.operation_id)
                if failed_index + 1 < len(plan.operations) - 1:
                    with self.assertRaises(MODULE.StateMachineError):
                        state.record(plan.operations[failed_index + 1].operation_id, True)
                state.record(cleanup.operation_id, True)
                self.assertEqual(state.status, "failed-cleaned")
                self.assertEqual(
                    state.first_failure,
                    {
                        "failure_code": "InjectedFailure",
                        "operation_id": failed.operation_id,
                    },
                )

    def test_cleanup_failure_is_terminal_and_preserves_first_failure(self):
        plan = MODULE.build_complete_operation_plan()
        state = MODULE.OperationAttemptState(plan)
        first = plan.operations[0]
        cleanup = plan.operations[-1]
        state.record(first.operation_id, False, "OriginalFailure")
        state.record(cleanup.operation_id, False, "CleanupFailure")
        self.assertEqual(state.status, "cleanup-failed")
        self.assertEqual(state.first_failure["failure_code"], "OriginalFailure")
        self.assertIsNone(state.next_operation)


if __name__ == "__main__":
    unittest.main()
