from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_fixture_and_boundary_are_explicit() -> None:
    html = (ROOT / "index.html").read_text()
    script = (ROOT / "app.js").read_text()
    assert "astral-layer-trajectory-explorer-prototype-v1" in html
    assert "Illustrative geometry only." in html
    assert "const PATH_COUNT = 255" in script
    assert "const LAYER_COUNT = 78" in script
    assert "model activations, causal effects, or assessment evidence" in html


def test_interaction_contract_is_present() -> None:
    script = (ROOT / "app.js").read_text()
    assert 'data-mode' in script or 'querySelectorAll("[data-mode]")' in script
    assert "pointerdown" in script
    assert "pointermove" in script
    assert "wheel" in script
    assert "committedPushes" in script
