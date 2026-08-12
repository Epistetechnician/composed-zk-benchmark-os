import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "astral_v25_canonical_suite_runner", HERE / "run_canonical_suite.py"
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def _fake_archive(root: Path, name: str, files: tuple[str, ...]) -> Path:
    archive = root / name
    for relative in files:
        path = archive / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder")
    return archive


def _write_metadata(archive: Path, distribution: str, version: str) -> None:
    normalized = distribution.replace("-", "_")
    metadata = archive / f"{normalized}-{version}.dist-info" / "METADATA"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(f"Name: {distribution}\nVersion: {version}\n")


def _populate_runtime_archives(cache: Path) -> None:
    mlx = _fake_archive(cache, "mlx-archive", ("mlx/core.cpython-313-darwin.so",))
    _write_metadata(mlx, "mlx", "0.31.2")
    _fake_archive(cache, "mlx-lm-archive", ("mlx_lm/__init__.py",))
    for package in ("transformers", "safetensors"):
        _fake_archive(cache, f"{package}-archive", (f"{package}/__init__.py",))
    _fake_archive(
        cache,
        "tokenizers-archive",
        ("tokenizers/__init__.py", "tokenizers/tokenizers.abi3.so"),
    )
    _fake_archive(
        cache,
        "numpy-archive",
        ("numpy/__init__.py", "numpy/_core/_multiarray_umath.cpython-313-darwin.so"),
    )
    _fake_archive(
        cache,
        "regex-compatible-archive",
        ("regex/__init__.py", "regex/_regex.cpython-313-darwin.so"),
    )


def test_discover_layout_selects_cached_runtime_components(tmp_path):
    cache = tmp_path / "archive-v0"
    cache.mkdir()
    mlx = _fake_archive(cache, "mlx-archive", ("mlx/core.cpython-313-darwin.so",))
    _write_metadata(mlx, "mlx", "0.31.2")
    _fake_archive(cache, "mlx-lm-archive", ("mlx_lm/__init__.py",))
    for package in ("transformers", "safetensors", "tokenizers"):
        suffix = "tokenizers.abi3.so" if package == "tokenizers" else "__init__.py"
        _fake_archive(cache, f"{package}-archive", (f"{package}/__init__.py", f"{package}/{suffix}"))
    _fake_archive(
        cache,
        "numpy-archive",
        ("numpy/__init__.py", "numpy/_core/_multiarray_umath.cpython-313-darwin.so"),
    )
    incompatible_regex = _fake_archive(
        cache,
        "aaa-regex-incompatible-archive",
        ("regex/__init__.py", "regex/_regex.cpython-312-darwin.so"),
    )
    compatible_regex = _fake_archive(
        cache,
        "zzz-regex-compatible-archive",
        ("regex/__init__.py", "regex/_regex.cpython-313-darwin.so"),
    )
    native = _fake_archive(cache, "mlx-native", ("mlx/lib/libmlx.dylib",))
    _write_metadata(native, "mlx-metal", "0.31.2")
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    torch_stub = tmp_path / "torch-import-stub" / "torch.py"
    torch_stub.parent.mkdir()
    torch_stub.write_text("nn = object()\n")
    python = tmp_path / "python3.13"
    python.write_text("placeholder")

    layout = RUNNER.discover_layout(cache, site_packages, torch_stub, python)

    assert layout.python == python
    assert layout.torch_stub == torch_stub
    assert layout.dyld_library_path == native / "mlx" / "lib"
    assert layout.pythonpath[0] == torch_stub.parent
    assert layout.pythonpath[-1] == site_packages
    assert any(path / "mlx" == cache / "mlx-archive" / "mlx" for path in layout.pythonpath)
    assert compatible_regex in layout.pythonpath
    assert incompatible_regex not in layout.pythonpath


def test_discover_layout_rejects_missing_native_mlx_library(tmp_path):
    cache = tmp_path / "archive-v0"
    cache.mkdir()
    _populate_runtime_archives(cache)
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    torch_stub = tmp_path / "torch.py"
    torch_stub.write_text("nn = object()\n")
    python = tmp_path / "python3.13"
    python.write_text("placeholder")

    with pytest.raises(RuntimeError, match="MLX native library"):
        RUNNER.discover_layout(cache, site_packages, torch_stub, python)


def test_discover_layout_rejects_mismatched_native_mlx_library(tmp_path):
    cache = tmp_path / "archive-v0"
    cache.mkdir()
    _populate_runtime_archives(cache)
    native = _fake_archive(cache, "mlx-native", ("mlx/lib/libmlx.dylib",))
    _write_metadata(native, "mlx-metal", "0.31.1")
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    torch_stub = tmp_path / "torch.py"
    torch_stub.write_text("nn = object()\n")
    python = tmp_path / "python3.13"
    python.write_text("placeholder")

    with pytest.raises(RuntimeError, match="MLX native library matching MLX version"):
        RUNNER.discover_layout(cache, site_packages, torch_stub, python)


def test_discover_layout_rejects_tokenizers_archive_without_native_extension(tmp_path):
    cache = tmp_path / "archive-v0"
    cache.mkdir()
    _populate_runtime_archives(cache)
    native = _fake_archive(cache, "mlx-native", ("mlx/lib/libmlx.dylib",))
    _write_metadata(native, "mlx-metal", "0.31.2")
    (cache / "tokenizers-archive" / "tokenizers" / "tokenizers.abi3.so").unlink()
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    torch_stub = tmp_path / "torch.py"
    torch_stub.write_text("nn = object()\n")
    python = tmp_path / "python3.13"
    python.write_text("placeholder")

    with pytest.raises(RuntimeError, match="missing cached tokenizers"):
        RUNNER.discover_layout(cache, site_packages, torch_stub, python)


def test_build_env_is_explicit_and_does_not_write_bytecode(tmp_path):
    layout = RUNNER.RuntimeLayout(
        python=tmp_path / "python3.13",
        pythonpath=(tmp_path / "torch", tmp_path / "packages", tmp_path / "site-packages"),
        dyld_library_path=tmp_path / "lib",
        torch_stub=tmp_path / "torch" / "torch.py",
    )

    env = RUNNER.build_env(
        layout,
        {
            "PATH": "/usr/bin",
            "PYTHONPATH": "ambient",
            "PYTEST_ADDOPTS": "-k only_one_test",
            "PYTEST_PLUGINS": "untrusted_plugin",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "0",
        },
    )

    assert env["PATH"] == "/usr/bin"
    assert env["PYTHONPATH"] == ":".join(str(path) for path in layout.pythonpath)
    assert env["DYLD_LIBRARY_PATH"] == str(layout.dyld_library_path)
    assert env["PYTHONNOUSERSITE"] == "1"
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONHASHSEED"] == "0"
    assert "PYTEST_ADDOPTS" not in env
    assert "PYTEST_PLUGINS" not in env
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_canonical_command_rejects_arguments_that_could_change_the_suite(tmp_path):
    layout = RUNNER.RuntimeLayout(
        python=tmp_path / "python3.13",
        pythonpath=(),
        dyld_library_path=tmp_path / "lib",
        torch_stub=tmp_path / "torch.py",
    )

    with pytest.raises(ValueError, match="exact canonical suite"):
        RUNNER.canonical_command(layout, ("-k", "only_one_test"))


def test_run_canonical_suite_scrubs_ambient_pytest_controls(monkeypatch, tmp_path):
    layout = RUNNER.RuntimeLayout(
        python=tmp_path / "python3.13",
        pythonpath=(),
        dyld_library_path=tmp_path / "lib",
        torch_stub=tmp_path / "torch.py",
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k only_one_test")
    monkeypatch.setenv("PYTEST_PLUGINS", "untrusted_plugin")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "0")
    calls = []

    def fake_run(command, *, cwd, env, check):
        calls.append((command, cwd, env))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(RUNNER.subprocess, "run", fake_run)

    assert RUNNER.run_canonical_suite(layout, tmp_path) == 0
    assert len(calls) == 2
    for _, _, env in calls:
        assert "PYTEST_ADDOPTS" not in env
        assert "PYTEST_PLUGINS" not in env
        assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
