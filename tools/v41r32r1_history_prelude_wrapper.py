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
import sys
from pathlib import Path


RGS_ROOT = Path(os.environ.get("RGS_ROOT", "/home/dev/rgs")).resolve()
EXPECTED_COMMIT = "c3b287d4227db94a43af7888d0211fb337c330fa"
EXPECTED_ARCHIVE = "sha256:8b1802d97b14d83b6d6d4596589664885efd973cec1e02ac03250acf0e250645"
RUN_ID = "v41r27-panel-8-seed-412019"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def require_bindings() -> None:
    if os.environ.get("RGS_SOURCE_COMMIT") != EXPECTED_COMMIT:
        raise RuntimeError("V41R32R1 source commit binding mismatch")
    if os.environ.get("RGS_SOURCE_ARCHIVE_SHA256") != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R32R1 source archive binding mismatch")
    if not (RGS_ROOT / "scripts" / "run_v41r27_worker.py").is_file():
        raise RuntimeError("V41R32R1 frozen worker missing")


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require_bindings()
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
    del base, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    restore_rng(torch, prelude_start_rng)
    torch.cuda.synchronize()
    result = worker.run(args.output, RUN_ID)
    receipt = {
        "wrapper_sha256": sha256(Path(__file__).resolve()),
        "run_id": RUN_ID,
        "source_commit": EXPECTED_COMMIT,
        "source_archive_sha256": EXPECTED_ARCHIVE,
        "prelude_case_ids": [case["case_id"] for case in selected],
        "prelude_protected_case_ids": [row["case_id"] for row in protected_selected],
        "prelude_rng_captured": bool(before_import_rng and prelude_start_rng and post_prelude_rng),
        "result_sha256": result.get("result_sha256"),
    }
    args.output.joinpath("v41r32r1-wrapper-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
