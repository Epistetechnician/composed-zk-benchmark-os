from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import random
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
STATE_SLICE = PROTOCOL["state_slice"]
FACT_KINDS = tuple(PROTOCOL["fact_kinds"])
QUERY_CLASSES = tuple(PROTOCOL["query_classes"])
LABELS = tuple(PROTOCOL["labels"])
PERMUTATIONS = tuple(itertools.permutations(range(4)))
ATOM = re.compile(r"\br[123](?:entity|handle|route|token|vault|family|query)-[0-9a-f]{5,}\b")
GENERIC_ATOM = re.compile(r"\b(?:[a-z]{2,12}-)?[a-z]{4,}-[0-9a-f]{5,}\b")
HEX = re.compile(r"\b[0-9a-f]{16,}\b")
SPACE = re.compile(r"\s+")
FACT_TERMS = {
    "nonce_fact": ("beacon", "signal"),
    "entity_relation": ("station", "neighbor"),
    "changed_rule": ("charter", "verdict"),
    "opaque_mapping": ("glyph", "translation"),
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def without_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def normalize_skeleton(value: str) -> str:
    value = ATOM.sub("<atom>", value.lower())
    value = GENERIC_ATOM.sub("<atom>", value)
    value = HEX.sub("<hex>", value)
    value = re.sub(r"\d+", "<n>", value)
    return SPACE.sub(" ", value).strip()


def structural_ngrams(value: str, width: int = 7) -> set[str]:
    tokens = re.findall(r"[a-z]+|<[^>]+>|[.;:?]", normalize_skeleton(value))
    return {
        sha256_text(" ".join(tokens[index : index + width]))
        for index in range(max(0, len(tokens) - width + 1))
    }


def content_strings(family: dict[str, Any]) -> Iterable[str]:
    for key in (
        "family_id", "namespace_id", "source_document", "source_sha256",
        "support_document", "support_sha256", "semantic_ast_sha256",
    ):
        if isinstance(family.get(key), str):
            yield family[key]
    for record in family.get("records", []):
        for key in ("subject", "alias", "bridge", "value"):
            if isinstance(record, dict) and isinstance(record.get(key), str):
                yield record[key]
    for query in family.get("queries", []):
        for key in ("query_id", "question", "prompt", "prompt_sha256", "template_id"):
            if isinstance(query, dict) and isinstance(query.get(key), str):
                yield query[key]
        for option in query.get("options", []) if isinstance(query, dict) else []:
            if isinstance(option, str):
                yield option


class Deriver:
    def __init__(self, seed: bytes) -> None:
        if len(seed) != 32:
            raise ValueError("seed must contain exactly 32 bytes")
        self.seed = seed

    def digest(self, *parts: Any) -> str:
        return hashlib.sha256(self.seed + canonical_bytes(parts)).hexdigest()

    def atom(self, prefix: str, *parts: Any) -> str:
        return f"{prefix}-{self.digest('atom', prefix, *parts)[:12]}"

    def index(self, modulus: int, *parts: Any) -> int:
        return int(self.digest("index", *parts)[:16], 16) % modulus


def tag_id(tag: str, *values: Any, length: int = 24) -> str:
    return f"{tag}-{hashlib.sha256(canonical_bytes([tag, *values])).hexdigest()[:length]}"


def question_for(kind: str, evaluation: str, variant: int, record: dict[str, str]) -> str:
    noun, answer = FACT_TERMS[kind]
    templates = {
        "paraphrase": (
            "Name the {answer} catalogued beside {subject}.",
            "Find {subject}'s catalogued {answer}.",
            "The atlas indexes {subject}; which {answer} completes that index?",
            "Select the {answer} paired with atlas {noun} {subject}.",
        ),
        "multi_hop": (
            "Starting from handle {alias}, locate the indexed {answer}.",
            "Trace handle {alias} to its station, then identify the {answer}.",
            "Which {answer} follows the atlas link headed by {alias}?",
            "Use {alias} as the first hop and report the terminal {answer}.",
        ),
        "withheld_composition": (
            "Begin at route {bridge}; follow both atlas links to the {answer}.",
            "What {answer} ends the two-link path whose route is {bridge}?",
            "Compose the route and handle edges from {bridge}; select the result.",
            "Resolve the complete atlas path beginning with {bridge}.",
        ),
    }
    return templates[evaluation][variant].format(
        noun=noun, answer=answer, subject=record["subject"],
        alias=record["alias"], bridge=record["bridge"],
    )


def render_prompt(question: str, options: list[str]) -> str:
    names = ("alpha", "beta", "gamma", "delta")
    return "\n".join(
        ["Atlas examination; reference leaves remain closed.", question]
        + [f"Choice {name} ({label}): {option}" for name, label, option in zip(names, LABELS, options)]
        + ["Emit exactly one capital letter from A through D.", ""]
    )


def expected_family(seed: bytes, kind: str, ordinal: int) -> dict[str, Any]:
    deriver = Deriver(seed)
    family_id = tag_id("r3family", deriver.digest("family", kind, ordinal))
    namespace = deriver.atom("r3vault", kind, ordinal)
    records = [
        {
            "subject": deriver.atom("r3entity", kind, ordinal, row),
            "alias": deriver.atom("r3handle", kind, ordinal, row),
            "bridge": deriver.atom("r3route", kind, ordinal, row),
            "value": deriver.atom("r3token", kind, ordinal, row),
        }
        for row in range(4)
    ]
    noun, answer = FACT_TERMS[kind]
    source_lines = [f"Atlas vault {namespace} enumerates four fabricated {noun} records."]
    support_lines = [f"Routing leaf {namespace} records the graph edges for those entries."]
    for record in records:
        source_lines.append(f"Catalog {record['subject']} has {answer} {record['value']} in this vault.")
        support_lines.append(
            f"Route {record['bridge']} reaches handle {record['alias']}; the handle resolves to {record['subject']}."
        )
    source = "\n".join(source_lines) + "\n"
    support = "\n".join(support_lines) + "\n"
    target_index = deriver.index(4, "target", kind, ordinal)
    family: dict[str, Any] = {
        "family_id": family_id,
        "namespace_id": namespace,
        "fact_kind": kind,
        "block_index": ordinal // 24,
        "family_in_block": ordinal % 24,
        "records": records,
        "target_index": target_index,
        "source_document": source,
        "source_sha256": sha256_text(source),
        "support_document": support,
        "support_sha256": sha256_text(support),
        "queries": [],
    }
    graph = {
        "version": "mesh.astral_v28r3_semantic_graph.v1",
        "fact_kind": kind,
        "namespace_id": namespace,
        "target_index": target_index,
        "vertices": records,
        "edges": ["route_to_handle", "handle_to_entity", "entity_to_token"],
    }
    family["semantic_ast_sha256"] = stable_hash(graph)
    target = records[target_index]
    for evaluation_index, evaluation in enumerate(QUERY_CLASSES):
        for variant in range(4):
            question = question_for(kind, evaluation, variant, target)
            choice = PERMUTATIONS[(5 * (ordinal % 24) + 11 * evaluation_index) % 24][variant]
            distractors = [row["value"] for index, row in enumerate(records) if index != target_index]
            rotation = (2 * variant + evaluation_index) % 3
            distractors = distractors[rotation:] + distractors[:rotation]
            options, cursor = [], 0
            for index in range(4):
                if index == choice:
                    options.append(target["value"])
                else:
                    options.append(distractors[cursor])
                    cursor += 1
            prompt = render_prompt(question, options)
            family["queries"].append(
                {
                    "query_id": tag_id("r3query", family_id, evaluation, variant),
                    "evaluation_kind": evaluation,
                    "variant": variant,
                    "template_id": f"r3-{kind}-{evaluation}-atlas-{variant}",
                    "question": question,
                    "options": options,
                    "expected_choice": choice,
                    "expected_label": LABELS[choice],
                    "prompt": prompt,
                    "prompt_sha256": sha256_text(prompt),
                }
            )
    return family


def validate_fingerprint(value: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("fingerprint.object")
        return {}
    if value.get("version") != "mesh.astral_v28r3_predecessor_fingerprint.v1":
        errors.append("fingerprint.version")
    if value.get("fingerprint_sha256") != stable_hash(without_hash(value, "fingerprint_sha256")):
        errors.append("fingerprint.hash")
    return value


def validate_corpus(
    corpus: Any,
    *,
    seed: bytes,
    fingerprint: dict[str, Any],
    errors: list[str],
    families_per_kind: int = 1536,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(corpus, dict) or corpus.get("version") != PROTOCOL["corpus_version"]:
        errors.append("corpus.version")
        return [], {}
    families = corpus.get("families")
    if not isinstance(families, list) or len(families) != families_per_kind * 4:
        errors.append("corpus.census")
        return [], {}
    if corpus.get("manifest_sha256") != stable_hash(without_hash(corpus, "manifest_sha256")):
        errors.append("corpus.manifest")
    exact = set(fingerprint.get("exact_string_sha256s", []))
    skeletons = set(fingerprint.get("normalized_surface_skeleton_sha256s", []))
    ngrams = set(fingerprint.get("structural_seven_gram_sha256s", []))
    asts = set(fingerprint.get("semantic_ast_sha256s", []))
    templates = set(fingerprint.get("template_ids", []))
    query_map: dict[str, dict[str, Any]] = {}
    cursor = 0
    for kind in FACT_KINDS:
        for ordinal in range(families_per_kind):
            family = families[cursor]
            cursor += 1
            if family != expected_family(seed, kind, ordinal):
                errors.append(f"corpus.rederivation.{kind}.{ordinal}")
                continue
            if family["semantic_ast_sha256"] in asts:
                errors.append("corpus.semantic_ast_overlap")
            if any(query["template_id"] in templates for query in family["queries"]):
                errors.append("corpus.template_overlap")
            if any(sha256_text(text) in exact for text in content_strings(family)):
                errors.append("corpus.exact_overlap")
            surfaces = [family["source_document"], family["support_document"]]
            surfaces.extend(text for query in family["queries"] for text in (query["question"], query["prompt"]))
            if any(sha256_text(normalize_skeleton(text)) in skeletons for text in surfaces):
                errors.append("corpus.skeleton_overlap")
            if any(structural_ngrams(text) & ngrams for text in surfaces):
                errors.append("corpus.seven_gram_overlap")
            for query in family["queries"]:
                if query["query_id"] in query_map:
                    errors.append("corpus.duplicate_query")
                query_map[query["query_id"]] = query
    return families, query_map


def interval(values: list[float]) -> dict[str, Any]:
    count = len(values)
    mean = statistics.fmean(values) if values else 0.0
    standard_error = statistics.stdev(values) / math.sqrt(count) if count > 1 else math.inf
    critical = float(PROTOCOL["critical_value"])
    lower = mean - critical * standard_error
    upper = mean + critical * standard_error
    margin = float(PROTOCOL["novelty_equivalence_margin"])
    return {
        "family_cluster_count": count,
        "mean_chance_normalized_lift": mean,
        "standard_error": standard_error,
        "critical_value": critical,
        "lower": lower,
        "upper": upper,
        "equivalence_passed": lower > -margin and upper < margin,
    }


def validate_baseline_run(
    run: Any,
    *,
    arm_id: str,
    families: list[dict[str, Any]],
    query_map: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not isinstance(run, dict) or run.get("arm_id") != arm_id:
        errors.append(f"novelty.{arm_id}.run")
        return {}, {}
    observations = run.get("observations")
    expected_order = [q["query_id"] for family in families for q in family["queries"]]
    if not isinstance(observations, list) or len(observations) != len(expected_order):
        errors.append(f"novelty.{arm_id}.census")
        return {}, {}
    if run.get("observations_sha256") != stable_hash(observations):
        errors.append(f"novelty.{arm_id}.hash")
    joined: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(observations):
        query_id = row.get("query_id") if isinstance(row, dict) else None
        if query_id != expected_order[index] or query_id not in query_map or query_id in joined:
            errors.append(f"novelty.{arm_id}.order")
            continue
        query = query_map[query_id]
        scores = row.get("label_scores")
        tokens = row.get("token_ids")
        if (
            row.get("prompt_sha256") != query["prompt_sha256"]
            or not isinstance(tokens, list)
            or not tokens
            or row.get("tokenized_input_sha256") != stable_hash(tokens)
            or not isinstance(scores, list)
            or len(scores) != 4
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores)
        ):
            errors.append(f"novelty.{arm_id}.observation")
            continue
        selected = max(range(4), key=lambda choice: (float(scores[choice]), -choice))
        expected_correct = selected == query["expected_choice"]
        enriched = {**row, "correct": expected_correct}
        if row.get("predicted_label") != LABELS[selected]:
            errors.append(f"novelty.{arm_id}.prediction")
        joined[query_id] = enriched
    family_rows = []
    for family in families:
        all_values, by_class = [], {query_class: [] for query_class in QUERY_CLASSES}
        for query in family["queries"]:
            value = 1.0 if joined.get(query["query_id"], {}).get("correct") else 0.0
            all_values.append(value)
            by_class[query["evaluation_kind"]].append(value)
        normalize = lambda accuracy: (accuracy - 0.25) / 0.75
        family_rows.append(
            {"fact_kind": family["fact_kind"], "overall": normalize(statistics.fmean(all_values)),
             **{name: normalize(statistics.fmean(values)) for name, values in by_class.items()}}
        )
    metrics: dict[str, Any] = {"overall": interval([row["overall"] for row in family_rows])}
    metrics["fact_kinds"] = {
        kind: interval([row["overall"] for row in family_rows if row["fact_kind"] == kind])
        for kind in FACT_KINDS
    }
    metrics["query_classes"] = {
        name: interval([row[name] for row in family_rows]) for name in QUERY_CLASSES
    }
    metrics["equivalence_passed"] = all(
        row["equivalence_passed"]
        for row in [metrics["overall"], *metrics["fact_kinds"].values(), *metrics["query_classes"].values()]
    )
    return joined, metrics


def baseline_family_scores(
    families: list[dict[str, Any]], observations: dict[str, dict[str, Any]]
) -> dict[str, float]:
    return {
        family["family_id"]: statistics.fmean(
            1.0 if observations[query["query_id"]]["correct"] else 0.0
            for query in family["queries"]
        )
        for family in families
    }


def _load_gate1() -> Any:
    path = HERE.parent / "astral-rgs-acquisition-v28-gate1" / "gate1.py"
    spec = importlib.util.spec_from_file_location("astral_v28r3_reused_gate1_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen Gate 1 recomputation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_gate1(
    packet: Any,
    *,
    baseline_scores: dict[str, float],
    baseline_accuracy: float,
    artifact_root: Path | None,
    errors: list[str],
) -> list[str]:
    if not isinstance(packet, dict) or packet.get("version") != PROTOCOL["campaign_packet_version"]:
        errors.append("gate1.packet")
        return []
    if packet.get("packet_sha256") != stable_hash(without_hash(packet, "packet_sha256")):
        errors.append("gate1.packet_hash")
    gate = _load_gate1()
    gate.STATE_SLICE = STATE_SLICE
    gate.CELL_VERSION = PROTOCOL["cell_version"]
    gate.V28R2_NO_UPDATE_ACCURACY = baseline_accuracy
    gate.V28R2_BASELINE_FAMILY_SCORES_SHA256 = stable_hash(baseline_scores)
    local_errors: list[str] = []
    controls = packet.get("controls")
    if not isinstance(controls, list) or [row.get("arm_id") for row in controls] != list(PROTOCOL["nonpersistent_arms"]):
        local_errors.append("gate1.controls")
    else:
        for control in controls:
            gate.validate_control(control, errors=local_errors)
    expected = [
        (arm, seed, order)
        for arm in PROTOCOL["persistent_arms"]
        for seed in PROTOCOL["seeds"]
        for order in PROTOCOL["task_orders"]
    ]
    cells = packet.get("cells")
    actual = [(row.get("arm_id"), row.get("seed"), row.get("order_id")) for row in cells] if isinstance(cells, list) else []
    if actual != expected:
        local_errors.append("gate1.cell_order")
        cells = []
    passed: dict[str, list[list[dict[str, Any]]]] = {arm: [] for arm in PROTOCOL["persistent_arms"]}
    stopped = {arm: False for arm in PROTOCOL["persistent_arms"]}
    for cell in cells:
        arm = cell["arm_id"]
        skipped = cell.get("status") == "NotRunByPreregisteredArmFutility"
        if stopped[arm] and not skipped:
            local_errors.append(f"gate1.{arm}.post_stop")
        qualifies_cell = gate.validate_cell(cell, errors=local_errors)
        if artifact_root is not None:
            gate.validate_cell_artifacts(cell, root=artifact_root, errors=local_errors)
        if qualifies_cell:
            passed[arm].append(cell["observations"])
        elif not skipped:
            stopped[arm] = True
    summaries = packet.get("arm_summaries")
    summary_by_arm = {row.get("arm_id"): row for row in summaries} if isinstance(summaries, list) else {}
    qualifying = []
    for arm in PROTOCOL["persistent_arms"]:
        summary = summary_by_arm.get(arm, {})
        if summary.get("completed_cell_count") != len(passed[arm]):
            local_errors.append(f"gate1.{arm}.completed_count")
        expected_bootstrap = None
        if len(passed[arm]) == 9:
            expected_bootstrap = gate.recompute_bootstrap(
                passed[arm], baseline_scores=baseline_scores,
                seed_material=packet["protocol_sha256"] + arm,
            )
        if summary.get("bootstrap") != expected_bootstrap:
            local_errors.append(f"gate1.{arm}.bootstrap")
        qualifies = bool(expected_bootstrap and expected_bootstrap["passes"])
        if summary.get("qualifies") is not qualifies:
            local_errors.append(f"gate1.{arm}.qualifies")
        if qualifies:
            qualifying.append(arm)
    if packet.get("qualifying_arms") != qualifying:
        local_errors.append("gate1.qualifying_arms")
    expected_status = "AcquisitionQualifiedCandidates" if len(qualifying) >= 2 else "AcquisitionSingleCandidate" if qualifying else "AcquisitionNoCandidate"
    if packet.get("status") != expected_status:
        local_errors.append("gate1.status")
    errors.extend(local_errors)
    return qualifying


def validate_manifest(root: Path, errors: list[str]) -> None:
    manifest_path = root / "artifact-manifest.json"
    if not manifest_path.is_file():
        errors.append("artifact.manifest_missing")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("manifest_sha256") != stable_hash(files):
        errors.append("artifact.manifest_hash")
        return
    listed = set()
    for row in files:
        relative = row.get("path")
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            errors.append("artifact.path")
            continue
        path = root / relative
        listed.add(relative)
        if not path.is_file() or path.is_symlink() or sha256_file(path) != row.get("sha256") or path.stat().st_size != row.get("size_bytes"):
            errors.append("artifact.file")
    allowed_late = {
        "artifact-manifest.json",
        "astral-validation-report.json",
        "astral-validation-process.json",
        "astral-abort-validation-report.json",
        "astral-abort-validation-process.json",
    }
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.relative_to(root).as_posix() not in allowed_late}
    if actual != listed:
        errors.append("artifact.census")


def _validate_campaign(
    campaign: Any,
    *,
    fingerprint: Any,
    artifact_root: str | Path | None = None,
    families_per_kind: int = 1536,
) -> dict[str, Any]:
    errors: list[str] = []
    fingerprint = validate_fingerprint(fingerprint, errors)
    if not isinstance(campaign, dict):
        return report(errors=[*errors, "campaign.object"], status="Invalid", metrics={}, qualifying=[])
    if campaign.get("version") != "mesh.astral_v28r3_integrated_campaign.v1" or campaign.get("state_slice") != PROTOCOL["execution_state_slice"]:
        errors.append("campaign.version")
    if campaign.get("campaign_sha256") != stable_hash(without_hash(campaign, "campaign_sha256")):
        errors.append("campaign.hash")
    seed_hex = campaign.get("seed_hex")
    try:
        seed = bytes.fromhex(seed_hex)
    except (TypeError, ValueError):
        seed = b""
    if len(seed) != 32 or campaign.get("seed_commitment") != sha256_text(seed_hex or ""):
        errors.append("campaign.seed")
    families, query_map = validate_corpus(
        campaign.get("corpus"), seed=seed, fingerprint=fingerprint, errors=errors,
        families_per_kind=families_per_kind,
    )
    runs = campaign.get("novelty_runs")
    run_by_arm = {row.get("arm_id"): row for row in runs} if isinstance(runs, list) else {}
    if set(run_by_arm) != set(PROTOCOL["baseline_arms"]):
        errors.append("novelty.arms")
    observations, metrics = {}, {}
    for arm in PROTOCOL["baseline_arms"]:
        observations[arm], metrics[arm] = validate_baseline_run(
            run_by_arm.get(arm), arm_id=arm, families=families,
            query_map=query_map, errors=errors,
        )
    if all(observations.values()) and observations["pre_update"] != observations["no_update"]:
        errors.append("novelty.exact_parity")
    if len(run_by_arm) == 2:
        processes = {
            run_by_arm[arm].get(field)
            for arm in PROTOCOL["baseline_arms"]
            for field in ("preparation_process_id", "evaluation_process_id")
        }
        if len(processes) != 4 or None in processes:
            errors.append("novelty.process_isolation")
        for key in ("checkpoint_sha256", "tokenizer_sha256", "implementation_sha256", "shared_scorer_sha256"):
            if run_by_arm["pre_update"].get(key) != run_by_arm["no_update"].get(key):
                errors.append(f"novelty.parity.{key}")
    novelty_passed = not errors and all(row.get("equivalence_passed") for row in metrics.values())
    qualifying: list[str] = []
    gate_packet = campaign.get("acquisition_packet")
    if novelty_passed:
        baseline_scores = baseline_family_scores(families, observations["no_update"])
        baseline_accuracy = statistics.fmean(baseline_scores.values())
        qualifying = validate_gate1(
            gate_packet, baseline_scores=baseline_scores, baseline_accuracy=baseline_accuracy,
            artifact_root=Path(artifact_root) if artifact_root else None, errors=errors,
        )
    elif gate_packet is not None:
        errors.append("campaign.acquisition_before_novelty")
    expected_status = "Invalid" if errors else gate_packet.get("status") if novelty_passed else "CorpusNotNovel"
    if campaign.get("status") != expected_status:
        errors.append("campaign.status")
    if artifact_root is not None:
        validate_manifest(Path(artifact_root), errors)
    return report(
        errors=errors,
        status="Invalid" if errors else expected_status,
        metrics=metrics,
        qualifying=qualifying,
    )


def validate_campaign(
    campaign: Any,
    *,
    fingerprint: Any,
    artifact_root: str | Path | None = None,
    families_per_kind: int = 1536,
) -> dict[str, Any]:
    try:
        return _validate_campaign(
            campaign,
            fingerprint=fingerprint,
            artifact_root=artifact_root,
            families_per_kind=families_per_kind,
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        IndexError,
        ValueError,
        OSError,
        statistics.StatisticsError,
    ) as exc:
        return report(
            errors=[f"validator.malformed_input.{type(exc).__name__}"],
            status="Invalid",
            metrics={},
            qualifying=[],
        )


def report(*, errors: list[str], status: str, metrics: dict[str, Any], qualifying: list[str]) -> dict[str, Any]:
    claim_ceiling = "NoScientificClaim"
    if not errors and status == "CorpusNotNovel":
        claim_ceiling = "LocalModelBackedAcquisitionNoveltyPreflightV28R3"
    elif not errors and status in {
        "AcquisitionNoCandidate", "AcquisitionSingleCandidate", "AcquisitionQualifiedCandidates"
    }:
        claim_ceiling = PROTOCOL["claim_ceiling"]
    value = {
        "version": "astral.v28r3_campaign_validation_report.v1",
        "state_slice": STATE_SLICE,
        "valid": not errors,
        "status": status,
        "errors": sorted(set(errors)),
        "novelty_metrics": metrics,
        "qualifying_arms": qualifying,
        "claim_ceiling": claim_ceiling,
        "retention_recovery_validated": False,
        "selection_validated": False,
        "assessment_validated": False,
        "independent_replication_validated": False,
    }
    return {**value, "report_sha256": stable_hash(value)}
