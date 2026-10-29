"""Classify HSAI Aeneas-lane stop docs (phases 667-764) by cause. Read-only, hermetic."""
import pathlib
import re
import sys

RULES = [  # first match wins
    ("toolchain", r"local-attempt|driver-link|rustup|rust-token|charon-(cargo-lock|canonical-path|license|version|fetch|identity)|leantar|lake-identity|lean-bind|version-flag|architecture|component|inventory|lean-build"),
    ("provenance", r"provenance|acquisition|archive|tarinfo|materialization|identity-(log|stderr)|metadata|unlocalized|parser|helper-spec|fixture|runner"),
    ("ordering", r"ordering|order|protocol|ambiguity|manual-orchestration|zsh|primary|worktree|run-root|assertion|scope|sandbox|timeout|unexpected|generated-module|witness"),
]


def classify(name):
    for cat, pat in RULES:
        if re.search(pat, name):
            return cat
    return "unclassified"


def collect(docs):
    out = {}
    for p in sorted(docs.glob("[67][0-9][0-9]-phase-hsai-gateway-threat-ordinal-*.md")):
        n = int(p.name[:3])
        if 667 <= n <= 764 and re.search(r"(stop|failure|mismatch)\.md$", p.name):
            out[p.name] = classify(p.name)
    return out


if __name__ == "__main__":
    res = collect(pathlib.Path(sys.argv[1]))
    counts = {}
    for v in res.values():
        counts[v] = counts.get(v, 0) + 1
    print(len(res), counts)
