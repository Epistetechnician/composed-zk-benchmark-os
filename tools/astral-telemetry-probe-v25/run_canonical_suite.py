#!/usr/bin/env python3
"""Run the authorized Astral suite with the cached offline MLX runtime."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

CANONICAL_TEST_PATHS = (
    "experiments/astral_fsm/tests",
    "tools/astral-hybrid-instrument-v24/tests",
    "tools/astral-telemetry-probe-v25/tests",
)
REQUIRED_PACKAGE_DIRS = (
    "mlx_lm",
    "numpy",
    "transformers",
    "safetensors",
    "tokenizers",
    "regex",
)


class RuntimeLayout:
    __slots__ = ("python", "pythonpath", "dyld_library_path", "torch_stub")

    def __init__(
        self,
        python: Path,
        pythonpath: tuple[Path, ...],
        dyld_library_path: Path,
        torch_stub: Path,
    ) -> None:
        self.python = python
        self.pythonpath = pythonpath
        self.dyld_library_path = dyld_library_path
        self.torch_stub = torch_stub


def _archive_roots(cache_root: Path, relative: str) -> list[Path]:
    return sorted(
        {path.parent.parent for path in cache_root.glob(f"*/{relative}")},
        key=lambda path: str(path),
    )


def _require_one(
    cache_root: Path,
    relative: str,
    label: str,
    native_marker: str | None = None,
) -> Path:
    matches = _archive_roots(cache_root, relative)
    if native_marker is not None:
        matches = [path for path in matches if (path / native_marker).is_file()]
    if not matches:
        raise RuntimeError(f"missing cached {label}: {relative}")
    return matches[0]


def _cpython_abi_tag(python: Path) -> str:
    match = re.search(r"python(\d+)\.(\d+)$", python.name)
    if match is None:
        raise RuntimeError(f"cannot infer CPython ABI from interpreter name: {python.name}")
    return f"cpython-{match.group(1)}{match.group(2)}"


def discover_layout(
    cache_root: Path,
    site_packages: Path,
    torch_stub: Path,
    python: Path,
) -> RuntimeLayout:
    """Discover only local runtime components; never install or download."""
    cache_root = cache_root.expanduser()
    site_packages = site_packages.expanduser()
    torch_stub = torch_stub.expanduser()
    python = python.expanduser()
    if not cache_root.is_dir():
        raise RuntimeError(f"MLX cache root is not a directory: {cache_root}")
    if not site_packages.is_dir():
        raise RuntimeError(f"site-packages is not a directory: {site_packages}")
    if not torch_stub.is_file():
        raise RuntimeError(f"import-only torch shim is missing: {torch_stub}")
    if not python.is_file():
        raise RuntimeError(f"Python interpreter is missing: {python}")

    abi_tag = _cpython_abi_tag(python)
    mlx_roots = _archive_roots(cache_root, "mlx/core.cpython-313-darwin.so")
    if not mlx_roots:
        raise RuntimeError("missing cached MLX CPython 3.13 extension")
    mlx_root = mlx_roots[0]
    mlx_lm_root = _require_one(cache_root, "mlx_lm/__init__.py", "MLX-LM package")
    package_markers = {
        "numpy": f"numpy/_core/_multiarray_umath.{abi_tag}-darwin.so",
        "tokenizers": "tokenizers/tokenizers.abi3.so",
        "regex": f"regex/_{abi_tag.replace('cpython-', '')}",
    }
    package_roots = []
    for package in REQUIRED_PACKAGE_DIRS:
        marker = package_markers.get(package)
        if package == "regex":
            marker = f"regex/_regex.{abi_tag}-darwin.so"
        package_roots.append(
            _require_one(cache_root, f"{package}/__init__.py", package, marker)
        )
    native_matches = sorted(cache_root.glob("*/mlx/lib/libmlx.dylib"), key=lambda path: str(path))
    if not native_matches:
        raise RuntimeError("missing MLX native library: mlx/lib/libmlx.dylib")
    native_root = native_matches[0]

    paths: list[Path] = [torch_stub.parent, mlx_root, mlx_lm_root, *package_roots, site_packages]
    deduped = tuple(dict.fromkeys(paths))
    return RuntimeLayout(
        python=python,
        pythonpath=deduped,
        dyld_library_path=native_root.parent,
        torch_stub=torch_stub,
    )


def build_env(layout: RuntimeLayout, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in layout.pythonpath)
    env["DYLD_LIBRARY_PATH"] = str(layout.dyld_library_path)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    return env


def _preflight_command(layout: RuntimeLayout) -> list[str]:
    return [
        str(layout.python),
        "-c",
        "import mlx.core as mx, mlx_lm; print(f'mlx={mx.__file__} mlx_lm={mlx_lm.__file__}')",
    ]


def canonical_command(layout: RuntimeLayout, extra_args: tuple[str, ...] = ()) -> list[str]:
    return [
        str(layout.python),
        "-m",
        "pytest",
        "-q",
        *CANONICAL_TEST_PATHS,
        *extra_args,
    ]


def run_canonical_suite(
    layout: RuntimeLayout,
    repo_root: Path,
    extra_args: tuple[str, ...] = (),
) -> int:
    env = build_env(layout)
    preflight = subprocess.run(_preflight_command(layout), cwd=repo_root, env=env, check=False)
    if preflight.returncode:
        return preflight.returncode
    return subprocess.run(
        canonical_command(layout, extra_args),
        cwd=repo_root,
        env=env,
        check=False,
    ).returncode


def _default_path(value: str) -> Path:
    return Path(value).expanduser()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=_default_path, default=Path("~/.cache/uv/archive-v0"))
    parser.add_argument(
        "--site-packages",
        type=_default_path,
        default=Path("~/.hermes/hermes-agent/venv/lib/python3.11/site-packages"),
    )
    parser.add_argument(
        "--torch-stub",
        type=_default_path,
        default=Path("/tmp/astral_torch_import_stub/torch.py"),
    )
    parser.add_argument("--python", dest="python_path", type=_default_path, default=Path("/opt/homebrew/bin/python3.13"))
    parser.add_argument("--repo-root", type=_default_path, default=Path(__file__).resolve().parents[2])
    args, extra_args = parser.parse_known_args(argv)
    try:
        layout = discover_layout(args.cache_root, args.site_packages, args.torch_stub, args.python_path)
        return run_canonical_suite(layout, args.repo_root, tuple(extra_args))
    except (OSError, RuntimeError) as exc:
        print(f"offline canonical preflight blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
