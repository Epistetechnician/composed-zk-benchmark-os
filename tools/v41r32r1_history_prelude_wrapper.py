"""V41R32R1 external process-history prelude wrapper.

The frozen RGS worker remains the only training implementation. This wrapper
adds the preregistered no-update scoring prelude, then calls its public ``run``
entrypoint in the same Python process.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path


RGS_ROOT = Path(os.environ.get("RGS_ROOT", "/home/dev/rgs")).resolve()
EXPECTED_COMMIT = "754220f7fc360d8dd15e5837190b895ea0550f30"
EXPECTED_ARCHIVE = "sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580"
EXPECTED_TREE = "sha256:8af3681cbee926b3d5b1255184537d7b5147f3e8ce3c62e0e4c6ff8bf927de52"
EXPECTED_ENTRYPOINT = "sha256:cccc6a69caace07871274a929785c75de98a3fe6975acd67d4866ee4c7ae8859"
EXPECTED_METHOD = "sha256:f9fa45c268fccdecde2f3dfb2c6720ed0a47e2004f1f4b50d9c4c89767ba98dd"
EXPECTED_REQUIREMENTS = "sha256:0a114a8f7abaee60c0aff87e27354e2eae5090772b20b1bbd30093ad6d1c3541"
EXPECTED_WRAPPER = ""
EXPECTED_LAUNCHER = ""
EXPECTED_SOURCE_FILES = {
    "scripts/run_v41r27_worker.py": EXPECTED_ENTRYPOINT,
    "mesh_brain/meshmodel/v41r27_agem_retention.py": EXPECTED_METHOD,
    "requirements-v41-h100-profile.txt": EXPECTED_REQUIREMENTS,
}
RUN_ID = "v41r27-panel-8-seed-412019"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def tree_manifest_sha256(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(root).parts:
            continue
        relative = path.relative_to(root).as_posix()
        if relative == ".astral-source-binding.json":
            continue
        rows.append(f"{relative}\0{sha256(path)}\n")
    return "sha256:" + hashlib.sha256("".join(rows).encode()).hexdigest()


def verify_archive(archive_path: Path) -> None:
    if not archive_path.is_file() or sha256(archive_path) != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R33R1 uploaded source archive mismatch")


def verify_extracted_tree(root: Path) -> None:
    if tree_manifest_sha256(root) != EXPECTED_TREE:
        raise RuntimeError("V41R33R1 extracted source tree mismatch")


def verify_source_files(root: Path) -> None:
    for relative, expected in EXPECTED_SOURCE_FILES.items():
        path = root / relative
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"V41R33R1 source file mismatch: {relative}")


def verify_runtime_hashes(launcher_path: Path | None) -> None:
    if EXPECTED_WRAPPER and sha256(Path(__file__).resolve()) != EXPECTED_WRAPPER:
        raise RuntimeError("V41R33R1 wrapper hash mismatch")
    if EXPECTED_LAUNCHER:
        if launcher_path is None or sha256(launcher_path.resolve()) != EXPECTED_LAUNCHER:
            raise RuntimeError("V41R33R1 launcher hash mismatch")


def require_bindings(archive_path: Path) -> None:
    if os.environ.get("RGS_SOURCE_COMMIT") != EXPECTED_COMMIT:
        raise RuntimeError("V41R33R1 source commit binding mismatch")
    if os.environ.get("RGS_SOURCE_ARCHIVE_SHA256") != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R33R1 source archive environment binding mismatch")
    verify_archive(archive_path.resolve())
    actual_commit = subprocess.run(
        ["git", "get-tar-commit-id"],
        input=archive_path.resolve().read_bytes(), check=True, capture_output=True,
    ).stdout.decode().strip()
    if actual_commit != EXPECTED_COMMIT:
        raise RuntimeError("V41R33R1 extracted source commit mismatch")
    entrypoint = RGS_ROOT / "scripts" / "run_v41r27_worker.py"
    method = RGS_ROOT / "mesh_brain/meshmodel/v41r27_agem_retention.py"
    requirements = RGS_ROOT / "requirements-v41-h100-profile.txt"
    if not all(path.is_file() for path in (entrypoint, method, requirements)):
        raise RuntimeError("V41R33R1 frozen source missing")
    verify_extracted_tree(RGS_ROOT)
    verify_source_files(RGS_ROOT)


def capture_rng(torch: object) -> dict[str, object]:
    state: dict[str, object] = {"python": random.getstate()}
    try:
        import numpy
        state["numpy"] = numpy.random.get_state()
    except ImportError:
        state["numpy"] = None
    state["torch_cpu"] = torch.get_rng_state()  # type: ignore[attr-defined]
    state["torch_cuda"] = torch.cuda.get_rng_state_all()  # type: ignore[attr-defined]
    return state


def restore_rng(torch: object, state: dict[str, object]) -> None:
    random.setstate(state["python"])  # type: ignore[arg-type]
    if state["numpy"] is not None:
        import numpy
        numpy.random.set_state(state["numpy"])  # type: ignore[arg-type]
    torch.set_rng_state(state["torch_cpu"])  # type: ignore[attr-defined]
    torch.cuda.set_rng_state_all(state["torch_cuda"])  # type: ignore[attr-defined]


def main(argv: list[str] | None = None, *, launcher_path: Path | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    args = parser.parse_args(argv)
    initial_python = random.getstate()
    try:
        import numpy
        initial_numpy = numpy.random.get_state()
    except ImportError:
        initial_numpy = None
    verify_runtime_hashes(launcher_path)
    require_bindings(args.archive)
    sys.path.insert(0, str(RGS_ROOT / "scripts"))
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

    import torch

    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    import run_v41r27_worker as worker
    from run_v41_h100_profile import collate_training_rows, load_base, score_rows
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, Mxfp4Config

    before_import_rng = capture_rng(torch)
    tokenizer = AutoTokenizer.from_pretrained(worker.MODEL_ID, revision=worker.MODEL_REVISION)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    base, _, _ = load_base(torch, AutoConfig, AutoModelForCausalLM, Mxfp4Config)
    base.eval()
    acquisition = worker.acquisition_instrument()
    protected_packet = worker.protected_instrument()
    specs = {row["run_id"]: row for row in worker.run_specs()}
    spec = specs[RUN_ID]
    panel = int(spec["panel_id"].rsplit("-", 1)[1])
    cases = acquisition["cases"]
    protected = protected_packet["rows"]
    selected = [cases[index] for index in range(panel * 4, panel * 4 + 4)]
    protected_selected = [protected[index] for index in range(panel * 16, panel * 16 + 16)]
    exact_rows = [worker.score_row(case) for case in selected]
    prelude_start_rng = capture_rng(torch)
    with torch.no_grad():
        worker.score_rows(base, tokenizer, exact_rows, torch)
        worker.score_rows(base, tokenizer, protected_selected, torch)
    torch.cuda.synchronize()
    post_prelude_rng = capture_rng(torch)
    allocator_before_delete = dict(torch.cuda.memory_stats())
    del base, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    restore_rng(torch, prelude_start_rng)
    random.setstate(initial_python)
    if initial_numpy is not None:
        import numpy
        numpy.random.set_state(initial_numpy)
    torch.cuda.synchronize()
    allocator_after_delete = dict(torch.cuda.memory_stats())
    result = worker.run(args.output, RUN_ID)
    receipt = {
        "wrapper_sha256": sha256(Path(__file__).resolve()),
        "launcher_sha256": sha256(launcher_path.resolve()) if launcher_path else None,
        "launcher_path": str(launcher_path.resolve()) if launcher_path else None,
        "implementation_path": str(Path(__file__).resolve()),
        "archive_path": str(args.archive.resolve()),
        "archive_sha256": sha256(args.archive.resolve()),
        "run_id": RUN_ID,
        "source_commit": EXPECTED_COMMIT,
        "source_archive_sha256": EXPECTED_ARCHIVE,
        "prelude_case_ids": [case["case_id"] for case in selected],
        "prelude_protected_case_ids": [row["case_id"] for row in protected_selected],
        "prelude_rng_captured": bool(before_import_rng and prelude_start_rng and post_prelude_rng),
        "explicit_generators": [],
        "dataloader_worker_seeds": [],
        "allocator_before_delete": allocator_before_delete,
        "allocator_after_delete": allocator_after_delete,
        "objects_deleted": True,
        "source_tree_sha256": EXPECTED_TREE,
        "entrypoint_sha256": EXPECTED_ENTRYPOINT,
        "method_sha256": EXPECTED_METHOD,
        "requirements_sha256": EXPECTED_REQUIREMENTS,
        "result_sha256": result.get("result_sha256"),
    }
    args.output.joinpath("v41r32r1-wrapper-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
