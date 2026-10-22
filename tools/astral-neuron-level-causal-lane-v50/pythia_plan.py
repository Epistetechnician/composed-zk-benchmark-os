"""V50 model/layer plan (pure; no torch). State slices: astral-neuron-level-causal-lane-v50-execution."""
import hashlib

DEPTHS = (0.3, 0.55, 0.8)
MODELS = {
    "pythia-1.4b": {"hf_id": "EleutherAI/pythia-1.4b", "n_layers": 24, "role": "primary"},
    "pythia-2.8b": {"hf_id": "EleutherAI/pythia-2.8b", "n_layers": 32, "role": "replication"},
}
PAIRS = {" is": " are", " was": " were", " does": " do", " has": " have"}


def layers_for(n_layers):
    out = sorted({int(round(d * n_layers)) for d in DEPTHS})
    if len(out) != 3 or out[0] < 1 or out[-1] >= n_layers:
        raise ValueError("bad layer plan")
    return out


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_model_dir(model_dir, expected):
    """expected: {relative filename: sha256}. Every listed file must match; extra weight files fail."""
    import os
    if not expected:
        raise ValueError("no expected hashes recorded")
    for name, want in expected.items():
        if file_sha256(os.path.join(model_dir, name)) != want:
            raise ValueError("model file hash mismatch: %s" % name)
    present = {n for n in os.listdir(model_dir) if n.endswith((".safetensors", ".bin"))}
    if present - set(expected):
        raise ValueError("unrecorded weight files present")
    return True
