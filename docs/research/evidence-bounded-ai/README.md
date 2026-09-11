# Evidence-Bounded AI

State slice: `evidence-bounded-aligned-ai-research-paper-v1`.

This directory contains the research paper
**Evidence-Bounded AI: A Claim-Ceiling Architecture for Aligned Agents,
Interpretability, and Continual Learning**.

The paper is a systems-and-methodology synthesis. It does not claim general
alignment, introspection, causal self-modeling, benchmark superiority,
formal semantic correctness, or production readiness. Repository results are
reported at their recorded claim ceilings; design-only protocols and terminal
negative results are not promoted into positive scientific evidence.

## Build

Requirements:

- LuaLaTeX;
- Biber;
- TeX Live packages used by the source;
- EB Garamond.

From this directory:

```sh
./build.sh
```

The script builds into the ignored `build/` directory and copies the verified
PDF to `output/pdf/evidence-bounded-ai.pdf`.

The visual language adapts the pure-LaTeX mechanisms from
[Foadsf/vintage-latex](https://github.com/Foadsf/vintage-latex): EB Garamond,
warm paper and ink, printer's rules, engraved-style plates, and searchable
vector output. The five illustrations are generated through `luamplib` and
the pinned [fiziko](https://github.com/jemmybutton/fiziko) MetaPost library,
which supplies the shaded spheres, tubes, brushes, and springs. The build
fetches Fiziko commit `54a63dba8e6700a5e70d3508838edebcbf0f45fe` into the
ignored paper-local build directory rather than vendoring its GPL-3.0 source.
The Vintage LaTeX adaptation keeps upstream attribution and is released under
CC BY-SA 4.0.

## Evidence boundary

The paper's positive engineering findings are local, deterministic, and
contract-qualified. Scientific case studies preserve their original stop
rules, custody boundaries, independent-validation requirements, and claim
ceilings. The untracked `semantica/` directory and unrelated dirty work are
not inputs to the paper's evidence base.
