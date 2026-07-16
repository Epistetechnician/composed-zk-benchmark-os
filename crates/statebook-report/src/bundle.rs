use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::path::{Component, Path};

use serde_json::{json, Value};

use crate::bounds::{
    BUNDLE_SCHEMA_VERSION_V1, MANIFEST_DIGEST_PATH, MANIFEST_PATH, MAX_BUNDLE_BYTES_V1,
    MAX_BUNDLE_PATH_LENGTH_V1, MAX_NONCLAIMS_V1, MAX_OBSERVATIONS_V1, MAX_TRACE_RECORDS_V1,
    NONCLAIMS_SCHEMA_VERSION_V1, RECORD_BUDGET_PATH, RECORD_COMPLETENESS_PATH,
    RECORD_DECISION_PATH, RECORD_EVIDENCE_PATH, RECORD_NONCLAIMS_PATH, RECORD_POLICY_PATH,
    RECORD_QUEUE_PATH, RECORD_TRACE_PATH, RECORD_VALUATION_PATH, REQUIRED_MEMBER_PATHS,
    TRACE_BOUND_MEMBER_PATHS, TRACE_SCHEMA_VERSION_V1,
};
use crate::canonical::{
    audit_trace_digest, digest_to_hex, manifest_digest, member_digest, nonclaim_set_digest,
    parse_digest_hex,
};
use crate::error::BundleErrorV1;
use crate::json_util::{
    canonical_json, parse_strict_json, reject_secret_retention, reject_unknown_fields,
    require_string, validate_digest_hex, validate_exact_rational, validate_identifier,
};
use crate::types::{
    AuditBundleV1, BudgetSectionV1, CompletenessSectionV1, DecisionRecordSectionV1,
    EvidenceSectionV1, ExactRationalV1, ManifestV1, MaterializationReceiptV1, NonclaimsSectionV1,
    PolicySectionV1, QueueSectionV1, TraceSectionV1, ValidatedAuditBundleV1, ValuationSectionV1,
};

pub fn composition_binding_digest(dimension_digests: &BTreeMap<String, String>) -> [u8; 32] {
    let mut pairs: Vec<_> = dimension_digests.iter().collect();
    pairs.sort_by(|left, right| left.0.cmp(right.0));
    let members: Vec<(String, [u8; 32])> = pairs
        .into_iter()
        .filter_map(|(name, digest_hex)| {
            parse_digest_hex(digest_hex)
                .ok()
                .map(|digest| (name.clone(), digest))
        })
        .collect();
    manifest_digest("composition-binding-v1", &members)
}

pub fn materialize_audit_bundle_v1(
    root: &Path,
    bundle: &AuditBundleV1,
) -> Result<MaterializationReceiptV1, BundleErrorV1> {
    validate_bundle_input(bundle)?;
    fs::create_dir_all(root.join("records"))
        .map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?;
    fs::create_dir_all(root.join("digests"))
        .map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?;

    let member_payloads = build_member_payloads(bundle)?;
    let mut member_digests = BTreeMap::new();
    let mut digest_pairs = Vec::new();
    let mut total_bytes = 0_usize;

    for (path, bytes) in &member_payloads {
        reject_secret_retention(bytes)?;
        total_bytes = total_bytes.saturating_add(bytes.len());
        if total_bytes > MAX_BUNDLE_BYTES_V1 {
            return Err(BundleErrorV1::BundleTooLarge);
        }
        let digest = member_digest(path, bytes);
        member_digests.insert(path.clone(), digest_to_hex(digest));
        digest_pairs.push((path.clone(), digest));
    }

    let nonclaim_set_digest_value = nonclaim_set_digest(&bundle.nonclaims.nonclaims);
    let content_digest_pairs = bound_digest_pairs(&digest_pairs);
    let trace_bytes = member_payloads
        .iter()
        .find(|(path, _)| path == RECORD_TRACE_PATH)
        .map(|(_, bytes)| bytes.as_slice())
        .ok_or_else(|| BundleErrorV1::InvalidInput("missing trace payload".into()))?;
    let trace = parse_trace_section(trace_bytes)?;
    let audit_trace_digest_value = parse_digest_hex(&trace.audit_trace_digest)
        .map_err(|_| BundleErrorV1::TraceDigestMismatch)?;
    let recomputed_trace = audit_trace_digest(
        &trace.trace_id,
        &trace.terms_digest,
        &trace.state_key_digest,
        &trace.residual_digest,
        &trace.composition_digest,
        &trace.decision_context_digest,
        &trace.decision_record_digest,
        &content_digest_pairs,
    );
    if recomputed_trace != audit_trace_digest_value {
        return Err(BundleErrorV1::TraceDigestMismatch);
    }

    let manifest_digest_value = manifest_digest(&bundle.bundle_id, &digest_pairs);

    let manifest = ManifestV1 {
        schema_version: BUNDLE_SCHEMA_VERSION_V1.to_owned(),
        bundle_id: bundle.bundle_id.clone(),
        members: member_digests.clone(),
        manifest_digest: digest_to_hex(manifest_digest_value),
        audit_trace_digest: digest_to_hex(audit_trace_digest_value),
        nonclaim_set_digest: digest_to_hex(nonclaim_set_digest_value),
    };
    let manifest_bytes = canonical_json(&serde_json::to_value(&manifest).unwrap())?;
    total_bytes = total_bytes.saturating_add(manifest_bytes.len());
    if total_bytes > MAX_BUNDLE_BYTES_V1 {
        return Err(BundleErrorV1::BundleTooLarge);
    }

    write_file(root, MANIFEST_PATH, &manifest_bytes)?;
    write_file(
        root,
        MANIFEST_DIGEST_PATH,
        format!("{}\n", digest_to_hex(manifest_digest_value)).as_bytes(),
    )?;
    for (path, bytes) in member_payloads {
        write_file(root, &path, &bytes)?;
    }

    Ok(MaterializationReceiptV1 {
        bundle_id: bundle.bundle_id.clone(),
        manifest_digest: digest_to_hex(manifest_digest_value),
        audit_trace_digest: digest_to_hex(audit_trace_digest_value),
        nonclaim_set_digest: digest_to_hex(nonclaim_set_digest_value),
        member_digests,
    })
}

pub fn readback_validate_audit_bundle_v1(
    root: &Path,
) -> Result<ValidatedAuditBundleV1, BundleErrorV1> {
    validate_bundle_root(root)?;
    let manifest_bytes = read_regular_file(root, MANIFEST_PATH)?;
    reject_secret_retention(&manifest_bytes)?;
    if manifest_bytes.len() > MAX_BUNDLE_BYTES_V1 {
        return Err(BundleErrorV1::BundleTooLarge);
    }

    let manifest_value = parse_strict_json(&manifest_bytes, MANIFEST_PATH)?;
    reject_unknown_fields(
        &manifest_value,
        &[
            "schema_version",
            "bundle_id",
            "members",
            "manifest_digest",
            "audit_trace_digest",
            "nonclaim_set_digest",
        ],
        MANIFEST_PATH,
    )?;
    let schema_version = require_string(&manifest_value, "schema_version", MANIFEST_PATH)?;
    if schema_version != BUNDLE_SCHEMA_VERSION_V1 {
        return Err(BundleErrorV1::UnknownSchemaVersion(MANIFEST_PATH.into()));
    }
    let bundle_id = require_string(&manifest_value, "bundle_id", MANIFEST_PATH)?;
    validate_identifier(&bundle_id, MANIFEST_PATH)?;
    let manifest_digest_claimed =
        require_string(&manifest_value, "manifest_digest", MANIFEST_PATH)?;
    validate_digest_hex(&manifest_digest_claimed, MANIFEST_PATH)?;
    let audit_trace_digest_claimed =
        require_string(&manifest_value, "audit_trace_digest", MANIFEST_PATH)?;
    validate_digest_hex(&audit_trace_digest_claimed, MANIFEST_PATH)?;
    let nonclaim_set_digest_claimed =
        require_string(&manifest_value, "nonclaim_set_digest", MANIFEST_PATH)?;
    validate_digest_hex(&nonclaim_set_digest_claimed, MANIFEST_PATH)?;

    let members_object = manifest_value
        .get("members")
        .and_then(Value::as_object)
        .ok_or_else(|| BundleErrorV1::MalformedJson(MANIFEST_PATH.into()))?;
    if members_object.len() != REQUIRED_MEMBER_PATHS.len() {
        return Err(BundleErrorV1::MalformedJson(MANIFEST_PATH.into()));
    }

    let mut member_digests = BTreeMap::new();
    let mut digest_pairs = Vec::new();
    let mut total_bytes = manifest_bytes.len();

    for path in REQUIRED_MEMBER_PATHS {
        let digest_hex = members_object
            .get(*path)
            .and_then(Value::as_str)
            .ok_or_else(|| BundleErrorV1::MissingFile((*path).into()))?;
        validate_digest_hex(digest_hex, path)?;
        let bytes = read_regular_file(root, path)?;
        reject_secret_retention(&bytes)?;
        total_bytes = total_bytes.saturating_add(bytes.len());
        if total_bytes > MAX_BUNDLE_BYTES_V1 {
            return Err(BundleErrorV1::BundleTooLarge);
        }
        let digest = member_digest(path, &bytes);
        if digest_to_hex(digest) != digest_hex {
            return Err(BundleErrorV1::StaleMemberDigest((*path).into()));
        }
        member_digests.insert((*path).to_owned(), digest_hex.to_owned());
        digest_pairs.push(((*path).to_owned(), digest));
    }

    let manifest_digest_value = manifest_digest(&bundle_id, &digest_pairs);
    if digest_to_hex(manifest_digest_value) != manifest_digest_claimed {
        return Err(BundleErrorV1::StaleManifestDigest);
    }

    let manifest_digest_file = read_regular_file(root, MANIFEST_DIGEST_PATH)?;
    let manifest_digest_file_text = std::str::from_utf8(&manifest_digest_file)
        .map_err(|_| BundleErrorV1::MalformedJson(MANIFEST_DIGEST_PATH.into()))?
        .trim();
    if manifest_digest_file_text != manifest_digest_claimed {
        return Err(BundleErrorV1::StaleManifestDigest);
    }

    let trace = parse_trace_section(&read_regular_file(root, RECORD_TRACE_PATH)?)?;
    if trace.audit_trace_digest != audit_trace_digest_claimed {
        return Err(BundleErrorV1::TraceDigestMismatch);
    }

    let nonclaims = parse_nonclaims_section(&read_regular_file(root, RECORD_NONCLAIMS_PATH)?)?;
    let recomputed_nonclaim_digest = digest_to_hex(nonclaim_set_digest(&nonclaims.nonclaims));
    if recomputed_nonclaim_digest != nonclaim_set_digest_claimed {
        return Err(BundleErrorV1::TamperedNonclaimSet);
    }
    if nonclaims.nonclaim_set_digest != nonclaim_set_digest_claimed {
        return Err(BundleErrorV1::TamperedNonclaimSet);
    }

    let completeness =
        parse_completeness_section(&read_regular_file(root, RECORD_COMPLETENESS_PATH)?)?;
    let recomposed = composition_binding_digest(&completeness.dimension_digests);
    if digest_to_hex(recomposed) != completeness.composition_digest {
        return Err(BundleErrorV1::CompositionDigestMismatch);
    }
    if completeness.composition_digest != trace.composition_digest {
        return Err(BundleErrorV1::CompositionDigestMismatch);
    }

    let decision = parse_decision_section(&read_regular_file(root, RECORD_DECISION_PATH)?)?;
    if decision.decision_context_digest != trace.decision_context_digest {
        return Err(BundleErrorV1::DecisionContextDigestMismatch);
    }
    if decision.record_digest != trace.decision_record_digest {
        return Err(BundleErrorV1::DecisionContextDigestMismatch);
    }

    let content_digest_pairs = bound_digest_pairs(&digest_pairs);
    let recomputed_trace = audit_trace_digest(
        &trace.trace_id,
        &trace.terms_digest,
        &trace.state_key_digest,
        &trace.residual_digest,
        &trace.composition_digest,
        &trace.decision_context_digest,
        &trace.decision_record_digest,
        &content_digest_pairs,
    );
    if digest_to_hex(recomputed_trace) != audit_trace_digest_claimed {
        return Err(BundleErrorV1::TraceDigestMismatch);
    }

    Ok(ValidatedAuditBundleV1 {
        bundle_id,
        manifest_digest: manifest_digest_claimed,
        audit_trace_digest: audit_trace_digest_claimed,
        nonclaim_set_digest: nonclaim_set_digest_claimed,
        member_digests,
        trace,
    })
}

fn validate_bundle_input(bundle: &AuditBundleV1) -> Result<(), BundleErrorV1> {
    validate_identifier(&bundle.bundle_id, "bundle_id")?;
    validate_digest_hex(&bundle.terms_digest, "terms_digest")?;
    validate_digest_hex(&bundle.state_key_digest, "state_key_digest")?;
    validate_digest_hex(&bundle.residual_digest, "residual_digest")?;
    validate_digest_hex(&bundle.composition_digest, "composition_digest")?;
    validate_digest_hex(&bundle.decision_context_digest, "decision_context_digest")?;
    if bundle.nonclaims.nonclaims.len() > MAX_NONCLAIMS_V1 {
        return Err(BundleErrorV1::TooManyNonclaims);
    }
    if bundle.evidence.observation_count as usize > MAX_OBSERVATIONS_V1 {
        return Err(BundleErrorV1::TooManyObservations);
    }
    if bundle.completeness.dimension_digests.len() > MAX_TRACE_RECORDS_V1 {
        return Err(BundleErrorV1::TooManyTraceRecords);
    }
    let recomposed = composition_binding_digest(&bundle.completeness.dimension_digests);
    if digest_to_hex(recomposed) != bundle.composition_digest {
        return Err(BundleErrorV1::CompositionDigestMismatch);
    }
    if bundle.decision_record.decision_context_digest != bundle.decision_context_digest {
        return Err(BundleErrorV1::DecisionContextDigestMismatch);
    }
    Ok(())
}

fn build_member_payloads(bundle: &AuditBundleV1) -> Result<Vec<(String, Vec<u8>)>, BundleErrorV1> {
    let trace_id = format!("trace-{}", bundle.bundle_id);
    let nonclaim_set_digest_hex = digest_to_hex(nonclaim_set_digest(&bundle.nonclaims.nonclaims));
    let mut nonclaims = bundle.nonclaims.clone();
    nonclaims.nonclaim_set_digest = nonclaim_set_digest_hex;

    let mut payloads = vec![
        (
            RECORD_DECISION_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.decision_record).unwrap())?,
        ),
        (
            RECORD_COMPLETENESS_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.completeness).unwrap())?,
        ),
        (
            RECORD_EVIDENCE_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.evidence).unwrap())?,
        ),
        (
            RECORD_POLICY_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.policy).unwrap())?,
        ),
        (
            RECORD_VALUATION_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.valuation).unwrap())?,
        ),
        (
            RECORD_BUDGET_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.budget).unwrap())?,
        ),
        (
            RECORD_QUEUE_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&bundle.queue).unwrap())?,
        ),
        (
            RECORD_NONCLAIMS_PATH.to_owned(),
            canonical_json(&serde_json::to_value(&nonclaims).unwrap())?,
        ),
    ];

    let bound_pairs: Vec<(String, [u8; 32])> = payloads
        .iter()
        .map(|(path, bytes)| (path.clone(), member_digest(path, bytes)))
        .collect();
    let audit_trace = audit_trace_digest(
        &trace_id,
        &bundle.terms_digest,
        &bundle.state_key_digest,
        &bundle.residual_digest,
        &bundle.composition_digest,
        &bundle.decision_context_digest,
        &bundle.decision_record.record_digest,
        &bound_pairs,
    );
    let trace = TraceSectionV1 {
        schema_version: TRACE_SCHEMA_VERSION_V1.to_owned(),
        trace_id,
        terms_digest: bundle.terms_digest.clone(),
        state_key_digest: bundle.state_key_digest.clone(),
        residual_digest: bundle.residual_digest.clone(),
        composition_digest: bundle.composition_digest.clone(),
        decision_context_digest: bundle.decision_context_digest.clone(),
        decision_record_digest: bundle.decision_record.record_digest.clone(),
        audit_trace_digest: digest_to_hex(audit_trace),
        member_digests: bound_pairs
            .iter()
            .map(|(path, digest)| (path.clone(), digest_to_hex(*digest)))
            .collect(),
    };
    payloads.push((
        RECORD_TRACE_PATH.to_owned(),
        canonical_json(&serde_json::to_value(&trace).unwrap())?,
    ));

    Ok(payloads)
}

fn bound_digest_pairs(digest_pairs: &[(String, [u8; 32])]) -> Vec<(String, [u8; 32])> {
    digest_pairs
        .iter()
        .filter(|(path, _)| TRACE_BOUND_MEMBER_PATHS.contains(&path.as_str()))
        .cloned()
        .collect()
}

fn parse_decision_section(bytes: &[u8]) -> Result<DecisionRecordSectionV1, BundleErrorV1> {
    let value = parse_strict_json(bytes, RECORD_DECISION_PATH)?;
    reject_unknown_fields(
        &value,
        &[
            "schema_version",
            "outcome",
            "intent_digest",
            "decision_context_digest",
            "instant_release_amount",
            "ledger_tip_before",
            "ledger_tip_after",
            "reasons",
            "evaluated_at",
            "record_digest",
        ],
        RECORD_DECISION_PATH,
    )?;
    let section: DecisionRecordSectionV1 = serde_json::from_value(value)
        .map_err(|_| BundleErrorV1::MalformedJson(RECORD_DECISION_PATH.into()))?;
    validate_digest_hex(&section.intent_digest, RECORD_DECISION_PATH)?;
    validate_digest_hex(&section.decision_context_digest, RECORD_DECISION_PATH)?;
    validate_digest_hex(&section.record_digest, RECORD_DECISION_PATH)?;
    validate_digest_hex(&section.ledger_tip_before, RECORD_DECISION_PATH)?;
    validate_digest_hex(&section.ledger_tip_after, RECORD_DECISION_PATH)?;
    validate_exact_rational(&section.instant_release_amount, RECORD_DECISION_PATH)?;
    Ok(section)
}

fn parse_completeness_section(bytes: &[u8]) -> Result<CompletenessSectionV1, BundleErrorV1> {
    let value = parse_strict_json(bytes, RECORD_COMPLETENESS_PATH)?;
    reject_unknown_fields(
        &value,
        &["schema_version", "composition_digest", "dimension_digests"],
        RECORD_COMPLETENESS_PATH,
    )?;
    let section: CompletenessSectionV1 = serde_json::from_value(value)
        .map_err(|_| BundleErrorV1::MalformedJson(RECORD_COMPLETENESS_PATH.into()))?;
    validate_digest_hex(&section.composition_digest, RECORD_COMPLETENESS_PATH)?;
    for digest in section.dimension_digests.values() {
        validate_digest_hex(digest, RECORD_COMPLETENESS_PATH)?;
    }
    Ok(section)
}

fn parse_nonclaims_section(bytes: &[u8]) -> Result<NonclaimsSectionV1, BundleErrorV1> {
    let value = parse_strict_json(bytes, RECORD_NONCLAIMS_PATH)?;
    reject_unknown_fields(
        &value,
        &["schema_version", "nonclaims", "nonclaim_set_digest"],
        RECORD_NONCLAIMS_PATH,
    )?;
    let section: NonclaimsSectionV1 = serde_json::from_value(value)
        .map_err(|_| BundleErrorV1::MalformedJson(RECORD_NONCLAIMS_PATH.into()))?;
    if section.schema_version != NONCLAIMS_SCHEMA_VERSION_V1 {
        return Err(BundleErrorV1::UnknownSchemaVersion(
            RECORD_NONCLAIMS_PATH.into(),
        ));
    }
    if section.nonclaims.len() > MAX_NONCLAIMS_V1 {
        return Err(BundleErrorV1::TooManyNonclaims);
    }
    validate_digest_hex(&section.nonclaim_set_digest, RECORD_NONCLAIMS_PATH)?;
    Ok(section)
}

fn parse_trace_section(bytes: &[u8]) -> Result<TraceSectionV1, BundleErrorV1> {
    let value = parse_strict_json(bytes, RECORD_TRACE_PATH)?;
    reject_unknown_fields(
        &value,
        &[
            "schema_version",
            "trace_id",
            "terms_digest",
            "state_key_digest",
            "residual_digest",
            "composition_digest",
            "decision_context_digest",
            "decision_record_digest",
            "audit_trace_digest",
            "member_digests",
        ],
        RECORD_TRACE_PATH,
    )?;
    let section: TraceSectionV1 = serde_json::from_value(value)
        .map_err(|_| BundleErrorV1::MalformedJson(RECORD_TRACE_PATH.into()))?;
    if section.schema_version != TRACE_SCHEMA_VERSION_V1 {
        return Err(BundleErrorV1::UnknownSchemaVersion(
            RECORD_TRACE_PATH.into(),
        ));
    }
    validate_identifier(&section.trace_id, RECORD_TRACE_PATH)?;
    for field in [
        &section.terms_digest,
        &section.state_key_digest,
        &section.residual_digest,
        &section.composition_digest,
        &section.decision_context_digest,
        &section.decision_record_digest,
        &section.audit_trace_digest,
    ] {
        validate_digest_hex(field, RECORD_TRACE_PATH)?;
    }
    if section.member_digests.len() != TRACE_BOUND_MEMBER_PATHS.len() {
        return Err(BundleErrorV1::MalformedJson(RECORD_TRACE_PATH.into()));
    }
    Ok(section)
}

fn validate_bundle_root(root: &Path) -> Result<(), BundleErrorV1> {
    if !root.is_dir() {
        return Err(BundleErrorV1::InvalidInput("root must be directory".into()));
    }
    let mut seen = BTreeMap::new();
    collect_files(root, root, &mut seen)?;
    for required in REQUIRED_MEMBER_PATHS {
        if !seen.contains_key(*required) {
            return Err(BundleErrorV1::MissingFile((*required).into()));
        }
    }
    if !seen.contains_key(MANIFEST_PATH) {
        return Err(BundleErrorV1::MissingFile(MANIFEST_PATH.into()));
    }
    if !seen.contains_key(MANIFEST_DIGEST_PATH) {
        return Err(BundleErrorV1::MissingFile(MANIFEST_DIGEST_PATH.into()));
    }
    let allowed: BTreeMap<&str, ()> = REQUIRED_MEMBER_PATHS
        .iter()
        .copied()
        .chain([MANIFEST_PATH, MANIFEST_DIGEST_PATH])
        .map(|path| (path, ()))
        .collect();
    for path in seen.keys() {
        if !allowed.contains_key(path.as_str()) {
            return Err(BundleErrorV1::ExtraFile(path.clone()));
        }
    }
    Ok(())
}

fn collect_files(
    root: &Path,
    current: &Path,
    seen: &mut BTreeMap<String, ()>,
) -> Result<(), BundleErrorV1> {
    for entry in
        fs::read_dir(current).map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?
    {
        let entry = entry.map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?;
        let path = entry.path();
        let relative = path
            .strip_prefix(root)
            .map_err(|_| BundleErrorV1::PathTraversal(path.display().to_string()))?
            .to_string_lossy()
            .replace('\\', "/");
        if relative.len() > MAX_BUNDLE_PATH_LENGTH_V1 {
            return Err(BundleErrorV1::PathTooLong);
        }
        if relative.contains("..") {
            return Err(BundleErrorV1::PathTraversal(relative));
        }
        for component in Path::new(&relative).components() {
            if matches!(
                component,
                Component::ParentDir | Component::RootDir | Component::Prefix(_)
            ) {
                return Err(BundleErrorV1::PathTraversal(relative.clone()));
            }
        }
        #[cfg(unix)]
        {
            if path
                .symlink_metadata()
                .map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?
                .file_type()
                .is_symlink()
            {
                return Err(BundleErrorV1::Symlink(relative));
            }
        }
        if path.is_dir() {
            collect_files(root, &path, seen)?;
        } else {
            seen.insert(relative, ());
        }
    }
    Ok(())
}

fn write_file(root: &Path, relative: &str, bytes: &[u8]) -> Result<(), BundleErrorV1> {
    if relative.len() > MAX_BUNDLE_PATH_LENGTH_V1 || relative.contains("..") {
        return Err(BundleErrorV1::PathTraversal(relative.into()));
    }
    let path = root.join(relative);
    for component in path.components() {
        if matches!(component, Component::ParentDir) {
            return Err(BundleErrorV1::PathTraversal(relative.into()));
        }
    }
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?;
    }
    let mut file =
        fs::File::create(&path).map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?;
    file.write_all(bytes)
        .map_err(|error| BundleErrorV1::Filesystem(error.to_string()))?;
    Ok(())
}

fn read_regular_file(root: &Path, relative: &str) -> Result<Vec<u8>, BundleErrorV1> {
    if relative.len() > MAX_BUNDLE_PATH_LENGTH_V1 || relative.contains("..") {
        return Err(BundleErrorV1::PathTraversal(relative.into()));
    }
    let path = root.join(relative);
    #[cfg(unix)]
    if fs::symlink_metadata(&path)
        .map_err(|_| BundleErrorV1::MissingFile(relative.into()))?
        .file_type()
        .is_symlink()
    {
        return Err(BundleErrorV1::Symlink(relative.into()));
    }
    fs::read(&path).map_err(|_| BundleErrorV1::MissingFile(relative.into()))
}

pub fn build_golden_bundle_from_decision(
    bundle_id: &str,
    decision_json: &Value,
) -> Result<AuditBundleV1, BundleErrorV1> {
    let intent_digest = require_string(decision_json, "intent_digest", "decision")?;
    let decision_context_digest =
        require_string(decision_json, "decision_context_digest", "decision")?;
    let record_digest = require_string(decision_json, "record_digest", "decision")?;
    let outcome = require_string(decision_json, "outcome", "decision")?;
    let ledger_tip_before = require_string(decision_json, "ledger_tip_before", "decision")?;
    let ledger_tip_after = require_string(decision_json, "ledger_tip_after", "decision")?;
    let evaluated_at = decision_json
        .get("evaluated_at")
        .and_then(Value::as_i64)
        .ok_or_else(|| BundleErrorV1::MalformedJson("decision.evaluated_at".into()))?;
    let reasons = decision_json
        .get("reasons")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
        .into_iter()
        .filter_map(|value| value.as_str().map(str::to_owned))
        .collect();
    let instant_release_amount: ExactRationalV1 = serde_json::from_value(
        decision_json
            .get("instant_release_amount")
            .cloned()
            .unwrap_or(json!({"numerator":"0","denominator":"1"})),
    )
    .map_err(|_| BundleErrorV1::MalformedJson("decision.instant_release_amount".into()))?;

    let mut dimension_digests = BTreeMap::new();
    dimension_digests.insert(
        "execution".to_owned(),
        "1111111111111111111111111111111111111111111111111111111111111111".to_owned(),
    );
    dimension_digests.insert(
        "capital".to_owned(),
        "2222222222222222222222222222222222222222222222222222222222222222".to_owned(),
    );
    dimension_digests.insert(
        "settlement".to_owned(),
        "3333333333333333333333333333333333333333333333333333333333333333".to_owned(),
    );
    dimension_digests.insert(
        "assurance".to_owned(),
        "4444444444444444444444444444444444444444444444444444444444444444".to_owned(),
    );
    dimension_digests.insert(
        "recovery".to_owned(),
        "5555555555555555555555555555555555555555555555555555555555555555".to_owned(),
    );
    dimension_digests.insert(
        "residual".to_owned(),
        "6666666666666666666666666666666666666666666666666666666666666666".to_owned(),
    );
    dimension_digests.insert(
        "terms".to_owned(),
        "7777777777777777777777777777777777777777777777777777777777777777".to_owned(),
    );
    let composition_digest = digest_to_hex(composition_binding_digest(&dimension_digests));

    Ok(AuditBundleV1 {
        bundle_id: bundle_id.to_owned(),
        terms_digest: "7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788".to_owned(),
        state_key_digest: "f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08"
            .to_owned(),
        residual_digest: "67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a"
            .to_owned(),
        composition_digest: composition_digest.clone(),
        decision_context_digest: decision_context_digest.clone(),
        decision_record: DecisionRecordSectionV1 {
            schema_version: 1,
            outcome,
            intent_digest,
            decision_context_digest,
            instant_release_amount,
            ledger_tip_before: ledger_tip_before.clone(),
            ledger_tip_after: ledger_tip_after.clone(),
            reasons,
            evaluated_at,
            record_digest,
        },
        completeness: CompletenessSectionV1 {
            schema_version: "statebook-p3-composition:v1".to_owned(),
            composition_digest: composition_digest.clone(),
            dimension_digests,
        },
        evidence: EvidenceSectionV1 {
            schema_version: "statebook-p4-evidence-snapshot:v1".to_owned(),
            snapshot_digest: "8888888888888888888888888888888888888888888888888888888888888888"
                .to_owned(),
            observation_count: 8,
        },
        policy: PolicySectionV1 {
            schema_version: "statebook-p4-policy:v1".to_owned(),
            policy_digest: "9999999999999999999999999999999999999999999999999999999999999999"
                .to_owned(),
        },
        valuation: ValuationSectionV1 {
            schema_version: "statebook-p4-valuation-profile:v1".to_owned(),
            valuation_digest: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                .to_owned(),
        },
        budget: BudgetSectionV1 {
            schema_version: "statebook-p4-ledger-tip:v1".to_owned(),
            ledger_tip_before,
            ledger_tip_after,
        },
        queue: QueueSectionV1 {
            schema_version: "statebook-p4-settlement-state:v1".to_owned(),
            queue_status: "none".to_owned(),
            transfer_status: "unreserved".to_owned(),
        },
        nonclaims: NonclaimsSectionV1 {
            schema_version: NONCLAIMS_SCHEMA_VERSION_V1.to_owned(),
            nonclaims: vec![
                "no_transfer_command".to_owned(),
                "no_signing_request".to_owned(),
                "no_authority".to_owned(),
                "no_value_movement".to_owned(),
            ],
            nonclaim_set_digest: String::new(),
        },
    })
}
