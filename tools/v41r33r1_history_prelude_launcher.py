"""V41R33R1 archive-gated launcher for the frozen prelude wrapper."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXPECTED_ARCHIVE = (
    "sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580"
)
EXPECTED_TREE = (
    "sha256:652633475af44cd6053b9dec6f44c7420c2668eb0e9253c4b994e9199ff9b9f5"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    args, _ = parser.parse_known_args(argv)
    if not args.archive.is_file() or sha256(args.archive.resolve()) != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R33R1 uploaded source archive mismatch before wrapper import")

    import v41r32r1_history_prelude_wrapper as implementation

    implementation.EXPECTED_COMMIT = "754220f7fc360d8dd15e5837190b895ea0550f30"
    implementation.EXPECTED_ARCHIVE = EXPECTED_ARCHIVE
    implementation.EXPECTED_TREE = EXPECTED_TREE
    implementation.EXPECTED_WRAPPER = (
        "sha256:e3fb6e35082d078734375c4e93d070d2ad8a7107c7cf4c0dc320949f24f8b4a5"
    )
    implementation.EXPECTED_LAUNCHER = sha256(Path(__file__).resolve())
    return implementation.main(launcher_path=Path(__file__).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
