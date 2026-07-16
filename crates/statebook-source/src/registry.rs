use crate::bounds::{
    MAX_CLAIM_OR_LIMITATION_COUNT_V1, MAX_PROVENANCE_FIELD_BYTES_V1, MAX_REGISTRATIONS_V1,
    REGISTRATION_SCHEMA_V1,
};
use crate::canonical::{digest_to_hex, registration_digest};
use crate::error::SourceErrorV1;
use crate::types::{EvidenceClassV1, RegistrationStatusV1, SourceRegistrationV1, SourceRegistryV1};

fn registration_key(
    venue_namespace: &str,
    source_contract_id: &str,
    source_revision: &str,
) -> String {
    format!("{venue_namespace}|{source_contract_id}|{source_revision}")
}

impl SourceRegistryV1 {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn len(&self) -> usize {
        self.registrations.len()
    }

    pub fn is_empty(&self) -> bool {
        self.registrations.is_empty()
    }

    pub fn get(
        &self,
        venue_namespace: &str,
        source_contract_id: &str,
        source_revision: &str,
    ) -> Option<&SourceRegistrationV1> {
        self.registrations.get(&registration_key(
            venue_namespace,
            source_contract_id,
            source_revision,
        ))
    }

    #[allow(clippy::too_many_arguments)]
    pub fn register(
        &mut self,
        venue_namespace: &str,
        source_contract_id: &str,
        source_revision: &str,
        published_at: i64,
        retrieved_at: i64,
        evidence_class: EvidenceClassV1,
        content_sha256: &str,
        supported_claims: Vec<String>,
        limitations: Vec<String>,
    ) -> Result<SourceRegistrationV1, SourceErrorV1> {
        if self.registrations.len() >= MAX_REGISTRATIONS_V1 {
            return Err(SourceErrorV1::TooManyRegistrations);
        }
        if supported_claims.len() > MAX_CLAIM_OR_LIMITATION_COUNT_V1
            || limitations.len() > MAX_CLAIM_OR_LIMITATION_COUNT_V1
        {
            return Err(SourceErrorV1::TooManyClaimsOrLimitations);
        }
        for field in [
            venue_namespace,
            source_contract_id,
            source_revision,
            content_sha256,
        ] {
            if field.len() > MAX_PROVENANCE_FIELD_BYTES_V1 {
                return Err(SourceErrorV1::NoncanonicalIdentifier);
            }
        }
        if !evidence_class.may_enter_assurance() {
            return Err(SourceErrorV1::IllustrativeNarrativeRejected);
        }

        let key = registration_key(venue_namespace, source_contract_id, source_revision);
        if let Some(existing) = self.registrations.get(&key) {
            if existing.content_sha256 != content_sha256 {
                return Err(SourceErrorV1::ActiveRevisionConflict);
            }
            return Ok(existing.clone());
        }

        let status = RegistrationStatusV1::Active;
        let digest = registration_digest(
            venue_namespace,
            source_contract_id,
            source_revision,
            content_sha256,
            evidence_class.as_str(),
            "active",
        );
        let registration = SourceRegistrationV1 {
            schema_version: REGISTRATION_SCHEMA_V1.to_owned(),
            venue_namespace: venue_namespace.to_owned(),
            source_contract_id: source_contract_id.to_owned(),
            source_revision: source_revision.to_owned(),
            published_at,
            retrieved_at,
            evidence_class,
            content_sha256: content_sha256.to_owned(),
            supported_claims,
            limitations,
            status,
            registration_digest: digest_to_hex(digest),
        };
        self.registrations.insert(key, registration.clone());
        Ok(registration)
    }

    pub fn supersede(
        &mut self,
        venue_namespace: &str,
        source_contract_id: &str,
        source_revision: &str,
    ) -> Result<SourceRegistrationV1, SourceErrorV1> {
        let key = registration_key(venue_namespace, source_contract_id, source_revision);
        let Some(existing) = self.registrations.get_mut(&key) else {
            return Err(SourceErrorV1::RevisionNotFound);
        };
        existing.status = RegistrationStatusV1::Superseded;
        existing.registration_digest = digest_to_hex(registration_digest(
            venue_namespace,
            source_contract_id,
            source_revision,
            &existing.content_sha256,
            existing.evidence_class.as_str(),
            "superseded",
        ));
        Ok(existing.clone())
    }
}
