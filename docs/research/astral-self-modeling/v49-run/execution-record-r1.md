# Astral V49 execution record r1 (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, neuron-control-lanes-unreviewed-execution-v1.

- Node: gman `astral-v49-neuron-r1`, h100-1, image pytorch-2.13-cuda12.9, europe-north1, id 6ffef873-ff32-4f4f-bcfe-b6c32212e149, $0.084/min. Billed 25.63 min = $2.1532 (ceiling USD 30). Stopped after the run.
- Model: Qwen/Qwen3-1.7B-MLX-bf16 rev 720c04346ea2b095c801ebbd545c109230964cd4, downloaded once on the node, run with HF_HUB_OFFLINE=1.
- Code (sha256): v49.py 691ac92d..., torch_backend.py (post-fix) uploaded and hash-verified, run_node.py 0a66fdce....
- Preregistered cfg: seed 49, k 32, draws 1000, min_effect 0.5, alpha 0.05; 3 layers (10,16,22) x 6144 MLP neurons; task: subject-verb agreement logit margin.
- First attempt crashed in the shuffled-control label flip (code bug, no result produced); fixed and rerun.
- Result (result-r1.json, sha256 f9338e92...): `NoCandidate`. Selected-set ablation effect: tune -1.17, assess -1.12; matched-random gap about -1.16; p = 1.0; text-only/shuffled/constant controls did not separate.

## Defect disclosed after reading the result
The fit score was `max(0, -d margin/d mask)` but ablation effect is `+d margin/d mask`, so selection picked units whose ablation *raises* the margin (negative effects). The NoCandidate outcome therefore reflects a sign error in selection, not evidence about neuron-level causality. Per the slice rule a failed gate is not retuned; any corrected run needs a fresh identity (r2) with this defect and the r1 result disclosed. No claim is made from r1.

Nonclaims: no accepted evidence, Level2+, proof, SOTA, benchmark, introspection or production claim. Lanes B-D remain hermetic fake-backend code only.
