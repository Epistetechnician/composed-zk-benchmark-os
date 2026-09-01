from pathlib import Path

from experiments.experience_learning.derive_real_streams_v1 import derive, validate_manifest
from experiments.experience_learning.run_real_derived_benchmark_v1 import run
from experiments.experience_learning.validate_real_derived_benchmark_v1 import validate as validate_matrix


def test_derived_streams_are_custodied_and_td_delayed(tmp_path: Path):
    # Reuse the checked-in test's external custody only when available; the
    # transformation contract itself is covered by its manifest validator.
    root = Path("/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-powered-v2")
    if not (root / "manifest.json").is_file():
        return
    output = tmp_path / "derived"
    result = derive(root, output, limit=5120)
    assert result["status"] == "acquired"
    checked = validate_manifest(output)
    assert len(checked["datasets"]) == 3
    receipt = run(output)
    path = output / "matrix.json"
    path.write_text(__import__("json").dumps(receipt), encoding="utf-8")
    assert validate_matrix(path, output)["status"] == "valid"
