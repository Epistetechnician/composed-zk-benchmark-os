use std::fmt;

use crate::bounds::MAX_IDENTIFIER_BYTES_V1;
use crate::error::{AdapterErrorV1, BundleErrorV1};
use crate::types::ExactRationalV1;
use serde::de::{self, Deserializer, MapAccess, SeqAccess, Visitor};
use serde::Deserialize;
use serde_json::{Map, Number, Value};

pub fn parse_strict_json(bytes: &[u8], context: &str) -> Result<Value, BundleErrorV1> {
    let text =
        std::str::from_utf8(bytes).map_err(|_| BundleErrorV1::MalformedJson(context.into()))?;
    let unique: UniqueValue = serde_json::from_str(text).map_err(|error| {
        let message = error.to_string();
        if message.contains("duplicate JSON key") {
            BundleErrorV1::DuplicateJsonKey(context.into())
        } else {
            BundleErrorV1::MalformedJson(context.into())
        }
    })?;
    Ok(unique.0)
}

pub fn parse_strict_json_adapter(bytes: &[u8]) -> Result<Value, AdapterErrorV1> {
    let text = std::str::from_utf8(bytes).map_err(|_| AdapterErrorV1::MalformedJson)?;
    let unique: UniqueValue = serde_json::from_str(text).map_err(|error| {
        let message = error.to_string();
        if message.contains("duplicate JSON key") {
            AdapterErrorV1::DuplicateJsonKey
        } else {
            AdapterErrorV1::MalformedJson
        }
    })?;
    Ok(unique.0)
}

struct UniqueValue(Value);

impl<'de> Deserialize<'de> for UniqueValue {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_any(UniqueValueVisitor)
    }
}

struct UniqueValueVisitor;

impl<'de> Visitor<'de> for UniqueValueVisitor {
    type Value = UniqueValue;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a JSON value without duplicate object keys")
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Bool(value)))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Number(Number::from(value))))
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Number(Number::from(value))))
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::String(value.to_owned())))
    }

    fn visit_string<E>(self, value: String) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::String(value)))
    }

    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Null))
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Null))
    }

    fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element::<UniqueValue>()? {
            values.push(value.0);
        }
        Ok(UniqueValue(Value::Array(values)))
    }

    fn visit_map<A>(self, mut access: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut values = Map::new();
        while let Some(key) = access.next_key::<String>()? {
            if values.contains_key(&key) {
                return Err(de::Error::custom(format!("duplicate JSON key: {key}")));
            }
            let value = access.next_value::<UniqueValue>()?;
            values.insert(key, value.0);
        }
        Ok(UniqueValue(Value::Object(values)))
    }
}

pub fn validate_digest_hex(value: &str, context: &str) -> Result<(), BundleErrorV1> {
    if value.len() != 64 {
        return Err(BundleErrorV1::NoncanonicalDigest(context.into()));
    }
    if !value
        .bytes()
        .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(BundleErrorV1::NoncanonicalDigest(context.into()));
    }
    Ok(())
}

pub fn validate_digest_hex_adapter(value: &str) -> Result<(), AdapterErrorV1> {
    if value.len() != 64 {
        return Err(AdapterErrorV1::NoncanonicalDigest);
    }
    if !value
        .bytes()
        .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(AdapterErrorV1::NoncanonicalDigest);
    }
    Ok(())
}

pub fn validate_identifier(value: &str, context: &str) -> Result<(), BundleErrorV1> {
    if value.is_empty() || value.len() > MAX_IDENTIFIER_BYTES_V1 {
        return Err(BundleErrorV1::NoncanonicalIdentifier(context.into()));
    }
    if !value
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
    {
        return Err(BundleErrorV1::NoncanonicalIdentifier(context.into()));
    }
    Ok(())
}

pub fn validate_identifier_adapter(value: &str) -> Result<(), AdapterErrorV1> {
    if value.is_empty() || value.len() > MAX_IDENTIFIER_BYTES_V1 {
        return Err(AdapterErrorV1::NoncanonicalIdentifier);
    }
    if !value
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
    {
        return Err(AdapterErrorV1::NoncanonicalIdentifier);
    }
    Ok(())
}

pub fn validate_exact_rational(
    value: &ExactRationalV1,
    context: &str,
) -> Result<(), BundleErrorV1> {
    if value.numerator.is_empty() || value.denominator.is_empty() {
        return Err(BundleErrorV1::MalformedJson(context.into()));
    }
    if !value
        .numerator
        .bytes()
        .all(|byte| byte.is_ascii_digit() || byte == b'-')
        || !value.denominator.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(BundleErrorV1::MalformedJson(context.into()));
    }
    if value.denominator == "0" {
        return Err(BundleErrorV1::MalformedJson(context.into()));
    }
    Ok(())
}

pub fn reject_secret_retention(bytes: &[u8]) -> Result<(), BundleErrorV1> {
    let text = std::str::from_utf8(bytes).unwrap_or("");
    let forbidden = [
        "response_body",
        "raw_response",
        "api_key",
        "\"secret\"",
        "password",
        "private_key",
    ];
    for token in forbidden {
        if text.contains(token) {
            return Err(BundleErrorV1::SecretRetention);
        }
    }
    Ok(())
}

pub fn require_string(value: &Value, field: &str, context: &str) -> Result<String, BundleErrorV1> {
    value
        .get(field)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| BundleErrorV1::MalformedJson(format!("{context}.{field}")))
}

pub fn require_string_adapter(value: &Value, field: &str) -> Result<String, AdapterErrorV1> {
    value
        .get(field)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| AdapterErrorV1::MissingField(field.into()))
}

pub fn reject_unknown_fields(
    value: &Value,
    allowed: &[&str],
    context: &str,
) -> Result<(), BundleErrorV1> {
    let Some(object) = value.as_object() else {
        return Err(BundleErrorV1::MalformedJson(context.into()));
    };
    for key in object.keys() {
        if !allowed.contains(&key.as_str()) {
            return Err(BundleErrorV1::MalformedJson(format!(
                "{context}.unknown:{key}"
            )));
        }
    }
    Ok(())
}

pub fn reject_unknown_fields_adapter(
    value: &Value,
    allowed: &[&str],
) -> Result<(), AdapterErrorV1> {
    let Some(object) = value.as_object() else {
        return Err(AdapterErrorV1::MalformedJson);
    };
    for key in object.keys() {
        if !allowed.contains(&key.as_str()) {
            return Err(AdapterErrorV1::UnknownField(key.clone()));
        }
    }
    Ok(())
}

pub fn canonical_json(value: &Value) -> Result<Vec<u8>, BundleErrorV1> {
    serde_json::to_vec(value).map_err(|_| BundleErrorV1::MalformedJson("serialize".into()))
}
