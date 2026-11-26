use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const PQAI_FINALITY_SCHEMA_V1: &str = "statebook.pqai-finality-clock.v1";
pub const PQAI_FINALITY_DOMAIN_V1: &[u8] = b"statebook:pqai-finality:v1\0";
pub const PQAI_FINALITY_CLAIM_BOUNDARY: &str =
    "local hermetic cryptographic finality posture assessment without live chain telemetry or settlement authority";

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CryptographicFinalityStateV1 {
    ClassicalPreQuantum,
    PqaiReadyCalldataFallback,
    PqaiScaledHashDa,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AccountAuthAssumptionV1 {
    EcrecoverPreQuantum,
    Eip8141FrameHashRoot,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ConsensusSignatureAssumptionV1 {
    Bls12381PreQuantum,
    Eip8288HashAggregate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DataAvailabilityAssumptionV1 {
    Kzg4844PreQuantum,
    CalldataFallbackConservative,
    Eip8479HashPcsWhirBasefold,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HashPrimitiveClassV1 {
    ConservativeSha256Blake3,
    AlgebraicPoseidon2,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PqaiFinalityContextV1 {
    pub source_finality_domain: String,
    pub destination_finality_domain: String,
    pub account_auth: AccountAuthAssumptionV1,
    pub consensus_signatures: ConsensusSignatureAssumptionV1,
    pub data_availability: DataAvailabilityAssumptionV1,
    pub hash_primitive: HashPrimitiveClassV1,
    pub hash_root_digest_hex: String,
    pub require_pqai: bool,
    pub forbid_algebraic_hash_root: bool,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct PqaiFinalityReportV1 {
    pub schema_version: String,
    pub source_finality_domain: String,
    pub destination_finality_domain: String,
    pub cryptographic_finality_state: CryptographicFinalityStateV1,
    pub admitted: bool,
    pub blocking_dependencies: Vec<String>,
    pub advisory_warnings: Vec<String>,
    pub report_digest_hex: String,
    pub claim_boundary: String,
    pub explicit_nonclaims: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq, Error)]
pub enum PqaiFinalityError {
    #[error("finality domain identifier must be non-empty ASCII")]
    InvalidFinalityDomain,
    #[error("hash_root_digest_hex must be 64 lowercase hex characters")]
    InvalidHashRootDigest,
}

fn validate_domain(domain: &str) -> Result<(), PqaiFinalityError> {
    if domain.is_empty()
        || domain.len() > 128
        || !domain
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.' | b':'))
    {
        return Err(PqaiFinalityError::InvalidFinalityDomain);
    }
    Ok(())
}

fn validate_digest_hex(digest_hex: &str) -> Result<(), PqaiFinalityError> {
    if digest_hex.len() != 64
        || !digest_hex
            .bytes()
            .all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(PqaiFinalityError::InvalidHashRootDigest);
    }
    Ok(())
}

fn compute_report_digest(
    ctx: &PqaiFinalityContextV1,
    state: CryptographicFinalityStateV1,
    admitted: bool,
    blocking: &[String],
) -> String {
    let mut h = Sha256::new();
    h.update(PQAI_FINALITY_DOMAIN_V1);
    h.update(ctx.source_finality_domain.as_bytes());
    h.update(b"\0");
    h.update(ctx.destination_finality_domain.as_bytes());
    h.update(b"\0");
    h.update(format!("{:?}|{:?}|{:?}|{:?}", ctx.account_auth, ctx.consensus_signatures, ctx.data_availability, ctx.hash_primitive).as_bytes());
    h.update(b"\0");
    h.update(ctx.hash_root_digest_hex.as_bytes());
    h.update(b"\0");
    h.update(format!("{state:?}|{admitted}").as_bytes());
    for dep in blocking {
        h.update(b"\0");
        h.update(dep.as_bytes());
    }
    hex::encode(h.finalize())
}

pub fn assess_pqai_finality_v1(
    ctx: &PqaiFinalityContextV1,
) -> Result<PqaiFinalityReportV1, PqaiFinalityError> {
    validate_domain(&ctx.source_finality_domain)?;
    validate_domain(&ctx.destination_finality_domain)?;
    validate_digest_hex(&ctx.hash_root_digest_hex)?;

    let mut blocking = Vec::new();
    let mut warnings = Vec::new();

    if ctx.account_auth == AccountAuthAssumptionV1::EcrecoverPreQuantum {
        blocking.push("pre_quantum_account_auth:ecrecover_secp256k1".to_string());
    }
    if ctx.consensus_signatures == ConsensusSignatureAssumptionV1::Bls12381PreQuantum {
        blocking.push("pre_quantum_consensus_signatures:bls12_381".to_string());
    }
    if ctx.data_availability == DataAvailabilityAssumptionV1::Kzg4844PreQuantum {
        blocking.push("pre_quantum_data_availability:kzg_4844".to_string());
    }
    if ctx.hash_primitive == HashPrimitiveClassV1::AlgebraicPoseidon2 {
        if ctx.forbid_algebraic_hash_root {
            blocking.push("algebraic_hash_root_forbidden:poseidon2".to_string());
        } else {
            warnings.push(
                "elevated_algebraic_hash_assumption:poseidon2_prefer_sha256_or_blake3".to_string(),
            );
        }
    }

    let state = if !blocking.is_empty() {
        CryptographicFinalityStateV1::ClassicalPreQuantum
    } else {
        match ctx.data_availability {
            DataAvailabilityAssumptionV1::Eip8479HashPcsWhirBasefold => {
                CryptographicFinalityStateV1::PqaiScaledHashDa
            }
            DataAvailabilityAssumptionV1::CalldataFallbackConservative => {
                CryptographicFinalityStateV1::PqaiReadyCalldataFallback
            }
            DataAvailabilityAssumptionV1::Kzg4844PreQuantum => {
                CryptographicFinalityStateV1::ClassicalPreQuantum
            }
        }
    };

    let admitted = if ctx.require_pqai {
        state != CryptographicFinalityStateV1::ClassicalPreQuantum && blocking.is_empty()
    } else {
        true
    };

    let report_digest_hex = compute_report_digest(ctx, state, admitted, &blocking);

    Ok(PqaiFinalityReportV1 {
        schema_version: PQAI_FINALITY_SCHEMA_V1.to_string(),
        source_finality_domain: ctx.source_finality_domain.clone(),
        destination_finality_domain: ctx.destination_finality_domain.clone(),
        cryptographic_finality_state: state,
        admitted,
        blocking_dependencies: blocking,
        advisory_warnings: warnings,
        report_digest_hex,
        claim_boundary: PQAI_FINALITY_CLAIM_BOUNDARY.to_string(),
        explicit_nonclaims: vec![
            "does not verify live L1/L2 consensus headers or RPC state".to_string(),
            "does not authorize external capital release or settlement".to_string(),
            "cryptographic finality state is evaluated strictly from declared assumptions"
                .to_string(),
        ],
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_digest() -> String {
        "a".repeat(64)
    }

    #[test]
    fn pqai_scaled_hash_da_admits_under_require_pqai() {
        let ctx = PqaiFinalityContextV1 {
            source_finality_domain: "ethereum-l1-pq-cl".to_string(),
            destination_finality_domain: "statebook-rollup-pqai".to_string(),
            account_auth: AccountAuthAssumptionV1::Eip8141FrameHashRoot,
            consensus_signatures: ConsensusSignatureAssumptionV1::Eip8288HashAggregate,
            data_availability: DataAvailabilityAssumptionV1::Eip8479HashPcsWhirBasefold,
            hash_primitive: HashPrimitiveClassV1::ConservativeSha256Blake3,
            hash_root_digest_hex: sample_digest(),
            require_pqai: true,
            forbid_algebraic_hash_root: true,
        };
        let report = assess_pqai_finality_v1(&ctx).expect("assess");
        assert_eq!(
            report.cryptographic_finality_state,
            CryptographicFinalityStateV1::PqaiScaledHashDa
        );
        assert!(report.admitted);
        assert!(report.blocking_dependencies.is_empty());
        assert_eq!(report.report_digest_hex.len(), 64);
    }

    #[test]
    fn pqai_ready_calldata_fallback_admits_without_blobs() {
        let ctx = PqaiFinalityContextV1 {
            source_finality_domain: "ethereum-l1-pq-cl".to_string(),
            destination_finality_domain: "statebook-calldata-fallback".to_string(),
            account_auth: AccountAuthAssumptionV1::Eip8141FrameHashRoot,
            consensus_signatures: ConsensusSignatureAssumptionV1::Eip8288HashAggregate,
            data_availability: DataAvailabilityAssumptionV1::CalldataFallbackConservative,
            hash_primitive: HashPrimitiveClassV1::ConservativeSha256Blake3,
            hash_root_digest_hex: sample_digest(),
            require_pqai: true,
            forbid_algebraic_hash_root: true,
        };
        let report = assess_pqai_finality_v1(&ctx).expect("assess");
        assert_eq!(
            report.cryptographic_finality_state,
            CryptographicFinalityStateV1::PqaiReadyCalldataFallback
        );
        assert!(report.admitted);
    }

    #[test]
    fn single_pre_quantum_dependency_downgrades_and_fails_closed() {
        let ctx = PqaiFinalityContextV1 {
            source_finality_domain: "ethereum-l1-mixed".to_string(),
            destination_finality_domain: "statebook-l2".to_string(),
            account_auth: AccountAuthAssumptionV1::EcrecoverPreQuantum,
            consensus_signatures: ConsensusSignatureAssumptionV1::Eip8288HashAggregate,
            data_availability: DataAvailabilityAssumptionV1::Eip8479HashPcsWhirBasefold,
            hash_primitive: HashPrimitiveClassV1::ConservativeSha256Blake3,
            hash_root_digest_hex: sample_digest(),
            require_pqai: true,
            forbid_algebraic_hash_root: true,
        };
        let report = assess_pqai_finality_v1(&ctx).expect("assess");
        assert_eq!(
            report.cryptographic_finality_state,
            CryptographicFinalityStateV1::ClassicalPreQuantum
        );
        assert!(!report.admitted);
        assert_eq!(
            report.blocking_dependencies,
            vec!["pre_quantum_account_auth:ecrecover_secp256k1"]
        );
    }

    #[test]
    fn algebraic_hash_root_rejected_when_forbidden() {
        let ctx = PqaiFinalityContextV1 {
            source_finality_domain: "ethereum-l1-pq-cl".to_string(),
            destination_finality_domain: "statebook-l2".to_string(),
            account_auth: AccountAuthAssumptionV1::Eip8141FrameHashRoot,
            consensus_signatures: ConsensusSignatureAssumptionV1::Eip8288HashAggregate,
            data_availability: DataAvailabilityAssumptionV1::Eip8479HashPcsWhirBasefold,
            hash_primitive: HashPrimitiveClassV1::AlgebraicPoseidon2,
            hash_root_digest_hex: sample_digest(),
            require_pqai: true,
            forbid_algebraic_hash_root: true,
        };
        let report = assess_pqai_finality_v1(&ctx).expect("assess");
        assert!(!report.admitted);
        assert_eq!(
            report.cryptographic_finality_state,
            CryptographicFinalityStateV1::ClassicalPreQuantum
        );
    }

    #[test]
    fn invalid_inputs_fail_closed() {
        let mut ctx = PqaiFinalityContextV1 {
            source_finality_domain: "bad domain!".to_string(),
            destination_finality_domain: "ok".to_string(),
            account_auth: AccountAuthAssumptionV1::Eip8141FrameHashRoot,
            consensus_signatures: ConsensusSignatureAssumptionV1::Eip8288HashAggregate,
            data_availability: DataAvailabilityAssumptionV1::Eip8479HashPcsWhirBasefold,
            hash_primitive: HashPrimitiveClassV1::ConservativeSha256Blake3,
            hash_root_digest_hex: sample_digest(),
            require_pqai: true,
            forbid_algebraic_hash_root: true,
        };
        assert_eq!(
            assess_pqai_finality_v1(&ctx),
            Err(PqaiFinalityError::InvalidFinalityDomain)
        );
        ctx.source_finality_domain = "ok".to_string();
        ctx.hash_root_digest_hex = "not-hex".to_string();
        assert_eq!(
            assess_pqai_finality_v1(&ctx),
            Err(PqaiFinalityError::InvalidHashRootDigest)
        );
    }
}
