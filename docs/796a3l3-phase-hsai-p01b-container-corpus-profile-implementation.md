# Phase 796-A3L3 HSAI P01B Container Corpus/Profile Implementation

## Status

Complete as an audited local implementation of the exact corpus/profile slice
authorized by Phase 796-A3L2.

State slice:
`phase-796a3l3-hsai-p01b-container-corpus-profile-implementation`.

Classification: `P01BContainerCorpusProfileImplementationAccepted`.

Execution status: `LocalValidationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

Decision: `accept_corpus_profile_implementation_only`.

## Bound Git Objects

```text
A3L2 predecessor commit = 1bb1835826a89bbdc02693a6dc30b3dd0744fb5a
A3L2 boundary sha256 = a9e43d8d354759f7a55f45b9ef650e3e36c108dc3d30f09844b1cd3688c29f8a
implementation commit = 0d67de690625fb47b26c3b47f7cc195ec2adfc7c
implementation tree = 3c81b177f66ade993862810df8d1174f05927c18
```

The implementation commit changes exactly the six runtime/data paths authorized
by A3L2. This phase note and the four standard mirrors form the following
audit/documentation commit. The cumulative branch range therefore retains the
required two-commit and eleven-path shape.

## Implemented Surface

| File | Bytes | SHA-256 |
|---|---:|---|
| `tools/hsai-formal-preflight/p01b_container_corpus.py` | 27,778 | `f788f0d97fc3ca26b32d23ffaa83d43edf4b6c04189aa0ebca2c3c877cd94598` |
| `tools/hsai-formal-preflight/p01b_container_seccomp.json` | 13,470 | `536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74` |
| `tools/hsai-formal-preflight/p01b_container_seccomp_license.txt` | 11,358 | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json` | 1,116 | `e4e20cd2de3830961c669cd99233e3490320143462b23027726e7f02d95c337b` |
| `tools/hsai-formal-preflight/p01b_container_test_corpus.json` | 27,079 | `6f719e8a113464334b368e6470126b8339c5ed66f115ebced4c724555405b064` |
| `tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py` | 28,804 | `89b4bf9d10ce2eb5f9fc5117e02b761bd2ed492ae39087d4723d5877aabb07b4` |

The checker uses descriptor-relative, no-follow regular-file reads with bounded
sizes, mode checks, and pre/post identity checks. It validates canonical JSON,
the exact eleven-file source manifest, frozen source commit and tree, focused
and complete ID arrays, argv, environment, profile, license, and provenance.

Test identities are reconstructed twice over the retained manifest-bound source
bytes. A restricted static scanner builds synthetic `unittest.TestCase`
classes for `TestLoader` name reconstruction; an independent AST pass derives
the same names. Neither path imports, reopens, or executes suite source.

## Rejected Candidate And Correction

Immutable development candidate
`6646319395539efb1a4602a32c5d7bc6ab2b8d58` was rejected. The security
review found that `TestLoader.discover` reopened validated suite files through
mutable pathnames, leaving a replacement race and unmanifested local
import-shadow authority.

The replacement commit removes pathname discovery and all suite-module import
execution. A regression test supplies source containing an unmanifested import
and a raising test body while trapping both Python import and
`TestLoader.discover`; static identity reconstruction succeeds without
executing either. Both final reviewers inspected only the immutable replacement
commit.

## Frozen Correspondence

```text
source commit = 53442464ec851be46dd1e47b44b0918a14e9cf4a
source tree = 571e9aa4011a60b2af8e8069812aa71ca31b5641
source manifest sha256 = adebe965254ffa43e3c2579262dc365486c27eadb492d1fe55eaf73cf3eb00b6
focused future workload tests = 68
focused ID array sha256 = 43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543
complete future workload tests = 151
complete ID array sha256 = 87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8
combined test ID digest = 1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726
```

The future workload count remains 151 because the future `/input` projection
is the five frozen suite files. The new checker test is a repository validation
test and is not silently added to that future workload.

All three A3L2 schema golden vectors pass:

```text
corpus schema sha256 = 3494d76c1e9b0cd29ac00218b7aac06f55213fae9fca862d19c740eebb0adac2
provenance schema sha256 = 31f43727cb321bc0943019bc0a6d48c36900047a64e0cf2db2b62d1ebab8260f
audit schema sha256 = 544da1c5356c622e56960059b68f31e46bb521673ce76e3c8ae140c6ce84b305
```

## Validation

Under the exact environment and argv retained in the canonical audit record:

```text
Python 3.9.6 focused A3L3 tests: 21 passed, 0 failed, 0 skipped
Python 3.9.6 complete formal-preflight tests: 172 passed, 0 failed, 0 skipped
Python 3.11 focused A3L3 tests: 21 passed, 0 failed, 0 skipped
Python 3.11 complete formal-preflight tests: 172 passed, 0 failed, 0 skipped
ruff: passed
cargo fmt --all -- --check: passed
unaffected Rust workspace tests: passed
unaffected Rust workspace clippy with -D warnings: passed
candidate-range git diff --check: passed
candidate six-path diff-tree check: passed
```

The unaffected Rust commands exclude `hsai-agent-admission` and
`hsai-e2e-harness` because the preserved user-owned admission edit removes
exports consumed by those existing packages. That file remains unstaged at
SHA-256
`41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de`.
The A3L3 implementation changes no Rust or Cargo file. The repository has no
root `package.json`, so a root `pnpm run lint` command is unavailable; no
`npm` substitute was used.

No validation command used Docker, a Docker socket, network, archive
acquisition, image inspection, container execution, or a backend.

## Independent Reviews

Each review record below is canonical compact sorted-key ASCII JSON with no
trailing newline. Its published digest is raw SHA-256 of those JSON bytes.
Records and digests are ordered by `reviewer_id`.

```json
{"decision":"accept","findings":[],"reviewed_commit":"0d67de690625fb47b26c3b47f7cc195ec2adfc7c","reviewer_id":"codex-subagent:019f66d5-0d2a-70d2-9720-9e0a1cad18b6","reviewer_role":"independent-security-capability-reviewer"}
```

```text
review record bytes = 223
review record sha256 = 893916efd65d36a601330bcd0f4aa2d6850e81b41c44995928c7cf3e173030bd
```

```json
{"decision":"accept","findings":[],"reviewed_commit":"0d67de690625fb47b26c3b47f7cc195ec2adfc7c","reviewer_id":"codex-subagent:019f66d5-11fc-7780-85c0-cc706b6cef6e","reviewer_role":"independent-contract-reproducibility-reviewer"}
```

```text
review record bytes = 228
review record sha256 = 542d5aab744c6871281c6d9f888c2c927ad64dd098abc1d471de44e3aa317731
```

The aggregate object is also canonical compact sorted-key ASCII JSON with no
trailing newline. Its digest is raw SHA-256.

```json
{"decision":"accept","review_record_digests":["893916efd65d36a601330bcd0f4aa2d6850e81b41c44995928c7cf3e173030bd","542d5aab744c6871281c6d9f888c2c927ad64dd098abc1d471de44e3aa317731"],"schema":"hsai-p01b-container-corpus-profile-review-aggregate-v1"}
```

```text
aggregate bytes = 247
aggregate decision sha256 = d17c8634fc786d039bc0d5e90d1346032c3ebf166b95af80c74b488c4dcf8ec5
```

## Canonical Audit Record

The following record uses schema
`hsai-p01b-container-corpus-profile-audit-v1`. It is 9,673 bytes of
canonical compact recursively sorted-key ASCII JSON with no trailing newline.
Its published digest is raw SHA-256. The record hashes the ten non-self files;
`self_path` names this phase note and Git supplies its external identity.

```json
{"aggregate_decision_sha256":"d17c8634fc786d039bc0d5e90d1346032c3ebf166b95af80c74b488c4dcf8ec5","authority":{"accepted_evidence_authorized":false,"accepted_evidence_created":false,"archive_acquisition_authorized":false,"backend_execution_authorized":false,"container_action_authorized":false,"container_execution_authorized":false,"docker_inspection_authorized":false,"docker_socket_access_authorized":false,"evidence_escalation_authorized":false,"image_action_authorized":false,"level2_plus_authorized":false,"network_authorized":false,"phase_796_a3_authorized":false,"phase_796_a3l3_implementation_authorized":true,"production_transport_implementation_authorized":false,"runtime_filesystem_write_authorized":false,"socket_import_authorized":false,"stronger_claims_authorized":false,"subprocess_import_authorized":false},"changed_files":[{"bytes":27778,"path":"tools/hsai-formal-preflight/p01b_container_corpus.py","sha256":"f788f0d97fc3ca26b32d23ffaa83d43edf4b6c04189aa0ebca2c3c877cd94598"},{"bytes":13470,"path":"tools/hsai-formal-preflight/p01b_container_seccomp.json","sha256":"536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74"},{"bytes":11358,"path":"tools/hsai-formal-preflight/p01b_container_seccomp_license.txt","sha256":"cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"},{"bytes":1116,"path":"tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json","sha256":"e4e20cd2de3830961c669cd99233e3490320143462b23027726e7f02d95c337b"},{"bytes":27079,"path":"tools/hsai-formal-preflight/p01b_container_test_corpus.json","sha256":"6f719e8a113464334b368e6470126b8339c5ed66f115ebced4c724555405b064"},{"bytes":28804,"path":"tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py","sha256":"89b4bf9d10ce2eb5f9fc5117e02b761bd2ed492ae39087d4723d5877aabb07b4"},{"bytes":1404453,"path":"AGENTS.md","sha256":"a2fef257a13dd9e283028ac8139b584633a1e92cd6bb44663bae8a01b07d0cd3"},{"bytes":323923,"path":"README.md","sha256":"aa94c23d68b96f2405de5fd79ccadf2db58cf31f338efbf61b14faeabbd090dd"},{"bytes":1187688,"path":"docs/12-task-list.md","sha256":"b21ab4a4f8afef5aa86313452bc3280d8ff6df7089222e22e4c96e07b49ba40b"},{"bytes":764086,"path":"docs/90-whole-codebase-validation-report.md","sha256":"1dd89758316e2d015cb5cced59a7056e4b8ea68895769171c379a5a0e2734ad8"}],"changed_paths":["tools/hsai-formal-preflight/p01b_container_corpus.py","tools/hsai-formal-preflight/p01b_container_seccomp.json","tools/hsai-formal-preflight/p01b_container_seccomp_license.txt","tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json","tools/hsai-formal-preflight/p01b_container_test_corpus.json","tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py","AGENTS.md","README.md","docs/12-task-list.md","docs/796a3l3-phase-hsai-p01b-container-corpus-profile-implementation.md","docs/90-whole-codebase-validation-report.md"],"decision":"accept_corpus_profile_implementation_only","implementation_commit":"0d67de690625fb47b26c3b47f7cc195ec2adfc7c","implementation_tree":"3c81b177f66ade993862810df8d1174f05927c18","predecessor_commit":"1bb1835826a89bbdc02693a6dc30b3dd0744fb5a","preserved_dirty_state":[{"path":"crates/hsai-agent-admission/src/lib.rs","sha256":"41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de","staged":false}],"repository_status":{"staged":[],"unstaged":["crates/hsai-agent-admission/src/lib.rs"],"untracked":[]},"review_record_digests":["893916efd65d36a601330bcd0f4aa2d6850e81b41c44995928c7cf3e173030bd","542d5aab744c6871281c6d9f888c2c927ad64dd098abc1d471de44e3aa317731"],"review_records":[{"decision":"accept","findings":[],"reviewed_commit":"0d67de690625fb47b26c3b47f7cc195ec2adfc7c","reviewer_id":"codex-subagent:019f66d5-0d2a-70d2-9720-9e0a1cad18b6","reviewer_role":"independent-security-capability-reviewer"},{"decision":"accept","findings":[],"reviewed_commit":"0d67de690625fb47b26c3b47f7cc195ec2adfc7c","reviewer_id":"codex-subagent:019f66d5-11fc-7780-85c0-cc706b6cef6e","reviewer_role":"independent-contract-reproducibility-reviewer"}],"schema":"hsai-p01b-container-corpus-profile-audit-v1","self_path":"docs/796a3l3-phase-hsai-p01b-container-corpus-profile-implementation.md","validation_receipts":[{"argv":["/usr/bin/python3","-B","-m","unittest","tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py","-v"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"517e8e2466680413a409c09bbb726ae6f9f8c68b638e0574dc3d4aaaff091db9","stdout_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},{"argv":["/usr/bin/python3","-B","-m","unittest","discover","-s","tools/hsai-formal-preflight/tests","-p","test_*.py","-v"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"4b4025a296bb1f2d2499e80ef46d6fafefd871684af8a71174f1d4ed539bf515","stdout_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},{"argv":["/Users/shaanp/.local/bin/ruff","check","tools/hsai-formal-preflight/p01b_container_corpus.py","tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","stdout_sha256":"82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18"},{"argv":["/Users/shaanp/.cargo/bin/cargo","fmt","--all","--","--check"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","stdout_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},{"argv":["/Users/shaanp/.cargo/bin/cargo","test","--workspace","--all-features","--exclude","hsai-agent-admission","--exclude","hsai-e2e-harness","--quiet"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","stdout_sha256":"1a1ab9f5eaa54e0752986515a678de34bd59caddf52e3516e0f12245b7965f53"},{"argv":["/Users/shaanp/.cargo/bin/cargo","clippy","--workspace","--all-targets","--all-features","--exclude","hsai-agent-admission","--exclude","hsai-e2e-harness","--","-D","warnings"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"59639588a6f1826f129cbcd121edc07279dab94786f5fa5bde6b3439b2e845cc","stdout_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},{"argv":["/opt/homebrew/bin/git","diff","--check","1bb1835826a89bbdc02693a6dc30b3dd0744fb5a..0d67de690625fb47b26c3b47f7cc195ec2adfc7c"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","stdout_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},{"argv":["/opt/homebrew/bin/git","diff-tree","--no-commit-id","--name-only","-r","0d67de690625fb47b26c3b47f7cc195ec2adfc7c"],"cwd":"/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os","environment":{"CARGO_TERM_COLOR":"never","GIT_CONFIG_NOSYSTEM":"1","HOME":"/Users/shaanp","LANG":"C","LC_ALL":"C","PATH":"/Users/shaanp/.cargo/bin:/Users/shaanp/.local/bin:/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/tmp","TZ":"UTC"},"exit_code":0,"stderr_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","stdout_sha256":"5cd451f1dba50aed776722847725ec5d93a8b008f73c5ce6f3a47e180154d1aa"}]}
```

```text
audit record bytes = 9673
audit record sha256 = 553198b652366919d42fcaa80409f21f14bec2755c18a305c8d0b8576d7adabf
```

## Claim Boundary

This phase is local implementation and audit evidence only. It closes the
canonical corpus class C08 and records profile provenance. It does not prove
that a seccomp profile was applied, a container was contained, a cgroup limit
was enforced, an image was accepted, a runtime was reproduced, or a backend
was correct.

No image, Docker, container, archive, network, backend, Lean, SMT, Z3, COBALT,
proof, accepted-evidence, Level2+, score-axis, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, external-audit, or
action-authority claim is authorized or created.

## Next Gate

The next responsible slice is another docs-first boundary for the unresolved
driver, probe, containment, platform/runtime provenance, ingress/egress
certificate, and receipt-schema classes. A3L3 does not authorize that
implementation and does not authorize a synthetic or live container run.
