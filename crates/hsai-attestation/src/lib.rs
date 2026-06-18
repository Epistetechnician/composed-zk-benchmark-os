//! Attestation-verification lane — the capstone of the trust stack.
//!
//! Since L2, every distinctness envelope from the distinct-agent lane has
//! carried one open assumption: that the anchor is valid
//! (`Anchor::validity_assumption(subject)`). This lane discharges it. It turns a
//! managed attestation [`Token`] for an anchor into a `ClaimEnvelope` that
//! GUARANTEES that exact anchor-validity predicate, so `conjoin`-ing the two
//! removes the assumption and makes the distinctness envelope admissible under a
//! `require_closed` policy for the first time in the build.
//!
//! # Honesty boundary (the whole point of this phase)
//!
//! This is attestation at the *interface* level. The reference
//! [`ManagedTokenVerifier`] checks the token's anchor id, nonce, report-data
//! binding, measurements, and freshness, but does **not** cryptographically verify
//! the managed attestation service's signature over the token (an Azure
//! Attestation / Intel Trust Authority JWT against the service JWKS, or a vendor
//! quote against its root cert). That signature check is the single real
//! integration step and the point at which the stack leaves the pure-data regime.
//! It is deliberately out of scope here, and is the clean seam the
//! [`AttestationVerifier`] trait marks.
//!
//! Therefore:
//! - a verified attestation is `Attested`, never `Proven`;
//! - discharging anchor-validity establishes hardware-bounded distinctness only
//!   (ledger A4b), not competence or safety;
//! - a rejected input contributes no guarantee and no trust root;
//! - an expired token never verifies.
//!
//! [`Anchor`]: hsai_distinct_agent::Anchor

use hsai_agent_case::{AgentCase, EvidenceLane};
use hsai_claim_envelope::{ClaimEnvelope, LaneId, Maturity, TimeWindow, TrustRoot, VkId};
use hsai_distinct_agent::Anchor;
use p256::ecdsa::{signature::Verifier, Signature, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

/// A managed attestation token. Pure data until a verifier accepts it.
///
/// `[not_before, not_after]` is the token's validity window (inclusive).
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct Token {
    /// Optional compact managed-attestation JWT carrying the same fields.
    ///
    /// The reference [`ManagedTokenVerifier`] ignores this field. Signature
    /// verifying backends require it and reject tokens whose local fields do not
    /// match the signed claims.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signed_jwt: Option<String>,
    /// Which anchor this token attests; must equal the `Anchor`'s id.
    pub anchor_id: String,
    /// Anti-replay nonce.
    pub nonce: u64,
    /// Provider custom-data binding. For Phala/dstack this maps to reportData.
    pub report_data: Vec<u8>,
    /// Measured code/firmware digest.
    pub measurements: Vec<u8>,
    /// Inclusive start of the validity window.
    pub not_before: u64,
    /// Inclusive end of the validity window.
    pub not_after: u64,
}

/// A token a verifier accepted. Carries only the fields a downstream lane needs.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct VerifiedAttestation {
    /// The attested anchor id.
    pub anchor_id: String,
    /// Inclusive start of the accepted window.
    pub not_before: u64,
    /// Inclusive end of the accepted window.
    pub not_after: u64,
    /// Trust roots relied on by the verifier backend itself.
    ///
    /// Anchor trust roots are still emitted separately by [`AttestationLane`].
    /// Signature-verifying backends use this field to disclose the accepted
    /// managed verifier key or provider root.
    #[serde(default, skip_serializing_if = "BTreeSet::is_empty")]
    pub verifier_trust_roots: BTreeSet<TrustRoot>,
}

/// Why a token failed verification.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum VerifyError {
    /// `token.anchor_id` did not match the anchor being checked.
    AnchorMismatch,
    /// `token.nonce` did not match the expected nonce.
    NonceMismatch,
    /// `token.measurements` did not match the expected measurements.
    MeasurementMismatch,
    /// `token.report_data` did not match the expected report-data binding.
    ReportDataMismatch,
    /// `now` was outside `[not_before, not_after]`.
    Expired,
    /// Reserved for real signature-verifying backends. The reference
    /// [`ManagedTokenVerifier`] NEVER returns this — it does not check the
    /// managed service signature.
    SignatureUnverified,
}

/// A backend that decides whether a [`Token`] verifies.
///
/// A real backend FIRST verifies the managed service's signature over the token,
/// then the fields below. The reference impl verifies only the fields, and is
/// the seam where a signature-verifying backend drops in.
pub trait AttestationVerifier {
    /// Verify `token` for `anchor_id` at time `now` against the expected nonce
    /// and measurements.
    fn verify(
        &self,
        token: &Token,
        expected_nonce: u64,
        expected_report_data: &[u8],
        expected_measurements: &[u8],
        anchor_id: &str,
        now: u64,
    ) -> Result<VerifiedAttestation, VerifyError>;
}

/// The reference attestation backend.
///
/// Returns `Ok` iff `token.anchor_id == anchor_id`, `token.nonce ==
/// expected_nonce`, `token.report_data == expected_report_data`,
/// `token.measurements == expected_measurements`, and `not_before <= now <=
/// not_after`. It does **not** verify the managed service signature and never
/// returns [`VerifyError::SignatureUnverified`].
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ManagedTokenVerifier;

impl AttestationVerifier for ManagedTokenVerifier {
    fn verify(
        &self,
        token: &Token,
        expected_nonce: u64,
        expected_report_data: &[u8],
        expected_measurements: &[u8],
        anchor_id: &str,
        now: u64,
    ) -> Result<VerifiedAttestation, VerifyError> {
        if token.anchor_id != anchor_id {
            return Err(VerifyError::AnchorMismatch);
        }
        if token.nonce != expected_nonce {
            return Err(VerifyError::NonceMismatch);
        }
        if token.report_data != expected_report_data {
            return Err(VerifyError::ReportDataMismatch);
        }
        if token.measurements != expected_measurements {
            return Err(VerifyError::MeasurementMismatch);
        }
        if now < token.not_before || now > token.not_after {
            return Err(VerifyError::Expired);
        }
        // DEFERRED REAL STEP: the managed service signature is not verified here.
        // The lane below therefore caps maturity at Attested, never Proven.
        Ok(VerifiedAttestation {
            anchor_id: token.anchor_id.clone(),
            not_before: token.not_before,
            not_after: token.not_after,
            verifier_trust_roots: BTreeSet::new(),
        })
    }
}

/// One local ES256 verification key for a managed attestation JWT issuer.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ManagedJwtEs256Key {
    /// JWT `kid` accepted for this key.
    pub kid: String,
    /// P-256 public key x-coordinate, 32 bytes.
    pub x: Vec<u8>,
    /// P-256 public key y-coordinate, 32 bytes.
    pub y: Vec<u8>,
    /// Verifying-key trust root disclosed when this key accepts a token.
    pub trust_root: TrustRoot,
}

impl ManagedJwtEs256Key {
    /// Construct a local ES256 key and its default verifying-key trust root.
    pub fn new(kid: impl Into<String>, x: Vec<u8>, y: Vec<u8>) -> Self {
        let kid = kid.into();
        let trust_root = TrustRoot::VerifyingKey(VkId(format!("managed-jwt-es256:{kid}")));
        Self {
            kid,
            x,
            y,
            trust_root,
        }
    }
}

/// Offline managed-JWT verifier for one issuer and one verification mode.
///
/// This backend performs local ES256 signature verification against an in-memory
/// key set. It does not fetch JWKS, call a managed attestation service, verify
/// DCAP quotes, use network access, or emit `Proven`.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ManagedJwtVerifier {
    /// Required JWT issuer.
    pub issuer: String,
    keys_by_kid: BTreeMap<String, ManagedJwtEs256Key>,
}

impl ManagedJwtVerifier {
    /// Build a verifier from an expected issuer and local ES256 keys.
    pub fn new(issuer: impl Into<String>, keys: Vec<ManagedJwtEs256Key>) -> Self {
        Self {
            issuer: issuer.into(),
            keys_by_kid: keys.into_iter().map(|key| (key.kid.clone(), key)).collect(),
        }
    }

    fn verify_signature(
        &self,
        header: &ManagedJwtHeader,
        signing_input: &str,
        signature: &[u8],
    ) -> Result<&ManagedJwtEs256Key, VerifyError> {
        if header.alg != "ES256" {
            return Err(VerifyError::SignatureUnverified);
        }
        let key = self
            .keys_by_kid
            .get(&header.kid)
            .ok_or(VerifyError::SignatureUnverified)?;
        if key.x.len() != 32 || key.y.len() != 32 {
            return Err(VerifyError::SignatureUnverified);
        }

        let mut sec1 = Vec::with_capacity(65);
        sec1.push(0x04);
        sec1.extend_from_slice(&key.x);
        sec1.extend_from_slice(&key.y);
        let verifying_key =
            VerifyingKey::from_sec1_bytes(&sec1).map_err(|_| VerifyError::SignatureUnverified)?;
        let signature =
            Signature::from_slice(signature).map_err(|_| VerifyError::SignatureUnverified)?;
        verifying_key
            .verify(signing_input.as_bytes(), &signature)
            .map_err(|_| VerifyError::SignatureUnverified)?;
        Ok(key)
    }
}

impl AttestationVerifier for ManagedJwtVerifier {
    fn verify(
        &self,
        token: &Token,
        expected_nonce: u64,
        expected_report_data: &[u8],
        expected_measurements: &[u8],
        anchor_id: &str,
        now: u64,
    ) -> Result<VerifiedAttestation, VerifyError> {
        let signed_jwt = token
            .signed_jwt
            .as_deref()
            .ok_or(VerifyError::SignatureUnverified)?;
        let parsed = parse_managed_jwt(signed_jwt)?;
        let key =
            self.verify_signature(&parsed.header, &parsed.signing_input, &parsed.signature)?;
        let claims = parsed.claims;

        if claims.iss != self.issuer {
            return Err(VerifyError::SignatureUnverified);
        }
        if now < claims.nbf || now > claims.exp {
            return Err(VerifyError::Expired);
        }
        if claims.anchor_id != anchor_id || token.anchor_id != claims.anchor_id {
            return Err(VerifyError::AnchorMismatch);
        }
        if claims.nonce != expected_nonce || token.nonce != claims.nonce {
            return Err(VerifyError::NonceMismatch);
        }

        let report_data =
            decode_hex(&claims.report_data_hex).map_err(|_| VerifyError::SignatureUnverified)?;
        if report_data != expected_report_data || token.report_data != report_data {
            return Err(VerifyError::ReportDataMismatch);
        }

        let measurements =
            decode_hex(&claims.measurements_hex).map_err(|_| VerifyError::SignatureUnverified)?;
        if measurements != expected_measurements || token.measurements != measurements {
            return Err(VerifyError::MeasurementMismatch);
        }
        if token.not_before != claims.nbf || token.not_after != claims.exp {
            return Err(VerifyError::SignatureUnverified);
        }

        Ok(VerifiedAttestation {
            anchor_id: claims.anchor_id,
            not_before: claims.nbf,
            not_after: claims.exp,
            verifier_trust_roots: BTreeSet::from([key.trust_root.clone()]),
        })
    }
}

#[derive(Debug, Deserialize)]
struct ManagedJwtHeader {
    alg: String,
    kid: String,
}

#[derive(Debug, Deserialize)]
struct ManagedJwtClaims {
    iss: String,
    anchor_id: String,
    nonce: u64,
    report_data_hex: String,
    measurements_hex: String,
    nbf: u64,
    exp: u64,
}

struct ParsedManagedJwt {
    header: ManagedJwtHeader,
    claims: ManagedJwtClaims,
    signing_input: String,
    signature: Vec<u8>,
}

fn parse_managed_jwt(jwt: &str) -> Result<ParsedManagedJwt, VerifyError> {
    let mut parts = jwt.split('.');
    let header_b64 = parts.next().ok_or(VerifyError::SignatureUnverified)?;
    let claims_b64 = parts.next().ok_or(VerifyError::SignatureUnverified)?;
    let signature_b64 = parts.next().ok_or(VerifyError::SignatureUnverified)?;
    if parts.next().is_some() {
        return Err(VerifyError::SignatureUnverified);
    }

    let header = serde_json::from_slice(&base64url_decode(header_b64)?)
        .map_err(|_| VerifyError::SignatureUnverified)?;
    let claims = serde_json::from_slice(&base64url_decode(claims_b64)?)
        .map_err(|_| VerifyError::SignatureUnverified)?;
    let signature = base64url_decode(signature_b64)?;
    let signing_input = format!("{header_b64}.{claims_b64}");

    Ok(ParsedManagedJwt {
        header,
        claims,
        signing_input,
        signature,
    })
}

fn base64url_decode(input: &str) -> Result<Vec<u8>, VerifyError> {
    let mut out = Vec::new();
    let mut buffer = 0_u32;
    let mut bits = 0_u8;

    for byte in input.bytes() {
        if byte == b'=' {
            return Err(VerifyError::SignatureUnverified);
        }
        let value = match byte {
            b'A'..=b'Z' => byte - b'A',
            b'a'..=b'z' => byte - b'a' + 26,
            b'0'..=b'9' => byte - b'0' + 52,
            b'-' => 62,
            b'_' => 63,
            _ => return Err(VerifyError::SignatureUnverified),
        } as u32;
        buffer = (buffer << 6) | value;
        bits += 6;
        while bits >= 8 {
            bits -= 8;
            out.push(((buffer >> bits) & 0xff) as u8);
        }
    }

    let mask = if bits == 0 { 0 } else { (1_u32 << bits) - 1 };
    if buffer & mask != 0 {
        return Err(VerifyError::SignatureUnverified);
    }
    Ok(out)
}

fn decode_hex(input: &str) -> Result<Vec<u8>, ()> {
    if input.len() % 2 != 0 {
        return Err(());
    }
    input
        .as_bytes()
        .chunks_exact(2)
        .map(|pair| {
            let hi = hex_nibble(pair[0])?;
            let lo = hex_nibble(pair[1])?;
            Ok((hi << 4) | lo)
        })
        .collect()
}

fn hex_nibble(byte: u8) -> Result<u8, ()> {
    match byte {
        b'0'..=b'9' => Ok(byte - b'0'),
        b'a'..=b'f' => Ok(byte - b'a' + 10),
        b'A'..=b'F' => Ok(byte - b'A' + 10),
        _ => Err(()),
    }
}

/// Compute the HSAI report-data binding for managed attestation providers.
///
/// The profile binds the provider custom-data field to the exact agent public
/// key, nonce, and case hash being admitted. Length prefixes avoid ambiguous
/// concatenations while preserving the PRD's `agent_pubkey || nonce ||
/// case_hash` intent.
pub fn report_data_binding(agent_pubkey: &[u8], nonce: u64, case_hash: &[u8]) -> Vec<u8> {
    let mut hasher = Sha256::new();
    hasher.update(b"hsai-attestation-report-data:v1");
    hasher.update((agent_pubkey.len() as u64).to_be_bytes());
    hasher.update(agent_pubkey);
    hasher.update(nonce.to_be_bytes());
    hasher.update((case_hash.len() as u64).to_be_bytes());
    hasher.update(case_hash);
    hasher.finalize().to_vec()
}

/// One attestation to evaluate: an anchor, its token, and the expectations the
/// verifier checks the token against.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AttestationInput {
    /// The anchor being attested.
    pub anchor: Anchor,
    /// The managed token claiming to attest `anchor`.
    pub token: Token,
    /// The nonce the verifier expects in the token.
    pub expected_nonce: u64,
    /// The provider custom-data binding the verifier expects in the token.
    pub expected_report_data: Vec<u8>,
    /// The measurements the verifier expects in the token.
    pub expected_measurements: Vec<u8>,
}

/// The attestation evidence lane, parameterized over a verifier backend.
///
/// Each accepted input contributes its anchor's validity predicate as a
/// guarantee and its trust root; the emitted valid window is the meet
/// (intersection) of the accepted tokens' windows. If nothing verifies, the lane
/// claims nothing (an honest `Stub`).
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AttestationLane<V: AttestationVerifier> {
    /// The verifier backend.
    pub verifier: V,
    /// The attestations to evaluate.
    pub inputs: Vec<AttestationInput>,
}

impl<V: AttestationVerifier> AttestationLane<V> {
    /// Construct a lane from a verifier and a set of inputs.
    pub fn new(verifier: V, inputs: Vec<AttestationInput>) -> Self {
        Self { verifier, inputs }
    }
}

impl<V: AttestationVerifier> EvidenceLane for AttestationLane<V> {
    fn id(&self) -> LaneId {
        LaneId::Named("attestation".to_owned())
    }

    fn ceiling(&self) -> Maturity {
        Maturity::Attested
    }

    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
        let now = case.observed_at;
        let mut guarantees = BTreeSet::new();
        let mut trust_roots = BTreeSet::new();
        let mut window = TimeWindow::all();

        for input in &self.inputs {
            if let Ok(verified) = self.verifier.verify(
                &input.token,
                input.expected_nonce,
                &input.expected_report_data,
                &input.expected_measurements,
                &input.anchor.anchor_id(),
                now,
            ) {
                guarantees.insert(input.anchor.validity_assumption(&case.subject));
                trust_roots.insert(input.anchor.trust_root());
                trust_roots.extend(verified.verifier_trust_roots);
                window = window.intersect(&TimeWindow {
                    start: verified.not_before,
                    end: verified.not_after,
                });
            }
        }

        if guarantees.is_empty() {
            // Nothing verified: claim nothing, honest Stub.
            ClaimEnvelope::new(
                BTreeSet::new(),
                BTreeSet::new(),
                case.oracle.excluded.clone(),
                Maturity::Stub,
                BTreeSet::new(),
                TimeWindow::all(),
                self.id(),
            )
        } else {
            // The emitted guarantee is exactly `Anchor::validity_assumption(subject)`
            // — the distinct-agent open assumption — so `conjoin` discharges it.
            ClaimEnvelope::new(
                guarantees,
                BTreeSet::new(),
                case.oracle.excluded.clone(),
                Maturity::Attested,
                trust_roots,
                window,
                self.id(),
            )
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{ActionId, MemoryRoot, ModelId, OracleContract, Verdict};
    use hsai_claim_envelope::{admits, conjoin, AcceptancePolicy, SubjectId};
    use hsai_distinct_agent::{distinctness, AnchorBundle, DistinctAgentLane};
    use p256::ecdsa::{signature::Signer, SigningKey};
    use proptest::collection::{btree_set, vec as pvec};
    use proptest::prelude::*;
    use serde_json::json;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn hw_anchor() -> Anchor {
        Anchor::HardwareAttested {
            vendor: "nvidia".to_owned(),
            device: "devX".to_owned(),
        }
    }

    fn fixture_case(observed_at: u64) -> AgentCase {
        AgentCase {
            action: ActionId("action1".to_owned()),
            subject: subject("agentA"),
            claimed_model: ModelId("modelA".to_owned()),
            memory_root: MemoryRoot([7; 32]),
            observed_at,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([distinctness(&subject("agentA"))]),
                excluded: BTreeSet::new(),
            },
        }
    }

    fn good_token() -> Token {
        Token {
            signed_jwt: None,
            anchor_id: hw_anchor().anchor_id(),
            nonce: 42,
            report_data: report_data_binding(b"agent-pubkey", 42, b"case-hash"),
            measurements: vec![1, 2, 3],
            not_before: 100,
            not_after: 300,
        }
    }

    fn good_input() -> AttestationInput {
        AttestationInput {
            anchor: hw_anchor(),
            token: good_token(),
            expected_nonce: 42,
            expected_report_data: report_data_binding(b"agent-pubkey", 42, b"case-hash"),
            expected_measurements: vec![1, 2, 3],
        }
    }

    fn jwt_key(seed: u8, kid: &str) -> (SigningKey, ManagedJwtEs256Key) {
        let bytes = [seed; 32];
        let signing_key = SigningKey::from_bytes((&bytes).into()).expect("valid test key");
        let encoded = signing_key.verifying_key().to_encoded_point(false);
        let x = encoded.x().expect("uncompressed point has x").to_vec();
        let y = encoded.y().expect("uncompressed point has y").to_vec();
        (signing_key, ManagedJwtEs256Key::new(kid, x, y))
    }

    fn base64url_encode(input: &[u8]) -> String {
        const ALPHABET: &[u8; 64] =
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
        let mut out = String::new();
        for chunk in input.chunks(3) {
            let b0 = chunk[0];
            let b1 = *chunk.get(1).unwrap_or(&0);
            let b2 = *chunk.get(2).unwrap_or(&0);
            let triple = ((b0 as u32) << 16) | ((b1 as u32) << 8) | b2 as u32;
            out.push(ALPHABET[((triple >> 18) & 0x3f) as usize] as char);
            out.push(ALPHABET[((triple >> 12) & 0x3f) as usize] as char);
            if chunk.len() > 1 {
                out.push(ALPHABET[((triple >> 6) & 0x3f) as usize] as char);
            }
            if chunk.len() > 2 {
                out.push(ALPHABET[(triple & 0x3f) as usize] as char);
            }
        }
        out
    }

    fn hex_encode(input: &[u8]) -> String {
        input.iter().map(|byte| format!("{byte:02x}")).collect()
    }

    struct JwtFixture {
        signing_key: SigningKey,
        key: ManagedJwtEs256Key,
        token: Token,
        input: AttestationInput,
    }

    fn signed_jwt(
        signing_key: &SigningKey,
        kid: &str,
        alg: &str,
        issuer: &str,
        token: &Token,
    ) -> String {
        let header = serde_json::to_vec(&json!({
            "alg": alg,
            "kid": kid,
            "typ": "JWT",
        }))
        .expect("header serializes");
        let claims = serde_json::to_vec(&json!({
            "iss": issuer,
            "anchor_id": token.anchor_id,
            "nonce": token.nonce,
            "report_data_hex": hex_encode(&token.report_data),
            "measurements_hex": hex_encode(&token.measurements),
            "nbf": token.not_before,
            "exp": token.not_after,
        }))
        .expect("claims serialize");
        let signing_input = format!(
            "{}.{}",
            base64url_encode(&header),
            base64url_encode(&claims)
        );
        let signature: Signature = signing_key.sign(signing_input.as_bytes());
        let signature_bytes = signature.to_bytes();
        format!(
            "{}.{}",
            signing_input,
            base64url_encode(signature_bytes.as_ref())
        )
    }

    fn jwt_fixture(issuer: &str, kid: &str) -> JwtFixture {
        let (signing_key, key) = jwt_key(7, kid);
        let mut token = good_token();
        token.signed_jwt = Some(signed_jwt(&signing_key, kid, "ES256", issuer, &token));
        let input = AttestationInput {
            anchor: hw_anchor(),
            token: token.clone(),
            expected_nonce: 42,
            expected_report_data: report_data_binding(b"agent-pubkey", 42, b"case-hash"),
            expected_measurements: vec![1, 2, 3],
        };
        JwtFixture {
            signing_key,
            key,
            token,
            input,
        }
    }

    fn jwt_verifier(issuer: &str, key: ManagedJwtEs256Key) -> ManagedJwtVerifier {
        ManagedJwtVerifier::new(issuer, vec![key])
    }

    fn lane(inputs: Vec<AttestationInput>) -> AttestationLane<ManagedTokenVerifier> {
        AttestationLane::new(ManagedTokenVerifier, inputs)
    }

    fn verify_input(
        input: &AttestationInput,
        now: u64,
    ) -> Result<VerifiedAttestation, VerifyError> {
        ManagedTokenVerifier.verify(
            &input.token,
            input.expected_nonce,
            &input.expected_report_data,
            &input.expected_measurements,
            &input.anchor.anchor_id(),
            now,
        )
    }

    // AT-1: a verified token guarantees anchor validity, Attested, with the
    // vendor trust root and the token window.
    #[test]
    fn at_1_verified_token_guarantees_anchor_validity() {
        let case = fixture_case(150);
        let env = lane(vec![good_input()]).evaluate(&case);

        assert_eq!(
            env.guarantees,
            BTreeSet::from([hw_anchor().validity_assumption(&case.subject)])
        );
        assert!(env.assumptions.is_empty());
        assert_eq!(env.excludes, case.oracle.excluded);
        assert_eq!(env.maturity, Maturity::Attested);
        assert!(env.maturity < Maturity::Proven); // never Proven
        assert_eq!(env.trust_roots, BTreeSet::from([hw_anchor().trust_root()]));
        assert_eq!(
            env.valid,
            TimeWindow {
                start: 100,
                end: 300
            }
        );
    }

    // AT-2: the capstone — distinctness finally closes and is admitted.
    #[test]
    fn at_2_capstone_distinctness_closes_and_is_admitted() {
        let case = fixture_case(150);
        let bundle = AnchorBundle(BTreeSet::from([hw_anchor()]));

        let distinct_env = DistinctAgentLane::new(bundle).evaluate(&case);
        let attestation_env = lane(vec![good_input()]).evaluate(&case);
        let closed = conjoin(distinct_env, attestation_env);

        assert_eq!(
            closed.guarantees,
            BTreeSet::from([
                distinctness(&case.subject),
                hw_anchor().validity_assumption(&case.subject),
            ])
        );
        assert!(closed.assumptions.is_empty()); // discharged — CLOSED
        assert_eq!(closed.maturity, Maturity::Attested);
        assert_eq!(
            closed.trust_roots,
            BTreeSet::from([hw_anchor().trust_root()])
        );

        let require_closed = AcceptancePolicy {
            require: BTreeSet::from([distinctness(&case.subject)]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::new(),
            require_closed: true,
            at: 150,
        };
        assert_eq!(admits(require_closed, closed), Ok(()));
    }

    // AT-3: nonce mismatch -> verify Err(NonceMismatch) -> lane guarantees nothing.
    #[test]
    fn at_3_nonce_mismatch_guarantees_nothing() {
        let case = fixture_case(150);
        let mut input = good_input();
        input.expected_nonce = 999;

        assert_eq!(
            verify_input(&input, case.observed_at),
            Err(VerifyError::NonceMismatch)
        );

        let env = lane(vec![input]).evaluate(&case);
        assert!(env.guarantees.is_empty());
        assert!(env.trust_roots.is_empty());
        assert_eq!(env.maturity, Maturity::Stub);
    }

    // AT-4: now > not_after -> verify Err(Expired) -> lane guarantees nothing.
    #[test]
    fn at_4_expired_guarantees_nothing() {
        let case = fixture_case(400); // window is [100, 300]
        let input = good_input();

        assert_eq!(
            verify_input(&input, case.observed_at),
            Err(VerifyError::Expired)
        );

        let env = lane(vec![input]).evaluate(&case);
        assert!(env.guarantees.is_empty());
        assert_eq!(env.maturity, Maturity::Stub);
    }

    // AT-5: measurement mismatch -> verify Err(MeasurementMismatch) -> nothing.
    #[test]
    fn at_5_measurement_mismatch_guarantees_nothing() {
        let case = fixture_case(150);
        let mut input = good_input();
        input.expected_measurements = vec![9, 9];

        assert_eq!(
            verify_input(&input, case.observed_at),
            Err(VerifyError::MeasurementMismatch)
        );

        let env = lane(vec![input]).evaluate(&case);
        assert!(env.guarantees.is_empty());
        assert_eq!(env.maturity, Maturity::Stub);
    }

    // AT-6: report-data mismatch -> verify Err(ReportDataMismatch) -> nothing.
    #[test]
    fn at_6_report_data_mismatch_guarantees_nothing() {
        let case = fixture_case(150);
        let mut input = good_input();
        input.expected_report_data = report_data_binding(b"other-agent-pubkey", 42, b"case-hash");

        assert_eq!(
            verify_input(&input, case.observed_at),
            Err(VerifyError::ReportDataMismatch)
        );

        let env = lane(vec![input]).evaluate(&case);
        assert!(env.guarantees.is_empty());
        assert_eq!(env.maturity, Maturity::Stub);
    }

    #[test]
    fn report_data_binding_is_deterministic_and_domain_separated() {
        let left = report_data_binding(b"agent-pubkey", 42, b"case-hash");
        let right = report_data_binding(b"agent-pubkey", 42, b"case-hash");
        let changed_nonce = report_data_binding(b"agent-pubkey", 43, b"case-hash");
        let ambiguous_concat = report_data_binding(b"agent", 42, b"-pubkeycase-hash");

        assert_eq!(left, right);
        assert_eq!(left.len(), 32);
        assert_ne!(left, changed_nonce);
        assert_ne!(left, ambiguous_concat);
    }

    // The reference verifier reports anchor mismatch and never claims to have
    // verified a signature.
    #[test]
    fn anchor_mismatch_and_signature_never_unverified() {
        let case = fixture_case(150);
        let mut input = good_input();
        input.token.anchor_id = "hw:other:dev".to_owned();

        let result = verify_input(&input, case.observed_at);
        assert_eq!(result, Err(VerifyError::AnchorMismatch));
        assert_ne!(result, Err(VerifyError::SignatureUnverified));
        assert!(lane(vec![input]).evaluate(&case).guarantees.is_empty());
    }

    #[test]
    fn managed_jwt_verifier_closes_distinctness_and_discloses_key_root() {
        let issuer = "https://managed.example/issuer";
        let fixture = jwt_fixture(issuer, "kid-1");
        let case = fixture_case(150);
        let verifier = jwt_verifier(issuer, fixture.key.clone());

        let env = AttestationLane::new(verifier, vec![fixture.input.clone()]).evaluate(&case);

        assert_eq!(env.maturity, Maturity::Attested);
        assert!(env.maturity < Maturity::Proven);
        assert_eq!(
            env.guarantees,
            BTreeSet::from([hw_anchor().validity_assumption(&case.subject)])
        );
        assert_eq!(
            env.trust_roots,
            BTreeSet::from([hw_anchor().trust_root(), fixture.key.trust_root.clone()])
        );

        let closed = conjoin(
            DistinctAgentLane::new(AnchorBundle(BTreeSet::from([hw_anchor()]))).evaluate(&case),
            env,
        );
        assert!(closed.assumptions.is_empty());
        assert_eq!(closed.maturity, Maturity::Attested);
        assert_eq!(
            admits(
                AcceptancePolicy {
                    require: BTreeSet::from([distinctness(&case.subject)]),
                    min_maturity: Maturity::Attested,
                    forbid_roots: BTreeSet::new(),
                    require_closed: true,
                    at: 150,
                },
                closed,
            ),
            Ok(())
        );
    }

    #[test]
    fn managed_jwt_rejects_bad_signature_algorithm_kid_and_issuer() {
        let issuer = "https://managed.example/issuer";
        let fixture = jwt_fixture(issuer, "kid-1");
        let verifier = jwt_verifier(issuer, fixture.key.clone());

        let mut bad_sig = fixture.token.clone();
        let signed = bad_sig.signed_jwt.as_mut().expect("jwt present");
        signed.pop();
        signed.push('A');
        assert_eq!(
            verifier.verify(
                &bad_sig,
                42,
                &fixture.input.expected_report_data,
                &fixture.input.expected_measurements,
                &hw_anchor().anchor_id(),
                150,
            ),
            Err(VerifyError::SignatureUnverified)
        );

        let mut bad_alg = good_token();
        bad_alg.signed_jwt = Some(signed_jwt(
            &fixture.signing_key,
            "kid-1",
            "HS256",
            issuer,
            &bad_alg,
        ));
        assert_eq!(
            verifier.verify(
                &bad_alg,
                42,
                &fixture.input.expected_report_data,
                &fixture.input.expected_measurements,
                &hw_anchor().anchor_id(),
                150,
            ),
            Err(VerifyError::SignatureUnverified)
        );

        let mut unknown_kid = good_token();
        unknown_kid.signed_jwt = Some(signed_jwt(
            &fixture.signing_key,
            "kid-other",
            "ES256",
            issuer,
            &unknown_kid,
        ));
        assert_eq!(
            verifier.verify(
                &unknown_kid,
                42,
                &fixture.input.expected_report_data,
                &fixture.input.expected_measurements,
                &hw_anchor().anchor_id(),
                150,
            ),
            Err(VerifyError::SignatureUnverified)
        );

        let wrong_issuer = jwt_verifier("https://managed.example/other", fixture.key);
        assert_eq!(
            wrong_issuer.verify(
                &fixture.token,
                42,
                &fixture.input.expected_report_data,
                &fixture.input.expected_measurements,
                &hw_anchor().anchor_id(),
                150,
            ),
            Err(VerifyError::SignatureUnverified)
        );
    }

    #[test]
    fn managed_jwt_rejects_stale_and_mapping_mismatches_without_roots() {
        let issuer = "https://managed.example/issuer";
        let fixture = jwt_fixture(issuer, "kid-1");
        let verifier = jwt_verifier(issuer, fixture.key.clone());

        assert_eq!(
            verifier.verify(
                &fixture.token,
                42,
                &fixture.input.expected_report_data,
                &fixture.input.expected_measurements,
                &hw_anchor().anchor_id(),
                400,
            ),
            Err(VerifyError::Expired)
        );

        let mut wrong_report = fixture.input.clone();
        wrong_report.expected_report_data = report_data_binding(b"other", 42, b"case-hash");
        assert_eq!(
            verifier.verify(
                &wrong_report.token,
                wrong_report.expected_nonce,
                &wrong_report.expected_report_data,
                &wrong_report.expected_measurements,
                &wrong_report.anchor.anchor_id(),
                150,
            ),
            Err(VerifyError::ReportDataMismatch)
        );

        let mut wrong_measurement = fixture.input.clone();
        wrong_measurement.expected_measurements = vec![9, 9, 9];
        assert_eq!(
            verifier.verify(
                &wrong_measurement.token,
                wrong_measurement.expected_nonce,
                &wrong_measurement.expected_report_data,
                &wrong_measurement.expected_measurements,
                &wrong_measurement.anchor.anchor_id(),
                150,
            ),
            Err(VerifyError::MeasurementMismatch)
        );

        let mut wrong_anchor = fixture.input.clone();
        wrong_anchor.token.anchor_id = "hw:other:anchor".to_owned();
        assert_eq!(
            verifier.verify(
                &wrong_anchor.token,
                wrong_anchor.expected_nonce,
                &wrong_anchor.expected_report_data,
                &wrong_anchor.expected_measurements,
                &wrong_anchor.anchor.anchor_id(),
                150,
            ),
            Err(VerifyError::AnchorMismatch)
        );

        let rejected_env =
            AttestationLane::new(verifier, vec![wrong_measurement]).evaluate(&fixture_case(150));
        assert!(rejected_env.guarantees.is_empty());
        assert!(rejected_env.trust_roots.is_empty());
        assert_eq!(rejected_env.maturity, Maturity::Stub);
    }

    // --- ATI-1..5 invariants ---

    fn anchor_strategy() -> impl Strategy<Value = Anchor> {
        prop_oneof![
            (0_u8..4, 0_u8..4).prop_map(|(v, d)| Anchor::HardwareAttested {
                vendor: format!("vendor-{v}"),
                device: format!("device-{d}"),
            }),
            (0_u8..4, 0_u64..100).prop_map(|(s, a)| Anchor::Staked {
                stake: format!("stake-{s}"),
                amount: a,
            }),
            (0_u8..4, 0_u8..4).prop_map(|(i, c)| Anchor::HumanCredentialed {
                issuer: format!("issuer-{i}"),
                credential: format!("cred-{c}"),
            }),
        ]
    }

    fn bytes() -> impl Strategy<Value = Vec<u8>> {
        pvec(any::<u8>(), 0..4)
    }

    prop_compose! {
        fn input_strategy()(
            anchor in anchor_strategy(),
            token_nonce in 0_u64..8,
            expected_nonce in 0_u64..8,
            token_meas in bytes(),
            expected_meas in bytes(),
            report_data in bytes(),
            expected_report_data in bytes(),
            anchor_id_match in any::<bool>(),
            not_before in 0_u64..500,
            dur in 0_u64..500,
        ) -> AttestationInput {
            let anchor_id = if anchor_id_match {
                anchor.anchor_id()
            } else {
                format!("WRONG:{}", anchor.anchor_id())
            };
            AttestationInput {
                anchor,
                token: Token {
                    signed_jwt: None,
                    anchor_id,
                    nonce: token_nonce,
                    report_data,
                    measurements: token_meas,
                    not_before,
                    not_after: not_before + dur,
                },
                expected_nonce,
                expected_report_data,
                expected_measurements: expected_meas,
            }
        }
    }

    fn inputs_strategy() -> impl Strategy<Value = Vec<AttestationInput>> {
        pvec(input_strategy(), 0..5)
    }

    fn case_strategy() -> impl Strategy<Value = AgentCase> {
        (0_u8..4, 0_u64..1200).prop_map(|(s, observed_at)| AgentCase {
            action: ActionId("action".to_owned()),
            subject: SubjectId(format!("subject-{s}")),
            claimed_model: ModelId("model".to_owned()),
            memory_root: MemoryRoot([0; 32]),
            observed_at,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::new(),
                excluded: BTreeSet::new(),
            },
        })
    }

    prop_compose! {
        fn verifying_bundle_and_case()(
            anchors in btree_set(anchor_strategy(), 1..4),
            s in 0_u8..4,
            observed_at in 0_u64..1200,
        ) -> (AnchorBundle, AgentCase) {
            let case = AgentCase {
                action: ActionId("action".to_owned()),
                subject: SubjectId(format!("subject-{s}")),
                claimed_model: ModelId("model".to_owned()),
                memory_root: MemoryRoot([0; 32]),
                observed_at,
                oracle: OracleContract {
                    expected: Verdict::Accept,
                    target_guarantees: BTreeSet::new(),
                    excluded: BTreeSet::new(),
                },
            };
            (AnchorBundle(anchors), case)
        }
    }

    fn accepted(inputs: &[AttestationInput], now: u64) -> Vec<&AttestationInput> {
        inputs
            .iter()
            .filter(|input| verify_input(input, now).is_ok())
            .collect()
    }

    // Treats a window with start > end as empty (a subset of anything).
    fn window_subseteq(sub: &TimeWindow, sup: &TimeWindow) -> bool {
        sub.start > sub.end
            || (sup.start <= sup.end && sup.start <= sub.start && sub.end <= sup.end)
    }

    proptest! {
        // ATI-1: the lane never exceeds Attested (never Proven).
        #[test]
        fn ati_1_ceiling_never_proven(inputs in inputs_strategy(), case in case_strategy()) {
            let env = lane(inputs).evaluate(&case);
            prop_assert!(env.maturity <= Maturity::Attested);
        }

        // ATI-2: guarantees and trust roots come from exactly the accepted inputs;
        // rejected inputs add neither, and no assumption is emitted.
        #[test]
        fn ati_2_selective(inputs in inputs_strategy(), case in case_strategy()) {
            let env = lane(inputs.clone()).evaluate(&case);
            let acc = accepted(&inputs, case.observed_at);
            let expected_guarantees = acc
                .iter()
                .map(|input| input.anchor.validity_assumption(&case.subject))
                .collect::<BTreeSet<_>>();
            let expected_roots = acc
                .iter()
                .map(|input| input.anchor.trust_root())
                .collect::<BTreeSet<_>>();

            prop_assert_eq!(env.guarantees, expected_guarantees);
            prop_assert_eq!(env.trust_roots, expected_roots);
            prop_assert!(env.assumptions.is_empty());
        }

        // ATI-3: the emitted valid window is a subset of each accepted window.
        #[test]
        fn ati_3_window_subseteq_each_accepted(inputs in inputs_strategy(), case in case_strategy()) {
            let env = lane(inputs.clone()).evaluate(&case);
            for input in accepted(&inputs, case.observed_at) {
                let token_window = TimeWindow {
                    start: input.token.not_before,
                    end: input.token.not_after,
                };
                prop_assert!(window_subseteq(&env.valid, &token_window));
            }
        }

        // ATI-4: conjoining a verified attestation discharges the matching
        // anchor-validity assumption from the distinct-agent envelope.
        #[test]
        fn ati_4_discharge(bundle_and_case in verifying_bundle_and_case()) {
            let (bundle, case) = bundle_and_case;
            // One always-verifying input per anchor.
            let inputs = bundle
                .0
                .iter()
                .map(|anchor| AttestationInput {
                    anchor: anchor.clone(),
                    token: Token {
                        signed_jwt: None,
                        anchor_id: anchor.anchor_id(),
                        nonce: 1,
                        report_data: Vec::new(),
                        measurements: Vec::new(),
                        not_before: 0,
                        not_after: u64::MAX,
                    },
                    expected_nonce: 1,
                    expected_report_data: Vec::new(),
                    expected_measurements: Vec::new(),
                })
                .collect::<Vec<_>>();

            let distinct_env = DistinctAgentLane::new(bundle.clone()).evaluate(&case);
            let attestation_env = lane(inputs).evaluate(&case);
            let closed = conjoin(distinct_env, attestation_env);

            for anchor in &bundle.0 {
                prop_assert!(!closed
                    .assumptions
                    .contains(&anchor.validity_assumption(&case.subject)));
            }
            prop_assert!(closed.assumptions.is_empty());
        }

        // ATI-5: evaluate is deterministic (byte-identical envelopes).
        #[test]
        fn ati_5_deterministic(inputs in inputs_strategy(), case in case_strategy()) {
            let lane = lane(inputs);
            prop_assert_eq!(lane.evaluate(&case), lane.evaluate(&case));
        }
    }
}
