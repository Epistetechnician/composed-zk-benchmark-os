//! Caller-owned file persistence for the off-chain event log.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-offchain-journal-v1`.
//! This module only persists and replays local bytes. It does not create
//! authority, call a provider, connect to a market, or move value.

use crate::{encode_event_log, replay_projection, OffchainBlocker, OffchainMarketLog};
use hsai_control_plane::Digest;
use hsai_outcome_work_market::MarketStatus;
use serde_json::Error as JsonError;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EventLogStorageError {
    InvalidPath,
    NotFound,
    AlreadyExists,
    StaleTemporaryArtifact,
    Io(String),
    Serialization(String),
    NonCanonicalBytes,
    InvalidEventLog(Vec<OffchainBlocker>),
    Stale {
        expected: Option<Digest>,
        actual: Option<Digest>,
    },
    ReadbackDigestMismatch {
        expected: Digest,
        actual: Digest,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct OffchainMarketLogFileStore {
    path: PathBuf,
}

impl OffchainMarketLogFileStore {
    pub fn new(path: impl Into<PathBuf>) -> Result<Self, EventLogStorageError> {
        let path = path.into();
        if path.as_os_str().is_empty() {
            return Err(EventLogStorageError::InvalidPath);
        }
        Ok(Self { path })
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn read(&self) -> Result<OffchainMarketLog, EventLogStorageError> {
        self.read_optional()?.ok_or(EventLogStorageError::NotFound)
    }

    pub fn read_if_digest(
        &self,
        expected: &Digest,
    ) -> Result<OffchainMarketLog, EventLogStorageError> {
        let log = self.read()?;
        let actual = log.digest();
        if &actual != expected {
            return Err(EventLogStorageError::ReadbackDigestMismatch {
                expected: expected.clone(),
                actual,
            });
        }
        Ok(log)
    }

    pub fn initialize(&self, log: &OffchainMarketLog) -> Result<(), EventLogStorageError> {
        if self.read_optional()?.is_some() {
            return Err(EventLogStorageError::AlreadyExists);
        }
        self.write_atomically(log)
    }

    pub fn replace_if_digest(
        &self,
        expected: Option<Digest>,
        log: &OffchainMarketLog,
    ) -> Result<(), EventLogStorageError> {
        let current = self.read_optional()?;
        let actual = current.as_ref().map(OffchainMarketLog::digest);
        if actual != expected {
            return Err(EventLogStorageError::Stale { expected, actual });
        }
        self.write_atomically(log)
    }

    fn read_optional(&self) -> Result<Option<OffchainMarketLog>, EventLogStorageError> {
        let bytes = match fs::read(&self.path) {
            Ok(bytes) => bytes,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                if self.temporary_exists()? {
                    return Err(EventLogStorageError::StaleTemporaryArtifact);
                }
                return Ok(None);
            }
            Err(error) => return Err(io_error("read event log", error)),
        };
        decode_and_validate(&bytes).map(Some)
    }

    fn write_atomically(&self, log: &OffchainMarketLog) -> Result<(), EventLogStorageError> {
        validate_event_log(log)?;
        let bytes = encode_event_log(log).map_err(EventLogStorageError::InvalidEventLog)?;
        let expected = log.digest();
        let temporary_path = self.temporary_path();
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary_path)
            .map_err(|error| {
                if error.kind() == std::io::ErrorKind::AlreadyExists {
                    EventLogStorageError::StaleTemporaryArtifact
                } else {
                    io_error("create temporary event log", error)
                }
            })?;
        if let Err(error) = file.write_all(&bytes).and_then(|_| file.sync_all()) {
            let _ = fs::remove_file(&temporary_path);
            return Err(io_error("write temporary event log", error));
        }
        drop(file);
        if let Err(error) = fs::rename(&temporary_path, &self.path) {
            let _ = fs::remove_file(&temporary_path);
            return Err(io_error("replace event log", error));
        }

        let readback =
            fs::read(&self.path).map_err(|error| io_error("read back event log", error))?;
        let readback_log = decode_and_validate(&readback)?;
        let actual = readback_log.digest();
        if actual != expected {
            return Err(EventLogStorageError::ReadbackDigestMismatch { expected, actual });
        }
        Ok(())
    }

    fn temporary_path(&self) -> PathBuf {
        let mut temporary = self.path.as_os_str().to_os_string();
        temporary.push(".tmp");
        PathBuf::from(temporary)
    }

    fn temporary_exists(&self) -> Result<bool, EventLogStorageError> {
        match fs::metadata(self.temporary_path()) {
            Ok(_) => Ok(true),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(false),
            Err(error) => Err(io_error("inspect temporary event log", error)),
        }
    }
}

fn validate_event_log(log: &OffchainMarketLog) -> Result<(), EventLogStorageError> {
    if log.market.status != MarketStatus::Open {
        return Err(EventLogStorageError::InvalidEventLog(vec![
            OffchainBlocker::MarketNotOpen,
        ]));
    }
    if log.events.is_empty() {
        return Ok(());
    }
    replay_projection(log)
        .map(|_| ())
        .map_err(EventLogStorageError::InvalidEventLog)
}

fn decode_and_validate(bytes: &[u8]) -> Result<OffchainMarketLog, EventLogStorageError> {
    let log: OffchainMarketLog = serde_json::from_slice(bytes).map_err(serialization_error)?;
    let canonical = encode_event_log(&log).map_err(EventLogStorageError::InvalidEventLog)?;
    if canonical != bytes {
        return Err(EventLogStorageError::NonCanonicalBytes);
    }
    validate_event_log(&log)?;
    Ok(log)
}

fn serialization_error(error: JsonError) -> EventLogStorageError {
    EventLogStorageError::Serialization(error.to_string())
}

fn io_error(operation: &str, error: std::io::Error) -> EventLogStorageError {
    EventLogStorageError::Io(format!("{operation}: {error}"))
}
