# Whole Codebase Validation Report

Status: local validation report only.

This report records the end-to-end local validation run after Phase S
audit-index ergonomics output plumbing, protected-path overlap hardening, the
Phase 102 opt-in Phala provider-client implementation, the Phase 105
operator-only live runner implementation, and the Phase 106 Phala Cloud API
live artifact materialization implementation, and the Phase 107 Phala DCAP/PCCS
collateral materialization implementation, and the Phase 108 Phala local
DCAP/QVL verification artifact implementation, and the Phase 109 managed JWKS
fetch artifact implementation, and the Phase 110 Phala local PCCS-compatible
service artifact implementation, and the Phase 111 Phala direct Intel PCS
artifact implementation, the docs-first Phase 112 TLS channel-binding boundary,
the Phase 113 Phala TLS channel-binding artifact implementation, the
docs-first Phase 114 reviewed promotion preflight implementation boundary,
the Phase 115 reviewed promotion preflight implementation, the docs-first
Phase 116 accepted-ledger append boundary, the Phase 117 accepted-ledger append
implementation, the docs-first Phase 118 accepted-ledger materialization
boundary, the Phase 119 accepted-ledger materialization implementation, the
docs-first Phase 120 official-submission package materialization boundary, and
the Phase 121 official-submission package materialization implementation, and
the docs-first Phase 122 external replay and official-submission promotion
boundary, and the Phase 123 external replay submission preflight
implementation, and the docs-first Phase 124 external replay preflight output
boundary, the Phase 125 external replay preflight output implementation, and
the Phase 126 Phase W coverage-hardening follow-up, and the Phase 127 DSL
coverage campaign, and the Phase 128 soak serialization coverage campaign, and
the Phase 129 proposal validation coverage campaign, and the Phase 130 Phala
provider-client coverage campaign, and the Phase 131 Phala captured-artifact
validation coverage campaign, and the Phase 132 local JSON adapter coverage
campaign, and the Phase 133 zk-Harness export helper coverage campaign, and the
docs-first Phase 134 PCSM-governed agent admission boundary, and the Phase 135
zk-Harness dry-run validation coverage campaign, and the Phase 136 HSAI agent
admission core, the Phase 137 HSAI admission e2e harness integration, and the
docs-first Phase 138 HSAI admission journal materialization boundary, and the
docs-first Phase 139 PCSM bounded-proof handoff intake boundary, and the Phase
140 PCSM bounded-proof handoff intake metadata implementation, and the Phase
141 HSAI admission journal materialization implementation, and the docs-first
Phase 142 HSAI admission journal semantic readback boundary, and the Phase 143
HSAI admission journal semantic readback implementation, and the docs-first
Phase 144 HSAI admission journal adversarial invariant boundary, and the Phase
145 HSAI admission journal adversarial invariant implementation, and the
docs-first Phase 146 HSAI admission provenance and transaction integrity
boundary, and the Phase 147 HSAI admission provenance and transaction integrity
implementation, and the docs-first Phase 148 HSAI admission input semantic
integrity boundary, and the Phase 149 HSAI admission input semantic integrity
implementation, and the docs-first Phase 150 HSAI admission candidate semantic
closure boundary, and the Phase 151 HSAI admission candidate semantic closure
implementation, and the docs-first Phase 152 HSAI admission journal duplicate
JSON boundary, and the Phase 153 HSAI admission journal duplicate JSON
implementation, and the Phase 154 new benchmark families (`NestedLoop` and
`GuardHeavyMachine`) implementation, and the Phase 155 operator soak campaign
runner example, and the Phase 156 mutation engine depth implementation, and
the Phase 157 mutation distinguishability scoring implementation, and the
Phase 158 oracle completeness audit implementation, and the Phase 159 formal
lane interface stub implementation, and the Phase 160 mutation × formal
cross-product mapping implementation, and the Phase 161 mutation engine
completion implementation, and the Phase 162 distinguishability soak telemetry
implementation, and the Phase 163 formal lane pipeline implementation, and the
Phase 164 remaining benchmark families implementation, and the Phase 165 formal
pipeline observability hardening implementation, and the Phase 166 mutation
coverage first tranche, and the Phase 167 mutation coverage second tranche,
plus earlier
coverage-hardening follow-up work for serialization error paths, crate error
constructors, and local soak runner resume/output/error-policy paths. It
evaluates the implemented codebase as a local Level 1 Rust foundation by
running the available workspace gates and mapping those gates to the repo's
major behavioral surfaces.

It does not claim per-function formal correctness, 100% line coverage, official
accepted Evidence Ledger mutation, official benchmark evidence, ZK backend
performance, Level2+ evidence, live provider evidence, production readiness,
semantic correctness, or global software-agent uniqueness.

Phase 114 authorizes only inert Phase W preflight metadata and fail-closed
validation. It does not authorize accepted Evidence Ledger mutation, official
benchmark submission, external replay, live backend execution, generated
benchmark artifacts, score-axis population, ZK backend performance claims, or
Level2+ evidence creation.

Phase 115 implements that inert preflight surface in `zkbench-core`: promotion
preflight request/report metadata, deterministic JSON/Markdown/digest helpers,
required non-claim labels, fail-closed validation, and official-submission
package metadata validation. It still creates no accepted Evidence Ledger entry,
performs no official submission, runs no external replay, creates no generated
benchmark artifact, and populates no score axes.

Phase 117 implements the guarded local append transaction over a caller-supplied
in-memory `EvidenceLedger`. Phase 119 implements the corresponding local JSON
materialization path for exactly one caller-selected ledger file. These phases
create local accepted-ledger entries only under explicit Level1-or-below
transaction inputs. They do not create official accepted evidence, perform
official submission, run external replay, create generated benchmark artifacts,
or populate score axes.

Phase 120 opens the docs-first boundary for a local official-submission package
output root. Phase 121 implements that local output plumbing in `zkbench-core`:
valid package metadata plus a valid accepted ledger JSON can materialize
declared local package files and digest sidecars after fail-closed validation.
It creates no committed generated package artifact, performs no official
endpoint call, submits no official benchmark result, populates no score axes,
and creates no Level2+ evidence.

Phase 122 opens the docs-first boundary for a future external replay and
official-submission promotion path. It defines required inputs, validation
order, future artifact shape, redaction requirements, operator acknowledgement,
and evidence-class separation. It authorizes no implementation, external
replay execution, network access, credentials, generated artifacts, accepted
Evidence Ledger mutation, official benchmark submission, score-axis
population, or Level2+ evidence.

Phase 123 implements the local preflight surface for that boundary in
`zkbench-core`. It validates accepted ledger JSON, Phase 121 package output,
operator-expected package digests, non-secret benchmark target metadata,
external replay provenance, source artifact digests, explicit operator
acknowledgement, future output-root safety, redaction policy, blocking markers,
and claim-class separation. It runs no external replay, calls no endpoint, uses
no credentials, writes no generated artifacts, mutates no accepted Evidence
Ledger, populates no score axes, and creates no Level2+ evidence.

Phase 124 opens the docs-first boundary for a future local output-root
materializer for Phase 123 preflight reports. It defines declared local review
files, digest sidecars, redaction requirements, protected-root rules,
fail-closed output validation, and future hermetic tests. It authorizes no Rust
implementation, generated output, committed artifact, external replay,
endpoint call, credential access, accepted Evidence Ledger mutation,
score-axis population, or Level2+ evidence.

Phase 125 implements that local output-root surface in `zkbench-core`. It
materializes deterministic declared `external-replay-submission/*` review files
and digest sidecars from a valid Phase 123 request/report pair, validates
readback, rejects request/report drift, rejects raw-material retention, rejects
protected roots and repair overwrites, and still runs no external replay, calls
no endpoint, uses no credentials, mutates no accepted Evidence Ledger,
populates no score axes, and creates no Level2+ evidence.

Phase 126 hardens focused local regression coverage for the Phase 125
output-root surface. It adds digest-consistent negative tests for malformed
materialized files and readback drift, plus output-root safety tests for files,
repository overlap, parent-directory components, and symlinks. It changes no
production API, runs no external replay, calls no endpoint, uses no credentials,
mutates no accepted Evidence Ledger, populates no score axes, creates no
Level2+ evidence, and does not claim 100% coverage.

Phase 127 hardens focused local regression coverage for the hermetic
DSL/oracle/validation path. It adds guard/action combinator tests,
expression-helper tests, oracle rejection tests, arithmetic error tests,
missing-initial-value tests, and parser/lowering validation rejection tests.
It changes no production API, runs no external replay, calls no endpoint, uses
no credentials, mutates no accepted Evidence Ledger, populates no score axes,
creates no Level2+ evidence, and does not claim 100% coverage.

Phase 128 hardens focused local regression coverage for the hermetic local
soak JSON serialization path. It adds successful pretty-JSON round-trip tests
for every soak serialization wrapper and malformed JSON error-context tests for
every corresponding soak deserializer wrapper. It changes no production API,
runs no external replay, calls no endpoint, uses no credentials, mutates no
accepted Evidence Ledger, populates no score axes, creates no Level2+ evidence,
and does not claim 100% coverage.

Phase 129 hardens focused local regression coverage for the hermetic evidence
append proposal validation path. It adds rejection-path coverage for empty
proposal identifiers, non-design evidence class, Level2 claim boundary,
accepted-evidence flag assertion, empty artifact reference, unresolved blocking
import issues, blocked claim-boundary issue kinds, forbidden official-evidence
text, forbidden formal-proof text, and forbidden soundness-proof wording across
proposal notes, provenance summaries, review requirement notes, and review
findings. It changes no production API, runs no external replay, calls no
endpoint, uses no credentials, mutates no accepted Evidence Ledger, populates
no score axes, creates no Level2+ evidence, and does not claim 100% coverage.

Phase 130 hardens focused local regression coverage for the opt-in
Phala/dstack operator-live provider-client fail-closed path. It adds
zero-timeout config rejection, unapproved credential-source rejection before
transport, HTTP `403` auth mapping, and non-UTF-8 bearer-token rejection before
network construction. It changes no production API, runs no live Phala call,
creates no operator live test, uses no real credentials, mutates no accepted
Evidence Ledger, populates no score axes, creates no Level2+ evidence, and
does not claim 100% coverage.

Phase 131 hardens focused local regression coverage for the existing Phala
captured-artifact parser and validator. It adds rejection-path coverage for
invalid JSON, malformed quote hex, invalid case-hash length, future
observations, untrusted managed-verifier kind/status, missing required event
log entries, mismatched event payloads, invalid Docker digest shape, and wrong
RTMR event indexes. It changes no production API, runs no live Phala call,
creates no operator live test, uses no real credentials, mutates no accepted
Evidence Ledger, populates no score axes, creates no Level2+ evidence, and
does not claim 100% coverage.

Phase 132 hardens focused local regression coverage for the existing local
JSON adapter. It adds rejection-path coverage for claim-boundary elevation,
adapter-id drift, missing generated and mutated subject payloads, selected
trace drift, mock replay mode without a mock command, mock capability-gap and
inconclusive status mapping, legacy manifest preparation, and empty-evidence
normalization. It changes no production API, runs no external replay, calls no
endpoint, uses no credentials, creates no generated benchmark artifacts,
mutates no accepted Evidence Ledger, populates no score axes, creates no
Level2+ evidence, and does not claim 100% coverage.

Phase 133 hardens focused local regression coverage for the existing
zk-Harness dry-run export helper surface. It adds direct pack export helper
coverage, dry-run plan JSON serialization/deserialization round-trip coverage,
adapter manifest JSON serialization/deserialization round-trip coverage, and
malformed JSON deserialization rejection for both helper families. It changes
no production API, runs no zk-Harness execution, runs no external replay,
calls no endpoint, uses no credentials, creates no generated benchmark
artifacts, mutates no accepted Evidence Ledger, populates no score axes,
creates no Level2+ evidence, and does not claim 100% coverage.

Phase 134 is a docs-first architecture boundary for PCSM-governed agent-output
admission. It maps the recoverable-ghost-states PCSM handoff into a future local
admission-governance template for typed candidates, deterministic admission
decisions, append-only admission journals, source-digest binding, and explicit
nonclaims. It imports no recoverable-ghost runtime or artifact, changes no Rust
source, mutates no accepted Evidence Ledger, runs no external replay, runs no
live backend, creates no generated benchmark artifact, populates no score axes,
creates no Level2+ evidence, and does not claim semantic correctness,
production readiness, or global software-agent uniqueness.

Phase 135 hardens focused local regression coverage for the existing
zk-Harness dry-run validation surface. It adds exact issue-path coverage for
empty identifiers, unsupported-feature warnings, metric drift, command inertness
and relative-path drift, artifact mapping drift, family label drift, trace
local-only drift, and forbidden benchmark-evidence language. It changes no
production API, runs no zk-Harness execution, runs no external replay, calls no
endpoint, uses no credentials, creates no generated benchmark artifacts, mutates
no accepted Evidence Ledger, populates no score axes, creates no Level2+
evidence, and does not claim 100% coverage.

Phase 136 implements the local HSAI agent admission core in a new
`hsai-agent-admission` crate. It adds strict typed admission candidates,
deterministic admission policies, accepted/rejected/quarantined decisions,
append-only in-memory admission journal validation, replay and stale-chain
guards, source digest binding, required nonclaim enforcement, and accepted
claim-envelope handoff from admitted claim-envelope proposals. It imports no
recoverable-ghost runtime or artifact, performs no provider call, uses no
credentials, mutates no accepted Evidence Ledger, runs no external replay,
runs no live backend, creates no generated benchmark artifact, populates no
score axes, creates no Level2+ evidence, and does not claim proof, benchmark
evidence, semantic correctness, production readiness, or global software-agent
uniqueness.

Phase 137 integrates the Phase 136 admission core into the existing pure-data
HSAI e2e harness. It adds local regression checks showing that an admitted
closed attested claim-envelope proposal can append to the admission journal and
then reach Phase 4 anchor registration, while rejected candidates export no
accepted envelope and raw provider-shaped candidates are quarantined before
registry or economy use. It imports no recoverable-ghost runtime or artifact,
performs no provider call, uses no credentials, mutates no accepted Evidence
Ledger, runs no external replay, runs no live backend, creates no generated
benchmark artifact, populates no score axes, creates no Level2+ evidence, and
does not claim proof, benchmark evidence, semantic correctness, production
readiness, or global software-agent uniqueness.

Phase 138 opens a docs-first boundary for future local admission-journal
materialization. It defines declared `admission-journal/*` file roles, manifest
fields, digest sidecars, serialized journal validation, decision JSONL
review-index checks, source-digest disclosure, output-root safety, stale-tip
and replay checks, redaction requirements, rejected/quarantined audit
retention, and future implementation exit criteria. It changes no Rust source,
adds no generated output, performs no provider call, uses no credentials,
mutates no accepted Evidence Ledger, runs no external replay, runs no live
backend, creates no benchmark artifact, populates no score axes, creates no
Level2+ evidence, and does not claim proof, benchmark evidence, semantic
correctness, production readiness, or global software-agent uniqueness.

Phase 139 opens a docs-first boundary for future intake of a committed
recoverable-ghost-states PCSM CL12 bounded-proof handoff. It defines source
repo identity, committed source revision, source handoff path, handoff SHA-256
digest binding, verifier-status fields, bounded-proof fields, blocked-preflight
preservation, `threshold_admitted=false` preservation, digest-only source
artifact references, required nonclaims, future HSAI admission mapping limits,
and fail-closed rejection rules. It changes no Rust source, imports no PCSM
runtime or recoverable-ghost artifacts, accepts no dirty or staged-only source
snapshot, adds no generated output, performs no provider call, uses no
credentials, mutates no accepted Evidence Ledger, runs no external replay,
runs no live backend, creates no benchmark artifact, populates no score axes,
creates no Level2+ evidence, and does not claim full breakthrough-threshold
admission, proof, benchmark evidence, semantic correctness, production
readiness, or global software-agent uniqueness.

Phase 140 implements the local structured metadata validator for that bounded
handoff intake boundary inside `hsai-agent-admission`. It adds typed source
repo status, verifier status, bounded-proof intake, and intake-error data;
required nonclaim helpers; fail-closed validation for clean committed source
identity, declared handoff path, handoff digest, verifier statuses,
blocked-preflight status, `threshold_admitted=false`, bounded PCSM counts,
digest-only source artifact references, and authority/evidence escalation
flags; and a mapper to `AdmissionSourceKind::PcsmBoundedProofHandoff` with a
`LocalOnly` claim boundary and no accepted claim envelope. It reads no
filesystem path, runs no source repo command, imports no PCSM runtime or
recoverable-ghost artifacts, accepts no dirty or staged-only source snapshot,
adds no generated output, performs no provider call, uses no credentials,
mutates no accepted Evidence Ledger, runs no external replay, runs no live
backend, creates no benchmark artifact, populates no score axes, creates no
Level2+ evidence, and does not claim full breakthrough-threshold admission,
proof, benchmark evidence, semantic correctness, production readiness, or
global software-agent uniqueness.

Phase 141 implements local admission-journal output-root materialization inside
`hsai-agent-admission`. It adds request, manifest, decision-row,
source-digest, redaction-report, validation-report, and error types; required
nonclaim helpers; declared `admission-journal/*` file writes; SHA-256 sidecar
generation; readback validation; protected-root, symlink-root, stale-tip,
invalid-journal, missing-nonclaim, undeclared-file, and stale-digest
rejection; and rejected/quarantined decision retention as audit metadata. It
imports no PCSM runtime or recoverable-ghost artifacts, parses no
recoverable-ghost files, runs no source repo command, performs no provider
call, uses no credentials, commits no generated bundle, mutates no accepted
Evidence Ledger, runs no external replay, runs no live backend, creates no
benchmark artifact, populates no score axes, creates no Level2+ evidence, and
does not claim full breakthrough-threshold admission, proof, benchmark
evidence, semantic correctness, production readiness, or global
software-agent uniqueness.

Phase 142 opens the docs-first boundary for future semantic readback hardening
of Phase 141 admission-journal bundles. It requires independent parsing and
cross-validation of the manifest, serialized journal, decision JSONL, source
digest index, nonclaims, redaction report, validation report, declared file
digests, and primary/sidecar file types so digest-consistent tampering is
rejected. It defines explicit error surfaces, hermetic mutation tests, one
future PCSM-intake-through-semantic-readback path, and future implementation
exit criteria. It changes no Rust source, parses no recoverable-ghost file,
runs no source repo command, imports no PCSM runtime or artifact, creates no
generated output, mutates no accepted Evidence Ledger, populates no score axes,
creates no Level2+ evidence, and does not claim threshold admission, proof,
benchmark evidence, semantic correctness, production readiness, or global
software-agent uniqueness. Actual cross-repo intake remains blocked because
the source handoff was staged in a dirty recoverable-ghost-states checkout on
2026-06-23.

Phase 143 implements that semantic readback hardening inside
`hsai-agent-admission`. It validates primary and sidecar file types, parses
every declared file, validates the serialized journal, recomputes manifest
counts and tips, compares decision rows and source digests, rejects conflicting
artifact ids, requires canonical nonclaims and strict redaction, and validates
the derived validation report. Focused mutation tests cover digest-consistent
drift across every semantic surface plus a complete local PCSM metadata path
through materialization and readback. It parses no recoverable-ghost file, runs
no source repo command, imports no PCSM runtime or artifact, commits no
generated bundle, mutates no accepted Evidence Ledger, populates no score axes,
creates no Level2+ evidence, and does not claim threshold admission, proof,
benchmark evidence, semantic correctness, production readiness, or global
software-agent uniqueness.

Phase 144 opens the docs-first boundary for three remaining local adversarial
invariants: rejected and quarantined decisions cannot retain or expose accepted
envelopes, serialized admission-journal structures must reject unknown JSON
fields, and readback must reject symlink output roots and bundle directories.
It defines required future errors, adversarial tests, compatible test-only
coverage hardening, and implementation exit criteria. It changes no Rust
source, parses no recoverable-ghost file, creates no generated output, mutates
no accepted Evidence Ledger, populates no score axes, creates no Level2+
evidence, and creates no stronger claim.

Phase 145 implements the Phase 144 invariants inside `hsai-agent-admission`.
Decision envelope access is verdict-aware; journal validation rejects retained
envelopes under rejected or quarantined verdicts; strict typed JSON round-trip
validation rejects recursively unknown fields; and readback rejects symlink or
non-directory roots and bundle directories. Expanded fail-closed tests cover
malformed, partial, substituted, drifted, unsafe, and adversarial states.
Focused coverage measured `96.80%` regions, `94.92%` functions, and `97.45%`
lines without a 100% claim. This phase parses no recoverable-ghost file,
creates no committed generated output, mutates no accepted Evidence Ledger,
populates no score axes, creates no Level2+ evidence, and creates no stronger
claim.

Phase 146 opens the docs-first boundary for three high-severity local integrity
gaps: caller-supplied decisions must equal deterministic policy evaluation,
PCSM candidates must bind the complete validated intake digest, and protected
root overlap must reject output ancestors before overwrite deletion. It defines
required candidate and policy snapshots, append and journal validation rules,
reserved digest behavior, symmetric path checks, adversarial tests, deferred
medium findings, and implementation exit criteria. It changes no Rust source,
parses no recoverable-ghost file, creates no generated output, mutates no
accepted Evidence Ledger, populates no score axes, creates no Level2+ evidence,
and creates no stronger claim.

Phase 147 implements the Phase 146 invariants. Journal entries retain complete
candidate and policy snapshots, append requires the explicit policy, and
journal validation independently recomputes the decision and verifies all
snapshot and digest relationships. PCSM candidates bind the full validated
intake digest under a reserved id. Output-root validation rejects protected
overlap in both directions before overwrite deletion. Focused tests reject
forged decisions, snapshot drift, reserved digest collision, fully rehashed
tampering, and protected ancestor deletion while preserving valid HSAI flows.
This phase parses no recoverable-ghost file, creates no committed generated
output, mutates no accepted Evidence Ledger, populates no score axes, creates no
Level2+ evidence, and creates no stronger claim.

Phase 148 opens the docs-first boundary for the remaining local admission input
semantic gaps. It requires exact source-kind payload shapes, raw provider
non-admissibility, portable nonzero artifact digests with one digest per
logical id, checked PCSM count conservation, journal-entry count agreement,
and an exact duplicate-free required verifier set whose outcomes all pass. It
defines deterministic reason ordering, adversarial tests, compatibility rules,
deferred filesystem and JSON-parser findings, and future implementation exit
criteria. It changes no Rust source, parses no recoverable-ghost file, creates
no generated output, mutates no accepted Evidence Ledger, populates no score
axes, creates no Level2+ evidence, and creates no stronger claim.

Phase 149 implements the Phase 148 invariants. Admission validates source-kind
case/envelope shapes, AgentCase subject agreement, raw provider
non-admissibility, portable artifact IDs, nonzero hashes, and one digest per
logical artifact id before policy acceptance. PCSM intake validation now
requires checked accepted-plus-rejected count conservation, journal-entry count
agreement, and an exact required verifier-name set with no representable
duplicate, unknown, missing, or failing status. Focused tests cover malformed
source shapes, artifact identities, count overflow and drift, and verifier-set
ambiguity while preserving the valid local PCSM journal path. This phase parses
no recoverable-ghost file, creates no committed generated output, mutates no
accepted Evidence Ledger, populates no score axes, creates no Level2+ evidence,
and creates no stronger claim.

Phase 150 opens the docs-first boundary for the remaining candidate-model
semantic gaps. It requires portable nonempty candidate IDs, nonempty trimmed
subjects, exact source-kind claim-boundary coupling, accepted-envelope export
only for accepted envelope proposals, and mandatory reserved PCSM intake digest
placement only on PCSM candidates. It defines deterministic reason ordering,
adversarial tests, compatibility rules, deferred parser and filesystem
findings, and future implementation exit criteria. It changes no Rust source,
parses no recoverable-ghost file, creates no generated output, mutates no
accepted Evidence Ledger, populates no score axes, creates no Level2+ evidence,
and creates no stronger claim.

Phase 151 implements the Phase 150 candidate semantic closure. Admission now
rejects ambiguous candidate IDs and subjects, requires exact source-kind claim
boundaries, limits accepted-envelope creation to accepted envelope proposals,
and enforces reserved PCSM intake digest placement. The public envelope helper
now requires candidate, policy, and decision inputs and re-evaluates them
before export. HSAI e2e callers were updated without changing serialized
journal shape. Focused tests cover every source kind and claim boundary,
identity drift, reserved-ID misuse, forged decision export, and valid case,
envelope, provider-quarantine, and PCSM paths. This phase parses no
recoverable-ghost file, creates no committed generated output, mutates no
accepted Evidence Ledger, populates no score axes, creates no Level2+ evidence,
and creates no stronger claim.

Phase 152 opens the docs-first boundary for recursive duplicate JSON object-key
rejection in admission-journal semantic readback. It requires a dependency-free
Serde visitor before the existing typed canonical round-trip, complete-input
validation, nested object and array traversal, existing malformed-file error
mapping, and adversarial coverage for all declared JSON documents and decision
JSONL rows. It explicitly defers repeated array-element checks and filesystem
transaction hardening. It changes no Rust source, parses no recoverable-ghost
file, creates no generated output, mutates no accepted Evidence Ledger,
populates no score axes, creates no Level2+ evidence, and creates no stronger
claim.

Phase 153 implements the Phase 152 duplicate JSON parser hardening inside
`hsai-agent-admission`. `parse_json_value_rejecting_duplicate_keys` now runs
before typed canonical round-trip validation, rejects recursive duplicate object
keys and trailing non-whitespace, maps failures to the existing
`MalformedDeclaredFile` surface, and preserves separate-scope key validity.
Focused tests cover every declared admission-journal JSON document and decision
JSONL row. This phase adds no Cargo metadata or dependencies, parses no
recoverable-ghost file, creates no committed generated output, mutates no
accepted Evidence Ledger, populates no score axes, creates no Level2+ evidence,
and creates no stronger claim.

Phase 154 unblocks two future benchmark families as deterministic local
generators over the existing Surface DSL: `NestedLoop` (two stacked bounded
loops with inner/outer counters, two `LoopSpec` entries, and one invariant) and
`GuardHeavyMachine` (acquire/release/advance/finish transitions exercising
`GuardExpr::And` and `GuardExpr::Or`, one `LoopSpec`, and one invariant). It
extends `FamilyKind::is_implemented`, the family template registry,
`GeneratorConfig::nested_loop` and `GeneratorConfig::guard_heavy_machine`
constructors, the generator dispatch in `DeterministicGenerator::generate_family`,
the zk-Harness inert `candidate_family_label` mapping, and the local soak
runner's `generator_config_for_case`. Both families preserve
`ClaimBoundary::Level1LocalReplay`, the local-semantic-fixture nonclaim,
deterministic family ids, and local JSON replay behavior. Phase 154 adds no
Cargo metadata change, dependency, new DSL type, or new mutation pass; the four
remaining family implementations are handled later by Phase 164. zk-Harness
labels remain inert dry-run metadata only. Soak campaign results stay
`Level0DesignNote`.

Phase 155 unblocks the soak campaign runner by adding a single operator-facing
example binary `operator_soak_campaign` under
`crates/zkbench-core/examples/`. It wraps the existing shipped
`plan_soak_shards` and `run_soak_campaign` library surface, reads a fixed
authorized set of environment variables, requires an explicit fixed
acknowledgement, validates inputs through the existing
`SoakRunConfig::validate` and `validate_soak_campaign_config`, enforces the
`Level0DesignNote` cap, and emits a non-secret summary JSON to stdout. It is
not a CLI tool (no argument parsing, no `clap`, no `std::env::args`), not a
shipped `[[bin]]` target, and not a package runtime file. Nine hermetic
source-contract tests over the example bytes assert the acknowledgement gate,
the authorized env var surface, the shipped library usage, the required
nonclaims, the absence of subprocess/network/CLI-parsing substrings, the
absence of unauthorized env var prefixes, the absence of hardcoded roots or
campaign ids, fail-closed input validation, and the claim boundary cap. Phase
155 adds no Cargo metadata change, dependency, library API, library behavior,
soak semantics, claim boundary, validation, or artifact layout change.

Phase 156 widens the mutation engine from 3 of 14 declared `MutationClass`
variants to 8 of 14 by adding five new deterministic `MutationPass` impls
(`InvariantWeakeningPass`, `InvariantStrengtheningPass`, `StaleStateReadsPass`,
`InvalidUnrollBoundsPass`, `ObservationOmissionPass`) under
`crates/zkbench-core/src/mutation/`. It reuses the existing `finish_mutation`
helper unchanged so `validate_surface_spec`, `lower_to_ir`, provenance,
deterministic id derivation, and `ClaimBoundary::Level1LocalReplay` are
preserved. It adds five shared `pub(crate)` helpers in `apply.rs`
(`select_primary_trace`, `invariant_mut`, `loop_mut`, `guard_read_fields`,
`action_write_fields`, `guard_is_executable_expr`). `apply_default_mutations`
is deliberately unchanged so the strict engine contract (every configured
pass must find an eligible target on the supplied instance) is preserved;
the new passes are individually runnable via `apply_mutation_pass` and
composable via `MutationEngine::default().with_pass(...)`. Eleven focused
tests in `crates/zkbench-core/tests/phase_156_mutation_depth.rs` cover each
new pass's applies path, the no-eligible-target path for passes that have a
clean non-applicable family, a custom-engine determinism check, and a
`MutationClass` scope guard. Phase 156 adds no new `MutationClass` variant,
no DSL/oracle/scoring/evidence change, no Cargo metadata change, no
dependency, and no stronger claim; every mutated instance remains
`Level1LocalReplay`.

Phase 157 adds the analytical lens over the widened mutation surface:
`crates/zkbench-core/src/scoring/distinguishability.rs` composes each
mutation's declared `ExpectedVerdict` with each `BackendOutcome` variant via
the existing `classify_result` to produce a deterministic complete matrix.
`MutationDistinguishabilityAxis` (`TruePositive`, `DetectedRejection`,
`UnsoundAcceptanceCandidate`, `FalseRejectionCandidate`, `Inconclusive`)
carries `axis_severity` as a local-only triage hint (not a score).
`classify_mutation_distinguishability` iterates over all `BackendOutcome`
variants so the matrix is complete and deterministic by construction.
`summarize_mutation_distinguishability` aggregates counts per axis across
multiple matrices and carries mandatory nonclaims. Eleven focused tests in
`crates/zkbench-core/tests/phase_157_distinguishability.rs` cover every
verdict × outcome pairing, matrix completeness per mutation class, the four
interesting axis mappings, summary aggregation, mandatory nonclaims,
severity monotonicity, determinism, and an `ExpectedVerdict`/
`BackendOutcome`/`ResultClassification` scope guard. Phase 157 adds no new
verdict/outcome/classification variant, no `ScoreReport` axis population,
no Cargo metadata change, no dependency, and no stronger claim; every
matrix is `Level1LocalReplay`.

Phase 158 makes the v0 oracle's completeness over the generated surface
auditable: `crates/zkbench-core/src/dsl/oracle_completeness.rs` walks every
transition guard, transition action, invariant guard, and loop bound in
declaration order and classifies each via the existing `contains_raw_text`
helpers plus a local integer-operand check, producing an
`OracleCompletenessAudit` with per-construct labels (`Executable`,
`RawTextCapabilityGap`, `NonExecutableOperandCapabilityGap`,
`StructurallyIncapable`). The audit mirrors the shipped oracle over the bounded
raw-text static checks because it reuses the oracle's own raw-text detection
helpers. Six focused integration tests in
`crates/zkbench-core/tests/phase_158_oracle_completeness.rs`
plus inline unit tests verify shipped families are fully executable, count
consistency, determinism, and absence of structurally incapable constructs.
Phase 158 adds no `evaluate_trace`/`OracleOutcome`/DSL change, no Cargo
metadata change, no dependency, and no stronger claim; the audit is
`Level0DesignNote`.

Phase 159 introduces the formal-lane interface seam: a new
`crates/zkbench-core/src/formal/` module with `FormalPropertyScope`,
`FormalPropertyAssertion`, `FormalLaneProofStatus` (with `claim_boundary`
mapping), `FormalLaneProof`, `FormalLaneError`, the `FormalVerifier` trait
(mirroring `hsai-attestation::AttestationVerifier`), the `NoopFormalVerifier`
reference impl that always returns `DeclaredOnly` and `Level0DesignNote`,
the `FormalLane<V>` wrapper with `evaluate`, and `FormalLaneOutcome`. The
`NoopFormalVerifier` never escalates above `Level0DesignNote` and never
returns `MachineCheckedScoped` or `IndependentlyReproduced`; those statuses
and their Level 5/6 claim-boundary mappings exist only so a future
implementation phase can reuse them. Six focused integration tests in
`crates/zkbench-core/tests/phase_159_formal_lane.rs` plus inline unit tests
verify noop behavior, no escalation, malformed input rejection, mandatory
nonclaims, and scope-guard variant counts, plus a source-scan test proving
the module contains no forbidden formal-tool or network/filesystem
integrations. Phase 159 adds no Cargo dependency, no real formal-tool
integration, no `ClaimEnvelope` coupling, no HSAI-crate change, and no
stronger claim; every `FormalLaneProof` is `Level0DesignNote`.

Phase 160 connects the mutation and formal halves: a new
`crates/zkbench-core/src/formal/cross_product.rs` module maps each of the 14
declared `MutationClass` variants to the `FormalPropertyScope` it most
directly stress-tests via `mutation_class_formal_stress`, and derives a
`FormalPropertyAssertion` template from an existing `SurfaceSpec` via
`derive_formal_property_assertion_template` (returning `Some` when a matching
construct exists, `None` otherwise). `FormalPropertyScopeKind` carries the
scope *kind* without binding to ids, distinct from `FormalPropertyScope`.
Twelve focused integration tests in
`crates/zkbench-core/tests/phase_160_cross_product.rs` plus inline unit tests
verify profile coverage, scope mapping correctness, nonclaim presence,
template derivation `Some`/`None` paths, determinism, and scope-guard variant
counts. Phase 160 adds no `MutationClass`/formal-type change, no Cargo
metadata change, no dependency, no real formal-tool call, and no stronger
claim; the mapping is `Level0DesignNote`.

Phase 161 completes the local mutation-engine surface for the six remaining
declared `MutationClass` variants: nondeterministic transition injection,
recursion-envelope mismatch, public/private boundary mismatch, witness aliasing,
semantic no-op drift, and trace-ordering corruption. It also adds central
`apply_mutation_for_class` dispatch for all 14 variants and routes the soak
runner through that dispatch. Seven focused tests in
`crates/zkbench-core/tests/phase_161_mutation_completion.rs` verify each added
pass, no-target handling where applicable, and full dispatch coverage. Phase
161 adds no new `MutationClass` variant, no Cargo metadata change, no dependency,
no external execution, no accepted Evidence Ledger mutation, no official
benchmark submission, no score-axis population, no Level2+ evidence, and no
stronger claim; every mutated instance remains `Level1LocalReplay`.

Phase 162 adds internal distinguishability telemetry to soak runs. It exposes
`observed_distinguishability_axis`, backward-compatible serde-default telemetry
fields, and soak-runner recording for successful mutation replays. Two focused
tests in `crates/zkbench-core/tests/phase_162_distinguishability_telemetry.rs`
verify counter recording and merge behavior. Phase 162 does not populate
`ScoreReport` axes, does not create benchmark evidence, does not add external
execution, and does not create a stronger claim; telemetry remains internal
local metadata.

Phase 163 wires the formal-lane pipeline into the local soak path. The shipped
pipeline derives declared-only formal assertion templates when possible,
evaluates them through the shipped `NoopFormalVerifier`, and records declared
only formal-lane telemetry counters. Two focused tests in
`crates/zkbench-core/tests/phase_163_formal_lane_pipeline.rs` verify the
declared-only pipeline and soak telemetry. Phase 163 calls no formal tool,
creates no proof, creates no benchmark evidence, and does not escalate above
`Level0DesignNote` formal-lane metadata.

Phase 164 implements the four remaining deterministic local benchmark families:
`RecursiveEnvelope`, `MemoryHeavyStateMachine`, `PublicPrivateBoundaryStress`,
and `ZkMlControlFlowMixed`. It updates the family registry, generator config
constructors, template registry, soak generator mapping, zk-Harness dry-run
labels, and full-pipeline stress path. Focused tests in
`crates/zkbench-core/tests/phase_154_new_families.rs` and
`crates/zkbench-core/tests/phase_164_remaining_families.rs` verify generation,
local oracle evaluation, registry exposure, local JSON replay, soak handling,
and `Level1LocalReplay` claim caps. Phase 164 adds no live ZK backend, no zkML
execution, no benchmark evidence, no Level2+ evidence, and no stronger claim.

Phase 165 hardens the formal-lane pipeline observability layer without changing
claim strength. `FormalLanePipelineOutcome` now records the source
`MutationClass`, primary `FormalPropertyScopeKind`, optional proof status,
no-template reason, and mandatory nonclaims. Soak telemetry records
no-template, scope-count, and proof-status metrics, and validation rejects
impossible formal-lane counter relationships and classification drift. Focused
tests in `crates/zkbench-core/tests/phase_163_formal_lane_pipeline.rs` and
`crates/zkbench-core/tests/soak_telemetry.rs` verify derived and no-template
paths. Phase 165 calls no formal tool, creates no proof, creates no formal
evidence, creates no benchmark evidence, and does not escalate above
`Level0DesignNote` formal-lane metadata.

Phase 166 starts a bounded coverage campaign over local mutation code. It adds
focused tests for `PublicPrivateBoundaryMismatchPass` covering the class
reporter, public-input witness-policy movement, public-field reclassification,
observed-field reclassification, no-public-target failure, and
no-declared-trace failure. The targeted module moved from `50.00%` line /
`20.00%` function coverage to `100.00%` line / `100.00%` function coverage
under `cargo llvm-cov -p zkbench-core --all-features --summary-only`; one LLVM
region remains uncovered. Phase 166 changes no production Rust source, creates
no benchmark evidence, creates no Level2+ evidence, and does not claim
whole-workspace 100% coverage.

Phase 167 continues that bounded coverage campaign over local mutation code. It
adds focused tests for `TraceOrderingCorruptionPass` covering the class
reporter, deterministic first-two-step swapping, provenance metadata,
no-accepted-trace failure, and single-step-trace failure. The targeted module
moved from `69.44%` line / `33.33%` function / `83.33%` region coverage to
`100.00%` line / `100.00%` function / `100.00%` region coverage under
`cargo llvm-cov -p zkbench-core --all-features --summary-only`. Phase 167
changes no production Rust source, creates no benchmark evidence, creates no
Level2+ evidence, and does not claim whole-workspace 100% coverage.

## State Slice

This report touches only:

- `crates/hsai-attestation-phala/examples/operator_live_phala_api_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_api_artifact_contract.rs`
- `docs/106-phala-cloud-api-live-artifact-implementation-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_dcap_pccs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_dcap_pccs_contract.rs`
- `docs/107-phala-dcap-pccs-collateral-implementation-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_dcap_qvl_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_dcap_qvl_contract.rs`
- `docs/108-phala-local-dcap-qvl-verification-notes.md`
- `crates/hsai-attestation/examples/operator_live_jwks_artifact.rs`
- `crates/hsai-attestation/tests/managed_jwks_artifact_contract.rs`
- `docs/109-managed-jwks-fetch-artifact-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_local_pccs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_local_pccs_contract.rs`
- `docs/110-phala-local-pccs-service-artifact-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_intel_pcs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_intel_pcs_contract.rs`
- `docs/111-phala-intel-pcs-direct-artifact-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_tls_channel_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_tls_channel_contract.rs`
- `crates/hsai-e2e-harness/tests/claim_boundary_source_scan.rs`
- `docs/112-phala-tls-channel-binding-artifact-boundary-spec.md`
- `docs/113-phala-tls-channel-binding-artifact-implementation-notes.md`
- `crates/hsai-attestation-phala/Cargo.toml`
- `Cargo.lock`
- `crates/zkbench-core/tests/soak_runner_smoke.rs`
- `crates/zkbench-core/tests/phase_v_coverage_hardening.rs`
- `crates/zkbench-core/src/evidence/promotion_preflight.rs`
- `crates/zkbench-core/src/evidence/accepted_append.rs`
- `crates/zkbench-core/src/evidence/accepted_append_output.rs`
- `crates/zkbench-core/src/evidence/official_submission_output.rs`
- `crates/zkbench-core/src/evidence/external_submission_preflight.rs`
- `crates/zkbench-core/src/evidence/external_submission_preflight_output.rs`
- `crates/zkbench-core/tests/phase_w_promotion_preflight.rs`
- `crates/zkbench-core/tests/phase_w_accepted_ledger_append.rs`
- `docs/114-phase-w-promotion-preflight-boundary-spec.md`
- `docs/115-phase-w-promotion-preflight-implementation-notes.md`
- `docs/116-phase-w-accepted-ledger-append-boundary-spec.md`
- `docs/117-phase-w-accepted-ledger-append-implementation-notes.md`
- `docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md`
- `docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md`
- `docs/120-phase-w-official-submission-package-materialization-boundary-spec.md`
- `docs/121-phase-w-official-submission-package-materialization-implementation-notes.md`
- `docs/122-phase-w-external-replay-official-submission-boundary-spec.md`
- `docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md`
- `docs/124-phase-w-external-replay-preflight-output-boundary-spec.md`
- `docs/125-phase-w-external-replay-preflight-output-implementation-notes.md`
- `docs/126-phase-w-coverage-hardening-notes.md`
- `docs/127-phase-dsl-coverage-campaign-notes.md`
- `crates/zkbench-core/tests/oracle_eval.rs`
- `crates/zkbench-core/tests/lowering.rs`
- `docs/128-phase-soak-serialization-coverage-notes.md`
- `crates/zkbench-core/tests/soak_serialization.rs`
- `docs/129-phase-proposal-validation-coverage-notes.md`
- `crates/zkbench-core/tests/evidence_append_proposal.rs`
- `docs/130-phase-phala-provider-coverage-notes.md`
- `crates/hsai-attestation-phala/tests/phala_operator_live_provider_client.rs`
- `docs/131-phase-phala-artifact-coverage-notes.md`
- `crates/hsai-attestation-phala/tests/phala_artifact.rs`
- `docs/132-phase-local-json-adapter-coverage-notes.md`
- `crates/zkbench-core/tests/local_json_adapter.rs`
- `docs/133-phase-zk-harness-export-coverage-notes.md`
- `crates/zkbench-core/tests/zk_harness_pack_mapping.rs`
- `docs/134-pcsm-governed-agent-admission-boundary-spec.md`
- `docs/135-phase-zk-harness-validation-coverage-notes.md`
- `crates/zkbench-core/tests/zk_harness_dry_run_plan.rs`
- `docs/136-phase-hsai-agent-admission-core-notes.md`
- `crates/hsai-agent-admission/Cargo.toml`
- `crates/hsai-agent-admission/src/lib.rs`
- `docs/137-phase-hsai-admission-e2e-harness-notes.md`
- `crates/hsai-e2e-harness/Cargo.toml`
- `crates/hsai-e2e-harness/src/lib.rs`
- `docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md`
- `docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md`
- `docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md`
- `docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md`
- `docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md`
- `docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md`
- `docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md`
- `docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md`
- `docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md`
- `docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md`
- `docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md`
- `docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md`
- `docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md`
- `docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md`
- `docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md`
- `docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md`
- `docs/154-phase-new-benchmark-families-boundary-spec.md`
- `docs/154-phase-new-benchmark-families-implementation-notes.md`
- `docs/155-phase-operator-soak-campaign-runner-boundary-spec.md`
- `docs/155-phase-operator-soak-campaign-runner-implementation-notes.md`
- `docs/156-phase-mutation-engine-depth-boundary-spec.md`
- `docs/156-phase-mutation-engine-depth-implementation-notes.md`
- `docs/157-phase-mutation-distinguishability-scoring-boundary-spec.md`
- `docs/157-phase-mutation-distinguishability-scoring-implementation-notes.md`
- `docs/158-phase-oracle-completeness-audit-boundary-spec.md`
- `docs/158-phase-oracle-completeness-audit-implementation-notes.md`
- `docs/159-phase-formal-lane-interface-stub-boundary-spec.md`
- `docs/159-phase-formal-lane-interface-stub-implementation-notes.md`
- `docs/160-phase-mutation-formal-cross-product-boundary-spec.md`
- `docs/160-phase-mutation-formal-cross-product-implementation-notes.md`
- `docs/161-phase-mutation-engine-completion-implementation-notes.md`
- `docs/162-phase-distinguishability-soak-telemetry-implementation-notes.md`
- `docs/163-phase-formal-lane-pipeline-implementation-notes.md`
- `docs/164-phase-remaining-benchmark-families-implementation-notes.md`
- `docs/165-phase-formal-pipeline-observability-hardening-notes.md`
- `docs/166-phase-mutation-coverage-first-tranche-notes.md`
- `docs/167-phase-mutation-coverage-second-tranche-notes.md`
- `crates/zkbench-core/examples/operator_soak_campaign.rs`
- `crates/zkbench-core/src/adapters/zk_harness/mapping.rs`
- `crates/zkbench-core/src/dsl/oracle_completeness.rs`
- `crates/zkbench-core/src/formal/`
- `crates/zkbench-core/src/generator/config.rs`
- `crates/zkbench-core/src/generator/deterministic.rs`
- `crates/zkbench-core/src/generator/templates.rs`
- `crates/zkbench-core/src/mutation/apply.rs`
- `crates/zkbench-core/src/mutation/invalid_unroll_bounds.rs`
- `crates/zkbench-core/src/mutation/invariant_strengthening.rs`
- `crates/zkbench-core/src/mutation/invariant_weakening.rs`
- `crates/zkbench-core/src/mutation/nondeterministic_transition_injection.rs`
- `crates/zkbench-core/src/mutation/observation_omission.rs`
- `crates/zkbench-core/src/mutation/public_private_boundary_mismatch.rs`
- `crates/zkbench-core/src/mutation/recursion_envelope_mismatch.rs`
- `crates/zkbench-core/src/mutation/semantic_no_op_drift.rs`
- `crates/zkbench-core/src/mutation/stale_state_reads.rs`
- `crates/zkbench-core/src/mutation/trace_ordering_corruption.rs`
- `crates/zkbench-core/src/mutation/witness_aliasing.rs`
- `crates/zkbench-core/src/scoring/distinguishability.rs`
- `crates/zkbench-core/src/soak/telemetry.rs`
- `crates/zkbench-core/tests/operator_soak_campaign_contract.rs`
- `crates/zkbench-core/tests/phase_154_new_families.rs`
- `crates/zkbench-core/tests/phase_156_mutation_depth.rs`
- `crates/zkbench-core/tests/phase_157_distinguishability.rs`
- `crates/zkbench-core/tests/phase_158_oracle_completeness.rs`
- `crates/zkbench-core/tests/phase_159_formal_lane.rs`
- `crates/zkbench-core/tests/phase_160_cross_product.rs`
- `crates/zkbench-core/tests/phase_161_mutation_completion.rs`
- `crates/zkbench-core/tests/phase_162_distinguishability_telemetry.rs`
- `crates/zkbench-core/tests/phase_163_formal_lane_pipeline.rs`
- `crates/zkbench-core/tests/phase_164_remaining_families.rs`
- `crates/zkbench-core/tests/soak_telemetry.rs`
- `Cargo.lock`
- `Cargo.toml`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

It does not change fixtures, generated artifacts, accepted Evidence Ledgers,
benchmark packs, report bundles, audit-index outputs, ergonomics outputs,
package runtime files, command-line tools outside operator-only examples, or UI
artifacts.

## Validation Commands

Run from repository root during Phase 167 coverage validation.

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test phase_161_mutation_completion
cargo test -p zkbench-core --test phase_163_formal_lane_pipeline
cargo test -p zkbench-core --test soak_telemetry
cargo check -p zkbench-core --examples
cargo test -p hsai-agent-admission
cargo test -p hsai-e2e-harness
cargo test -p zkbench-core
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
cargo llvm-cov -p zkbench-core --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml'
```

Phase 167 coverage validation passed. `cargo test --workspace --all-features`,
workspace clippy, workspace docs, `cargo check -p zkbench-core --examples`,
`cargo test -p hsai-agent-admission`, `cargo test -p hsai-e2e-harness`, and
`cargo test -p zkbench-core` all passed with all nine local generator families
implemented and all 14 declared mutation classes dispatching through the local
mutation engine. Focused Phase 167 checks verify the trace-ordering corruption
pass class reporter, deterministic first-two-step swapping, provenance
metadata, and fail-closed no-accepted-trace/single-step-trace paths. The `rg`
package-surface check
returned no package files (exit code 1 with empty output), confirming no
`package.json` or `pnpm-lock.yaml` surface exists.

No `package.json` or `pnpm-lock.yaml` exists in this repository, so no `pnpm`
gate is available.

The Phase 167 post-tranche
`cargo llvm-cov --workspace --all-features --summary-only` run reported
`88.05%` region coverage, `84.45%` function execution, and `86.55%` line
coverage across the workspace. The Phase 167 post-tranche
`cargo llvm-cov -p zkbench-core --all-features --summary-only` run reported
`84.39%` region coverage, `80.34%` function execution, and `83.05%` line
coverage for `zkbench-core`; the targeted `trace_ordering_corruption.rs` module
reported `100.00%` region coverage, `100.00%` function execution, and
`100.00%` line coverage. Branch coverage was not reported by these runs.

These coverage percentages are local test instrumentation only; they are not
100% coverage, production readiness, semantic correctness, official benchmark
evidence, official accepted Evidence Ledger mutation, or Level2+ evidence.

## Efficacy Map

The suite exercises the repo as a set of bounded local systems:

- DSL parsing, lowering, oracle evaluation, and generated fixtures.
- Deterministic generation, mutation, local JSON replay, and stress paths.
- Evidence primitives, evidence ledgers, append previews, review ledgers,
  proposal ledgers, and candidate validation.
- Benchmark pack writing/reading, pack-readiness metadata, score reports, and
  local-only claim-boundary checks.
- zk-Harness dry-run planning, inert execution metadata, manual handoff mapping,
  and no-live-execution guards.
- Phase L soak configuration, sharding, resume checkpoints, telemetry, health
  reports, failure corpus, and local campaign aggregation.
- Phase M recursion-envelope metadata and manual handoff mapping.
- Phase N zkML workload manifest metadata.
- Phase O pack-readiness construction and output plumbing.
- Phase P read-only dashboard/reporting metadata.
- Phase Q report-bundle metadata and adjacent output plumbing.
- Phase R local audit-index metadata and adjacent output plumbing.
- Phase S audit-index ergonomics, materialized output plumbing, stale-digest
  rejection, symlink rejection, partial-bundle rejection, non-repair overwrite
  behavior, and protected-path overlap hardening.
- Phase T cross-bundle audit-index in-memory views and materialized output
  plumbing, duplicate/conflict signal preservation, declared-file output,
  digest sidecars, stale-digest rejection, symlink rejection, partial-bundle
  rejection, corrupted-root non-repair, and protected-path overlap hardening.
- Phase U local benchmark artifact manifest validation, deterministic Markdown
  rendering, declared-file output, digest sidecars, stale-digest rejection,
  symlink-resolved protected overlap rejection, symlink rejection,
  partial-bundle rejection, corrupted-root non-repair, accepted Evidence Ledger
  non-mutation, score-axis non-population, and protected-path overlap
  hardening.
- Phase V local artifact campaign manifest validation, Phase U output-root
  validation before campaign input construction, deterministic validation
  reports and Markdown rendering, declared-file output, digest sidecars,
  stale-digest rejection, symlink-resolved protected overlap rejection, symlink
  rejection, partial-campaign rejection, corrupted-root non-repair, accepted
  Evidence Ledger non-mutation, score-axis non-population, and protected-path
  overlap hardening.
- Phase W reviewed promotion preflight metadata, accepted-ledger append
  validation, local accepted-ledger JSON materialization, local
  official-submission package output plumbing, accepted-ledger id matching,
  deterministic package JSON/Markdown output, digest sidecars, stale-digest
  rejection, unexpected-file rejection, overwrite package-drift rejection,
  official-endpoint non-submission, and score-axis non-population.
- HSAI claim-envelope algebra, agent-case lanes, distinct-agent registry,
  managed attestation, offline managed-JWT verification, Phala fixture and
  captured-artifact validation, hermetic fake-client live-verifier surface,
  operator-live artifact plumbing, opt-in Phala provider-client plumbing,
  operator-live runner source-contract checks, Phala API artifact
  materialization source-contract checks, Phala DCAP/PCCS collateral
  materialization source-contract checks, Phala local DCAP/QVL verification
  artifact source-contract checks, managed JWKS artifact source-contract
  checks, Phase 4 anchor registry, economy, membrane, economy simulation, and
  e2e harness invariants.

The strongest local statement supported by this run is:

The implemented local Rust foundation remains internally consistent under the
available unit, integration, doc, lint, formatting, hygiene, and claim-boundary
gates.

## Function-Level Boundary

This validation is function-aware through Rust unit tests, integration tests,
doc tests, clippy, and public API documentation generation. It is not
function-exhaustive proof.

The suite checks behavior through invariants, round trips, adversarial
fixtures, source scans, failure-mode tests, and cross-crate composition tests.
It does not prove that every function is covered by a test, that every branch is
exercised, or that every valid domain input has been sampled.

## Wholeness Boundary

The repo's current wholeness is local and compositional:

- local data models are serialized, deserialized, digested, and validated;
- output plumbing rejects drift instead of repairing corrupted roots;
- source metadata mutation remains forbidden where phases require read-only
  behavior;
- claim boundaries remain capped at their documented levels;
- live provider behavior, network calls, external benchmark execution, and
  official evidence promotion remain blocked unless a later explicit phase
  authorizes them.

This is not production readiness and not benchmark evidence. It is local
regression evidence that the implemented parts still fit together without
claim-boundary escalation.

## Residual Gaps

- No live external backend beyond the operator-run Phala calls, operator-run
  local QVL verification, operator-run managed JWKS fetch, operator-run
  localhost PCCS-compatible replay service, and operator-run direct Intel PCS
  QVL verification was exercised. No live managed-JWT token acceptance or TLS
  channel binding was exercised.
  `docs/97-phala-operator-live-invocation-boundary-spec.md` now defines the
  docs-first invocation boundary, and
  `docs/100-phala-operator-live-invocation-implementation-notes.md` now records
  local invocation plumbing with a hermetic credential-provider boundary,
  injected client boundary, redacted artifact-bundle assembly, replay checks,
  and fail-closed tests. No shipped network client, live Phala call, real
  operator credential source, operator live test, DCAP/PCCS/TLS path in that
  Phala invocation slice, or generated operator artifact exists.
  `docs/101-phala-operator-live-provider-client-boundary-spec.md` now defines
  the future concrete provider-client boundary behind the Phase 100 seam.
  `docs/102-phala-operator-live-provider-client-implementation-notes.md` now
  records an opt-in feature-gated provider-client implementation with a
  transport seam, allowlisted environment credential provider, ureq-backed HTTP
  transport, raw-response digest replacement, and hermetic fake-transport
  tests. `docs/104-phala-operator-live-runner-boundary-spec.md` defines the
  operator-only runner boundary, and
  `docs/105-phala-operator-live-runner-implementation-notes.md` records the
  feature-gated `operator_live_run` example that requires explicit
  acknowledgement, non-secret invocation JSON, matching credential-source
  declaration, and an operator-owned credential environment.
  `docs/106-phala-cloud-api-live-artifact-implementation-notes.md` records the
  Phala Cloud API response materialization path. During Phase 106, an
  operator-run Phala Cloud `/attestations/verify` call accepted the submitted
  TDX quote with checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`, and a
  local redacted `operator-live/*` artifact was generated outside git. No
  generated operator artifact is committed, and no local DCAP/PCCS/TLS path,
  accepted Evidence Ledger mutation, official benchmark submission, or claim
  above `Attested` exists.
  `docs/107-phala-dcap-pccs-collateral-implementation-notes.md` records the
  operator-only Phala Cloud collateral materialization path. During Phase 107,
  an operator-run Phala Cloud `/attestations/collateral/<checksum>` call
  returned the required collateral fields for checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`, and a
  digest-only local `dcap-pccs/*` artifact was generated outside git. No raw
  collateral response is retained in the materialized output, no generated
  collateral artifact is committed, no local Intel QVL/DCAP quote-signature
  verification exists, and no TLS path, accepted Evidence Ledger mutation,
  official benchmark submission, or claim above `Attested` exists.
  `docs/108-phala-local-dcap-qvl-verification-notes.md` records the
  operator-only local DCAP/QVL verification artifact path. During Phase 108,
  the raw quote for checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd` was
  downloaded as a 5010-byte binary attachment with SHA-256
  `7c92c34ddc9634c873ea1ca4953a45883ed5692a0c3865323e2044fc58aaf26e`, and
  `dcap-qvl` 0.5.2 verified it with QVL, QE, and platform status `UpToDate`
  and empty advisory IDs. The digest-only local `dcap-qvl/*` artifact was
  generated outside git. No raw quote or QVL report is committed, no repo-native
  DCAP verifier implementation exists, and no TLS path, accepted Evidence
  Ledger mutation, official benchmark submission, or claim above `Attested`
  exists.
  `docs/109-managed-jwks-fetch-artifact-notes.md` records the operator-only
  managed JWKS fetch artifact path. During Phase 109, Intel Trust Authority
  OpenID metadata was fetched from
  `https://portal.trustauthority.intel.com/.well-known/openid-configuration`
  as a 663-byte JSON response with SHA-256
  `a330c2032a986845f959284c4202972bc5e698d7ea652423ca5cebc4ea33edea`, and
  JWKS was fetched from `https://portal.trustauthority.intel.com/certs` as an
  11562-byte JSON response with SHA-256
  `4e1d55c79b698cde4987d791594495e70432879be621a1b6e42a9daafc84bee3`.
  The digest-only local `managed-jwks/*` artifact was generated outside git. No
  raw OpenID or JWKS response is committed, no token is accepted, no live
  managed-JWT signature verification exists, and no TLS path, accepted Evidence
  Ledger mutation, official benchmark submission, or claim above `Attested`
  exists.
  `docs/110-phala-local-pccs-service-artifact-notes.md` records the
  operator-only localhost PCCS-compatible replay service artifact path. During
  Phase 110, `PCCS_URL=http://127.0.0.1:38119 dcap-qvl verify` fetched four
  localhost PCCS-shaped endpoints and returned QVL, QE, and platform status
  `UpToDate` with empty advisory IDs. The final access log SHA-256 was
  `936d86e8e080df2e7b68bfb559b6d43aca5e6df5cbb7ffb1ca2152698531fd77`, and
  the QVL report SHA-256 was
  `36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7`.
  The digest-only local `local-pccs/*` artifact was generated outside git. No
  raw local PCCS access log or response body is committed, no production Intel
  PCS/PCCS operation exists, no fresh collateral authority is claimed, and no
  TLS path, accepted Evidence Ledger mutation, official benchmark submission,
  or claim above `Attested` exists.
  `docs/111-phala-intel-pcs-direct-artifact-notes.md` records the
  operator-only direct Intel PCS QVL artifact path. During Phase 111,
  `PCCS_URL=https://api.trustedservices.intel.com dcap-qvl verify` returned
  QVL, QE, and platform status `UpToDate` with empty advisory IDs. The QVL
  report SHA-256 was
  `36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7`, and
  verifier stderr SHA-256 was
  `0e49aa6e694e9654fb3686b74644d340269946900cdfc67954b35254af30474c`.
  The digest-only local `intel-pcs/*` artifact was generated outside git. No
  raw QVL report or raw quote is committed, no repo-native DCAP verifier exists,
  and no TLS path, accepted Evidence Ledger mutation, official benchmark
  submission, or claim above `Attested` exists.
  `docs/113-phala-tls-channel-binding-artifact-implementation-notes.md`
  records the operator-only TLS 1.3 channel artifact path. During Phase 113,
  rustls negotiated `TLS13_AES_256_GCM_SHA384` with
  `cloud-api.phala.com`, validated a three-certificate Web PKI chain, derived a
  32-byte RFC 9266 `EXPORTER-Channel-Binding` value, and received HTTP 200 for
  accepted TDX checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`
  on that same connection. The exporter SHA-256 was
  `a88d764e3daf48ec6a56cb31890304d3cbc5c4a8d6b140e07b5504d485bde9d7`.
  Exactly five digest-bound files were generated outside git. No credential,
  raw exporter, raw response, or peer certificate is committed. This is
  client-local connection evidence, not RA-TLS, an attested server
  certificate, independent evidence, accepted evidence, or proof.
- No committed generated benchmark artifact bundle, official benchmark
  submission, or committed accepted Evidence Ledger JSON file was created.
  Phase U now
  implements local artifact-bundle packaging APIs and hermetic temp-root tests,
  but it does not create durable submitted artifacts or promote them.
  `docs/98-phase-v-local-artifact-campaign-boundary-spec.md` defines the
  durable local artifact campaign boundary, and
  `docs/103-phase-v-local-artifact-campaign-implementation-notes.md` records
  local campaign output-plumbing APIs and hermetic tests. No committed durable
  campaign output, materialized official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+
  evidence exists.
  `docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md` now defines the
  future reviewed accepted-evidence and official-submission boundary. Phase 115
  adds inert official-submission package metadata validation only. No durable
  submitted artifact, materialized official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+ evidence
  exists.
  `docs/116-phase-w-accepted-ledger-append-boundary-spec.md` defines the next
  docs-first boundary for a future local accepted-ledger append transaction over
  explicit inputs. It authorizes no Rust implementation and no accepted Evidence
  Ledger mutation. No accepted ledger entry, official benchmark submission,
  external replay evidence, score-axis population, or Level2+ evidence exists.
  `docs/117-phase-w-accepted-ledger-append-implementation-notes.md` records the
  guarded local implementation of that transaction surface. It can append a
  Level1-or-below reviewed record into a caller-supplied in-memory
  `EvidenceLedger` only after preflight, candidate, review, preview, digest,
  and ledger-tip validation pass. No official benchmark submission, external
  replay evidence, score-axis population, or Level2+ evidence exists.
  `docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md` and
  `docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md`
  record local JSON materialization for that guarded append. It can load or
  create one explicit local ledger file, reject unsafe paths, apply the Phase
  117 transaction, and write the appended ledger through a same-directory
  temporary JSON file. No official benchmark submission, external replay
  evidence, score-axis population, or Level2+ evidence exists.
  `docs/120-phase-w-official-submission-package-materialization-boundary-spec.md`
  and
  `docs/121-phase-w-official-submission-package-materialization-implementation-notes.md`
  record local package materialization from valid official-submission metadata
  plus an accepted ledger JSON file. It can write declared digest-bound local
  review files only. No committed generated package output, official endpoint
  call, official benchmark submission, score-axis population, or Level2+
  evidence exists.
  `docs/122-phase-w-external-replay-official-submission-boundary-spec.md`
  defines the next docs-first boundary for future external replay and official
  submission promotion. It authorizes no implementation, external replay
  execution, official endpoint call, credentials, generated output, accepted
  Evidence Ledger mutation, score-axis population, or Level2+ evidence.
  `docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md`
  records local metadata preflight over accepted ledger JSON plus Phase 121
  package output. It validates operator acknowledgement, expected digests,
  future output-root safety, redaction policy, external replay provenance,
  source artifact digests, and claim-class separation. It runs no external
  replay, calls no endpoint, uses no credentials, writes no generated output,
  mutates no accepted Evidence Ledger, populates no score axes, and creates no
  Level2+ evidence.
  `docs/124-phase-w-external-replay-preflight-output-boundary-spec.md` defines
  the next docs-first boundary for a future local output-root materializer for
  those preflight reports. It authorizes no implementation, generated output,
  committed artifact, external replay execution, official endpoint call,
  credential access, accepted Evidence Ledger mutation, score-axis population,
  or Level2+ evidence.
  `docs/125-phase-w-external-replay-preflight-output-implementation-notes.md`
  records local output plumbing for those preflight reports. It writes and
  reads declared digest-bound review files only, rejects drift and
  raw-material retention, and still performs no external replay, endpoint call,
  credential access, accepted Evidence Ledger mutation, score-axis population,
  or Level2+ evidence creation.
- No broader Phase S ergonomics surface was authorized or tested beyond the
  implemented single-index local output boundary.

Any next broadening should start with a docs-first boundary and should name the
state slice before mutation.
