import ast, copy, json, os, sys, tempfile, unittest
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import pythia_plan, packet, run_v50_node, v50
from test_v50 import Fake, PLANTED


class RunnerFake(Fake):
    def layers(self):
        return {u: [7, 13, 19][u // 200] for u in range(600)}
    def __init__(self, model_dir, items, layers):
        super().__init__()


def frozen_fixture(tmp):
    pk = packet.build_packet("abc123")
    mdir = os.path.join(tmp, "model"); os.makedirs(mdir)
    open(os.path.join(mdir, "model.safetensors"), "wb").write(b"weights")
    h = {"model.safetensors": pythia_plan.file_sha256(os.path.join(mdir, "model.safetensors"))}
    upd = {"revision": "r" * 40, "file_hashes": h, "license_checked": "apache-2.0 verified"}
    receipt = {"provider": "GiveMeANode", "node_id": "n1", "allocation_id": "alloc-1", "usd_cap": 14.0}
    corpus = {"manifest": {"counts": {"fit": 1}}, "split_items": {"fit": [], "tune": [], "assess": []}}
    fz = packet.finalize(pk, {k: upd for k in pk["models"]}, v50.digest(corpus["manifest"]),
                         {"n": 200, "error": 0.01}, v50.digest(receipt))
    paths = {}
    for name, obj in (("packet", fz), ("corpus", corpus), ("receipt", receipt)):
        paths[name] = os.path.join(tmp, name + ".json"); json.dump(obj, open(paths[name], "w"))
    return fz, mdir, paths


class Plan(unittest.TestCase):
    def test_layers(self):
        self.assertEqual(pythia_plan.layers_for(24), [7, 13, 19])
        self.assertEqual(pythia_plan.layers_for(32), [10, 18, 26])
        with self.assertRaises(ValueError): pythia_plan.layers_for(2)

    def test_model_hash_verification(self):
        with tempfile.TemporaryDirectory() as t:
            f = os.path.join(t, "a.safetensors"); open(f, "wb").write(b"x")
            ok = {"a.safetensors": pythia_plan.file_sha256(f)}
            self.assertTrue(pythia_plan.verify_model_dir(t, ok))
            with self.assertRaises(ValueError): pythia_plan.verify_model_dir(t, {"a.safetensors": "0" * 64})
            open(os.path.join(t, "b.bin"), "wb").write(b"y")
            with self.assertRaises(ValueError): pythia_plan.verify_model_dir(t, ok)
            with self.assertRaises(ValueError): pythia_plan.verify_model_dir(t, {})


class Packet(unittest.TestCase):
    def test_code_frozen_pending_not_runnable(self):
        pk = packet.build_packet("abc")
        self.assertEqual(pk["status"], "code-frozen-data-pending")
        self.assertTrue(packet.verify_packet(pk, strict=False))
        with self.assertRaises(packet.PacketError): packet.verify_packet(pk, strict=True)

    def test_tamper(self):
        pk = packet.build_packet("abc")
        for edit in (lambda p: p["frozen"].__setitem__("known_bad_max_abs", 0.5),
                     lambda p: p.__setitem__("code_commit", "evil"),
                     lambda p: p["code"].__setitem__("v50.py", "0" * 64)):
            bad = copy.deepcopy(pk); edit(bad)
            with self.assertRaises(packet.PacketError): packet.verify_packet(bad, strict=False)
        # recomputed digest but code hash wrong still fails against files
        bad = copy.deepcopy(pk); bad["code"]["v50.py"] = "0" * 64
        bad["packet_digest"] = v50.digest({k: v for k, v in bad.items() if k != "packet_digest"})
        with self.assertRaises(packet.PacketError): packet.verify_packet(bad, strict=False)

    def test_finalize_requires_everything(self):
        pk = packet.build_packet("abc")
        part = packet.finalize(pk, {}, "d" * 64, {"n": 200}, "r" * 64)
        self.assertEqual(part["status"], "code-frozen-data-pending")
        with tempfile.TemporaryDirectory() as t:
            fz, _, _ = frozen_fixture(t)
            self.assertEqual(fz["status"], "frozen"); self.assertTrue(packet.verify_packet(fz, strict=True))


class Runner(unittest.TestCase):
    def args(self, mdir, paths, out, rate="10"):
        return ["--packet", paths["packet"], "--model-key", "pythia-1.4b", "--model-dir", mdir,
                "--corpus", paths["corpus"], "--receipt", paths["receipt"], "--out", out, "--usd-per-hour", rate]

    def test_end_to_end_fake(self):
        with tempfile.TemporaryDirectory() as t:
            fz, mdir, paths = frozen_fixture(t); out = os.path.join(t, "o.json")
            r = run_v50_node.main(self.args(mdir, paths, out), backend_factory=RunnerFake)
            self.assertEqual(r["status"], "Candidate"); self.assertEqual(json.load(open(out))["packet_digest"], fz["packet_digest"])
            self.assertLessEqual(r["spend_usd"], 14.0)

    def test_refuses_bad_inputs(self):
        with tempfile.TemporaryDirectory() as t:
            fz, mdir, paths = frozen_fixture(t); out = os.path.join(t, "o.json")
            open(os.path.join(mdir, "model.safetensors"), "wb").write(b"tampered")
            with self.assertRaises(ValueError): run_v50_node.main(self.args(mdir, paths, out), backend_factory=RunnerFake)
        with tempfile.TemporaryDirectory() as t:
            fz, mdir, paths = frozen_fixture(t); out = os.path.join(t, "o.json")
            json.dump({"allocation_id": "other"}, open(paths["receipt"], "w"))
            with self.assertRaises(v50.V50Error): run_v50_node.main(self.args(mdir, paths, out), backend_factory=RunnerFake)
        with tempfile.TemporaryDirectory() as t:
            fz, mdir, paths = frozen_fixture(t); out = os.path.join(t, "o.json")
            pk = packet.build_packet("abc"); json.dump(pk, open(paths["packet"], "w"))
            with self.assertRaises(packet.PacketError): run_v50_node.main(self.args(mdir, paths, out), backend_factory=RunnerFake)


class BackendContract(unittest.TestCase):
    """Torch is absent in CI: check the backend statically. Real behavior is verified only on the node."""
    def setUp(self):
        self.src = open(os.path.join(HERE, "..", "pythia_backend.py")).read()
        self.tree = ast.parse(self.src)

    def test_methods_present(self):
        cls = [n for n in self.tree.body if isinstance(n, ast.ClassDef) and n.name == "PythiaBackend"][0]
        have = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
        need = {"split", "scores", "layers", "magnitude", "mark_locked", "effect", "control_effect",
                "known_bad_effect", "activation_values", "total_effect", "direct_effect", "mediators"}
        self.assertTrue(need <= have, need - have)

    def test_offline_and_no_network(self):
        self.assertIn("local_files_only=True", self.src)
        self.assertEqual(self.src.count("from_pretrained("), 2); self.assertEqual(self.src.count("local_files_only=True"), 2)
        imports = {a.name.split(".")[0] for n in ast.walk(self.tree) if isinstance(n, ast.Import) for a in n.names}
        imports |= {n.module.split(".")[0] for n in ast.walk(self.tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imports & {"requests", "urllib", "socket", "http", "huggingface_hub", "subprocess"})
        self.assertIn("HF_HUB_OFFLINE", self.src); self.assertIn("before prediction lock", self.src)


if __name__ == "__main__":
    unittest.main()
