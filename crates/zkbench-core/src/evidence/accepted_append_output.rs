//! Materialized Phase W accepted-ledger append output.
//!
//! This module persists a guarded local accepted-ledger append to one explicit
//! caller-selected JSON ledger path. It does not submit to official endpoints,
//! run external replay, access credentials, or create Level2+ evidence.

use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::{
    apply_accepted_ledger_append_transaction, AcceptedLedgerAppendTransactionReport,
    AcceptedLedgerAppendTransactionRequest, EvidenceLedger,
};

/// Materialized accepted-ledger append request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MaterializedAcceptedLedgerAppendRequest {
    /// Explicit ledger JSON path.
    pub ledger_path: PathBuf,
    /// Whether a missing ledger file may be initialized as an empty ledger.
    pub create_if_missing: bool,
    /// Guarded append transaction.
    pub transaction: AcceptedLedgerAppendTransactionRequest,
}

/// Apply a guarded local append transaction to a materialized JSON ledger file.
pub fn apply_materialized_accepted_ledger_append_transaction(
    request: &MaterializedAcceptedLedgerAppendRequest,
) -> Result<AcceptedLedgerAppendTransactionReport> {
    validate_ledger_path(&request.ledger_path)?;
    let mut ledger = load_or_create_ledger(&request.ledger_path, request.create_if_missing)?;
    let report = apply_accepted_ledger_append_transaction(&request.transaction, &mut ledger)?;
    write_ledger_atomically(&request.ledger_path, &ledger)?;
    Ok(report)
}

fn load_or_create_ledger(path: &Path, create_if_missing: bool) -> Result<EvidenceLedger> {
    if path.exists() {
        if path.is_dir() {
            return Err(materialization_error(
                path,
                "accepted ledger path must be a JSON file, not a directory",
            ));
        }
        let ledger = EvidenceLedger::load_json(path)?;
        let validation = ledger.validate();
        if !validation.valid {
            return Err(materialization_error(
                path,
                format!(
                    "existing accepted ledger is invalid: {:?}",
                    validation.errors
                ),
            ));
        }
        Ok(ledger)
    } else if create_if_missing {
        Ok(EvidenceLedger::new())
    } else {
        Err(materialization_error(
            path,
            "accepted ledger file is missing and create_if_missing is false",
        ))
    }
}

fn write_ledger_atomically(path: &Path, ledger: &EvidenceLedger) -> Result<()> {
    let parent = path.parent().ok_or_else(|| {
        materialization_error(path, "accepted ledger path must have a parent directory")
    })?;
    let file_name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| {
            materialization_error(path, "accepted ledger path must have a valid file name")
        })?;
    let temp_path = parent.join(format!(".{file_name}.tmp"));
    if temp_path.exists() {
        fs::remove_file(&temp_path)
            .map_err(|error| materialization_error(&temp_path, error.to_string()))?;
    }
    ledger.save_json(&temp_path)?;
    fs::rename(&temp_path, path).map_err(|error| materialization_error(path, error.to_string()))?;
    Ok(())
}

fn validate_ledger_path(path: &Path) -> Result<()> {
    if path.as_os_str().is_empty() {
        return Err(materialization_error(
            path,
            "accepted ledger path must be non-empty",
        ));
    }
    if path
        .components()
        .any(|component| component == Component::ParentDir)
    {
        return Err(materialization_error(
            path,
            "accepted ledger path must not contain parent-directory components",
        ));
    }
    let parent = path.parent().ok_or_else(|| {
        materialization_error(path, "accepted ledger path must have a parent directory")
    })?;
    if !parent.exists() || !parent.is_dir() {
        return Err(materialization_error(
            parent,
            "accepted ledger parent directory must exist",
        ));
    }
    reject_symlink(parent)?;
    if path.exists() {
        reject_symlink(path)?;
    }
    Ok(())
}

fn reject_symlink(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| materialization_error(path, error.to_string()))?;
    if metadata.file_type().is_symlink() {
        return Err(materialization_error(
            path,
            "accepted ledger materialization path must not be a symlink",
        ));
    }
    Ok(())
}

fn materialization_error(path: &Path, message: impl Into<String>) -> ZkBenchError {
    ZkBenchError::evidence_ledger(path.display().to_string(), message.into())
}
