use serde_json::Value;
use statebook_core::{
    derive_state_key, parse_normalization_profile_v1, parse_source_contract_v1, validate_and_lower,
    StateKeyV1, ValidatedNormalizationProfileV1,
};

use crate::error::EvaluationErrorV1;

const CASES: &str =
    include_str!("../../statebook-core/tests/fixtures/terminal_contract_cases_v1.json");
const PROFILE: &[u8] =
    include_bytes!("../../statebook-core/tests/fixtures/normalization_profile_v1.json");

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EquivalenceLabelV1 {
    Equivalent,
    Distinct,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LabeledPairV1 {
    pub id: String,
    pub label: EquivalenceLabelV1,
    pub left_state_key: String,
    pub right_state_key: String,
    pub predicted_equivalent: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SemanticMetricsV1 {
    pub labeled_equivalent: u32,
    pub labeled_distinct: u32,
    pub true_positive: u32,
    pub false_positive: u32,
    pub false_negative: u32,
    pub true_negative: u32,
    pub precision_numerator: u32,
    pub precision_denominator: u32,
    pub recall_numerator: u32,
    pub recall_denominator: u32,
    pub false_equivalence_numerator: u32,
    pub false_equivalence_denominator: u32,
}

fn profile() -> Result<ValidatedNormalizationProfileV1, EvaluationErrorV1> {
    parse_normalization_profile_v1(PROFILE)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))
}

fn state_key_for(
    source: &Value,
    profile: &ValidatedNormalizationProfileV1,
) -> Result<StateKeyV1, EvaluationErrorV1> {
    let bytes = serde_json::to_vec(source)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let parsed = parse_source_contract_v1(&bytes)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let contract = validate_and_lower(parsed, profile)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    Ok(derive_state_key(&contract).state_key())
}

fn pointer_set(root: &mut Value, pointer: &str, value: Value) -> Result<(), EvaluationErrorV1> {
    let target = root
        .pointer_mut(pointer)
        .ok_or_else(|| EvaluationErrorV1::SemanticPipeline(format!("missing pointer {pointer}")))?;
    *target = value;
    Ok(())
}

/// Build the frozen labeled StateKey equivalence corpus.
pub fn labeled_semantic_pairs_v1() -> Result<Vec<LabeledPairV1>, EvaluationErrorV1> {
    let fixture: Value = serde_json::from_str(CASES)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let baseline = fixture
        .get("baseline")
        .cloned()
        .ok_or_else(|| EvaluationErrorV1::SemanticPipeline("missing baseline".into()))?;
    let profile = profile()?;
    let baseline_key = state_key_for(&baseline, &profile)?;

    let mut pairs = Vec::new();

    let mut lineage = baseline.clone();
    lineage["venue_namespace"] = serde_json::json!("fixture.venue.beta");
    lineage["source_contract_id"] = serde_json::json!("OTHER-SOURCE-ID");
    lineage["source_revision"] = serde_json::json!("rev-2");
    let lineage_key = state_key_for(&lineage, &profile)?;
    pairs.push(LabeledPairV1 {
        id: "equiv_lineage_only".to_owned(),
        label: EquivalenceLabelV1::Equivalent,
        left_state_key: baseline_key.to_hex(),
        right_state_key: lineage_key.to_hex(),
        predicted_equivalent: baseline_key == lineage_key,
    });

    let mut profile_json: Value = serde_json::from_slice(PROFILE)
        .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    profile_json["profile_version"] = serde_json::json!(2);
    let bumped = parse_normalization_profile_v1(
        &serde_json::to_vec(&profile_json)
            .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?,
    )
    .map_err(|error| EvaluationErrorV1::SemanticPipeline(error.to_string()))?;
    let profile_key = state_key_for(&baseline, &bumped)?;
    pairs.push(LabeledPairV1 {
        id: "equiv_profile_version_bump".to_owned(),
        label: EquivalenceLabelV1::Equivalent,
        left_state_key: baseline_key.to_hex(),
        right_state_key: profile_key.to_hex(),
        predicted_equivalent: baseline_key == profile_key,
    });

    let mutations = fixture
        .get("material_mutations")
        .and_then(Value::as_array)
        .ok_or_else(|| EvaluationErrorV1::SemanticPipeline("missing material_mutations".into()))?;
    for mutation in mutations {
        let name = mutation
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| EvaluationErrorV1::SemanticPipeline("mutation missing name".into()))?;
        let pointer = mutation
            .get("pointer")
            .and_then(Value::as_str)
            .ok_or_else(|| {
                EvaluationErrorV1::SemanticPipeline("mutation missing pointer".into())
            })?;
        let value = mutation
            .get("value")
            .cloned()
            .ok_or_else(|| EvaluationErrorV1::SemanticPipeline("mutation missing value".into()))?;
        let mut candidate = baseline.clone();
        pointer_set(&mut candidate, pointer, value)?;
        let candidate_key = state_key_for(&candidate, &profile)?;
        pairs.push(LabeledPairV1 {
            id: format!("distinct_{name}"),
            label: EquivalenceLabelV1::Distinct,
            left_state_key: baseline_key.to_hex(),
            right_state_key: candidate_key.to_hex(),
            predicted_equivalent: baseline_key == candidate_key,
        });
    }

    Ok(pairs)
}

pub fn evaluate_semantic_metrics_v1(pairs: &[LabeledPairV1]) -> SemanticMetricsV1 {
    let mut labeled_equivalent = 0_u32;
    let mut labeled_distinct = 0_u32;
    let mut true_positive = 0_u32;
    let mut false_positive = 0_u32;
    let mut false_negative = 0_u32;
    let mut true_negative = 0_u32;

    for pair in pairs {
        match pair.label {
            EquivalenceLabelV1::Equivalent => {
                labeled_equivalent += 1;
                if pair.predicted_equivalent {
                    true_positive += 1;
                } else {
                    false_negative += 1;
                }
            }
            EquivalenceLabelV1::Distinct => {
                labeled_distinct += 1;
                if pair.predicted_equivalent {
                    false_positive += 1;
                } else {
                    true_negative += 1;
                }
            }
        }
    }

    SemanticMetricsV1 {
        labeled_equivalent,
        labeled_distinct,
        true_positive,
        false_positive,
        false_negative,
        true_negative,
        precision_numerator: true_positive,
        precision_denominator: true_positive + false_positive,
        recall_numerator: true_positive,
        recall_denominator: true_positive + false_negative,
        false_equivalence_numerator: false_positive,
        false_equivalence_denominator: labeled_distinct,
    }
}

/// Replay the frozen corpus and accept only perfect fixture-local metrics.
pub fn replay_semantic_equivalence_corpus_v1() -> Result<SemanticMetricsV1, EvaluationErrorV1> {
    let pairs = labeled_semantic_pairs_v1()?;
    let metrics = evaluate_semantic_metrics_v1(&pairs);
    if metrics.labeled_equivalent == 0 || metrics.labeled_distinct == 0 {
        return Err(EvaluationErrorV1::SemanticPipeline(
            "corpus missing equivalent or distinct labels".into(),
        ));
    }
    if metrics.false_equivalence_numerator != 0 {
        return Err(EvaluationErrorV1::SemanticPipeline(format!(
            "false-equivalence rate nonzero: {}/{}",
            metrics.false_equivalence_numerator, metrics.false_equivalence_denominator
        )));
    }
    if metrics.precision_denominator == 0
        || metrics.precision_numerator != metrics.precision_denominator
    {
        return Err(EvaluationErrorV1::SemanticPipeline(
            "precision is not exactly 1 on fixture corpus".into(),
        ));
    }
    if metrics.recall_denominator == 0 || metrics.recall_numerator != metrics.recall_denominator {
        return Err(EvaluationErrorV1::SemanticPipeline(
            "recall is not exactly 1 on fixture corpus".into(),
        ));
    }
    Ok(metrics)
}
