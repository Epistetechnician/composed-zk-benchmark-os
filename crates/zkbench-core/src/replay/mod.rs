//! Replay manifest, local replay result, and deterministic JSON serialization.

pub mod local_runner;
pub mod manifest;
pub mod result;
pub mod serialization;

pub use local_runner::run_local_replay;
pub use manifest::{
    build_local_replay_manifest_for_instance, build_local_replay_manifest_for_mutation,
    ReplayArtifactRef, ReplayCommand, ReplayExpectedOutcome, ReplayManifest, ReplayManifestId,
    ReplayMode, ReplayProvenance, ReplaySerializationVersion, ReplaySubject, ReplaySubjectKind,
    ReplayTraceSelection,
};
pub use result::{
    ReplayFailureMode, ReplayResult, ReplayResultId, ReplayStatus, ReplayTraceResult,
};
pub use serialization::{
    deserialize_replay_manifest_json, deserialize_replay_result_json,
    serialize_replay_manifest_json, serialize_replay_result_json,
};
