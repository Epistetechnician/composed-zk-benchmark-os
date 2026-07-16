use crate::bounds::{MAX_FIELD_BYTES_V1, MAX_REGISTRATIONS_V1, REGISTRATION_SCHEMA_V1};
use crate::canonical::{digest_to_hex, registration_digest};
use crate::error::AuthorityErrorV1;
use crate::types::{AuthorityRegistrationV1, AuthorityRegistryV1, StatementStatusV1};

fn registration_key(
    authority_namespace: &str,
    authority_id: &str,
    statement_revision: &str,
) -> String {
    format!("{authority_namespace}|{authority_id}|{statement_revision}")
}

impl AuthorityRegistryV1 {
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
        authority_namespace: &str,
        authority_id: &str,
        statement_revision: &str,
    ) -> Option<&AuthorityRegistrationV1> {
        self.registrations.get(&registration_key(
            authority_namespace,
            authority_id,
            statement_revision,
        ))
    }

    #[allow(clippy::too_many_arguments)]
    pub fn register(
        &mut self,
        profile_id: &str,
        authority_namespace: &str,
        authority_id: &str,
        statement_revision: &str,
        eligible_account: &str,
        model_id: &str,
        model_version: &str,
        model_digest: &str,
        margin_rule_id: &str,
        jurisdiction: &str,
        subject_terms_digest: &str,
        economic_residual_digest: &str,
        recognized_numerator: &str,
        recognized_denominator: &str,
        issued_at: i64,
        expires_at: i64,
        statement_digest: &str,
    ) -> Result<AuthorityRegistrationV1, AuthorityErrorV1> {
        if self.registrations.len() >= MAX_REGISTRATIONS_V1 {
            return Err(AuthorityErrorV1::TooManyRegistrations);
        }
        for field in [
            profile_id,
            authority_namespace,
            authority_id,
            statement_revision,
            eligible_account,
            model_id,
            model_version,
            model_digest,
            margin_rule_id,
            jurisdiction,
            subject_terms_digest,
            economic_residual_digest,
            recognized_numerator,
            recognized_denominator,
            statement_digest,
        ] {
            if field.len() > MAX_FIELD_BYTES_V1 {
                return Err(AuthorityErrorV1::NoncanonicalIdentifier);
            }
        }

        let key = registration_key(authority_namespace, authority_id, statement_revision);
        if let Some(existing) = self.registrations.get(&key) {
            if existing.statement_digest != statement_digest {
                return Err(AuthorityErrorV1::ActiveRevisionConflict);
            }
            return Ok(existing.clone());
        }

        let status = StatementStatusV1::Active;
        let digest = registration_digest(
            authority_namespace,
            authority_id,
            statement_revision,
            statement_digest,
            status.as_str(),
        );
        let registration = AuthorityRegistrationV1 {
            schema_version: REGISTRATION_SCHEMA_V1.to_owned(),
            profile_id: profile_id.to_owned(),
            authority_namespace: authority_namespace.to_owned(),
            authority_id: authority_id.to_owned(),
            statement_revision: statement_revision.to_owned(),
            eligible_account: eligible_account.to_owned(),
            model_id: model_id.to_owned(),
            model_version: model_version.to_owned(),
            model_digest: model_digest.to_owned(),
            margin_rule_id: margin_rule_id.to_owned(),
            jurisdiction: jurisdiction.to_owned(),
            subject_terms_digest: subject_terms_digest.to_owned(),
            economic_residual_digest: economic_residual_digest.to_owned(),
            recognized_numerator: recognized_numerator.to_owned(),
            recognized_denominator: recognized_denominator.to_owned(),
            issued_at,
            expires_at,
            grants_execution_authority: false,
            status,
            statement_digest: statement_digest.to_owned(),
            registration_digest: digest_to_hex(digest),
        };
        self.registrations.insert(key, registration.clone());
        Ok(registration)
    }

    pub fn revoke(
        &mut self,
        authority_namespace: &str,
        authority_id: &str,
        statement_revision: &str,
    ) -> Result<AuthorityRegistrationV1, AuthorityErrorV1> {
        let key = registration_key(authority_namespace, authority_id, statement_revision);
        let Some(existing) = self.registrations.get_mut(&key) else {
            return Err(AuthorityErrorV1::StatementNotFound);
        };
        if existing.status == StatementStatusV1::Revoked {
            return Err(AuthorityErrorV1::AlreadyRevoked);
        }
        existing.status = StatementStatusV1::Revoked;
        existing.registration_digest = digest_to_hex(registration_digest(
            authority_namespace,
            authority_id,
            statement_revision,
            &existing.statement_digest,
            existing.status.as_str(),
        ));
        Ok(existing.clone())
    }
}
