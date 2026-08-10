use crate::{ExecutableIdentityFact, HostExecutableRole, MachinePolicyCandidate};
use serde::{Deserialize, Serialize};
use std::fmt;

pub const MAX_EXECUTABLE_BYTES: u64 = 1_073_741_824;
pub const HASH_CHUNK_BYTES: usize = 65_536;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "class", rename_all = "snake_case")]
pub enum CollectorError {
    UnsupportedPlatform,
    UnsupportedFilesystem,
    InvalidPolicy,
    MissingRole,
    InvalidRequestedPath,
    InvalidAllowedRoot,
    OverlappingAllowedRoots,
    OutsideAllowedRoot,
    Io {
        operation: &'static str,
        raw_os_error: Option<i32>,
    },
    NotDirectory,
    NotSymlink,
    NonUtf8Symlink,
    SymlinkCycle,
    TooManySymlinkHops,
    RootEscape,
    EntryIdentityDrift,
    NotRegularFile,
    EmptyFile,
    FileTooLarge,
    UnsafeMode,
    OwnerRejected,
    EarlyEof,
    ContentGrowth,
    MetadataDrift,
    SymlinkDrift,
    DirectoryDrift,
    DigestRejected,
}

impl fmt::Display for CollectorError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io {
                operation,
                raw_os_error,
            } => write!(
                formatter,
                "descriptor-relative collector I/O failure during {operation} ({raw_os_error:?})"
            ),
            other => write!(
                formatter,
                "descriptor-relative collector rejected: {other:?}"
            ),
        }
    }
}

impl std::error::Error for CollectorError {}

pub fn collect_executable_identity_fact(
    policy: &MachinePolicyCandidate,
    role: HostExecutableRole,
) -> Result<ExecutableIdentityFact, CollectorError> {
    platform::collect(policy, role)
}

#[cfg(not(target_os = "macos"))]
mod platform {
    use super::*;

    pub(super) fn collect(
        _policy: &MachinePolicyCandidate,
        _role: HostExecutableRole,
    ) -> Result<ExecutableIdentityFact, CollectorError> {
        Err(CollectorError::UnsupportedPlatform)
    }
}

#[cfg(target_os = "macos")]
mod platform {
    use super::{CollectorError, HASH_CHUNK_BYTES, MAX_EXECUTABLE_BYTES};
    use crate::{
        machine_policy_entry_sha256, machine_policy_sha256, validate_machine_policy_candidate,
        ExecutableIdentityFact, HostExecutableRole, MachinePolicyCandidate, MetadataSnapshot,
        ObservedPlatformIdentity, ReviewDecision, SymlinkHop, EXECUTABLE_FACT_SCHEMA,
        MAX_SYMLINK_HOPS,
    };
    use rustix::fd::OwnedFd;
    use rustix::fs::{
        fstat, fstatfs, openat, readlinkat, statat, AtFlags, FileType, Mode, OFlags, Stat, CWD,
    };
    use sha2::{Digest, Sha256};
    use std::collections::BTreeSet;
    use std::ffi::OsString;
    use std::fs::File;
    use std::io::Read;
    use std::path::{Component, Path, PathBuf};

    #[derive(Clone)]
    struct EntryRecord {
        parent_index: usize,
        name: OsString,
        original: MetadataSnapshot,
        opened_index: Option<usize>,
    }

    #[derive(Clone)]
    struct SymlinkRecord {
        parent_index: usize,
        name: OsString,
        text: Vec<u8>,
        original: MetadataSnapshot,
    }

    struct TerminalRecord {
        parent_index: usize,
        name: OsString,
        original: MetadataSnapshot,
    }

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum Checkpoint {
        AfterEntryMetadata,
        AfterDirectoryOpen,
        AfterSymlinkRead,
        AfterTerminalOpen,
        DuringHash,
        AfterPostReadMetadata,
        BeforeFinalRecheck,
    }

    trait Hook {
        fn checkpoint(&self, _checkpoint: Checkpoint, _path: &Path) {}
    }

    struct NoopHook;

    impl Hook for NoopHook {}

    #[cfg(test)]
    impl<F> Hook for F
    where
        F: Fn(Checkpoint, &Path),
    {
        fn checkpoint(&self, checkpoint: Checkpoint, path: &Path) {
            self(checkpoint, path);
        }
    }

    pub(super) fn collect(
        policy: &MachinePolicyCandidate,
        role: HostExecutableRole,
    ) -> Result<ExecutableIdentityFact, CollectorError> {
        collect_with_hook(policy, role, &NoopHook)
    }

    fn collect_with_hook<H: Hook>(
        policy: &MachinePolicyCandidate,
        role: HostExecutableRole,
        hook: &H,
    ) -> Result<ExecutableIdentityFact, CollectorError> {
        let matching_entries = policy
            .entries
            .iter()
            .filter(|entry| entry.role_id == role)
            .collect::<Vec<_>>();
        let entry = match matching_entries.as_slice() {
            [entry] => *entry,
            _ => return Err(CollectorError::MissingRole),
        };
        let requested = checked_absolute_path(&entry.requested_path)
            .ok_or(CollectorError::InvalidRequestedPath)?;
        let allowed_roots = policy
            .allowed_roots
            .iter()
            .map(|root| checked_absolute_path(root).ok_or(CollectorError::InvalidAllowedRoot))
            .collect::<Result<Vec<_>, _>>()?;
        if allowed_roots.is_empty() {
            return Err(CollectorError::InvalidAllowedRoot);
        }
        reject_overlapping_roots(&allowed_roots)?;
        let selected = allowed_roots
            .iter()
            .filter(|root| requested.starts_with(root))
            .collect::<Vec<_>>();
        let selected_root = match selected.as_slice() {
            [root] => (*root).clone(),
            _ => return Err(CollectorError::OutsideAllowedRoot),
        };
        if !validate_machine_policy_candidate(policy).is_empty() {
            return Err(CollectorError::InvalidPolicy);
        }
        if policy.platform.os != "macos" || policy.platform.arch != std::env::consts::ARCH {
            return Err(CollectorError::InvalidPolicy);
        }

        let root_fd = io(
            "open_root",
            openat(
                CWD,
                "/",
                OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
                Mode::empty(),
            ),
        )?;
        require_local_filesystem(&root_fd)?;

        let mut descriptors = vec![root_fd];
        let mut directory_records = Vec::new();
        let selected_root_index =
            walk_directory_path(&selected_root, 0, &mut descriptors, &mut directory_records)?;
        require_local_filesystem(&descriptors[selected_root_index])?;

        let mut resolution = requested;
        let mut resolution_states = BTreeSet::new();
        resolution_states.insert(path_label(&resolution));
        let mut symlink_records = Vec::new();
        let mut hops = Vec::new();

        let (terminal_fd, terminal_record, resolved_label) = 'resolve: loop {
            let relative = resolution
                .strip_prefix(&selected_root)
                .map_err(|_| CollectorError::RootEscape)?;
            let components = normal_components(relative);
            let mut parent_index = selected_root_index;
            let mut containing_path = selected_root.clone();
            let mut followed_link = false;

            if components.is_empty() {
                return Err(CollectorError::NotRegularFile);
            }

            for (index, name) in components.iter().enumerate() {
                let terminal = index + 1 == components.len();
                let entry_stat = io(
                    "stat_entry",
                    statat(&descriptors[parent_index], name, AtFlags::SYMLINK_NOFOLLOW),
                )?;
                let entry_snapshot = snapshot(&entry_stat)?;
                let entry_type = FileType::from_raw_mode(entry_stat.st_mode);
                let entry_path = containing_path.join(name);
                hook.checkpoint(Checkpoint::AfterEntryMetadata, &entry_path);

                if entry_type.is_symlink() {
                    let link = match readlinkat(&descriptors[parent_index], name, Vec::new()) {
                        Ok(link) => link,
                        Err(error) if error == rustix::io::Errno::INVAL => {
                            return Err(CollectorError::NotSymlink);
                        }
                        Err(error) => {
                            return Err(CollectorError::Io {
                                operation: "read_symlink",
                                raw_os_error: Some(error.raw_os_error()),
                            });
                        }
                    };
                    let link_bytes = link.as_bytes().to_vec();
                    let link_text = std::str::from_utf8(&link_bytes)
                        .map_err(|_| CollectorError::NonUtf8Symlink)?
                        .to_string();
                    hook.checkpoint(Checkpoint::AfterSymlinkRead, &entry_path);
                    let remainder = components[index + 1..]
                        .iter()
                        .fold(PathBuf::new(), |path, component| path.join(component));
                    let base = if Path::new(&link_text).is_absolute() {
                        PathBuf::from(&link_text)
                    } else {
                        containing_path.join(&link_text)
                    };
                    let next = normalize_joined_path(&base, &remainder)?;
                    if !next.starts_with(&selected_root) {
                        return Err(CollectorError::RootEscape);
                    }
                    symlink_records.push(SymlinkRecord {
                        parent_index,
                        name: name.clone(),
                        text: link_bytes,
                        original: entry_snapshot,
                    });
                    hops.push(SymlinkHop {
                        containing_directory: path_label(&containing_path),
                        path: path_label(&entry_path),
                        link_text,
                        resolved_path: path_label(&next),
                    });
                    if hops.len() > MAX_SYMLINK_HOPS {
                        return Err(CollectorError::TooManySymlinkHops);
                    }
                    let state = path_label(&next);
                    if !resolution_states.insert(state) {
                        return Err(CollectorError::SymlinkCycle);
                    }
                    resolution = next;
                    followed_link = true;
                    break;
                }

                if terminal {
                    if !entry_type.is_file() {
                        return Err(CollectorError::NotRegularFile);
                    }
                    let fd = io(
                        "open_terminal",
                        openat(
                            &descriptors[parent_index],
                            name,
                            OFlags::RDONLY
                                | OFlags::NOFOLLOW
                                | OFlags::NONBLOCK
                                | OFlags::NOCTTY
                                | OFlags::CLOEXEC,
                            Mode::empty(),
                        ),
                    )?;
                    hook.checkpoint(Checkpoint::AfterTerminalOpen, &entry_path);
                    let opened = io("stat_terminal", fstat(&fd))?;
                    if !same_object(&entry_stat, &opened) {
                        return Err(CollectorError::EntryIdentityDrift);
                    }
                    break 'resolve (
                        fd,
                        TerminalRecord {
                            parent_index,
                            name: name.clone(),
                            original: entry_snapshot,
                        },
                        path_label(&entry_path),
                    );
                }

                if !entry_type.is_dir() {
                    return Err(CollectorError::NotDirectory);
                }
                let child = io(
                    "open_directory",
                    openat(
                        &descriptors[parent_index],
                        name,
                        OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
                        Mode::empty(),
                    ),
                )?;
                hook.checkpoint(Checkpoint::AfterDirectoryOpen, &entry_path);
                let child_stat = io("stat_directory", fstat(&child))?;
                if !same_object(&entry_stat, &child_stat) {
                    return Err(CollectorError::EntryIdentityDrift);
                }
                let child_index = descriptors.len();
                descriptors.push(child);
                directory_records.push(EntryRecord {
                    parent_index,
                    name: name.clone(),
                    original: entry_snapshot,
                    opened_index: Some(child_index),
                });
                parent_index = child_index;
                containing_path.push(name);
            }

            if followed_link {
                continue;
            }
        };

        require_local_filesystem(&terminal_fd)?;
        let terminal_stat = io("stat_terminal_before_read", fstat(&terminal_fd))?;
        if !FileType::from_raw_mode(terminal_stat.st_mode).is_file() {
            return Err(CollectorError::NotRegularFile);
        }
        let pre_read = snapshot(&terminal_stat)?;
        validate_terminal_metadata(&pre_read, &entry.allowed_owner_uids)?;

        let mut file = File::from(terminal_fd);
        let observed_sha256 = hash_exact_file(
            &mut file,
            pre_read.byte_length,
            hook,
            Path::new(&resolved_label),
        )?;
        let post_stat = io("stat_terminal_after_read", fstat(&file))?;
        let post_read = snapshot(&post_stat)?;
        hook.checkpoint(
            Checkpoint::AfterPostReadMetadata,
            Path::new(&resolved_label),
        );
        if !stable_metadata_unchanged(&pre_read, &post_read) {
            return Err(CollectorError::MetadataDrift);
        }

        hook.checkpoint(Checkpoint::BeforeFinalRecheck, Path::new(&resolved_label));
        recheck_symlinks(&descriptors, &symlink_records)?;
        recheck_directories(&descriptors, &directory_records)?;
        recheck_terminal(&descriptors, &terminal_record, &pre_read, &file)?;

        if entry
            .admitted_sha256
            .binary_search(&observed_sha256)
            .is_err()
        {
            return Err(CollectorError::DigestRejected);
        }

        Ok(ExecutableIdentityFact {
            schema: EXECUTABLE_FACT_SCHEMA.to_string(),
            role_id: role,
            registry_id: policy.registry_id.clone(),
            machine_policy_id: policy.policy_id.clone(),
            machine_policy_sha256: machine_policy_sha256(policy)
                .expect("serializing a Rust data structure cannot fail"),
            policy_entry_sha256: machine_policy_entry_sha256(entry)
                .expect("serializing a Rust data structure cannot fail"),
            acceptance_policy_id: entry.acceptance_policy_id.clone(),
            decision: ReviewDecision::Accepted,
            declared_platform: policy.platform.clone(),
            observed_platform: ObservedPlatformIdentity {
                os: "macos".to_string(),
                arch: std::env::consts::ARCH.to_string(),
            },
            requested_path: entry.requested_path.clone(),
            ordered_symlink_hops: hops,
            canonical_regular_file_path: resolved_label,
            observed_sha256,
            pre_read_metadata: pre_read,
            post_read_metadata: post_read,
        })
    }

    fn walk_directory_path(
        path: &Path,
        root_index: usize,
        descriptors: &mut Vec<OwnedFd>,
        records: &mut Vec<EntryRecord>,
    ) -> Result<usize, CollectorError> {
        let mut parent_index = root_index;
        for name in normal_components(path) {
            let entry = io(
                "stat_allowed_root",
                statat(&descriptors[parent_index], &name, AtFlags::SYMLINK_NOFOLLOW),
            )?;
            if !FileType::from_raw_mode(entry.st_mode).is_dir() {
                return Err(CollectorError::NotDirectory);
            }
            let child = io(
                "open_allowed_root",
                openat(
                    &descriptors[parent_index],
                    &name,
                    OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
                    Mode::empty(),
                ),
            )?;
            let opened = io("stat_allowed_root_descriptor", fstat(&child))?;
            if !same_object(&entry, &opened) {
                return Err(CollectorError::EntryIdentityDrift);
            }
            let child_index = descriptors.len();
            descriptors.push(child);
            records.push(EntryRecord {
                parent_index,
                name,
                original: snapshot(&entry)?,
                opened_index: Some(child_index),
            });
            parent_index = child_index;
        }
        Ok(parent_index)
    }

    fn checked_absolute_path(value: &str) -> Option<PathBuf> {
        if value.is_empty()
            || value.as_bytes().contains(&0)
            || value.contains("//")
            || value.contains("/./")
            || value.contains("/../")
            || value.ends_with("/.")
            || value.ends_with("/..")
            || (value.len() > 1 && value.ends_with('/'))
        {
            return None;
        }
        let path = Path::new(value);
        if !path.is_absolute()
            || !path
                .components()
                .all(|component| matches!(component, Component::RootDir | Component::Normal(_)))
        {
            return None;
        }
        Some(path.to_path_buf())
    }

    fn reject_overlapping_roots(roots: &[PathBuf]) -> Result<(), CollectorError> {
        if roots.iter().enumerate().any(|(index, root)| {
            roots
                .iter()
                .skip(index + 1)
                .any(|other| root.starts_with(other) || other.starts_with(root))
        }) {
            return Err(CollectorError::OverlappingAllowedRoots);
        }
        Ok(())
    }

    fn normalize_joined_path(base: &Path, remainder: &Path) -> Result<PathBuf, CollectorError> {
        let mut result = PathBuf::from("/");
        for component in base.components().chain(remainder.components()) {
            match component {
                Component::RootDir => result = PathBuf::from("/"),
                Component::CurDir => {}
                Component::ParentDir => {
                    if !result.pop() {
                        return Err(CollectorError::RootEscape);
                    }
                }
                Component::Normal(value) => result.push(value),
                Component::Prefix(_) => return Err(CollectorError::RootEscape),
            }
        }
        Ok(result)
    }

    fn normal_components(path: &Path) -> Vec<OsString> {
        path.components()
            .filter_map(|component| match component {
                Component::Normal(value) => Some(value.to_os_string()),
                _ => None,
            })
            .collect()
    }

    fn path_label(path: &Path) -> String {
        path.to_string_lossy().into_owned()
    }

    fn snapshot(stat: &Stat) -> Result<MetadataSnapshot, CollectorError> {
        let byte_length = u64::try_from(stat.st_size).map_err(|_| CollectorError::FileTooLarge)?;
        Ok(MetadataSnapshot {
            device: u64::from(stat.st_dev as u32),
            inode: stat.st_ino,
            mode: stat.st_mode as u32,
            owner_uid: stat.st_uid,
            link_count: stat.st_nlink as u64,
            byte_length,
            modified_seconds: stat.st_mtime,
            modified_nanoseconds: stat.st_mtime_nsec,
            changed_seconds: stat.st_ctime,
            changed_nanoseconds: stat.st_ctime_nsec,
        })
    }

    fn same_object(left: &Stat, right: &Stat) -> bool {
        left.st_dev == right.st_dev && left.st_ino == right.st_ino
    }

    fn validate_terminal_metadata(
        metadata: &MetadataSnapshot,
        owners: &[u32],
    ) -> Result<(), CollectorError> {
        if metadata.byte_length == 0 {
            return Err(CollectorError::EmptyFile);
        }
        if metadata.byte_length > MAX_EXECUTABLE_BYTES {
            return Err(CollectorError::FileTooLarge);
        }
        if metadata.mode & 0o7000 != 0 || metadata.mode & 0o022 != 0 || metadata.mode & 0o111 == 0 {
            return Err(CollectorError::UnsafeMode);
        }
        if owners.binary_search(&metadata.owner_uid).is_err() {
            return Err(CollectorError::OwnerRejected);
        }
        Ok(())
    }

    fn stable_metadata_unchanged(before: &MetadataSnapshot, after: &MetadataSnapshot) -> bool {
        before == after
    }

    fn hash_exact_file<H: Hook>(
        file: &mut File,
        length: u64,
        hook: &H,
        path: &Path,
    ) -> Result<String, CollectorError> {
        let mut remaining = length;
        let mut hasher = Sha256::new();
        let mut buffer = vec![0_u8; HASH_CHUNK_BYTES];
        while remaining > 0 {
            let wanted = remaining.min(HASH_CHUNK_BYTES as u64) as usize;
            let read = file
                .read(&mut buffer[..wanted])
                .map_err(|error| CollectorError::Io {
                    operation: "hash_terminal",
                    raw_os_error: error.raw_os_error(),
                })?;
            if read == 0 {
                return Err(CollectorError::EarlyEof);
            }
            hasher.update(&buffer[..read]);
            remaining -= read as u64;
            hook.checkpoint(Checkpoint::DuringHash, path);
        }
        let mut probe = [0_u8; 1];
        if file.read(&mut probe).map_err(|error| CollectorError::Io {
            operation: "probe_terminal_growth",
            raw_os_error: error.raw_os_error(),
        })? != 0
        {
            return Err(CollectorError::ContentGrowth);
        }
        Ok(hasher
            .finalize()
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect())
    }

    fn recheck_symlinks(
        descriptors: &[OwnedFd],
        records: &[SymlinkRecord],
    ) -> Result<(), CollectorError> {
        for record in records {
            let current = statat(
                &descriptors[record.parent_index],
                &record.name,
                AtFlags::SYMLINK_NOFOLLOW,
            )
            .map_err(|_| CollectorError::SymlinkDrift)?;
            if snapshot(&current)? != record.original
                || !FileType::from_raw_mode(current.st_mode).is_symlink()
            {
                return Err(CollectorError::SymlinkDrift);
            }
            let text = readlinkat(&descriptors[record.parent_index], &record.name, Vec::new())
                .map_err(|_| CollectorError::SymlinkDrift)?;
            if text.as_bytes() != record.text {
                return Err(CollectorError::SymlinkDrift);
            }
        }
        Ok(())
    }

    fn recheck_directories(
        descriptors: &[OwnedFd],
        records: &[EntryRecord],
    ) -> Result<(), CollectorError> {
        for record in records {
            let current_entry = statat(
                &descriptors[record.parent_index],
                &record.name,
                AtFlags::SYMLINK_NOFOLLOW,
            )
            .map_err(|_| CollectorError::DirectoryDrift)?;
            if snapshot(&current_entry)? != record.original {
                return Err(CollectorError::DirectoryDrift);
            }
            if let Some(opened_index) = record.opened_index {
                let current_opened = fstat(&descriptors[opened_index])
                    .map_err(|_| CollectorError::DirectoryDrift)?;
                if !same_object(&current_entry, &current_opened) {
                    return Err(CollectorError::DirectoryDrift);
                }
            }
        }
        Ok(())
    }

    fn recheck_terminal(
        descriptors: &[OwnedFd],
        record: &TerminalRecord,
        accepted: &MetadataSnapshot,
        file: &File,
    ) -> Result<(), CollectorError> {
        let current_entry = statat(
            &descriptors[record.parent_index],
            &record.name,
            AtFlags::SYMLINK_NOFOLLOW,
        )
        .map_err(|_| CollectorError::EntryIdentityDrift)?;
        if snapshot(&current_entry)? != record.original {
            return Err(CollectorError::EntryIdentityDrift);
        }
        let current_opened = fstat(file).map_err(|_| CollectorError::EntryIdentityDrift)?;
        if !same_object(&current_entry, &current_opened) || snapshot(&current_opened)? != *accepted
        {
            return Err(CollectorError::EntryIdentityDrift);
        }
        Ok(())
    }

    fn require_local_filesystem(fd: &OwnedFd) -> Result<(), CollectorError> {
        let stats = io("stat_filesystem", fstatfs(fd))?;
        if stats.f_flags & (libc::MNT_LOCAL as u32) == 0 {
            return Err(CollectorError::UnsupportedFilesystem);
        }
        Ok(())
    }

    fn io<T>(operation: &'static str, result: rustix::io::Result<T>) -> Result<T, CollectorError> {
        result.map_err(|error| CollectorError::Io {
            operation,
            raw_os_error: Some(error.raw_os_error()),
        })
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use crate::{
            MachinePolicyEntry, PlatformIdentity, PolicyReviewDeclaration, EXECUTABLE_REGISTRY_ID,
            MACHINE_POLICY_SCHEMA, OPERATION_ORDER_SHA256, REGISTRY_DOCUMENT_SHA256,
        };
        use std::fs;
        use std::os::unix::fs::{symlink, MetadataExt, PermissionsExt};
        use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
        use std::sync::mpsc::sync_channel;
        use std::sync::{Mutex, MutexGuard};
        use std::time::{SystemTime, UNIX_EPOCH};

        static COUNTER: AtomicU64 = AtomicU64::new(0);
        static FILESYSTEM_TEST_LOCK: Mutex<()> = Mutex::new(());

        struct Fixture {
            _guard: MutexGuard<'static, ()>,
            root: PathBuf,
            tool: PathBuf,
        }

        impl Fixture {
            fn new(bytes: &[u8]) -> Self {
                let guard = FILESYSTEM_TEST_LOCK
                    .lock()
                    .unwrap_or_else(|poisoned| poisoned.into_inner());
                let timestamp = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_nanos();
                let ordinal = COUNTER.fetch_add(1, Ordering::Relaxed);
                let root = PathBuf::from(format!(
                    "/private/tmp/hsai-phase792-hook-{timestamp}-{ordinal}"
                ));
                fs::create_dir(&root).unwrap();
                let tool = root.join("tool");
                write_executable(&tool, bytes);
                Self {
                    _guard: guard,
                    root,
                    tool,
                }
            }

            fn policy(&self, requested: &Path, digest_bytes: &[u8]) -> MachinePolicyCandidate {
                let owner = fs::metadata(&self.tool).unwrap().uid();
                let digest = Sha256::digest(digest_bytes)
                    .iter()
                    .map(|byte| format!("{byte:02x}"))
                    .collect::<String>();
                let entries = HostExecutableRole::ALL
                    .iter()
                    .copied()
                    .map(|role| MachinePolicyEntry {
                        role_id: role,
                        requested_path: match role {
                            HostExecutableRole::GitExe => requested.display().to_string(),
                            HostExecutableRole::RustupExe => self.tool.display().to_string(),
                            _ => role.expected_fixed_path().unwrap().to_string(),
                        },
                        allowed_owner_uids: vec![owner],
                        admitted_sha256: vec![digest.clone()],
                        acceptance_policy_id: role.expected_policy_id().to_string(),
                    })
                    .collect();
                MachinePolicyCandidate {
                    schema: MACHINE_POLICY_SCHEMA.to_string(),
                    policy_id: "phase792-hook-policy".to_string(),
                    registry_id: EXECUTABLE_REGISTRY_ID.to_string(),
                    registry_document_sha256: REGISTRY_DOCUMENT_SHA256.to_string(),
                    operation_order_sha256: OPERATION_ORDER_SHA256.to_string(),
                    platform: PlatformIdentity {
                        os: "macos".to_string(),
                        arch: "aarch64".to_string(),
                        product_version: "test".to_string(),
                        build_version: "test".to_string(),
                    },
                    allowed_roots: vec![
                        self.root.display().to_string(),
                        "/usr/bin".to_string(),
                        "/usr/sbin".to_string(),
                    ],
                    entries,
                    review: PolicyReviewDeclaration {
                        policy_object_producer_id: "producer".to_string(),
                        reviewer_id: "reviewer".to_string(),
                        reviewed_at_utc: "2026-07-14T00:00:00Z".to_string(),
                        decision: ReviewDecision::Accepted,
                    },
                }
            }
        }

        impl Drop for Fixture {
            fn drop(&mut self) {
                let _ = fs::remove_dir_all(&self.root);
            }
        }

        fn write_executable(path: &Path, bytes: &[u8]) {
            fs::write(path, bytes).unwrap();
            fs::set_permissions(path, fs::Permissions::from_mode(0o755)).unwrap();
        }

        fn collect_with_channel_mutation<F>(
            policy: &MachinePolicyCandidate,
            checkpoint: Checkpoint,
            target: &Path,
            mutate: F,
        ) -> Result<ExecutableIdentityFact, CollectorError>
        where
            F: FnOnce() + Send,
        {
            std::thread::scope(|scope| {
                let (trigger_tx, trigger_rx) = sync_channel(0);
                let (ack_tx, ack_rx) = sync_channel(0);
                scope.spawn(move || {
                    trigger_rx.recv().unwrap();
                    mutate();
                    ack_tx.send(()).unwrap();
                });
                let triggered = AtomicBool::new(false);
                let hook = |observed, path: &Path| {
                    if observed == checkpoint
                        && path == target
                        && !triggered.swap(true, Ordering::SeqCst)
                    {
                        trigger_tx.send(()).unwrap();
                        ack_rx.recv().unwrap();
                    }
                };
                let result = collect_with_hook(policy, HostExecutableRole::GitExe, &hook);
                assert!(triggered.load(Ordering::SeqCst));
                result
            })
        }

        #[test]
        fn terminal_replacement_after_open_is_rejected() {
            let bytes = b"stable-open-descriptor";
            let fixture = Fixture::new(bytes);
            let policy = fixture.policy(&fixture.tool, bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::AfterTerminalOpen,
                &fixture.tool,
                || {
                    fs::rename(&fixture.tool, fixture.root.join("original")).unwrap();
                    write_executable(&fixture.tool, b"replacement");
                },
            );
            assert!(matches!(
                result,
                Err(CollectorError::DirectoryDrift | CollectorError::EntryIdentityDrift)
            ));
        }

        #[test]
        fn truncation_during_hash_is_rejected_as_early_eof() {
            let bytes = vec![0x5a; HASH_CHUNK_BYTES * 2];
            let fixture = Fixture::new(&bytes);
            let policy = fixture.policy(&fixture.tool, &bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::DuringHash,
                &fixture.tool,
                || {
                    fs::OpenOptions::new()
                        .write(true)
                        .open(&fixture.tool)
                        .unwrap()
                        .set_len(1)
                        .unwrap();
                },
            );

            assert_eq!(result, Err(CollectorError::EarlyEof));
        }

        #[test]
        fn symlink_text_replacement_after_read_is_rejected() {
            let bytes = b"symlink-target";
            let fixture = Fixture::new(bytes);
            let alternate = fixture.root.join("alternate");
            write_executable(&alternate, b"alternate-target");
            let link = fixture.root.join("link");
            symlink("tool", &link).unwrap();
            let policy = fixture.policy(&link, bytes);
            let result =
                collect_with_channel_mutation(&policy, Checkpoint::AfterSymlinkRead, &link, || {
                    fs::remove_file(&link).unwrap();
                    symlink("alternate", &link).unwrap();
                });

            assert_eq!(result, Err(CollectorError::SymlinkDrift));
        }

        #[test]
        fn symlink_replaced_by_regular_file_before_readlink_is_not_symlink() {
            let bytes = b"symlink-type-race";
            let fixture = Fixture::new(bytes);
            let link = fixture.root.join("link-type-race");
            symlink("tool", &link).unwrap();
            let policy = fixture.policy(&link, bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::AfterEntryMetadata,
                &link,
                || {
                    fs::remove_file(&link).unwrap();
                    write_executable(&link, bytes);
                },
            );

            assert_eq!(result, Err(CollectorError::NotSymlink));
        }

        #[test]
        fn mode_drift_after_post_read_metadata_is_rejected() {
            let bytes = b"mode-drift";
            let fixture = Fixture::new(bytes);
            let policy = fixture.policy(&fixture.tool, bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::AfterPostReadMetadata,
                &fixture.tool,
                || {
                    fs::set_permissions(&fixture.tool, fs::Permissions::from_mode(0o700)).unwrap();
                },
            );

            assert_eq!(result, Err(CollectorError::EntryIdentityDrift));
        }

        #[test]
        fn growth_during_hash_is_rejected() {
            let bytes = b"growth-window";
            let fixture = Fixture::new(bytes);
            let policy = fixture.policy(&fixture.tool, bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::DuringHash,
                &fixture.tool,
                || {
                    use std::io::Write;
                    fs::OpenOptions::new()
                        .append(true)
                        .open(&fixture.tool)
                        .unwrap()
                        .write_all(b"growth")
                        .unwrap();
                },
            );

            assert_eq!(result, Err(CollectorError::ContentGrowth));
        }

        #[test]
        fn metadata_mutation_during_hash_is_rejected() {
            let bytes = b"metadata-window";
            let fixture = Fixture::new(bytes);
            let policy = fixture.policy(&fixture.tool, bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::DuringHash,
                &fixture.tool,
                || {
                    fs::set_permissions(&fixture.tool, fs::Permissions::from_mode(0o700)).unwrap();
                },
            );

            assert_eq!(result, Err(CollectorError::MetadataDrift));
        }

        #[test]
        fn unlink_after_terminal_open_is_rejected() {
            let bytes = b"unlink-window";
            let fixture = Fixture::new(bytes);
            let policy = fixture.policy(&fixture.tool, bytes);
            let result = collect_with_channel_mutation(
                &policy,
                Checkpoint::AfterTerminalOpen,
                &fixture.tool,
                || {
                    fs::remove_file(&fixture.tool).unwrap();
                },
            );

            assert!(matches!(
                result,
                Err(CollectorError::DirectoryDrift | CollectorError::EntryIdentityDrift)
            ));
        }

        #[test]
        fn ancestor_replacement_windows_are_rejected() {
            for checkpoint in [
                Checkpoint::AfterEntryMetadata,
                Checkpoint::AfterDirectoryOpen,
            ] {
                let bytes = b"ancestor-window";
                let fixture = Fixture::new(bytes);
                let ancestor = fixture.root.join("ancestor");
                fs::create_dir(&ancestor).unwrap();
                let nested_tool = ancestor.join("tool");
                write_executable(&nested_tool, bytes);
                let policy = fixture.policy(&nested_tool, bytes);
                let result = collect_with_channel_mutation(&policy, checkpoint, &ancestor, || {
                    fs::rename(&ancestor, fixture.root.join("original-ancestor")).unwrap();
                    fs::create_dir(&ancestor).unwrap();
                    write_executable(&ancestor.join("tool"), bytes);
                });

                assert!(matches!(
                    result,
                    Err(CollectorError::EntryIdentityDrift
                        | CollectorError::DirectoryDrift
                        | CollectorError::Io { .. })
                ));
            }
        }

        #[test]
        fn synthetic_privileged_owner_and_timestamp_classes_fail_closed() {
            let baseline = MetadataSnapshot {
                device: 1,
                inode: 2,
                mode: 0o100755,
                owner_uid: 501,
                link_count: 1,
                byte_length: 4,
                modified_seconds: 5,
                modified_nanoseconds: 6,
                changed_seconds: 7,
                changed_nanoseconds: 8,
            };
            for mode in [0o104755, 0o102755, 0o101755] {
                let mut metadata = baseline.clone();
                metadata.mode = mode;
                assert_eq!(
                    validate_terminal_metadata(&metadata, &[501]),
                    Err(CollectorError::UnsafeMode)
                );
            }
            assert_eq!(
                validate_terminal_metadata(&baseline, &[0]),
                Err(CollectorError::OwnerRejected)
            );

            let mut owner_drift = baseline.clone();
            owner_drift.owner_uid = 0;
            assert!(!stable_metadata_unchanged(&baseline, &owner_drift));

            let mut modified_drift = baseline.clone();
            modified_drift.modified_nanoseconds += 1;
            assert!(!stable_metadata_unchanged(&baseline, &modified_drift));

            let mut changed_drift = baseline.clone();
            changed_drift.changed_nanoseconds += 1;
            assert!(!stable_metadata_unchanged(&baseline, &changed_drift));
        }

        #[test]
        fn synthetic_fifo_and_other_nonregular_types_fail_terminal_classification() {
            for file_type in [
                FileType::Directory,
                FileType::Fifo,
                FileType::Socket,
                FileType::CharacterDevice,
                FileType::BlockDevice,
            ] {
                assert!(!file_type.is_file());
            }
        }
    }
}
