import importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("v38_test",R/"v38.py");assert S and S.loader;V=importlib.util.module_from_spec(S);sys.modules[S.name]=V;S.loader.exec_module(V)
def rows(n,t=8):return[{"correct":i<n}for i in range(t)]
def cell(a,s,o,n,p):
 order=V.PROTOCOL["orders"][o];st=[]
 for i,t in enumerate(order,1):
  d={x:rows(8)for x in order[:i]}
  if i==4:d.update({x:rows(n)for x in order[:-1]})
  st.append({"stage":i,"direct":d})
 return{"arm_id":a,"seed":s,"order_id":o,"task_order":order,"stage_evaluations":st,"final_paraphrase":{x:rows(8)for x in order},"protected_after_final":rows(p,32),"reload_max_score_delta":0,"update_tokens":49152,"loss_trace":[{"loss":1}for _ in range(128)]}
def test_summary():
 specs={"recent_task_25":(7,28),"reservoir_task_25":(6,30),"joint_recent_alt_25":(6,32),"joint_reservoir_alt_25":(6,32)}
 cells=[cell(a,s,o,*specs[a])for a in V.PROTOCOL["arms"]for s in V.PROTOCOL["seeds"]for o in V.PROTOCOL["orders"]]
 assert V.summary(cells)["qualified"]
