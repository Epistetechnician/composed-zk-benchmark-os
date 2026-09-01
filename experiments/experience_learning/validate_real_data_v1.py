"""Independent-process readback validator for the real-data custody root.

State slice: ``oaklab-experience-learning-benchmark-v2``.
This command performs no acquisition and no mutation.  Run it after sealing
the external root to verify manifest, raw-file, and derived-panel digests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acquire_real_data_v1 import DEFAULT_ROOT, validate_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    print(json.dumps(validate_manifest(args.root), sort_keys=True))


if __name__ == "__main__":
    main()
