from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v40r2_fit_probe_validator", MODULE)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(validator)

ARTIFACT = Path(
    "/Users/shaanp/Documents/ResearchArtifacts/"
    "astral-rgs-v40r2-fit-probes-97e7ebe81c9f-r3/probe-qualification.json"
)


def packet():
    return json.loads(ARTIFACT.read_text())


def test_accepts_constructed_fit_probe_packet():
    result = validator.validate(packet())
    assert result["valid"], result["errors"]
    assert result["evaluation_forward_tokens"] == 3256320
    assert result["feature_probe_forward_tokens"] == 25728


@pytest.mark.parametrize(
    "mutation",
    ("assessment", "forward", "token", "budget", "feature_budget", "overlap", "runtime"),
)
def test_rejects_mutation(mutation):
    data = deepcopy(packet())
    if mutation == "assessment":
        data["overlay"]["families"][0]["family_id"] = "v40r2-assessment-00"
    elif mutation == "forward":
        data["forward_pass"] = True
    elif mutation == "token":
        data["qualification"]["prompt_rows"][0]["input_tokens"] += 1
    elif mutation == "budget":
        data["qualification"]["evaluation_forward_tokens"] += 1
    elif mutation == "feature_budget":
        data["qualification"]["feature_probe_forward_tokens"] += 1
    elif mutation == "overlap":
        data["overlay"]["protected_cases"][0]["candidates"][0] = data["overlay"][
            "families"
        ][0]["tasks"][0]["cases"][0]["target"]
    else:
        data["runtime"]["mlx"] = "changed"
    result = validator.validate(data)
    assert not result["valid"]
