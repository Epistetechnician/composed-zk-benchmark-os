import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("v36_test",R/"v36.py");assert S and S.loader;V=importlib.util.module_from_spec(S);sys.modules[S.name]=V;S.loader.exec_module(V)
def rows(n,t):return[{"correct":i<n}for i in range(t)]
def cell(a,s,o,n):
 return{"arm_id":a,"seed":s,"order_id":o,"first_after_first_direct":rows(8,8),"first_after_second_direct":rows(n,8),"second_after_second_direct":rows(8,8),"first_after_second_paraphrase":rows(n,8),"second_after_second_paraphrase":rows(8,8),"protected_after_second":rows(32,32),"reload_max_score_delta":0,"update_tokens":24576,"loss_trace":[{"loss":1}for _ in range(64)]}
def test_fixture_and_summary():
 assert len(V.fixture()["tasks"])==2;cells=[cell(a,s,o,8 if a=="joint_replay_25"else 6)for a in V.PROTOCOL["arms"]for s in V.PROTOCOL["seeds"]for o in V.PROTOCOL["orders"]];assert V.summary(cells)["qualified"]
