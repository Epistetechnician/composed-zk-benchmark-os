# Astral Research Atlas

State slice: `astral-research-atlas-accessible-tabs-v5`.

This is a repository-native static long-form research surface inspired by the
interaction pattern of an interactive mechanistic interpretability essay. It
uses the current Astral project documents as source links and keeps the claim
ceiling visible in the interface.

The architecture figure supports Report, Telemetry, and Effect inspection
modes. Phase, evidence, stack, and architecture controls support click, touch,
Enter, and Space activation.

Selected views are URL-synchronized with `view`, `phase`, `rung`, and `lane`
query parameters, so a specific inspection state can be reloaded or shared.
The architecture and phase tablists support roving focus, arrow keys, Home,
End, Enter, and Space activation.

It is intentionally separate from `tools/astral-research-progress-app/`, which
remains the telemetry/progress prototype.

Run from the repository root:

```text
python3 -m http.server 4173 --directory .
```

Open:

```text
http://localhost:4173/tools/astral-research-atlas/
```

The page has no build step, network dependency, model execution, artifact
mutation, or evidence-authority behavior. Its figures are explanatory
visualizations only.
