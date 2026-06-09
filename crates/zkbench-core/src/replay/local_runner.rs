//! Local replay runner convenience function.

use crate::adapters::LocalJsonAdapter;
use crate::error::Result;

use super::{ReplayManifest, ReplayResult};

/// Run a local replay manifest through the LocalJsonAdapter.
pub fn run_local_replay(manifest: &ReplayManifest) -> Result<ReplayResult> {
    LocalJsonAdapter::default().replay(manifest)
}
