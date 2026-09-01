import json

import pytest

from experiments.experience_learning.review_temporal_credit_v2 import review
from experiments.experience_learning.temporal_credit_qualification_v2 import run_qualification


def test_review_accepts_only_closure_and_disallows_execution(tmp_path):
    result = run_qualification()
    path = tmp_path / "qualification.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    decision = review(path)
    assert decision["decision"] == "accepted_for_closure_only"
    assert decision["execution_authorization"] is False
    assert decision["real_stream_execution"] == "sealed"


def test_review_rejects_candidate_status(tmp_path):
    result = run_qualification()
    result["status"] = "candidate"
    result["result_digest"] = ""  # review must reject before trusting this mutation
    path = tmp_path / "qualification.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError, match="result digest"):
        review(path)
