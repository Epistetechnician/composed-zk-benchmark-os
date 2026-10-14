import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]; S=importlib.util.spec_from_file_location("v33_test",R/"v33.py"); assert S and S.loader; V=importlib.util.module_from_spec(S); sys.modules[S.name]=V; S.loader.exec_module(V)
def rows(n,t): return [{"correct":i<n} for i in range(t)]
def test_fixture_and_summary():
    f=V.expected_fixture(); assert all(c["target"] not in c["train_prompt"] for c in f["cases"])
    arm={"direct":rows(8,8),"paraphrase":rows(7,8),"protected":rows(32,32),"loss_trace":[{"loss":2-i/32} for i in range(32)]}
    assert V.summary(rows(32,32),arm)["qualified"]
