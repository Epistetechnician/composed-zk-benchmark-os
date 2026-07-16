use std::fmt;

use crate::bounds::MAX_IDENTIFIER_BYTES_V1;
use crate::error::AuthorityErrorV1;
use serde::de::{self, Deserializer, MapAccess, SeqAccess, Visitor};
use serde::Deserialize;
use serde_json::{Map, Number, Value};

pub fn parse_strict_json(bytes: &[u8]) -> Result<Value, AuthorityErrorV1> {
    let text = std::str::from_utf8(bytes).map_err(|_| AuthorityErrorV1::MalformedJson)?;
    let unique: UniqueValue = serde_json::from_str(text).map_err(|error| {
        let message = error.to_string();
        if message.contains("duplicate JSON key") {
            AuthorityErrorV1::DuplicateJsonKey
        } else {
            AuthorityErrorV1::MalformedJson
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

pub fn require_string(value: &Value, field: &str) -> Result<String, AuthorityErrorV1> {
    value
        .get(field)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| AuthorityErrorV1::MissingField(field.into()))
}

pub fn require_i64(value: &Value, field: &str) -> Result<i64, AuthorityErrorV1> {
    value
        .get(field)
        .and_then(Value::as_i64)
        .ok_or_else(|| AuthorityErrorV1::MissingField(field.into()))
}

pub fn require_bool(value: &Value, field: &str) -> Result<bool, AuthorityErrorV1> {
    value
        .get(field)
        .and_then(Value::as_bool)
        .ok_or_else(|| AuthorityErrorV1::MissingField(field.into()))
}

pub fn reject_unknown_fields(value: &Value, allowed: &[&str]) -> Result<(), AuthorityErrorV1> {
    let Some(object) = value.as_object() else {
        return Err(AuthorityErrorV1::MalformedJson);
    };
    for key in object.keys() {
        if !allowed.contains(&key.as_str()) {
            return Err(AuthorityErrorV1::UnknownField(key.clone()));
        }
    }
    Ok(())
}

pub fn validate_identifier(value: &str) -> Result<(), AuthorityErrorV1> {
    if value.is_empty() || value.len() > MAX_IDENTIFIER_BYTES_V1 {
        return Err(AuthorityErrorV1::NoncanonicalIdentifier);
    }
    if !value
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
    {
        return Err(AuthorityErrorV1::NoncanonicalIdentifier);
    }
    Ok(())
}

pub fn validate_digest_hex(value: &str) -> Result<(), AuthorityErrorV1> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(AuthorityErrorV1::NoncanonicalDigest);
    }
    Ok(())
}

pub fn validate_rational(numerator: &str, denominator: &str) -> Result<(), AuthorityErrorV1> {
    if numerator.is_empty()
        || denominator.is_empty()
        || !numerator.bytes().all(|byte| byte.is_ascii_digit())
        || !denominator.bytes().all(|byte| byte.is_ascii_digit())
        || denominator == "0"
        || numerator.len() > MAX_IDENTIFIER_BYTES_V1
        || denominator.len() > MAX_IDENTIFIER_BYTES_V1
    {
        return Err(AuthorityErrorV1::NoncanonicalRational);
    }
    Ok(())
}

pub fn read_string_array(value: &Value, field: &str) -> Result<Vec<String>, AuthorityErrorV1> {
    let Some(array) = value.get(field).and_then(Value::as_array) else {
        return Ok(Vec::new());
    };
    let mut out = Vec::new();
    for item in array {
        let text = item.as_str().ok_or(AuthorityErrorV1::MalformedJson)?;
        validate_identifier(text)?;
        out.push(text.to_owned());
    }
    Ok(out)
}
