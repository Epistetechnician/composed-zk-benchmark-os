import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("v34t",R/"v34.py");assert S and S.loader;V=importlib.util.module_from_spec(S);sys.modules[S.name]=V;S.loader.exec_module(V)
def rows(n,t):return[{"correct":i<n}for i in range(t)]
def test_gate():
 loss=[{"loss":2-i/32}for i in range(32)];arms={a:{"direct":rows(8,8),"paraphrase":rows(7,8),"protected":rows(31,32),"loss_trace":loss}for a in V.P["arms"]};assert V.summary(arms)["selected_arm"]=="protected_replay_25"
