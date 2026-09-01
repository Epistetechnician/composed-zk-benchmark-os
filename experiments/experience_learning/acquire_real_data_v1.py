"""Acquire and custody bounded real experience streams.

State slice: ``oaklab-experience-learning-benchmark-v2``.

The acquisition boundary is deliberately separate from the learner.  Raw
archives are copied to an external, immutable root; deterministic parsers
derive ordered JSONL panels; and a manifest binds source URLs, raw digests,
derivation parameters, and derived digests.  The script never overwrites a
non-empty custody root.  Raw data are not committed to this repository.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import struct
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterator, Sequence

from .custody import load_custodied_jsonl, sha256_file


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
DEFAULT_ROOT = Path("/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1")
MANIFEST_NAME = "manifest.json"
RAW_DIR = "raw"
DERIVED_DIR = "derived"

SOURCES = {
    "noisy_mnist": {
        "kind": "noisy_mnist",
        "raw_name": "noisy-mnist-awgn.gz",
        "url": "https://www.csc.lsu.edu/~saikat/n-mnist/data/mnist-with-awgn.gz",
        "landing_page": "https://www.csc.lsu.edu/~saikat/n-mnist/",
        "citation": "LSU n-MNIST, AWGN variant; source landing page and linked archive",
        "license": "not stated on source landing page; raw archive retained locally only",
    },
    "sensor": {
        "kind": "sensor",
        "raw_name": "uci-har.zip",
        "url": "https://archive.ics.uci.edu/static/public/240/human%2Bactivity%2Brecognition%2Busing%2Bsmartphones.zip",
        "landing_page": "https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones",
        "citation": "Reyes-Ortiz et al. (2013), Human Activity Recognition Using Smartphones, UCI, DOI 10.24432/C54S4K",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
    },
    "long_horizon": {
        "kind": "long_horizon",
        "raw_name": "uci-household-power.zip",
        "url": "https://cdn.uci-ics-mlr-prod.aws.uci.edu/235/individual%2Bhousehold%2Belectric%2Bpower%2Bconsumption.zip",
        "landing_page": "https://dev.uci-ics-mlr-prod.aws.uci.edu/dataset/235/individual%2Bhousehold%2Belectric%2Bpower%2Bconsumption",
        "citation": "UCI Individual household electric power consumption dataset, DOI 10.24432/C58K54",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
    },
    "event_camera": {
        "kind": "event_camera",
        "raw_name": "edht21-dvs.zip",
        "url": "https://zenodo.org/records/4918320/files/DVS_Data.zip?download=1",
        "landing_page": "https://zenodo.org/records/4918320",
        "citation": "Event Data for Hand Tracking - EDHT21, DOI 10.5281/zenodo.4918320",
        "license": "Zenodo record does not expose a license in the retrieved metadata; local-only custody",
    },
}


def _canonical_without_digest(value: dict) -> bytes:
    payload = {key: item for key, item in value.items() if key != "manifest_sha256"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _download(url: str, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing raw artifact: {destination}")
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "oaklab-experience-learning-custody/1"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        partial.replace(destination)
    finally:
        if partial.exists():
            partial.unlink()


def _write_rows(path: Path, rows: Sequence[dict]) -> tuple[str, int]:
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n")
    return sha256_file(str(path)), path.stat().st_size


def _event_indices(features: Sequence[float], threshold: float = 0.0) -> list[int]:
    return [index for index, value in enumerate(features) if abs(float(value)) > threshold]


def _mnist_rows(raw_path: Path, limit: int) -> tuple[list[dict], dict]:
    """Read LSU's tar-in-gzip MATLAB archive without changing source ordering."""
    import scipy.io  # type: ignore[import-not-found]
    with gzip.open(raw_path, "rb") as compressed:
        tar_bytes = compressed.read()
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        if len(members) != 1:
            raise ValueError("AWGN archive must contain exactly one MATLAB file")
        member = members[0]
        matlab_bytes = archive.extractfile(member)
        if matlab_bytes is None:
            raise ValueError("AWGN MATLAB member is unreadable")
        values = scipy.io.loadmat(io.BytesIO(matlab_bytes.read()))
    images = values["train_x"]
    labels = values["train_y"]
    if images.shape[0] < limit or labels.shape[0] < limit or images.shape[1] != 784:
        raise ValueError("unexpected AWGN MNIST shape")
    rows = []
    for step in range(limit):
        features = [float(value) / 255.0 for value in images[step].tolist()]
        target = float(labels[step].argmax())
        rows.append({
            "step": step,
            "features": features,
            "target": target,
            "event_indices": _event_indices(features, threshold=0.0),
            "task_id": 0,
            "done": step == limit - 1,
            "source_id": f"train_x:{step}",
        })
    return rows, {
        "source_arrays": {"features": "train_x", "targets": "train_y"},
        "fixed_feature_scale": "pixel/255.0",
        "split": "train",
    }


def _nested_har_zip(raw_path: Path) -> zipfile.ZipFile:
    with zipfile.ZipFile(raw_path) as outer:
        members = [name for name in outer.namelist() if name.endswith("UCI HAR Dataset.zip")]
        if len(members) != 1:
            raise ValueError("UCI HAR outer archive must contain one nested dataset zip")
        return zipfile.ZipFile(io.BytesIO(outer.read(members[0])))


def _har_rows(raw_path: Path, limit: int) -> tuple[list[dict], dict]:
    with _nested_har_zip(raw_path) as archive:
        x_name = "UCI HAR Dataset/train/X_train.txt"
        y_name = "UCI HAR Dataset/train/y_train.txt"
        x_lines = archive.read(x_name).decode("utf-8").splitlines()
        y_lines = archive.read(y_name).decode("utf-8").splitlines()
    if len(x_lines) < limit or len(y_lines) < limit:
        raise ValueError("UCI HAR training split is shorter than requested panel")
    rows = []
    for step in range(limit):
        features = [float(value) for value in x_lines[step].split()]
        target = float(y_lines[step].strip())
        rows.append({
            "step": step,
            "features": features,
            "target": target,
            "event_indices": _event_indices(features, threshold=0.1),
            "task_id": int(target),
            "done": step == limit - 1,
            "source_id": f"train/X_train.txt:{step}",
        })
    return rows, {
        "source_files": [x_name, y_name],
        "split": "train",
        "feature_scale": "published UCI HAR feature values; no data-dependent normalization",
    }


def _power_rows(raw_path: Path, limit: int) -> tuple[list[dict], dict]:
    with zipfile.ZipFile(raw_path) as archive:
        name = "household_power_consumption.txt"
        if name not in archive.namelist():
            raise ValueError("household archive is missing its published text file")
        stream = io.TextIOWrapper(archive.open(name), encoding="latin-1")
        valid: list[list[float]] = []
        try:
            next(stream)  # published header
            for line in stream:
                fields = line.rstrip("\n").split(";")
                if len(fields) != 9 or "?" in fields:
                    continue
                values = [float(value) for value in fields[2:]]
                if all(math.isfinite(value) for value in values):
                    valid.append(values)
                    if len(valid) >= limit + 1:
                        break
        finally:
            stream.close()
    if len(valid) < limit + 1:
        raise ValueError("household archive lacks the requested consecutive valid rows")
    rows = []
    for step in range(limit):
        features = valid[step]
        next_features = valid[step + 1]
        rows.append({
            "step": step,
            "features": features,
            "target": next_features[0],
            "next_features": next_features,
            "event_indices": _event_indices(features, threshold=0.0),
            "task_id": 0,
            "done": step == limit - 1,
            "source_id": f"household_power_consumption.txt:valid_row_{step}",
        })
    return rows, {
        "source_file": name,
        "target": "next valid row Global_active_power",
        "feature_columns": [
            "Global_active_power", "Global_reactive_power", "Voltage",
            "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
        ],
        "missing_value_policy": "skip rows containing '?' and retain first contiguous valid panel",
        "feature_scale": "published physical units; no data-dependent normalization",
    }


def _aedat_events(data: bytes) -> Iterator[tuple[int, int, int, int]]:
    marker = b"#End Of ASCII Header"
    marker_index = data.find(marker)
    if marker_index < 0:
        raise ValueError("AEDAT header terminator not found")
    start = data.find(b"\n", marker_index) + 1
    if start <= 0 or (len(data) - start) % 8:
        raise ValueError("AEDAT v2 event payload is not aligned to 8-byte records")
    for offset in range(start, len(data), 8):
        address, timestamp = struct.unpack_from(">II", data, offset)
        x = (address >> 1) & 0x7F
        y = (address >> 8) & 0x7F
        polarity = address & 1
        yield timestamp, x, y, polarity


def _event_rows(raw_path: Path, limit: int) -> tuple[list[dict], dict]:
    with zipfile.ZipFile(raw_path) as archive:
        names = sorted(name for name in archive.namelist() if name.startswith("DVS_Data/dvs_2d_") and name.endswith(".aedat"))
        if not names:
            raise ValueError("EDHT21 archive has no 2D AEDAT recordings")
        payloads = [(name, archive.read(name)) for name in names]
    events_per_window = 256
    windows: list[tuple[list[float], list[int], str]] = []
    used_names = []
    for name, payload in payloads:
        current: list[tuple[int, int, int, int]] = []
        for event in _aedat_events(payload):
            current.append(event)
            if len(current) == events_per_window:
                timestamps = [item[0] for item in current]
                positives = sum(item[3] for item in current)
                features = [
                    len(current) / events_per_window,
                    positives / events_per_window,
                    sum(item[1] for item in current) / (events_per_window * 127.0),
                    sum(item[2] for item in current) / (events_per_window * 127.0),
                    (timestamps[-1] - timestamps[0]) / 1_000_000.0,
                ]
                windows.append((features, list(range(5)), name))
                current = []
                if name not in used_names:
                    used_names.append(name)
                if len(windows) >= limit + 1:
                    break
        if len(windows) >= limit + 1:
            break
    if len(windows) < limit + 1:
        raise ValueError("AEDAT recording lacks the requested event windows")
    rows = []
    for step in range(limit):
        features, event_indices, source_name = windows[step]
        target = windows[step + 1][0][0]  # next-window event rate
        rows.append({
            "step": step,
            "features": features,
            "target": target,
            "next_features": windows[step + 1][0],
            "event_indices": event_indices,
            "task_id": 0,
            "done": step == limit - 1,
            "source_id": f"{source_name}:window_{step}",
        })
    derivation = {
        "record_format": "AEDAT 2.0, big-endian uint32 address/timestamp pairs",
        "address_decode": "x=(address>>1)&127, y=(address>>8)&127, polarity=address&1",
        "window_events": events_per_window,
        "target": "next-window event rate",
        "feature_scale": "fixed sensor dimensions and timestamp tick (1 us) scales",
    }
    if len(used_names) == 1:
        derivation["source_file"] = used_names[0]
    else:
        derivation["source_files"] = used_names
    return rows, derivation


PARSERS = {
    "noisy_mnist": _mnist_rows,
    "sensor": _har_rows,
    "long_horizon": _power_rows,
    "event_camera": _event_rows,
}


def _ensure_empty_root(root: Path, reuse_raw: bool = False) -> None:
    if root.exists() and any(root.iterdir()):
        if not reuse_raw or not (root / RAW_DIR).is_dir():
            raise FileExistsError(f"refusing to reuse non-empty custody root: {root}")
        allowed = {RAW_DIR, DERIVED_DIR, "manifests"}
        unexpected = {path.name for path in root.iterdir()} - allowed
        if unexpected or any(
            any((root / child).iterdir())
            for child in (DERIVED_DIR, "manifests")
            if (root / child).is_dir()
        ):
            raise FileExistsError(f"raw reuse requires an otherwise empty custody root: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for child in (RAW_DIR, DERIVED_DIR):
        (root / child).mkdir(exist_ok=True)


def _safe_child(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"custody manifest path must stay below root: {relative}")
    resolved_root = root.resolve()
    resolved_candidate = (root / candidate).resolve()
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ValueError(f"custody manifest path escapes root: {relative}")
    return resolved_candidate


def acquire(
    root: Path = DEFAULT_ROOT,
    limit: int = 256,
    keys: Sequence[str] = tuple(SOURCES),
    reuse_raw: bool = False,
) -> dict:
    if limit < 2:
        raise ValueError("limit must leave at least one held-out next event/row")
    unknown = sorted(set(keys) - set(SOURCES))
    if unknown:
        raise ValueError(f"unknown datasets: {unknown}")
    _ensure_empty_root(root, reuse_raw=reuse_raw)
    records = []
    for key in keys:
        spec = SOURCES[key]
        raw_path = root / RAW_DIR / spec["raw_name"]
        if not (reuse_raw and raw_path.exists()):
            _download(spec["url"], raw_path)
        rows, derivation = PARSERS[key](raw_path, limit)
        derived_path = root / DERIVED_DIR / f"{key}.jsonl"
        derived_sha256, derived_bytes = _write_rows(derived_path, rows)
        records.append({
            "name": key,
            "kind": spec["kind"],
            "raw_file": str(Path(RAW_DIR) / spec["raw_name"]),
            "raw_bytes": raw_path.stat().st_size,
            "raw_sha256": sha256_file(str(raw_path)),
            "derived_file": str(Path(DERIVED_DIR) / f"{key}.jsonl"),
            "derived_bytes": derived_bytes,
            "derived_sha256": derived_sha256,
            "rows": len(rows),
            "feature_dim": len(rows[0]["features"]),
            "source_url": spec["url"],
            "landing_page": spec["landing_page"],
            "citation": spec["citation"],
            "license": spec["license"],
            "derivation": derivation,
        })
    manifest = {
        "schema_version": "oaklab.experience-learning.real-data-custody.v1",
        "state_slice": STATE_SLICE,
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "panel_limit": limit,
        "raw_retention": "external-local-only; do not publish raw archives without license review",
        "datasets": records,
    }
    manifest["manifest_sha256"] = hashlib.sha256(_canonical_without_digest(manifest)).hexdigest()
    _write_json(root / MANIFEST_NAME, manifest)
    (root / "README.md").write_text(
        "# Oak Lab real-data custody v1\n\n"
        f"State slice: `{STATE_SLICE}`.\n\n"
        "This root contains source archives and bounded derived JSONL panels. "
        "`manifest.json` binds every source and derived digest. The derived files "
        "preserve source order and are validated by the repository custody loader. "
        "Raw redistribution remains prohibited until each source license is reviewed.\n",
        encoding="utf-8",
    )
    return manifest


def validate_manifest(root: Path = DEFAULT_ROOT) -> dict:
    manifest_path = root / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("custody manifest state slice mismatch")
    expected_manifest_digest = manifest.get("manifest_sha256")
    actual_manifest_digest = hashlib.sha256(_canonical_without_digest(manifest)).hexdigest()
    if expected_manifest_digest != actual_manifest_digest:
        raise ValueError("custody manifest digest mismatch")
    records = manifest.get("datasets")
    if not isinstance(records, list) or not records:
        raise ValueError("custody manifest must contain datasets")
    checked = []
    seen_names = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("custody dataset record must be an object")
        name = record.get("name")
        if not isinstance(name, str) or name in seen_names:
            raise ValueError("custody dataset names must be unique strings")
        seen_names.add(name)
        raw_path = _safe_child(root, record["raw_file"])
        derived_path = _safe_child(root, record["derived_file"])
        if not raw_path.is_file() or not derived_path.is_file():
            raise FileNotFoundError(f"custody artifact missing for {name}")
        raw_digest_first = sha256_file(str(raw_path))
        raw_digest_second = sha256_file(str(raw_path))
        if (
            raw_digest_first != raw_digest_second
            or raw_digest_first != record["raw_sha256"]
            or raw_path.stat().st_size != record["raw_bytes"]
        ):
            raise ValueError(f"raw readback mismatch for {name}")
        experiences, custody = load_custodied_jsonl(
            str(derived_path), record["kind"], expected_sha256=record["derived_sha256"]
        )
        derived_digest_second = sha256_file(str(derived_path))
        if (
            derived_digest_second != custody.sha256
            or len(experiences) != record["rows"]
            or derived_path.stat().st_size != record["derived_bytes"]
        ):
            raise ValueError(f"derived readback mismatch for {name}")
        if len(experiences[0].features) != record["feature_dim"]:
            raise ValueError(f"feature dimension mismatch for {name}")
        checked.append({"name": name, "rows": len(experiences), "feature_dim": len(experiences[0].features)})
    return {
        "status": "valid",
        "state_slice": STATE_SLICE,
        "manifest_sha256": actual_manifest_digest,
        "datasets": checked,
    }


def seal(root: Path = DEFAULT_ROOT) -> None:
    """Make the explicit custody root read-only after validation."""
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--limit", type=int, default=256)
    parser.add_argument("--dataset", action="append", dest="datasets")
    parser.add_argument("--reuse-raw", action="store_true", help="use already downloaded raw files in an otherwise empty root")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    if args.validate:
        result = validate_manifest(args.root)
    else:
        result = acquire(args.root, args.limit, tuple(args.datasets or SOURCES), reuse_raw=args.reuse_raw)
        validation = validate_manifest(args.root)
        if args.seal:
            seal(args.root)
            validation = validate_manifest(args.root)
        result = {"status": "acquired", "manifest_sha256": result["manifest_sha256"], "validation": validation}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
