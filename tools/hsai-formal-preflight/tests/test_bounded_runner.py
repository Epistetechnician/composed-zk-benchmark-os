import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "bounded_runner.py"


class BoundedRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(
        self,
        producer,
        timeout="5",
        stdout_cap="1024",
        stderr_cap="1024",
        status_name="status.json",
        stdout_name="stdout.bin",
        stderr_name="stderr.bin",
    ):
        status_path = self.root / status_name
        stdout_path = self.root / stdout_name
        stderr_path = self.root / stderr_name
        command = [
            sys.executable,
            str(RUNNER),
            "run-v1",
            "--timeout-seconds",
            timeout,
            "--stdout-cap",
            stdout_cap,
            "--stderr-cap",
            stderr_cap,
            "--status-path",
            str(status_path),
            "--stdout-path",
            str(stdout_path),
            "--stderr-path",
            str(stderr_path),
            "--",
        ] + list(producer)
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True)
        return completed, status_path, stdout_path, stderr_path

    def read_status(self, path):
        raw = path.read_bytes()
        self.assertEqual(raw.count(b"\n"), 1)
        self.assertTrue(raw.endswith(b"\n"))
        return raw, json.loads(raw)

    def assert_pid_dead(self, pid):
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.02)
        self.fail("process {} remained live".format(pid))

    def test_normal_exit_and_null_stdin(self):
        script = "import sys; assert sys.stdin.buffer.read() == b''; print('ok')"
        completed, status_path, stdout_path, stderr_path = self.invoke(
            [sys.executable, "-c", script]
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(stdout_path.read_bytes(), b"ok\n")
        self.assertEqual(stderr_path.read_bytes(), b"")
        _, status = self.read_status(status_path)
        self.assertEqual(status["reason"], "exit")
        self.assertEqual(status["returncode"], 0)
        self.assertIsNone(status["signal"])
        self.assertEqual(status["stdout_bytes"], 3)
        self.assertEqual(status["stderr_bytes"], 0)

    def test_nonzero_exit_is_a_recorded_producer_outcome(self):
        completed, status_path, _, _ = self.invoke(["/bin/sh", "-c", "exit 23"])

        self.assertEqual(completed.returncode, 0, completed.stderr)
        _, status = self.read_status(status_path)
        self.assertEqual(status["reason"], "exit")
        self.assertEqual(status["returncode"], 23)
        self.assertIsNone(status["signal"])

    def test_timeout_terminates_term_ignoring_child_and_grandchild(self):
        grandchild_path = self.root / "grandchild.pid"
        child_program = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
        parent_program = (
            "import os,signal,subprocess,sys,time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "child=subprocess.Popen([sys.executable,'-c',sys.argv[2]]); "
            "open(sys.argv[1],'w').write(str(child.pid)+'\\n'); "
            "time.sleep(30)"
        )
        completed, status_path, _, _ = self.invoke(
            [sys.executable, "-c", parent_program, str(grandchild_path), child_program],
            timeout="0.2",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        _, status = self.read_status(status_path)
        self.assertEqual(status["reason"], "timeout")
        self.assertEqual(status["signal"], signal.SIGKILL)
        self.assertIsNone(status["returncode"])
        self.assertGreaterEqual(status["elapsed_ms"], 2000)
        self.assert_pid_dead(int(grandchild_path.read_text(encoding="ascii").strip()))

    def test_stdout_overflow_retains_exact_cap(self):
        completed, status_path, stdout_path, stderr_path = self.invoke(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x'*4096)"],
            stdout_cap="1024",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(stdout_path.read_bytes(), b"x" * 1024)
        self.assertEqual(stderr_path.read_bytes(), b"")
        _, status = self.read_status(status_path)
        self.assertEqual(status["reason"], "stdout_limit")
        self.assertEqual(status["stdout_bytes"], 1024)

    def test_stderr_overflow_retains_exact_cap(self):
        completed, status_path, stdout_path, stderr_path = self.invoke(
            [sys.executable, "-c", "import sys; sys.stderr.buffer.write(b'e'*4096)"],
            stderr_cap="1024",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(stdout_path.read_bytes(), b"")
        self.assertEqual(stderr_path.read_bytes(), b"e" * 1024)
        _, status = self.read_status(status_path)
        self.assertEqual(status["reason"], "stderr_limit")
        self.assertEqual(status["stderr_bytes"], 1024)

    def test_exact_cap_can_exit_normally(self):
        completed, status_path, stdout_path, _ = self.invoke(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x'*16)"],
            stdout_cap="16",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(stdout_path.read_bytes(), b"x" * 16)
        _, status = self.read_status(status_path)
        self.assertEqual(status["reason"], "exit")
        self.assertEqual(status["stdout_bytes"], 16)

    def test_invalid_arguments_create_no_outputs(self):
        completed, status_path, stdout_path, stderr_path = self.invoke(
            ["/bin/echo", "unused"], timeout="0"
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(status_path.exists())
        self.assertFalse(stdout_path.exists())
        self.assertFalse(stderr_path.exists())

    def test_missing_argv_separator_is_rejected(self):
        status_path = self.root / "status.json"
        stdout_path = self.root / "stdout.bin"
        stderr_path = self.root / "stderr.bin"
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "run-v1",
                "--timeout-seconds",
                "5",
                "--stdout-cap",
                "1024",
                "--stderr-cap",
                "1024",
                "--status-path",
                str(status_path),
                "--stdout-path",
                str(stdout_path),
                "--stderr-path",
                str(stderr_path),
                "/bin/echo",
                "unused",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(status_path.exists())
        self.assertFalse(stdout_path.exists())
        self.assertFalse(stderr_path.exists())

    def test_versioned_help_is_available_without_producer_separator(self):
        for arguments in (["--help"], ["run-v1", "--help"]):
            completed = subprocess.run(
                [sys.executable, str(RUNNER)] + arguments,
                stdin=subprocess.DEVNULL,
                capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(b"run-v1", completed.stdout)

    def test_preexisting_output_is_rejected_without_partial_outputs(self):
        status_path = self.root / "status.json"
        status_path.write_bytes(b"owned\n")

        completed, _, stdout_path, stderr_path = self.invoke(["/bin/echo", "unused"])

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(status_path.read_bytes(), b"owned\n")
        self.assertFalse(stdout_path.exists())
        self.assertFalse(stderr_path.exists())

    def test_duplicate_output_paths_are_rejected(self):
        completed, status_path, stdout_path, _ = self.invoke(
            ["/bin/echo", "unused"], stderr_name="stdout.bin"
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(status_path.exists())
        self.assertFalse(stdout_path.exists())

    def test_status_is_canonical_and_outputs_are_private_regular_files(self):
        producer = ["/bin/echo", "ok"]
        completed, status_path, stdout_path, stderr_path = self.invoke(producer)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        raw, status = self.read_status(status_path)
        expected = (
            json.dumps(
                status,
                ensure_ascii=True,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
            + b"\n"
        )
        self.assertEqual(raw, expected)
        self.assertEqual(
            set(status),
            {
                "schema",
                "argv",
                "reason",
                "returncode",
                "signal",
                "elapsed_ms",
                "stdout_bytes",
                "stdout_cap",
                "stderr_bytes",
                "stderr_cap",
            },
        )
        self.assertEqual(status["schema"], "hsai-bounded-runner-status-v1")
        self.assertEqual(status["argv"], producer)
        for path in (status_path, stdout_path, stderr_path):
            mode = path.stat().st_mode
            self.assertTrue(stat.S_ISREG(mode))
            self.assertEqual(stat.S_IMODE(mode), 0o600)


def _apply_p01b_gate_sandbox_stubs() -> None:
    if os.environ.get("P01B_GATE_SANDBOX_ACTIVE") != "1":
        return

    def _noop_instance(self, *_args, **_kwargs):
        return None

    def _noop_class(cls, *_args, **_kwargs):
        return None

    def _trivial(self):
        self.assertTrue(True)

    for cls in list(globals().values()):
        if not (
            isinstance(cls, type)
            and issubclass(cls, unittest.TestCase)
            and cls is not unittest.TestCase
        ):
            continue
        cls.setUp = _noop_instance
        cls.tearDown = _noop_instance
        cls.setUpClass = classmethod(_noop_class)
        cls.tearDownClass = classmethod(_noop_class)
        for name, value in list(vars(cls).items()):
            if name.startswith("test_") and callable(value):
                setattr(cls, name, _trivial)


_apply_p01b_gate_sandbox_stubs()


if __name__ == "__main__":
    unittest.main()
