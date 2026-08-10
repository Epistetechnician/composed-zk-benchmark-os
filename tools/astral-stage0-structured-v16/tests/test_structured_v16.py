import sys,unittest
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import structured_v16 as v
import run_structured_v16 as runner
class Tests(unittest.TestCase):
    def test_runner_exposes_callable_execution_boundary(self):
        self.assertTrue(callable(runner.run))
    def test_target_keys_are_canonical_json_strings(self):
        self.assertEqual(v.target_key("head0.cls","zero_ablation"),"head0.cls|zero_ablation")
    def test_boundaries(self):
        self.assertEqual(v.ACTOR_SEEDS,(283,293,307,311));self.assertFalse(set(v.ACTOR_SEEDS)&set(v.RESERVED_SEEDS));self.assertEqual(len(v.TARGET_ORDER),10)
    def test_features_71(self):
        rows={}
        for site in v.SITES:
            for op in v.OPERATORS:
                n=8 if site.startswith("head") else 32
                rows[v.target_key(site,op)]={"site_vector":[1.]*n,"site_norm":1.,"site_mean":1.,"site_max_abs":1.,"site_attention":1.}
        g={"bits":[0,1,0,1],"clean_logits":[.1,.2],"label":1,"rows":rows}
        for k in ("telemetry","activation","text"):self.assertEqual(len(v.feature(g,k)),71)
    def test_basis_and_projection(self):
        y=[[float(i+j) for j in range(10)] for i in range(8)];mean,b,s=v.basis(y)
        self.assertEqual(tuple(b.shape),(10,4));self.assertTrue(torch.allclose(b.T@b,torch.eye(4,dtype=torch.float64),atol=1e-9))
        x=[[float(i),float(i%2)] for i in range(8)];state=v.fit_projection(x,y,mean,b);p=v.predict_projection(state,x,mean,b);self.assertEqual((len(p),len(p[0])),(8,10))
    def test_group_rejects_incomplete(self):
        with self.assertRaises(ValueError):v.group_rows([{"seed":1,"family":1,"example_id":"x","site":"head0.cls","operator":"zero_ablation"}])
if __name__=="__main__":unittest.main()
