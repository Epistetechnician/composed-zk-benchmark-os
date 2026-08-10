"""V41R33R1 content-addressed launcher for the frozen prelude wrapper."""

from __future__ import annotations

import sys

import v41r32r1_history_prelude_wrapper as implementation


implementation.EXPECTED_COMMIT = "754220f7fc360d8dd15e5837190b895ea0550f30"
implementation.EXPECTED_ARCHIVE = (
    "sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580"
)
implementation.EXPECTED_TREE = implementation.EXPECTED_ARCHIVE

if __name__ == "__main__":
    raise SystemExit(implementation.main())
