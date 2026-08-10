import importlib.util
import sys
from collections import Counter
from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "v21.py"
SPEC = importlib.util.spec_from_file_location("astral_v21_tested", PATH)
V21 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V21
SPEC.loader.exec_module(V21)


def test_corpus_is_document_disjoint_and_exact():
    rows = V21.build_corpus()
    assert Counter(row.split for row in rows) == {"fit": 400, "tune": 100, "assessment": 100}
    documents = {split: {row.source_path for row in rows if row.split == split} for split in ("fit", "tune", "assessment")}
    assert {name: len(paths) for name, paths in documents.items()} == {"fit": 80, "tune": 20, "assessment": 20}
    assert documents["fit"].isdisjoint(documents["tune"])
    assert documents["fit"].isdisjoint(documents["assessment"])
    assert documents["tune"].isdisjoint(documents["assessment"])
    assert len({row.normalized_line_sha256 for row in rows}) == 600
    assert len({row.hinted_prompt for row in rows}) == 600


def test_hint_ablation_and_balanced_fit_cells():
    rows = V21.build_corpus()
    for row in rows:
        marker = f"[HINT] Choose {row.hint_option}. [/HINT]\n"
        assert row.hinted_prompt.replace(marker, "") == row.ablated_prompt
        assert row.observed_word in (row.option_a, row.option_b)
        assert row.distractor_word in (row.option_a, row.option_b)
        assert row.observed_word != row.distractor_word
    counts = Counter(V21.cell_key(row) for row in rows if row.split == "fit")
    assert set(counts.values()) == {25}


def test_fit_bins_are_ordinal():
    boundaries, centroids, indices = V21.V20.fit_bins(list(range(100)))
    assert boundaries == sorted(boundaries)
    assert centroids == sorted(centroids)
    assert Counter(indices) == {0: 20, 1: 20, 2: 20, 3: 20, 4: 20}
