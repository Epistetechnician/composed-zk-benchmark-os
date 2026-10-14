import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("v35t",R/"v35.py");assert S and S.loader;V=importlib.util.module_from_spec(S);sys.modules[S.name]=V;S.loader.exec_module(V)
def rows(n,t):return[{"correct":i<n}for i in range(t)]
def test_fresh_fixture_gate():
 assert len(V.fixture()["cases"])==8;loss=[{"loss":2-i/32}for i in range(32)];assert V.summary(rows(7,8),rows(7,8),rows(31,32),loss,0)["qualified"]
