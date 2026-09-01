"""Tests for the bounded operator capture wrapper.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "capture_operator_campaign_v1.sh"


def _executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_wrapper_uses_explicit_markers_and_bounded_cleanup(tmp_path: Path) -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in source
    assert "workload_start_utc=" in source
    assert "workload_end_utc=" in source
    assert "capture_stop_utc=" in source
    assert "WORKLOAD_STATUS=${PIPESTATUS[0]}" in source
    assert "kill -TERM" in source
    assert "kill -KILL" in source
    assert source.index("sudo powermetrics") < source.index("workload_start_utc=")


def test_wrapper_reaps_sampler_and_writes_end_markers(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    pid_file = tmp_path / "powermetrics.pid"
    _executable(
        fake_bin / "sudo",
        "#!/bin/sh\nexec \"$@\"\n",
    )
    _executable(
        fake_bin / "powermetrics",
        "#!/bin/sh\necho $$ > \"$FAKE_POWER_PID\"\ntrap 'exit 0' TERM INT\nwhile :; do sleep 1; done\n",
    )
    _executable(
        fake_bin / "python",
        "#!/bin/sh\nprintf 'fake_workload=%s\\n' \"$*\"\n",
    )
    output = tmp_path / "output"
    roots = {name: tmp_path / name for name in ("powered", "derived", "event")}
    for root in roots.values():
        root.mkdir()
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_POWER_PID"] = str(pid_file)
    completed = subprocess.run(
        [
            str(SCRIPT),
            "--output-root",
            str(output),
            "--powered-root",
            str(roots["powered"]),
            "--derived-root",
            str(roots["derived"]),
            "--event-root",
            str(roots["event"]),
        ],
        cwd=SCRIPT.parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    transcript = (output / "workload_transcript.txt").read_text(encoding="utf-8")
    assert "workload_start_utc=" in transcript
    assert "workload_end_utc=" in transcript
    assert "capture_stop_utc=" in transcript
    assert "workload_exit_status=0" in transcript
    pid = int(pid_file.read_text(encoding="utf-8"))
    assert subprocess.run(["kill", "-0", str(pid)], check=False).returncode != 0
