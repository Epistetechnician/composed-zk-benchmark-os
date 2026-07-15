# Phase 796-A3L2 HSAI P01B Corpus/Profile Implementation Boundary

## Status

Complete as a documentation-only authorization for one narrow, non-executing
implementation slice. It authorizes corpus normalization and immutable security
profile provenance only.

State slice:
`phase-796a3l2-hsai-p01b-corpus-profile-implementation-boundary`.

Decision: `authorize_corpus_profile_implementation_only`.

Execution status: `DocumentationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Bound Predecessor

```text
predecessor commit = 39a9331ec991c16fbe045414e220948a733994d5
Phase 796-A3L boundary = 87fb100d4454e9cc05c1b19baf47749230324fbc9ccf32f6a150a67e2f4b0ea7
Phase 796-A3L1 stop = 458d1d7c0688f45920d5308fa6670ef5f0ec2e6a4a30da6cd52af31424c3bb12
```

Phase 796-A3L1 closes C01 only. This boundary may close C08 and pin one C04
policy input. It does not authorize work on C02, C03, C05, C06, C07, C09, or
C10 and does not declare C04 closed.

## This Documentation State Slice

This phase may modify only:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l2-phase-hsai-p01b-linux-container-implementation-boundary.md
docs/90-whole-codebase-validation-report.md
docs/research/zk_external_source_index.md
```

It modifies no Python, profile, corpus, license, test, Rust, Cargo, package,
immutable-boundary, validator, accepted-evidence, or generated-artifact bytes.

## Exact Future A3L3 Diff

A3L3 may change exactly the union of these arrays and no other path.

Runtime/data files:

```text
tools/hsai-formal-preflight/p01b_container_corpus.py
tools/hsai-formal-preflight/p01b_container_seccomp.json
tools/hsai-formal-preflight/p01b_container_seccomp_license.txt
tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json
tools/hsai-formal-preflight/p01b_container_test_corpus.json
tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py
```

Documentation files:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l3-phase-hsai-p01b-container-corpus-profile-implementation.md
docs/90-whole-codebase-validation-report.md
```

The changed-path set must equal this exact eleven-path union. A3L3 may not
rename, delete, or modify any predecessor file outside it.

A3L3 uses an exact two-commit sequence. The candidate implementation commit
changes only the six runtime/data files. Two independent reviewers inspect
that immutable commit. A following audit/documentation commit changes only the
five documentation files and records the candidate commit, tree, receipts,
and reviews. The cumulative diff from the committed A3L2 boundary through the
audit/documentation commit must equal the eleven-path union above.

The profile and license are a narrow exception to the general no-vendored-
source rule: only the two exact commit-addressed byte strings and the local
canonical provenance record below are authorized immutable policy data.

## Capability Prohibitions

`p01b_container_corpus.py` is a read-only checker. Its own source may import
only Python standard-library modules needed for strict JSON, AST, unittest
discovery, hashing, paths, and type declarations. Source scans and runtime
instrumentation must prove that checker-owned code does not import, call, or
access:

```text
subprocess
socket
urllib
http
ssl
requests
Docker or container SDKs
package installers
dynamic imports
environment-derived authority
```

It may not write files, create directories, change modes, open the Docker
socket, inspect Docker, read an archive, parse gzip/TAR, execute a test, execute
a backend, or implement a production transport. `unittest.TestLoader`
discovery may transitively import the frozen suite modules and their existing
standard-library dependencies, including `subprocess`; that import authority
belongs to the frozen suite modules, not the checker, and no discovered test
method may execute. Tests may use test-owned temporary paths but the checker
itself remains read-only.

## Frozen Source Corpus

The source commit and tree are:

```text
commit = 53442464ec851be46dd1e47b44b0918a14e9cf4a
tree = 571e9aa4011a60b2af8e8069812aa71ca31b5641
```

The ordered source manifest is canonical compact sorted-key ASCII JSON with no
trailing newline. Its domain is
`hsai:p01b-container-corpus-source-manifest:v1`.

```json
[{"bytes":40913,"mode":"100644","path":"docs/796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md","sha256":"2b52a3b24d94b565434dc341d808fe7ee3ad44757ea5ff8365f8dc88aefe1ba0"},{"bytes":10911,"mode":"100644","path":"tools/hsai-formal-preflight/bounded_runner.py","sha256":"933c573a0820106df62b431db829668bf45a305b84a49a2d3bdcb6899b9b0198"},{"bytes":39729,"mode":"100644","path":"tools/hsai-formal-preflight/execution_state_machine.py","sha256":"1e264172d5f77580328456162a085b4b99bb0c9b15aa7abcdd51e8977b5a030f"},{"bytes":8719,"mode":"100644","path":"tools/hsai-formal-preflight/fixture_validator.py","sha256":"75a0e13aa06123b7bcc7ffd8d1f13bed9d318eb89f9e378e7c7ab6ff5bdd4c07"},{"bytes":127097,"mode":"100644","path":"tools/hsai-formal-preflight/p01b_archive_ledger.py","sha256":"ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f"},{"bytes":21947,"mode":"100644","path":"tools/hsai-formal-preflight/raw_archive_validator.py","sha256":"31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692"},{"bytes":10084,"mode":"100644","path":"tools/hsai-formal-preflight/tests/test_bounded_runner.py","sha256":"9c392c9b6b0804eeed730c03f35743176bc51e9953c6496f8888c32d7bc46e6a"},{"bytes":25849,"mode":"100644","path":"tools/hsai-formal-preflight/tests/test_execution_state_machine.py","sha256":"de805bfb3ca08856dd2a13e2759686b24031d0aa82ff39ce888434e570aa81c6"},{"bytes":11191,"mode":"100644","path":"tools/hsai-formal-preflight/tests/test_fixture_validator.py","sha256":"c6ec9bcd6e79d823e2cd2f4c7ea16c6f1cce908e6195606290efb42fbb2122c1"},{"bytes":143899,"mode":"100644","path":"tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py","sha256":"0ae3a2b348e491af7d2b362272255b0bd278961f4a4b7ca24718a4470692f81b"},{"bytes":2471,"mode":"100644","path":"tools/hsai-formal-preflight/tests/test_raw_archive_validator.py","sha256":"48e15976ba9a1dcbb86e1d5adc400a41dba328ebea1f156c5f0469e6a9ebdc77"}]
```

```text
source_manifest_bytes = 1938
source_manifest_sha256 = adebe965254ffa43e3c2579262dc365486c27eadb492d1fe55eaf73cf3eb00b6
```

## Corpus Artifact Schema

`p01b_container_test_corpus.json` uses schema
`hsai-p01b-container-test-corpus-v1`. Its exact schema descriptor is:

```json
{"container_environment":{"HOME":"/nonexistent","LANG":"C.UTF-8","LC_ALL":"C.UTF-8","PATH":"/usr/local/bin:/usr/bin:/bin","PYTHONDONTWRITEBYTECODE":"1","PYTHONHASHSEED":"0","PYTHONNOUSERSITE":"1","TMPDIR":"/work","TZ":"UTC"},"file_entry_fields":["bytes","mode","path","sha256"],"root_fields":["checker_source_sha256","container_environment","focused","full","schema","source_commit","source_files","source_manifest_sha256","source_tree","working_directory"],"suite_fields":["argv","count","id_array_sha256","ids","pattern","suite_files"],"working_directory":"/input"}
```

```text
corpus_schema_bytes = 567
corpus_schema_sha256 = 3494d76c1e9b0cd29ac00218b7aac06f55213fae9fca862d19c740eebb0adac2
```

The schema digest domain is `hsai:p01b-container-corpus-schema:v1`.
Duplicate, unknown, missing, non-ASCII, wrong-type, noncanonical, path-alias,
nonregular, size, mode, digest, count, order, and ID mismatch all reject.

The focused object must bind pattern `test_p01b_archive_ledger.py`, the one
focused suite path, the 68 ordered IDs, and this future workload argv:

```json
["/usr/local/bin/python3","-B","-m","unittest","discover","-s","tools/hsai-formal-preflight/tests","-p","test_p01b_archive_ledger.py"]
```

The full object must bind pattern `test_*.py`, the five suite paths in source
manifest order, the 151 ordered IDs, and:

```json
["/usr/local/bin/python3","-B","-m","unittest","discover","-s","tools/hsai-formal-preflight/tests","-p","test_*.py"]
```

Frozen candidate values are:

```text
focused_count = 68
focused_id_array_sha256 = 43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543
full_count = 151
full_id_array_sha256 = 87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8
test_id_digest = 1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726
```

The checker must reconstruct IDs independently with `unittest.TestLoader` and
AST inspection without invoking a test method. Loader discovery may import only
the frozen suite modules; checker-owned code still may not import or call
`subprocess`, socket, network, Docker, archive, package, dynamic-import, or
write APIs. Both arrays must equal the committed arrays exactly. The artifact
must bind the checker source SHA-256, the frozen source manifest, `/input`, and
the exact environment in the schema.

## Profile Provenance Schema

The authorized policy sources are commit-addressed Moby profile and license
bytes:

```text
repository = https://github.com/moby/profiles
tag = seccomp/v0.2.3
tag object = f1a0fd6b5a369fca061b041539129661ed337ef5
peeled commit = 836ae4d37ef2ec995c77c99fc55f5b5f3af3a897
profile path = seccomp/default.json
profile bytes = 13470
profile sha256 = 536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74
license path = LICENSE
license bytes = 11358
license sha256 = cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30
NOTICE status = absent at NOTICE and NOTICE.md
```

The canonical `git ls-remote` output uses one ASCII TAB between columns and one
LF after each line:

```text
f1a0fd6b5a369fca061b041539129661ed337ef5	refs/tags/seccomp/v0.2.3
836ae4d37ef2ec995c77c99fc55f5b5f3af3a897	refs/tags/seccomp/v0.2.3^{}
```

It is 135 bytes with SHA-256
`ef8d86358f2d2869ea6637304dd3942a4480eafba20122b895022d01f8b55dc9`.
The future provenance JSON must embed this exact output as a JSON string,
including both final LF bytes, rather than retaining only its digest.

`p01b_container_seccomp_provenance.json` uses schema
`hsai-p01b-container-seccomp-provenance-v1`. Its descriptor is:

```json
{"artifact_fields":["bytes","destination_path","source_path","sha256"],"root_fields":["license","notice_paths_absent","profile","repository","schema","tag","tag_object","peeled_commit","verification"],"verification_fields":["license_http_status","ls_remote_output","ls_remote_output_bytes","ls_remote_output_sha256","notice_http_status","profile_http_status"]}
```

```text
provenance_schema_bytes = 360
provenance_schema_sha256 = 31f43727cb321bc0943019bc0a6d48c36900047a64e0cf2db2b62d1ebab8260f
```

The schema digest domain is
`hsai:p01b-container-provenance-schema:v1`. Future normal tests must not fetch
any source. They compare the committed profile and license bytes, provenance
fields, schema, canonical encoding, and digests only.

The profile is candidate immutable policy data. It is not an applied seccomp
receipt, sandbox result, image acceptance, or run authority.

## Hermetic Tests

`test_p01b_container_corpus.py` must cover:

- exact checker, corpus, profile, license, and provenance source identities;
- independent TestLoader and AST ID equality without test execution;
- exact counts, order, argv, environment, source manifest, commit, and tree;
- duplicate, unknown, missing, wrong-type, noncanonical, and path attacks;
- profile and license byte/size/digest checks;
- provenance exact `ls-remote` bytes, tag-object, peeled-commit, path, status,
  and digest checks;
- absence of checker-owned subprocess, socket, network, Docker, archive,
  package, dynamic-import, environment-authority, and write surfaces; and
- zero repository mutation by the checker.

No A3L3 test may require network, Docker, a Docker socket, a local image,
Linux, cgroup v2, credentials, or a writable repository.

## Clean Audit Schema

The A3L3 phase note must retain
`hsai-p01b-container-corpus-profile-audit-v1` using this exact descriptor:

```json
{"authority_fields":["accepted_evidence_authorized","accepted_evidence_created","archive_acquisition_authorized","backend_execution_authorized","container_action_authorized","container_execution_authorized","docker_inspection_authorized","docker_socket_access_authorized","evidence_escalation_authorized","image_action_authorized","level2_plus_authorized","network_authorized","phase_796_a3_authorized","phase_796_a3l3_implementation_authorized","production_transport_implementation_authorized","runtime_filesystem_write_authorized","socket_import_authorized","stronger_claims_authorized","subprocess_import_authorized"],"changed_file_fields":["bytes","path","sha256"],"dirty_state_fields":["path","sha256","staged"],"repository_status_fields":["staged","unstaged","untracked"],"review_record_fields":["decision","findings","reviewed_commit","reviewer_id","reviewer_role"],"root_fields":["aggregate_decision_sha256","authority","changed_files","changed_paths","decision","implementation_commit","implementation_tree","predecessor_commit","preserved_dirty_state","repository_status","review_record_digests","review_records","schema","self_path","validation_receipts"],"validation_receipt_fields":["argv","cwd","environment","exit_code","stderr_sha256","stdout_sha256"]}
```

```text
audit_schema_bytes = 1268
audit_schema_sha256 = 544da1c5356c622e56960059b68f31e46bb521673ce76e3c8ae140c6ce84b305
```

The digest domain is
`hsai:p01b-container-corpus-profile-audit-schema:v1`. Arrays are ordered,
authority values are explicit booleans, and repository status separates
staged, unstaged, and untracked paths. Each independent review record is
canonical compact sorted-key ASCII JSON with no trailing newline. The ordered
`review_record_digests` array binds its records one-to-one in ascending
`reviewer_id` order. The aggregate decision digest hashes canonical compact
sorted-key ASCII JSON containing schema
`hsai-p01b-container-corpus-profile-review-aggregate-v1`, the decision, and
that ordered digest array.

`changed_paths` is the exact eleven-path cumulative array. `changed_files`
contains byte length and SHA-256 for the other ten paths. `self_path` is
`docs/796a3l3-phase-hsai-p01b-container-corpus-profile-implementation.md` and
must not appear in `changed_files`; hashing that phase note inside itself would
be a cycle. The final Git commit and tree supply its external identity. The
`implementation_commit` and `implementation_tree` fields name the preceding
six-file candidate implementation commit, never the documentation commit that
contains the audit.

## A3L3 Exit Gate

A3L3 succeeds only if:

1. the changed path set equals the exact eleven-path authorized union;
2. every runtime/data file has a published SHA-256;
3. all three canonical schema digests and all fixed identities match;
4. all new and existing formal-preflight tests pass with zero skips;
5. forbidden-import and runtime side-effect checks pass;
6. the pre-existing admission mutation remains unstaged at its exact hash;
7. no Docker command, API, socket, SDK, or object inspection occurs;
8. no archive or external source is accessed by normal tests; and
9. two canonical independent review records accept the clean implementation
   commit with zero findings.

The A3L3 phase note must bind the committed A3L2 predecessor, candidate
implementation commit and tree, exact cumulative changed-path array, SHA-256
values for the ten non-self paths, `self_path`, repository status projection,
preserved admission-path hash, exact validation argv and receipts, reviewer
IDs, review-record digests, and the aggregate decision digest. It must not
claim its own hash or documentation-commit identity and must not inspect Docker
to establish a before/after projection.

Success closes at most C08 and profile provenance. It authorizes only a later
docs-first boundary for the remaining schemas. It does not authorize driver,
probe, Docker transport, container, OOM, C09, archive, or backend work.

## Canonical Boundary Record

The retained record is 3106 bytes of canonical compact JSON with sorted keys
and no trailing newline. Its digest domain is
`hsai:p01b-container-corpus-profile-implementation-boundary:v1`.

```json
{"accepted_evidence_authorized":false,"accepted_evidence_created":false,"archive_acquisition_authorized":false,"audit_schema_sha256":"544da1c5356c622e56960059b68f31e46bb521673ce76e3c8ae140c6ce84b305","backend_execution_authorized":false,"container_action_authorized":false,"container_execution_authorized":false,"decision":"authorize_corpus_profile_implementation_only","docker_inspection_authorized":false,"docker_socket_access_authorized":false,"evidence_ceiling":"Level1LocalReplayOrLower","evidence_escalation_authorized":false,"future_state_slice":{"documentation_files":["AGENTS.md","README.md","docs/12-task-list.md","docs/796a3l3-phase-hsai-p01b-container-corpus-profile-implementation.md","docs/90-whole-codebase-validation-report.md"],"runtime_files":["tools/hsai-formal-preflight/p01b_container_corpus.py","tools/hsai-formal-preflight/p01b_container_seccomp.json","tools/hsai-formal-preflight/p01b_container_seccomp_license.txt","tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json","tools/hsai-formal-preflight/p01b_container_test_corpus.json","tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py"]},"image_action_authorized":false,"level2_plus_authorized":false,"network_authorized":false,"phase_796_a3_authorized":false,"phase_796_a3l1_stop_sha256":"458d1d7c0688f45920d5308fa6670ef5f0ec2e6a4a30da6cd52af31424c3bb12","phase_796_a3l3_implementation_authorized":true,"predecessor_commit":"39a9331ec991c16fbe045414e220948a733994d5","production_transport_implementation_authorized":false,"runtime_filesystem_write_authorized":false,"schema":"hsai-p01b-container-corpus-profile-implementation-boundary-v1","socket_import_authorized":false,"source_corpus":{"corpus_schema_sha256":"3494d76c1e9b0cd29ac00218b7aac06f55213fae9fca862d19c740eebb0adac2","focused_count":68,"focused_id_array_sha256":"43f7720588d4e3a149c92af6f95bf8825fede7ede5f08b98848c9ae9442ce543","full_count":151,"full_id_array_sha256":"87d423a462fcac2ad9bcd7f7e2b75349931e9be26baa45fd6e27e39ed0010ca8","source_commit":"53442464ec851be46dd1e47b44b0918a14e9cf4a","source_manifest_sha256":"adebe965254ffa43e3c2579262dc365486c27eadb492d1fe55eaf73cf3eb00b6","source_tree":"571e9aa4011a60b2af8e8069812aa71ca31b5641","test_id_digest":"1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726"},"source_profile":{"license_bytes":11358,"license_path":"LICENSE","license_sha256":"cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30","ls_remote_output_bytes":135,"ls_remote_output_sha256":"ef8d86358f2d2869ea6637304dd3942a4480eafba20122b895022d01f8b55dc9","notice_paths_absent":["NOTICE","NOTICE.md"],"peeled_commit":"836ae4d37ef2ec995c77c99fc55f5b5f3af3a897","profile_bytes":13470,"profile_path":"seccomp/default.json","profile_sha256":"536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74","provenance_schema_sha256":"31f43727cb321bc0943019bc0a6d48c36900047a64e0cf2db2b62d1ebab8260f","repository":"https://github.com/moby/profiles","tag":"seccomp/v0.2.3","tag_object":"f1a0fd6b5a369fca061b041539129661ed337ef5"},"stronger_claims_authorized":false,"subprocess_import_authorized":false}
```

```text
implementation_boundary_sha256 = a9e43d8d354759f7a55f45b9ef650e3e36c108dc3d30f09844b1cd3688c29f8a
phase_796_a3l3_implementation_authorized = true
container_action_authorized = false
docker_socket_access_authorized = false
subprocess_import_authorized = false
network_authorized = false
archive_acquisition_authorized = false
backend_execution_authorized = false
accepted_evidence_authorized = false
level2_plus_authorized = false
```

## Independent Review

Reviewers `019f6697-826a-74e3-84d5-4b98e01b15c5` and
`019f6697-e771-7300-b274-da8592e109f1` independently re-reviewed the corrected
precommit documentation state and returned `ACCEPT` with zero findings. Their
acceptance applies only to this bounded documentation authorization; it is not
implementation, execution, or evidence acceptance.

## Claim Boundary

Phase 796-A3L2 is not a driver, probe, supervisor, collector, Docker transport,
container run, OOM result, applied seccomp receipt, sandbox result, image
acceptance, archive acquisition, parser run, backend execution,
Lean/SMT/Z3/COBALT run, proof artifact, accepted evidence, Level2+ evidence,
score-axis result, semantic correctness, production readiness, SOTA,
breakthrough, full security, external audit, or action authority.
