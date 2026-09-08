use crate::{Digest, JournalBlocker, JournalState, ReplayJournal};
use serde_json::Error as JsonError;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum JournalStorageError {
    InvalidPath,
    NotFound,
    AlreadyExists,
    TemporaryArtifactExists,
    Io(String),
    Serialization(String),
    JournalAppendRejected(JournalBlocker),
    NonCanonicalBytes,
    InvalidJournal,
    TipMismatch {
        expected: Option<Digest>,
        actual: Option<Digest>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReplayJournalFileStore {
    path: PathBuf,
}

impl ReplayJournalFileStore {
    pub fn new(path: impl Into<PathBuf>) -> Result<Self, JournalStorageError> {
        let path = path.into();
        if path.as_os_str().is_empty() {
            return Err(JournalStorageError::InvalidPath);
        }
        Ok(Self { path })
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn read(&self) -> Result<ReplayJournal, JournalStorageError> {
        self.read_optional()?.ok_or(JournalStorageError::NotFound)
    }

    pub fn initialize(&self, journal: &ReplayJournal) -> Result<(), JournalStorageError> {
        if self.read_optional()?.is_some() {
            return Err(JournalStorageError::AlreadyExists);
        }
        self.write_atomically(journal)
    }

    pub fn replace_if_tip(
        &self,
        expected_tip: Option<Digest>,
        journal: &ReplayJournal,
    ) -> Result<(), JournalStorageError> {
        validate_journal(journal)?;
        let actual_tip = self
            .read_optional()?
            .and_then(|current| current.tip_digest());
        if actual_tip != expected_tip {
            return Err(JournalStorageError::TipMismatch {
                expected: expected_tip,
                actual: actual_tip,
            });
        }
        self.write_atomically(journal)
    }

    pub fn append_if_tip(
        &self,
        expected_tip: Option<Digest>,
        proposal_digest: Digest,
        receipt_digest: Digest,
        permit_digest: Digest,
        nonce: u64,
        state: JournalState,
    ) -> Result<ReplayJournal, JournalStorageError> {
        let current = self.read()?;
        let next = current
            .append_if_tip(
                expected_tip,
                proposal_digest,
                receipt_digest,
                permit_digest,
                nonce,
                state,
            )
            .map_err(JournalStorageError::JournalAppendRejected)?;
        self.replace_if_tip(current.tip_digest(), &next)?;
        Ok(next)
    }

    fn read_optional(&self) -> Result<Option<ReplayJournal>, JournalStorageError> {
        let bytes = match fs::read(&self.path) {
            Ok(bytes) => bytes,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let temporary_path = self.temporary_path();
                let temporary_bytes = match fs::read(&temporary_path) {
                    Ok(bytes) => bytes,
                    Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
                    Err(error) => return Err(io_error("read temporary journal", error)),
                };
                let journal = decode_and_validate(&temporary_bytes)?;
                fs::rename(&temporary_path, &self.path)
                    .map_err(|error| io_error("recover temporary journal", error))?;
                return Ok(Some(journal));
            }
            Err(error) => return Err(io_error("read journal", error)),
        };
        decode_and_validate(&bytes).map(Some)
    }

    fn write_atomically(&self, journal: &ReplayJournal) -> Result<(), JournalStorageError> {
        validate_journal(journal)?;
        let bytes = serde_json::to_vec(journal).map_err(serialization_error)?;
        let temporary_path = self.temporary_path();
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary_path)
            .map_err(|error| {
                if error.kind() == std::io::ErrorKind::AlreadyExists {
                    JournalStorageError::TemporaryArtifactExists
                } else {
                    io_error("create temporary journal", error)
                }
            })?;
        if let Err(error) = file.write_all(&bytes).and_then(|_| file.sync_all()) {
            let _ = fs::remove_file(&temporary_path);
            return Err(io_error("write temporary journal", error));
        }
        drop(file);
        if let Err(error) = fs::rename(&temporary_path, &self.path) {
            let _ = fs::remove_file(&temporary_path);
            return Err(io_error("replace journal", error));
        }
        Ok(())
    }

    fn temporary_path(&self) -> PathBuf {
        let mut temporary = self.path.as_os_str().to_os_string();
        temporary.push(".tmp");
        PathBuf::from(temporary)
    }
}

fn validate_journal(journal: &ReplayJournal) -> Result<(), JournalStorageError> {
    if journal.validate().is_empty() {
        Ok(())
    } else {
        Err(JournalStorageError::InvalidJournal)
    }
}

fn decode_and_validate(bytes: &[u8]) -> Result<ReplayJournal, JournalStorageError> {
    let journal: ReplayJournal = serde_json::from_slice(bytes).map_err(serialization_error)?;
    validate_journal(&journal)?;
    let canonical = serde_json::to_vec(&journal).map_err(serialization_error)?;
    if canonical != bytes {
        return Err(JournalStorageError::NonCanonicalBytes);
    }
    Ok(journal)
}

fn serialization_error(error: JsonError) -> JournalStorageError {
    JournalStorageError::Serialization(error.to_string())
}

fn io_error(operation: &str, error: std::io::Error) -> JournalStorageError {
    JournalStorageError::Io(format!("{operation}: {error}"))
}
