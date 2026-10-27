"""V60-local runner: same experiment as run_v60_node.py on Apple MPS (device chosen here); protocol doc 200 addendum 1."""
import os, sys
os.environ["HF_HUB_OFFLINE"] = "1"; os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import v60, run_v60_node


def factory(model_dir, items, layers):
    return v60.make_backend_class()(model_dir, items, layers, device=os.environ.get("V60_DEVICE", "mps"))


if __name__ == "__main__":
    run_v60_node.main(sys.argv[1:], backend_factory=factory)
