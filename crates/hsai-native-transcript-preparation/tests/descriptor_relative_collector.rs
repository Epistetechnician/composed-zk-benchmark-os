#![cfg(target_os = "macos")]

use hsai_native_transcript_preparation::*;
use sha2::{Digest, Sha256};
use std::fs;
use std::os::unix::ffi::OsStringExt;
use std::os::unix::fs::{symlink, MetadataExt, PermissionsExt};
use std::os::unix::net::UnixListener;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};
use std::time::{SystemTime, UNIX_EPOCH};

static FIXTURE_COUNTER: AtomicU64 = AtomicU64::new(0);
static FILESYSTEM_TEST_LOCK: Mutex<()> = Mutex::new(());

struct Fixture {
    _guard: MutexGuard<'static, ()>,
    root: PathBuf,
    direct: PathBuf,
    bytes: Vec<u8>,
}

impl Fixture {
    fn new() -> Self {
        let guard = FILESYSTEM_TEST_LOCK
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let ordinal = FIXTURE_COUNTER.fetch_add(1, Ordering::Relaxed);
        let root = PathBuf::from(format!(
            "/private/tmp/hsai-phase792-{}-{unique}-{ordinal}",
            std::process::id(),
        ));
        fs::create_dir(&root).unwrap();
        let direct = root.join("tool");
        let bytes = b"phase-792-descriptor-relative-collector\n".to_vec();
        fs::write(&direct, &bytes).unwrap();
        fs::set_permissions(&direct, fs::Permissions::from_mode(0o755)).unwrap();
        Self {
            _guard: guard,
            root,
            direct,
            bytes,
        }
    }

    fn policy_for(&self, requested: &Path) -> MachinePolicyCandidate {
        let owner_uid = fs::metadata(&self.direct).unwrap().uid();
        let observed = hex_sha256(&self.bytes);
        let entries = HostExecutableRole::ALL
            .iter()
            .copied()
            .map(|role| {
                let requested_path = match role {
                    HostExecutableRole::GitExe => requested.display().to_string(),
                    HostExecutableRole::RustupExe => self.direct.display().to_string(),
                    _ => role.expected_fixed_path().unwrap().to_string(),
                };
                MachinePolicyEntry {
                    role_id: role,
                    requested_path,
                    allowed_owner_uids: vec![owner_uid],
                    admitted_sha256: vec![observed.clone()],
                    acceptance_policy_id: role.expected_policy_id().to_string(),
                }
            })
            .collect();
        MachinePolicyCandidate {
            schema: MACHINE_POLICY_SCHEMA.to_string(),
            policy_id: "phase792-test-policy".to_string(),
            registry_id: EXECUTABLE_REGISTRY_ID.to_string(),
            registry_document_sha256: REGISTRY_DOCUMENT_SHA256.to_string(),
            operation_order_sha256: OPERATION_ORDER_SHA256.to_string(),
            platform: PlatformIdentity {
                os: "macos".to_string(),
                arch: std::env::consts::ARCH.to_string(),
                product_version: "hermetic-test".to_string(),
                build_version: "hermetic-test".to_string(),
            },
            allowed_roots: vec![
                self.root.display().to_string(),
                "/usr/bin".to_string(),
                "/usr/sbin".to_string(),
            ],
            entries,
            review: PolicyReviewDeclaration {
                policy_object_producer_id: "test-policy-producer".to_string(),
                reviewer_id: "test-policy-reviewer".to_string(),
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

fn hex_sha256(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

#[test]
fn accepts_direct_regular_file_and_binds_exact_policy_objects() {
    let fixture = Fixture::new();
    let policy = fixture.policy_for(&fixture.direct);

    let fact = collect_executable_identity_fact(&policy, HostExecutableRole::GitExe).unwrap();

    assert_eq!(fact.decision, ReviewDecision::Accepted);
    assert_eq!(fact.registry_id, policy.registry_id);
    assert_eq!(fact.machine_policy_id, policy.policy_id);
    assert_eq!(fact.declared_platform, policy.platform);
    assert_eq!(fact.observed_platform.os, "macos");
    assert_eq!(fact.observed_platform.arch, std::env::consts::ARCH);
    assert_eq!(
        fact.machine_policy_sha256,
        machine_policy_sha256(&policy).unwrap()
    );
    assert_eq!(
        fact.policy_entry_sha256,
        machine_policy_entry_sha256(
            policy
                .entries
                .iter()
                .find(|entry| entry.role_id == HostExecutableRole::GitExe)
                .unwrap()
        )
        .unwrap()
    );
    assert_eq!(fact.observed_sha256, hex_sha256(&fixture.bytes));
    assert_eq!(fact.pre_read_metadata, fact.post_read_metadata);
    assert!(fact.ordered_symlink_hops.is_empty());
}

#[test]
fn accepts_relative_and_absolute_symlinks_inside_the_selected_root() {
    let fixture = Fixture::new();
    let relative = fixture.root.join("relative-tool");
    symlink("tool", &relative).unwrap();
    let relative_fact = collect_executable_identity_fact(
        &fixture.policy_for(&relative),
        HostExecutableRole::GitExe,
    )
    .unwrap();
    assert_eq!(relative_fact.ordered_symlink_hops.len(), 1);
    assert_eq!(relative_fact.ordered_symlink_hops[0].link_text, "tool");

    let absolute = fixture.root.join("absolute-tool");
    symlink(&fixture.direct, &absolute).unwrap();
    let absolute_fact = collect_executable_identity_fact(
        &fixture.policy_for(&absolute),
        HostExecutableRole::GitExe,
    )
    .unwrap();
    assert_eq!(absolute_fact.ordered_symlink_hops.len(), 1);
    assert_eq!(
        absolute_fact.ordered_symlink_hops[0].resolved_path,
        fixture.direct.display().to_string()
    );
}

#[test]
fn accepts_ancestor_symlink_and_exactly_32_hops_but_rejects_33() {
    let fixture = Fixture::new();
    let ancestor = fixture.root.join("ancestor");
    symlink(".", &ancestor).unwrap();
    let ancestor_path = ancestor.join("tool");
    let ancestor_fact = collect_executable_identity_fact(
        &fixture.policy_for(&ancestor_path),
        HostExecutableRole::GitExe,
    )
    .unwrap();
    assert_eq!(ancestor_fact.ordered_symlink_hops.len(), 1);
    assert_eq!(
        ancestor_fact.ordered_symlink_hops[0].path,
        ancestor.display().to_string()
    );

    let absolute_ancestor = fixture.root.join("absolute-ancestor");
    symlink(&fixture.root, &absolute_ancestor).unwrap();
    let absolute_ancestor_path = absolute_ancestor.join("tool");
    let absolute_ancestor_fact = collect_executable_identity_fact(
        &fixture.policy_for(&absolute_ancestor_path),
        HostExecutableRole::GitExe,
    )
    .unwrap();
    assert_eq!(absolute_ancestor_fact.ordered_symlink_hops.len(), 1);
    assert_eq!(
        absolute_ancestor_fact.ordered_symlink_hops[0].resolved_path,
        fixture.direct.display().to_string()
    );

    for index in 0..32 {
        let target = if index == 31 {
            "tool".to_string()
        } else {
            format!("link-{}", index + 1)
        };
        symlink(target, fixture.root.join(format!("link-{index}"))).unwrap();
    }
    let accepted_path = fixture.root.join("link-0");
    let fact = collect_executable_identity_fact(
        &fixture.policy_for(&accepted_path),
        HostExecutableRole::GitExe,
    )
    .unwrap();
    assert_eq!(fact.ordered_symlink_hops.len(), 32);

    for index in 0..33 {
        let target = if index == 32 {
            "tool".to_string()
        } else {
            format!("long-{}", index + 1)
        };
        symlink(target, fixture.root.join(format!("long-{index}"))).unwrap();
    }
    let rejected_path = fixture.root.join("long-0");
    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&rejected_path),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::TooManySymlinkHops)
    );
}

#[test]
fn rejects_non_utf8_symlink_and_terminal_kind_and_size_boundaries() {
    let fixture = Fixture::new();
    let non_utf8 = fixture.root.join("non-utf8");
    symlink(std::ffi::OsString::from_vec(vec![0xff]), &non_utf8).unwrap();
    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&non_utf8),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::NonUtf8Symlink)
    );

    let empty = fixture.root.join("empty");
    fs::write(&empty, []).unwrap();
    fs::set_permissions(&empty, fs::Permissions::from_mode(0o755)).unwrap();
    assert_eq!(
        collect_executable_identity_fact(&fixture.policy_for(&empty), HostExecutableRole::GitExe),
        Err(CollectorError::EmptyFile)
    );

    let oversized = fixture.root.join("oversized");
    let oversized_file = fs::File::create(&oversized).unwrap();
    oversized_file.set_len(1_073_741_825).unwrap();
    fs::set_permissions(&oversized, fs::Permissions::from_mode(0o755)).unwrap();
    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&oversized),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::FileTooLarge)
    );

    let socket_path = fixture.root.join("socket");
    let _listener = UnixListener::bind(&socket_path).unwrap();
    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&socket_path),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::NotRegularFile)
    );

    let fifo_path = fixture.root.join("fifo");
    let fifo_status = Command::new("/usr/bin/mkfifo")
        .arg(&fifo_path)
        .status()
        .unwrap();
    assert!(fifo_status.success());
    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&fifo_path),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::NotRegularFile)
    );

    let mut device_policy = fixture.policy_for(Path::new("/dev/null"));
    device_policy.allowed_roots.push("/dev".to_string());
    device_policy.allowed_roots.sort();
    assert_eq!(
        collect_executable_identity_fact(&device_policy, HostExecutableRole::GitExe),
        Err(CollectorError::NotRegularFile)
    );
}

#[test]
fn rejects_cycle_root_escape_digest_mode_owner_and_nonregular_terminals() {
    let fixture = Fixture::new();

    let cycle = fixture.root.join("cycle");
    symlink("cycle", &cycle).unwrap();
    assert_eq!(
        collect_executable_identity_fact(&fixture.policy_for(&cycle), HostExecutableRole::GitExe),
        Err(CollectorError::SymlinkCycle)
    );

    let cycle_a = fixture.root.join("cycle-a");
    let cycle_b = fixture.root.join("cycle-b");
    symlink("cycle-b", &cycle_a).unwrap();
    symlink("cycle-a", &cycle_b).unwrap();
    assert_eq!(
        collect_executable_identity_fact(&fixture.policy_for(&cycle_a), HostExecutableRole::GitExe),
        Err(CollectorError::SymlinkCycle)
    );

    let escape = fixture.root.join("escape");
    symlink("/usr/bin/curl", &escape).unwrap();
    assert_eq!(
        collect_executable_identity_fact(&fixture.policy_for(&escape), HostExecutableRole::GitExe),
        Err(CollectorError::RootEscape)
    );

    let mut rejected_digest = fixture.policy_for(&fixture.direct);
    rejected_digest
        .entries
        .iter_mut()
        .find(|entry| entry.role_id == HostExecutableRole::GitExe)
        .unwrap()
        .admitted_sha256 = vec!["00".repeat(32)];
    assert_eq!(
        collect_executable_identity_fact(&rejected_digest, HostExecutableRole::GitExe),
        Err(CollectorError::DigestRejected)
    );

    fs::set_permissions(&fixture.direct, fs::Permissions::from_mode(0o775)).unwrap();
    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&fixture.direct),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::UnsafeMode)
    );
    fs::set_permissions(&fixture.direct, fs::Permissions::from_mode(0o755)).unwrap();

    let mut rejected_owner = fixture.policy_for(&fixture.direct);
    rejected_owner
        .entries
        .iter_mut()
        .find(|entry| entry.role_id == HostExecutableRole::GitExe)
        .unwrap()
        .allowed_owner_uids = vec![u32::MAX];
    assert_eq!(
        collect_executable_identity_fact(&rejected_owner, HostExecutableRole::GitExe),
        Err(CollectorError::OwnerRejected)
    );

    assert_eq!(
        collect_executable_identity_fact(
            &fixture.policy_for(&fixture.root),
            HostExecutableRole::GitExe
        ),
        Err(CollectorError::NotRegularFile)
    );
}

#[test]
fn rejects_invalid_policy_paths_overlapping_roots_and_fixed_role_drift() {
    let fixture = Fixture::new();
    let mut overlapping = fixture.policy_for(&fixture.direct);
    overlapping
        .allowed_roots
        .push(fixture.root.join("nested").display().to_string());
    overlapping.allowed_roots.sort();
    assert_eq!(
        collect_executable_identity_fact(&overlapping, HostExecutableRole::GitExe),
        Err(CollectorError::OverlappingAllowedRoots)
    );

    let mut malformed = fixture.policy_for(&fixture.direct);
    malformed
        .entries
        .iter_mut()
        .find(|entry| entry.role_id == HostExecutableRole::GitExe)
        .unwrap()
        .requested_path = format!("{}/./tool", fixture.root.display());
    assert_eq!(
        collect_executable_identity_fact(&malformed, HostExecutableRole::GitExe),
        Err(CollectorError::InvalidRequestedPath)
    );

    let mut fixed_drift = fixture.policy_for(&fixture.direct);
    fixed_drift
        .entries
        .iter_mut()
        .find(|entry| entry.role_id == HostExecutableRole::CurlExe)
        .unwrap()
        .requested_path = fixture.direct.display().to_string();
    assert_eq!(
        collect_executable_identity_fact(&fixed_drift, HostExecutableRole::CurlExe),
        Err(CollectorError::InvalidPolicy)
    );
}

#[test]
fn returns_specific_preflight_errors_for_missing_roles_roots_and_paths() {
    let fixture = Fixture::new();

    let mut missing = fixture.policy_for(&fixture.direct);
    missing
        .entries
        .retain(|entry| entry.role_id != HostExecutableRole::GitExe);
    assert_eq!(
        collect_executable_identity_fact(&missing, HostExecutableRole::GitExe),
        Err(CollectorError::MissingRole)
    );

    let mut relative_root = fixture.policy_for(&fixture.direct);
    relative_root.allowed_roots[0] = "relative/root".to_string();
    relative_root.allowed_roots.sort();
    assert_eq!(
        collect_executable_identity_fact(&relative_root, HostExecutableRole::GitExe),
        Err(CollectorError::InvalidAllowedRoot)
    );

    let mut empty_roots = fixture.policy_for(&fixture.direct);
    empty_roots.allowed_roots.clear();
    assert_eq!(
        collect_executable_identity_fact(&empty_roots, HostExecutableRole::GitExe),
        Err(CollectorError::InvalidAllowedRoot)
    );

    for invalid in [
        "relative/tool".to_string(),
        format!("{}/../tool", fixture.root.display()),
        format!("{}/tool/", fixture.root.display()),
        format!("{}/nu\0ll", fixture.root.display()),
    ] {
        let mut policy = fixture.policy_for(&fixture.direct);
        policy
            .entries
            .iter_mut()
            .find(|entry| entry.role_id == HostExecutableRole::GitExe)
            .unwrap()
            .requested_path = invalid;
        assert_eq!(
            collect_executable_identity_fact(&policy, HostExecutableRole::GitExe),
            Err(CollectorError::InvalidRequestedPath)
        );
    }

    let mut outside = fixture.policy_for(&fixture.direct);
    outside
        .entries
        .iter_mut()
        .find(|entry| entry.role_id == HostExecutableRole::GitExe)
        .unwrap()
        .requested_path = "/opt/hsai-outside-root".to_string();
    assert_eq!(
        collect_executable_identity_fact(&outside, HostExecutableRole::GitExe),
        Err(CollectorError::OutsideAllowedRoot)
    );
}

#[test]
fn rejects_every_privileged_writable_or_nonexecutable_mode_class() {
    let fixture = Fixture::new();
    for mode in [0o644, 0o775, 0o757] {
        fs::set_permissions(&fixture.direct, fs::Permissions::from_mode(mode)).unwrap();
        assert_eq!(
            collect_executable_identity_fact(
                &fixture.policy_for(&fixture.direct),
                HostExecutableRole::GitExe
            ),
            Err(CollectorError::UnsafeMode),
            "mode {mode:o} must be rejected"
        );
    }
}

#[test]
fn collector_source_has_no_process_network_shell_or_canonicalization_path() {
    let source = include_str!("../src/collector.rs");
    for forbidden in [
        "std::process",
        "Command::",
        "std::net",
        "TcpStream",
        "std::env::var",
        "canonicalize(",
        "unsafe {",
        "libc::open",
        "libc::stat",
    ] {
        assert!(
            !source.contains(forbidden),
            "forbidden collector surface: {forbidden}"
        );
    }
}
