use crate::{
    PhalaManagedVerifierError, PhalaManagedVerifierRequest, PhalaManagedVerifierResponse,
    PhalaOperatorLiveClient, PhalaOperatorLiveCredential, PhalaOperatorLiveCredentialProvider,
    PhalaOperatorLiveInvocationError, PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::io::Read;
use std::time::Duration;

/// Feature-gated provider-client configuration.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveProviderConfig {
    pub endpoint: String,
    pub timeout_seconds: u64,
    pub allowed_credential_sources: BTreeSet<String>,
}

impl PhalaOperatorLiveProviderConfig {
    pub fn new(
        endpoint: impl Into<String>,
        timeout_seconds: u64,
        allowed_credential_sources: BTreeSet<String>,
    ) -> Self {
        Self {
            endpoint: endpoint.into(),
            timeout_seconds,
            allowed_credential_sources,
        }
    }

    pub fn validate(&self) -> Result<(), PhalaOperatorLiveProviderError> {
        if self.endpoint.trim().is_empty() {
            return Err(PhalaOperatorLiveProviderError::EmptyEndpoint);
        }
        if self.timeout_seconds == 0
            || self.timeout_seconds > PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS
        {
            return Err(PhalaOperatorLiveProviderError::TimeoutOutOfBounds {
                actual: self.timeout_seconds,
                max: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
            });
        }
        if self.allowed_credential_sources.is_empty() {
            return Err(PhalaOperatorLiveProviderError::MissingAllowedCredentialSource);
        }
        Ok(())
    }
}

/// Raw provider response after transport, before normalization.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveRawResponse {
    pub status_code: u16,
    pub body: Vec<u8>,
}

impl PhalaOperatorLiveRawResponse {
    pub fn sha256(&self) -> Vec<u8> {
        Sha256::digest(&self.body).to_vec()
    }
}

/// Feature-gated transport seam. Tests use fake transports; real HTTP is opt-in.
pub trait PhalaOperatorLiveTransport {
    fn post_json(
        &self,
        endpoint: &str,
        bearer_token: &[u8],
        timeout_seconds: u64,
        body: &[u8],
    ) -> Result<PhalaOperatorLiveRawResponse, PhalaOperatorLiveProviderError>;
}

/// Blocking HTTP transport for operator-owned live runs.
#[derive(Clone, Debug, Default)]
pub struct UreqPhalaOperatorLiveTransport;

impl PhalaOperatorLiveTransport for UreqPhalaOperatorLiveTransport {
    fn post_json(
        &self,
        endpoint: &str,
        bearer_token: &[u8],
        timeout_seconds: u64,
        body: &[u8],
    ) -> Result<PhalaOperatorLiveRawResponse, PhalaOperatorLiveProviderError> {
        let bearer_token = std::str::from_utf8(bearer_token)
            .map_err(|_| PhalaOperatorLiveProviderError::CredentialNotUtf8)?;
        let agent = ureq::AgentBuilder::new()
            .timeout(Duration::from_secs(timeout_seconds))
            .redirects(0)
            .build();
        let response = agent
            .post(endpoint)
            .set("Content-Type", "application/json")
            .set("Authorization", &format!("Bearer {bearer_token}"))
            .send_bytes(body);
        match response {
            Ok(response) => {
                let status_code = response.status();
                let mut reader = response.into_reader();
                let mut body = Vec::new();
                reader
                    .read_to_end(&mut body)
                    .map_err(|_| PhalaOperatorLiveProviderError::TransportUnavailable)?;
                Ok(PhalaOperatorLiveRawResponse { status_code, body })
            }
            Err(ureq::Error::Status(status_code, response)) => {
                let mut reader = response.into_reader();
                let mut body = Vec::new();
                let _ = reader.read_to_end(&mut body);
                Ok(PhalaOperatorLiveRawResponse { status_code, body })
            }
            Err(ureq::Error::Transport(_)) => {
                Err(PhalaOperatorLiveProviderError::TransportUnavailable)
            }
        }
    }
}

/// Explicit process-environment credential provider for operator-owned runs.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaEnvCredentialProvider {
    pub allowed_sources: BTreeSet<String>,
}

impl PhalaEnvCredentialProvider {
    pub fn new(allowed_sources: BTreeSet<String>) -> Self {
        Self { allowed_sources }
    }
}

impl PhalaOperatorLiveCredentialProvider for PhalaEnvCredentialProvider {
    fn load(
        &self,
        source_id: &str,
    ) -> Result<PhalaOperatorLiveCredential, PhalaOperatorLiveInvocationError> {
        let env_name = source_id.strip_prefix("env:").ok_or_else(|| {
            PhalaOperatorLiveInvocationError::CredentialUnavailable(source_id.to_owned())
        })?;
        if !self.allowed_sources.contains(source_id) {
            return Err(PhalaOperatorLiveInvocationError::CredentialUnavailable(
                source_id.to_owned(),
            ));
        }
        let value = std::env::var(env_name).map_err(|_| {
            PhalaOperatorLiveInvocationError::CredentialUnavailable(source_id.to_owned())
        })?;
        PhalaOperatorLiveCredential::new(source_id.to_owned(), value.into_bytes())
    }
}

/// Concrete Phala/dstack provider client behind the Phase 100 injected seam.
#[derive(Clone, Debug)]
pub struct PhalaOperatorLiveProviderClient<T> {
    pub config: PhalaOperatorLiveProviderConfig,
    pub transport: T,
}

impl<T> PhalaOperatorLiveProviderClient<T> {
    pub fn new(config: PhalaOperatorLiveProviderConfig, transport: T) -> Self {
        Self { config, transport }
    }
}

impl<T: PhalaOperatorLiveTransport> PhalaOperatorLiveClient for PhalaOperatorLiveProviderClient<T> {
    fn verify_with_credential(
        &self,
        request: &PhalaManagedVerifierRequest,
        credential: &PhalaOperatorLiveCredential,
    ) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError> {
        self.config
            .validate()
            .map_err(PhalaOperatorLiveProviderError::into_managed_error)?;
        if !self
            .config
            .allowed_credential_sources
            .contains(credential.source_id())
        {
            return Err(PhalaManagedVerifierError::ClientUnavailable);
        }
        let body = serde_json::to_vec(request)
            .map_err(|_| PhalaManagedVerifierError::MalformedResponse)?;
        let raw = self
            .transport
            .post_json(
                &self.config.endpoint,
                credential.secret_bytes(),
                self.config.timeout_seconds,
                &body,
            )
            .map_err(PhalaOperatorLiveProviderError::into_managed_error)?;
        normalize_provider_response(raw)
    }
}

/// Provider-client-specific fail-closed errors.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PhalaOperatorLiveProviderError {
    EmptyEndpoint,
    TimeoutOutOfBounds { actual: u64, max: u64 },
    MissingAllowedCredentialSource,
    CredentialNotUtf8,
    TransportUnavailable,
}

impl PhalaOperatorLiveProviderError {
    fn into_managed_error(self) -> PhalaManagedVerifierError {
        match self {
            Self::EmptyEndpoint
            | Self::TimeoutOutOfBounds { .. }
            | Self::MissingAllowedCredentialSource => PhalaManagedVerifierError::ClientUnavailable,
            Self::CredentialNotUtf8 => PhalaManagedVerifierError::AuthenticationFailed,
            Self::TransportUnavailable => PhalaManagedVerifierError::TransportUnavailable,
        }
    }
}

impl std::fmt::Display for PhalaOperatorLiveProviderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

impl std::error::Error for PhalaOperatorLiveProviderError {}

fn normalize_provider_response(
    raw: PhalaOperatorLiveRawResponse,
) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError> {
    match raw.status_code {
        200..=299 => {
            let raw_digest = raw.sha256();
            let mut response: PhalaManagedVerifierResponse = serde_json::from_slice(&raw.body)
                .map_err(|_| PhalaManagedVerifierError::MalformedResponse)?;
            response.raw_response_digest = raw_digest;
            Ok(response)
        }
        401 | 403 => Err(PhalaManagedVerifierError::AuthenticationFailed),
        status => Err(PhalaManagedVerifierError::UnexpectedHttpStatus(status)),
    }
}
