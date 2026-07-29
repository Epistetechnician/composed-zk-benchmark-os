from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import random
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
SOURCE_LOCK_NAMES = (
    "rgs_corpus", "rgs_model_worker", "rgs_update_worker", "rgs_gate_core",
    "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli",
)
R1_VALIDATOR_SHA256 = "sha256:69a31f76df2fc470241d7050e27e170437aedba87a6c904e899a0888dc2f0fce"
ATOM = re.compile(r"\br7(?:entity|handle|route|token|vault|family|query)-[0-9a-f]{5,}\b")
GENERIC_ATOM = re.compile(r"\b(?:[a-z]{2,12}-)?[a-z]{4,}-[0-9a-f]{5,}\b")
HEX = re.compile(r"\b[0-9a-f]{16,}\b")


def load_v28r3() -> Any:
    path = HERE.parent / "astral-rgs-acquisition-v28r3/v28r3.py"
    spec = importlib.util.spec_from_file_location("astral_v28r3_for_v28r7", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("V28R3 clean-room primitives unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V3 = load_v28r3()
stable_hash = V3.stable_hash
sha256_file = V3.sha256_file
sha256_text = V3.sha256_text
without_hash = V3.without_hash
FACT_KINDS = tuple(PROTOCOL["fact_kinds"])
QUERY_CLASSES = tuple(PROTOCOL["query_classes"])
LABELS = tuple(PROTOCOL["labels"])


def question_for(evaluation: str, variant: int, record: dict[str, str]) -> str:
    templates = {
        "paraphrase": (
            "Which synthetic token does the observatory assign to node {subject}?",
            "Recover the observatory token registered for node {subject}.",
            "Node {subject} appears in the register; select its synthetic token.",
            "Identify the token paired with registered node {subject}.",
        ),
        "multi_hop": (
            "Use locator {alias} to find its node and return that node's token.",
            "Follow locator {alias} into the register; which token is attached?",
            "Resolve {alias} to a node, then select the corresponding token.",
            "What token terminates the locator path beginning at {alias}?",
        ),
        "withheld_composition": (
            "Traverse gateway {bridge}, then its locator, and return the terminal token.",
            "Which token closes the gateway-to-locator path from {bridge}?",
            "Compose both register edges beginning at gateway {bridge}; select the token.",
            "Starting with {bridge}, resolve the two-edge chain to its final token.",
        ),
    }
    return templates[evaluation][variant].format(**record)


def expected_family(seed: bytes, kind: str, ordinal: int) -> dict[str, Any]:
    deriver = V3.Deriver(seed)
    family_id = V3.tag_id("r7family", deriver.digest("v28r7-family", kind, ordinal))
    namespace = deriver.atom("r7vault", "v28r7", kind, ordinal)
    records = [{
        "subject": deriver.atom("r7entity", kind, ordinal, row),
        "alias": deriver.atom("r7handle", kind, ordinal, row),
        "bridge": deriver.atom("r7route", kind, ordinal, row),
        "value": deriver.atom("r7token", kind, ordinal, row),
    } for row in range(4)]
    source = "\n".join(
        [f"Mnemonic observatory {namespace} publishes four artificial node assignments."]
        + [f"Registered node {row['subject']} carries synthetic token {row['value']}." for row in records]
    ) + "\n"
    support = "\n".join(
        [f"Companion index {namespace} publishes locator and gateway connections."]
        + [f"Gateway {row['bridge']} enters locator {row['alias']}, and that locator identifies node {row['subject']}." for row in records]
    ) + "\n"
    target_index = deriver.index(4, "v28r7-target", kind, ordinal)
    family: dict[str, Any] = {
        "family_id": family_id, "namespace_id": namespace, "fact_kind": kind,
        "block_index": ordinal // 24, "family_in_block": ordinal % 24,
        "records": records, "target_index": target_index,
        "source_document": source, "source_sha256": sha256_text(source),
        "support_document": support, "support_sha256": sha256_text(support), "queries": [],
    }
    graph = {
        "version": "mesh.astral_v28r3_semantic_graph.v1", "fact_kind": kind,
        "namespace_id": namespace, "target_index": target_index, "vertices": records,
        "edges": ["route_to_handle", "handle_to_entity", "entity_to_token"],
    }
    family["semantic_ast_sha256"] = stable_hash(graph)
    target = records[target_index]
    for evaluation_index, evaluation in enumerate(QUERY_CLASSES):
        for variant in range(4):
            question = question_for(evaluation, variant, target)
            distractors = [row["value"] for index, row in enumerate(records) if index != target_index]
            rotation = (2 * variant + evaluation_index) % 3
            distractors = distractors[rotation:] + distractors[:rotation]
            choice = V3.PERMUTATIONS[(5 * (ordinal % 24) + 11 * evaluation_index) % 24][variant]
            options, cursor = [], 0
            for index in range(4):
                if index == choice:
                    options.append(target["value"])
                else:
                    options.append(distractors[cursor]); cursor += 1
            prompt = "\n".join([
                "Closed-book mnemonic evaluation; do not request the observatory register.",
                question, *(f"Candidate {label}: {option}" for label, option in zip(LABELS, options)),
                "Return one uppercase answer symbol: A, B, C, or D.", "",
            ])
            family["queries"].append({
                "query_id": V3.tag_id("r7query", family_id, evaluation, variant),
                "evaluation_kind": evaluation, "variant": variant,
                "template_id": f"r7-{kind}-{evaluation}-observatory-{variant}",
                "question": question, "options": options, "expected_choice": choice,
                "expected_label": LABELS[choice], "prompt": prompt, "prompt_sha256": sha256_text(prompt),
            })
    return family


def panel_indices(seed: bytes) -> list[int]:
    ranked = sorted(range(64), key=lambda index: (
        hashlib.sha256(b"v28r7-panel" + seed + index.to_bytes(2, "big")).digest(), index,
    ))
    return sorted(ranked[:8])


def evaluation_panel(families: list[dict[str, Any]], indices: list[int]) -> list[dict[str, Any]]:
    selected = set(indices)
    return sorted(
        (family for family in families if family["block_index"] in selected),
        key=lambda family: (
            int(family["block_index"]), FACT_KINDS.index(family["fact_kind"]),
            int(family["family_in_block"]), family["family_id"],
        ),
    )


def external_prompt(family: dict[str, Any], query: dict[str, Any]) -> str:
    return (
        "External dossier for this query:\n" + family["source_document"] + family["support_document"]
        + "\nAnswer using the dossier, then follow the query output contract.\n" + query["prompt"]
    )


def content_strings(family: dict[str, Any]) -> list[str]:
    values = [family[key] for key in (
        "family_id", "namespace_id", "source_document", "source_sha256",
        "support_document", "support_sha256", "semantic_ast_sha256",
    )]
    values.extend(record[key] for record in family["records"] for key in ("subject", "alias", "bridge", "value"))
    for query in family["queries"]:
        values.extend(query[key] for key in ("query_id", "question", "prompt", "prompt_sha256", "template_id"))
        values.extend(query["options"])
    return values


def normalize_skeleton(value: str) -> str:
    value = ATOM.sub("<atom>", value.lower())
    value = GENERIC_ATOM.sub("<atom>", value)
    value = HEX.sub("<hex>", value)
    value = re.sub(r"\d+", "<n>", value)
    return re.sub(r"\s+", " ", value).strip()


def structural_ngrams(value: str, width: int = 7) -> set[str]:
    tokens = re.findall(r"[a-z]+|<[^>]+>|[.;:?]", normalize_skeleton(value))
    return {sha256_text(" ".join(tokens[index:index + width])) for index in range(max(0, len(tokens) - width + 1))}


def validate_disjoint(family: dict[str, Any], prior: dict[str, set[str]], errors: list[str]) -> None:
    if family["semantic_ast_sha256"] in prior["semantic_ast_sha256s"]:
        errors.append("corpus.semantic_ast_overlap")
    if any(query["template_id"] in prior["template_ids"] for query in family["queries"]):
        errors.append("corpus.template_overlap")
    if any(sha256_text(value) in prior["exact_string_sha256s"] for value in content_strings(family)):
        errors.append("corpus.exact_overlap")
    surfaces = [family["source_document"], family["support_document"]]
    surfaces.extend(value for query in family["queries"] for value in (query["question"], query["prompt"]))
    if any(sha256_text(normalize_skeleton(value)) in prior["normalized_surface_skeleton_sha256s"] for value in surfaces):
        errors.append("corpus.skeleton_overlap")
    if any(structural_ngrams(value) & prior["structural_seven_gram_sha256s"] for value in surfaces):
        errors.append("corpus.seven_gram_overlap")


def family_scores(rows: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        grouped[row["family_id"]].append(row["correct"])
    return {key: sum(values) / len(values) for key, values in grouped.items()}


def source_rows(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for kind in FACT_KINDS:
        for family in sorted((row for row in families if row["fact_kind"] == kind), key=lambda row: row["family_id"]):
            source, support = family["source_document"], family["support_document"]
            rows.append({
                "row_id": "source-" + family["family_id"], "task_id": kind,
                "prompt": source.splitlines(keepends=True)[0],
                "completion": "".join(source.splitlines(keepends=True)[1:]) + support,
                "family_id": family["family_id"], "source_sha256": family["source_sha256"],
                "support_sha256": family["support_sha256"],
                "projection_policy": "complete_source_support_target_blind_hash_window_128",
            })
    return rows


def validate_bundles(root: Path, families: list[dict[str, Any]], panel: list[dict[str, Any]], errors: list[str]) -> None:
    paths = {name: root / "locks" / f"{name}.json" for name in ("source", "queries", "answers", "external")}
    if any(not path.is_file() for path in paths.values()):
        errors.append("bundles.required"); return
    values = {name: json.loads(path.read_text()) for name, path in paths.items()}
    expected_source = source_rows(families)
    expected_queries, expected_answers = [], []
    for family in panel:
        for query in family["queries"]:
            expected_queries.append({
                "query_id": query["query_id"], "family_id": family["family_id"],
                "fact_kind": family["fact_kind"], "query_class": query["evaluation_kind"],
                "prompt": query["prompt"],
            })
            expected_answers.append({"query_id": query["query_id"], "expected_label": query["expected_label"]})
    checks = (
        values["source"].get("rows") == expected_source,
        values["source"].get("rows_sha256") == stable_hash(expected_source),
        values["source"].get("evaluation_material_present") is False,
        values["queries"].get("queries") == expected_queries,
        values["queries"].get("queries_sha256") == stable_hash(expected_queries),
        values["queries"].get("source_material_present") is False,
        values["answers"].get("answers") == expected_answers,
        values["answers"].get("answers_sha256") == stable_hash(expected_answers),
        values["answers"].get("model_input") is False,
        values["external"].get("families") == panel,
        values["external"].get("families_sha256") == stable_hash(panel),
    )
    if not all(checks):
        errors.append("bundles.binding")


def interval(values: list[float], *, floor: float | None = None) -> dict[str, Any]:
    mean = statistics.fmean(values)
    se = statistics.stdev(values) / math.sqrt(len(values))
    lower = mean - PROTOCOL["critical_value"] * se
    if floor is None:
        upper = mean + PROTOCOL["critical_value"] * se
        margin = PROTOCOL["novelty_equivalence_margin"]
        return {"family_cluster_count": len(values), "mean_chance_normalized_lift": mean,
                "standard_error": se, "critical_value": PROTOCOL["critical_value"],
                "lower": lower, "upper": upper, "equivalence_passed": lower > -margin and upper < margin}
    return {"accuracy": mean, "floor": floor, "family_count": len(values),
            "standard_error": se, "critical_value": PROTOCOL["critical_value"],
            "lower_bound": lower, "passes": mean >= floor and lower > floor}


def novelty_metrics(panel: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["query_id"]: row for row in rows}
    records = []
    for family in panel:
        by_class = {name: [] for name in QUERY_CLASSES}
        values = []
        for query in family["queries"]:
            value = float(by_id[query["query_id"]]["correct"])
            values.append(value); by_class[query["evaluation_kind"]].append(value)
        norm = lambda x: (x - 0.25) / 0.75
        records.append({"fact_kind": family["fact_kind"], "overall": norm(statistics.fmean(values)),
                        **{name: norm(statistics.fmean(items)) for name, items in by_class.items()}})
    result: dict[str, Any] = {"overall": interval([row["overall"] for row in records])}
    result["fact_kinds"] = {kind: interval([row["overall"] for row in records if row["fact_kind"] == kind]) for kind in FACT_KINDS}
    result["query_classes"] = {name: interval([row[name] for row in records]) for name in QUERY_CLASSES}
    result["equivalence_passed"] = all(item["equivalence_passed"] for item in [result["overall"], *result["fact_kinds"].values(), *result["query_classes"].values()])
    return result


def pilot_metrics(rows: list[dict[str, Any]], baseline: dict[str, float]) -> dict[str, Any]:
    scores = family_scores(rows)
    result: dict[str, Any] = {"overall": cluster_metric(list(scores.values()), PROTOCOL["overall_floor"])}
    result["fact_kinds"] = {kind: cluster_metric(list(family_scores([r for r in rows if r["fact_kind"] == kind]).values()), PROTOCOL["dimension_floor"]) for kind in FACT_KINDS}
    result["query_classes"] = {name: cluster_metric(list(family_scores([r for r in rows if r["query_class"] == name]).values()), PROTOCOL["dimension_floor"]) for name in QUERY_CLASSES}
    result["paired_mean_gain"] = sum(scores[key] - baseline[key] for key in scores) / len(scores)
    result["absolute_gates_pass"] = result["overall"]["passes"] and all(row["passes"] for row in [*result["fact_kinds"].values(), *result["query_classes"].values()]) and result["paired_mean_gain"] >= PROTOCOL["gain_floor"]
    return result


def cluster_metric(values: list[float], floor: float) -> dict[str, Any]:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
    standard_error = math.sqrt(variance / len(values))
    lower = mean - PROTOCOL["critical_value"] * standard_error
    return {"accuracy": mean, "floor": floor, "family_count": len(values),
            "standard_error": standard_error, "critical_value": PROTOCOL["critical_value"],
            "lower_bound": lower, "passes": mean >= floor and lower > floor}


def bootstrap(rows: list[dict[str, Any]], baseline: dict[str, float], seed_material: str) -> dict[str, Any]:
    scores = family_scores(rows)
    kinds = {row["family_id"]: row["fact_kind"] for row in rows}
    strata = {kind: sorted(key for key in scores if kinds[key] == kind) for kind in FACT_KINDS}
    rng = random.Random(int(hashlib.sha256(seed_material.encode()).hexdigest(), 16))
    gains = []
    for _ in range(PROTOCOL["bootstrap_draws"]):
        selected = [key for kind in FACT_KINDS for key in (rng.choice(strata[kind]) for _ in strata[kind])]
        gains.append(sum(scores[key] - baseline[key] for key in selected) / len(selected))
    gains.sort()
    alpha = PROTOCOL["familywise_alpha"] / len(PROTOCOL["persistent_arms"])
    lower = gains[max(0, math.floor(alpha * len(gains)) - 1)]
    return {"draws": len(gains), "familywise_alpha": 0.05, "bonferroni_arm_count": 7,
            "one_sided_alpha": alpha, "lower_bound": lower, "gain_floor": 0.20,
            "passes": lower > 0.20, "draws_sha256": stable_hash(gains)}


def validate_manifest(root: Path, errors: list[str]) -> None:
    path = root / "artifact-manifest.json"
    if not path.is_file():
        errors.append("artifact.manifest_missing"); return
    manifest = json.loads(path.read_text())
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("manifest_sha256") != stable_hash(files):
        errors.append("artifact.manifest_hash"); return
    listed = set()
    for row in files:
        relative = row.get("path")
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            errors.append("artifact.path"); continue
        target = root / relative; listed.add(relative)
        if not target.is_file() or target.is_symlink() or sha256_file(target) != row.get("sha256") or target.stat().st_size != row.get("size_bytes"):
            errors.append(f"artifact.file:{relative}")
    late = {"artifact-manifest.json", "astral-validation-report.json", "astral-validation-process.json", "astral-validation-report-r2.json", "astral-validation-process-r2.json"}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.relative_to(root).as_posix() not in late}
    if actual != listed:
        errors.append("artifact.census")


def file_inventory(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("state inventory rejects symlinks")
        if path.is_file():
            rows.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return rows


def validate_source_locks(root: Path, packet: dict[str, Any], errors: list[str]) -> None:
    locks = packet.get("source_locks")
    if not isinstance(locks, dict) or set(locks) != set(SOURCE_LOCK_NAMES):
        errors.append("source_locks.census"); return
    for name in SOURCE_LOCK_NAMES:
        path = root / "source-locks" / f"{name}.source"
        if not path.is_file() or sha256_file(path) != locks.get(name):
            errors.append(f"source_locks.hash:{name}")
    if locks.get("astral_protocol") != sha256_file(PROTOCOL_PATH) or locks.get("astral_validator") != R1_VALIDATOR_SHA256:
        errors.append("source_locks.astral")


def validate_processes(root: Path, packet: dict[str, Any], errors: list[str]) -> None:
    processes = packet.get("processes")
    if not isinstance(processes, dict):
        errors.append("processes.object"); return
    for key, value in processes.items():
        if key in ("pre_update", "no_update"):
            path = root / "baselines" / key / "process.json"
        elif key in PROTOCOL["nonpersistent_arms"]:
            path = root / "controls" / key / "process.json"
        elif ":" in key:
            arm, phase = key.split(":", 1)
            if arm not in PROTOCOL["persistent_arms"] or phase not in ("prepare", "update", "evaluate"):
                errors.append(f"processes.key:{key}"); continue
            path = root / "arms" / arm / f"{phase}-process.json"
        else:
            errors.append(f"processes.key:{key}"); continue
        if not path.is_file() or json.loads(path.read_text()) != value:
            errors.append(f"processes.file:{key}")
    if not all(key in processes for key in ("pre_update", "no_update")):
        errors.append("processes.baselines")


def validate_rows(rows: Any, panel: list[dict[str, Any]], *, external: bool, errors: list[str], prefix: str) -> list[dict[str, Any]]:
    expected = [(family, query) for family in panel for query in family["queries"]]
    if not isinstance(rows, list) or len(rows) != len(expected):
        errors.append(f"{prefix}.census"); return []
    for index, (row, (family, query)) in enumerate(zip(rows, expected)):
        prompt = external_prompt(family, query) if external else query["prompt"]
        if row.get("query_id") != query["query_id"] or row.get("family_id") != family["family_id"] or row.get("fact_kind") != family["fact_kind"] or row.get("query_class") != query["evaluation_kind"] or row.get("prompt_sha256") != stable_hash(prompt):
            errors.append(f"{prefix}.binding:{index}"); continue
        tokens, scores = row.get("token_ids"), row.get("label_scores")
        if not isinstance(tokens, list) or not tokens or row.get("tokenized_input_sha256") != stable_hash(tokens):
            errors.append(f"{prefix}.tokens:{index}")
        if not isinstance(scores, list) or len(scores) != 4 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in scores):
            errors.append(f"{prefix}.scores:{index}"); continue
        selected = max(range(4), key=lambda choice: (float(scores[choice]), -choice))
        if row.get("predicted_label") != LABELS[selected] or row.get("expected_label") != query["expected_label"] or row.get("correct") is not (selected == query["expected_choice"]):
            errors.append(f"{prefix}.outcome:{index}")
        if external and (row.get("retrieved_family_id") != family["family_id"] or row.get("external_source_sha256") != family["source_sha256"] or row.get("external_support_sha256") != family["support_sha256"]):
            errors.append(f"{prefix}.external:{index}")
    return rows


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    validate_manifest(root, errors)
    required = {name: root / filename for name, filename in {
        "packet": "pilot-packet.json", "corpus": "corpus.json", "seed": "seed-material.json",
        "fingerprint": "predecessor-fingerprint.json", "panel": "panel-lock.json", "receipt": "preflight-receipt.json",
    }.items()}
    if any(not path.is_file() for path in required.values()):
        return report(errors + ["artifact.required_files"], "Invalid", [])
    values = {name: json.loads(path.read_text()) for name, path in required.items()}
    packet, corpus = values["packet"], values["corpus"]
    if packet.get("version") != PROTOCOL["packet_version"] or packet.get("packet_sha256") != stable_hash(without_hash(packet, "packet_sha256")):
        errors.append("packet.identity")
    if packet.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        errors.append("packet.protocol")
    validate_source_locks(root, packet, errors)
    if packet.get("source_locks") != values["receipt"].get("source_locks") or packet.get("source_bindings") != values["receipt"].get("source_bindings"):
        errors.append("preflight.binding")
    validate_processes(root, packet, errors)
    for name in ("rgs", "astral"):
        binding = packet.get("source_bindings", {}).get(name, {})
        if binding.get("dirty") is not False or not binding.get("commit") or not binding.get("tree"):
            errors.append(f"source_binding.{name}")
    seed_hex = values["seed"].get("seed_hex")
    try: seed = bytes.fromhex(seed_hex)
    except (TypeError, ValueError): seed = b""
    if len(seed) != 32 or values["seed"].get("seed_commitment") != sha256_text(seed_hex or "") or packet.get("seed_hex") != seed_hex:
        errors.append("seed.binding")
    fingerprint = values["fingerprint"]
    expected_sources = [PROTOCOL["v28r1_source_raw_corpus_sha256"], *PROTOCOL["predecessor_corpus_manifests"]]
    if fingerprint.get("fingerprint_sha256") != stable_hash(without_hash(fingerprint, "fingerprint_sha256")) or fingerprint.get("source_manifest_sha256s") != expected_sources:
        errors.append("fingerprint.binding")
    fingerprint_sets = {
        key: set(fingerprint.get(key, [])) for key in (
            "exact_string_sha256s", "normalized_surface_skeleton_sha256s",
            "structural_seven_gram_sha256s", "semantic_ast_sha256s", "template_ids",
        )
    }
    families = corpus.get("families")
    if corpus.get("version") != PROTOCOL["corpus_version"] or not isinstance(families, list) or len(families) != PROTOCOL["family_count"] or corpus.get("manifest_sha256") != stable_hash(without_hash(corpus, "manifest_sha256")):
        errors.append("corpus.identity"); families = []
    if families:
        cursor = 0
        for kind in FACT_KINDS:
            for ordinal in range(PROTOCOL["families_per_fact_kind"]):
                if families[cursor] != expected_family(seed, kind, ordinal):
                    errors.append(f"corpus.rederivation:{kind}:{ordinal}")
                else:
                    validate_disjoint(families[cursor], fingerprint_sets, errors)
                cursor += 1
    indices = panel_indices(seed) if len(seed) == 32 else []
    panel = evaluation_panel(families, indices)
    panel_lock = values["panel"]
    if panel_lock.get("block_indices") != indices or panel_lock.get("family_ids") != [row["family_id"] for row in panel] or len(panel) != PROTOCOL["panel_family_count"]:
        errors.append("panel.binding")
    if families and panel:
        validate_bundles(root, families, panel, errors)
    runs = packet.get("baseline_results")
    run_by_arm = {run.get("arm_id"): run for run in runs} if isinstance(runs, list) else {}
    for arm in ("pre_update", "no_update"):
        run = run_by_arm.get(arm, {})
        rows = validate_rows(run.get("observations"), panel, external=False, errors=errors, prefix=f"baseline.{arm}")
        if run.get("result_sha256") != stable_hash(without_hash(run, "result_sha256")) or run.get("observations_sha256") != stable_hash(rows):
            errors.append(f"baseline.{arm}.hash")
        if run.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1) > PROTOCOL["max_peak_rss_bytes"] or max(run.get("block_peak_rss_bytes", [PROTOCOL["max_peak_rss_bytes"] + 1])) > PROTOCOL["max_peak_rss_bytes"]:
            errors.append(f"baseline.{arm}.rss")
    parity = bool(run_by_arm) and run_by_arm.get("pre_update", {}).get("observations") == run_by_arm.get("no_update", {}).get("observations")
    novelty = {arm: novelty_metrics(panel, run_by_arm[arm]["observations"]) for arm in ("pre_update", "no_update")} if len(run_by_arm) == 2 else {}
    novelty_pass = parity and bool(novelty) and all(row["equivalence_passed"] for row in novelty.values())
    if packet.get("novelty_exact_parity") is not parity or packet.get("novelty_metrics") != novelty or packet.get("novelty_passed") is not novelty_pass:
        errors.append("novelty.recompute")
    baseline = family_scores(run_by_arm.get("no_update", {}).get("observations", []))
    if packet.get("baseline_family_scores_sha256") != stable_hash(baseline):
        errors.append("baseline.family_hash")
    controls = packet.get("controls")
    if novelty_pass and (not isinstance(controls, list) or [row.get("arm_id") for row in controls] != PROTOCOL["nonpersistent_arms"]):
        errors.append("controls.census")
    elif novelty_pass:
        for control in controls:
            validate_rows(control.get("observations"), panel, external=True, errors=errors, prefix=f"control.{control.get('arm_id')}")
            if control.get("result_sha256") != stable_hash(without_hash(control, "result_sha256")) or control.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1) > PROTOCOL["max_peak_rss_bytes"] or max(control.get("block_peak_rss_bytes", [PROTOCOL["max_peak_rss_bytes"] + 1])) > PROTOCOL["max_peak_rss_bytes"]:
                errors.append(f"control.{control.get('arm_id')}.integrity")
    summaries = packet.get("arm_summaries")
    if novelty_pass and (not isinstance(summaries, list) or [row.get("arm_id") for row in summaries] != PROTOCOL["persistent_arms"]):
        errors.append("arms.census"); summaries = []
    signals = []
    for summary in summaries or []:
        arm = summary["arm_id"]
        result_path = root / "arms" / arm / "result.json"
        if not summary.get("completed"):
            if summary.get("signal") is not False or result_path.exists(): errors.append(f"arm.{arm}.failed_state")
            continue
        result = json.loads(result_path.read_text()) if result_path.is_file() else {}
        rows = validate_rows(result.get("observations"), panel, external=False, errors=errors, prefix=f"arm.{arm}")
        if result.get("result_sha256") != stable_hash(without_hash(result, "result_sha256")) or result.get("observations_sha256") != stable_hash(rows):
            errors.append(f"arm.{arm}.hash")
        receipt_path = root / "arms" / arm / "update" / "update-receipt.json"
        receipt = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
        budget = receipt.get("budget", {})
        state = file_inventory(root / "arms" / arm / "update" / "state")
        if receipt.get("receipt_sha256") != stable_hash(without_hash(receipt, "receipt_sha256")) or any(budget.get(key) != value for key, value in PROTOCOL["budget"].items()) or receipt.get("gradient_steps") != 768 or receipt.get("training_examples") != 6144 or receipt.get("update_tokens") != 786432 or receipt.get("state_bytes", 67108865) > 67108864 or receipt.get("state_inventory") != state or receipt.get("state_inventory_sha256") != stable_hash(state):
            errors.append(f"arm.{arm}.budget")
        metrics = pilot_metrics(rows, baseline)
        boot = bootstrap(rows, baseline, packet["protocol_sha256"] + arm)
        peak_rss = max([
            *result.get("block_peak_rss_bytes", [PROTOCOL["max_peak_rss_bytes"] + 1]),
            result.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1),
            receipt.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1),
        ])
        rss_pass = peak_rss <= PROTOCOL["max_peak_rss_bytes"]
        signal = metrics["absolute_gates_pass"] and boot["passes"] and rss_pass
        expected = {"arm_id": arm, "completed": True, "metrics": metrics, "bootstrap": boot, "peak_rss_bytes": peak_rss, "rss_pass": rss_pass, "signal": signal}
        if summary != expected: errors.append(f"arm.{arm}.summary")
        if signal: signals.append(arm)
    expected_status = "CorpusNotNovel" if not novelty_pass else "PilotSignalPresent" if len(signals) >= 2 else "PilotSingleSignal" if len(signals) == 1 else "PilotNoSignal"
    if packet.get("signal_arms") != signals or packet.get("status") != expected_status:
        errors.append("packet.outcome")
    boundaries = {"retention_recovery_run": False, "selection_run": False, "assessment_opened": False, "confirmation_run": False, "independent_replication": False, "claim_ceiling": PROTOCOL["claim_ceiling"]}
    for key, value in boundaries.items():
        if packet.get(key) != value: errors.append(f"boundary.{key}")
    return report(errors, expected_status, signals)


def report(errors: list[str], status: str, signals: list[str]) -> dict[str, Any]:
    value = {
        "version": "astral.rgs_acquisition_v28r7.validation_report.r2",
        "state_slice": PROTOCOL["state_slice"], "valid": not errors,
        "status": "Invalid" if errors else status, "errors": sorted(set(errors)),
        "signal_arms": signals, "claim_ceiling": PROTOCOL["claim_ceiling"] if not errors else "NoScientificClaim",
        "qualification_validated": False, "assessment_validated": False,
        "retention_recovery_validated": False, "independent_replication_validated": False,
        "validator_source_sha256": sha256_file(Path(__file__)),
        "r1_validator_source_sha256": R1_VALIDATOR_SHA256,
        "model_execution_reused": False,
    }
    return {**value, "report_sha256": stable_hash(value)}
