# Phase 796-A3L5H HSAI P01B Authority Adapter Correction

## Status

Documentation-only correction. Scores remain unchanged.

This phase closes an ambiguity in Phase 796-A3L5C before any A3L7 readiness
command or A3L8 container command may run. It defines exact P01B wrapper
documents around the existing HSAI gateway admission objects. It does not
change Rust, Python, Cargo metadata, fixtures, package metadata, Docker state,
the registry, the network, retained runtime artifacts, accepted Evidence
Ledger state, or any score.

## Reason For Correction

A3L5C requires `authority/action.json`, `authority/policy.json`,
`authority/evidence-bundle.json`, and `authority/admission-decision.json` to
retain prior validated HSAI schemas and semantically authorize the exact local
program. That statement is insufficient to implement safely:

- `GatewayActionProposal`, `GatewayActionPolicy`, `AgentAdmissionCandidate`,
  and `AgentAdmissionDecision` do not serialize a `schema` field;
- `GatewayActionPolicy` has no production digest/domain;
- the prior objects do not encode the P01B implementation commit/tree,
  readiness-plan binding, claim-boundary binding, or network scope;
- A3L5C freezes no P01B program id, action id, target, source-artifact role,
  deterministic model-lane binding, or adapter validation rule;
- accepting arbitrary nonempty schema-labelled objects would allow C10 to
  close without reconstructing the production HSAI admission path.

Therefore C10 remains fail-closed until the adapter specified here is
implemented and tested. A digest match without the complete semantic
reconstruction below is invalid authority evidence.

## State Slice

This docs-first correction may change exactly:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l5h-phase-hsai-p01b-authority-adapter-correction.md
docs/90-whole-codebase-validation-report.md
```

Concurrent Statebook work and
`crates/hsai-agent-admission/src/lib.rs` remain outside this state slice and
unstaged. The admission source must remain byte-identical at SHA-256
`41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de`.

After this correction is committed and independently accepted, the existing
five-file A3L6 implementation slice may implement these adapters under the
A3L5C phase order. A3L7 remains prohibited until that exact five-file commit
passes its pinned gates and two independent zero-finding code reviews.

## Existing Production Objects

The adapter reuses, rather than replaces, the exact existing Serde objects.

`GatewayActionProposal` fields in Rust declaration order are:

```text
id,subject,action_kind,target,value_units,source_artifact_digests,nonclaims,
model_lane,threat_labels,direct_authority_requested,
signer_or_tool_requested_before_admission
```

Its production digest is SHA-256 of compact UTF-8 Serde JSON:

```text
["hsai-agent-admission:gateway-action-proposal:v1",<proposal>]
```

`GatewayActionPolicy` fields are:

```text
id,admission_policy,allowed_action_kinds,allowed_targets,max_value_units,
require_non_secret_model_lane
```

Its nested `AgentAdmissionPolicy` fields are:

```text
id,max_claim_boundary,required_nonclaims,require_source_artifacts,
allow_provider_direct_authority
```

There is no existing production policy digest. The P01B policy wrapper below
provides the missing domain without changing Rust.

`AgentAdmissionCandidate` fields in declaration order are:

```text
id,subject,source_kind,strict_typed,case,proposed_envelope,gateway_action,
gateway_policy_violations,requested_claim_boundary,source_artifact_digests,
nonclaims,provider_direct_authority_requested,
accepted_ledger_mutation_requested,score_axis_population_requested,
external_or_formal_evidence_claimed
```

For the accepted gateway candidate, `gateway_policy_violations` is absent
because Serde skips the empty set; `case` and `proposed_envelope` are JSON
null; and `gateway_action` is present. Its production digest is SHA-256 of:

```text
["hsai-agent-admission:candidate:v1",<candidate>]
```

`AgentAdmissionDecision` fields are:

```text
candidate_id,policy_id,verdict,reasons,candidate_digest,accepted_envelope
```

The accepted gateway decision has `verdict="Accepted"`, `reasons=[]`, and
`accepted_envelope=null`. Its production digest is SHA-256 of:

```text
["hsai-agent-admission:decision:v1",<decision>]
```

Rust newtypes serialize as bare strings. Unit enums serialize as their exact
case-sensitive variant names. `Hash` serializes as an array of 32 JSON integer
bytes. `BTreeSet` serializes in derived Rust `Ord` order. Production tagged
digests use Rust declaration order and compact `serde_json`; they are not P01B
sorted-key/NUL-domain digests. The adapter reconstructs both encodings and
rejects substitution between them.

## Exact Wrapper Documents

All wrapper JSON retains the A3L5C canonical sorted-key ASCII,
duplicate-key-rejecting, newline-free rule. A wrapper domain digest is:

```text
SHA256(ASCII(domain) || NUL || canonical_json_bytes(wrapper))
```

The raw SHA-256 of the stored wrapper bytes remains a separate candidate
manifest entry digest.

### Action document

Schema/domain:

```text
hsai-p01b-gateway-action-document-v1
hsai:p01b-gateway-action-document:v1
```

Exact fields:

```text
schema,program_id,network_scope,user_authorization_sha256,
implementation_commit,implementation_tree,a3l6_gate_bundle_sha256,
readiness_plan_sha256,claim_boundary_sha256,proposal_sha256,proposal
```

`proposal` is the exact `GatewayActionProposal`. `proposal_sha256` is its
production tagged digest. Every A3L5C `action_sha256` field is the wrapper
domain digest, not the raw file digest and not the proposal digest.

### Policy document

Schema/domain:

```text
hsai-p01b-gateway-policy-document-v1
hsai:p01b-gateway-policy-document:v1
```

Exact fields:

```text
schema,program_id,network_scope,implementation_commit,implementation_tree,
readiness_plan_sha256,claim_boundary_sha256,gateway_policy
```

`gateway_policy` is the exact `GatewayActionPolicy`. Every A3L5C
`policy_sha256` field is this wrapper's domain digest.

### Evidence-bundle document

Schema/domain:

```text
hsai-p01b-gateway-evidence-bundle-v1
hsai:p01b-gateway-evidence-bundle:v1
```

Exact fields:

```text
schema,action_sha256,policy_sha256,candidate_sha256,candidate
```

`candidate` must equal the exact output of
`gateway_action_candidate(action.proposal, policy.gateway_policy)`.
`candidate_sha256` is its production tagged digest. Every A3L5C
`evidence_bundle_sha256` field is this wrapper's domain digest.

### Admission-decision document

Schema/domain:

```text
hsai-p01b-gateway-admission-decision-v1
hsai:p01b-gateway-admission-decision:v1
```

Exact fields:

```text
schema,action_sha256,policy_sha256,evidence_bundle_sha256,decision_sha256,
decision
```

`decision` must equal the exact output of
`evaluate_admission(candidate, gateway_policy.admission_policy)`.
`decision_sha256` is its production tagged digest. Every A3L5C
`admission_decision_sha256` field is this wrapper's domain digest.

## Frozen Program And Network Scope

The exact `program_id` and proposal target are:

```text
hsai-p01b-retained-normal-oom-v1
```

The exact `network_scope` string in both action and policy wrappers is:

```text
a3l7-registry-read-index-platform-only;a3l8-local-docker-unix-control-plane-only;container-network-none;no-pull;no-build;no-login;no-other-registry;no-remote-endpoint;a3l9-no-network
```

This scope has one interpretation:

- only readiness roles `registry-index` and `registry-platform` may use the
  registry/network, through the exact readiness-plan argv;
- the remaining A3L7 commands are local observations;
- A3L8 may address only the frozen local Unix Docker endpoint, use only the
  already-resolved platform digest, and create both containers with
  `--network=none`;
- A3L8 may not pull, build, log in, resolve a tag, contact a registry, use a
  remote Docker host, launch a shell, or accept caller argv/environment/
  endpoint overrides;
- A3L9 uses only fresh local direct processes and no network.

The exact action id is:

```text
"p01b-" + user_authorization_sha256[0:16] + "-" + implementation_commit[0:16]
```

The exact subject is `hsai-p01b-local-operator`. The proposal has
`action_kind="ToolCall"`, `value_units=0`, `threat_labels=["Benign"]`,
`direct_authority_requested=false`, and
`signer_or_tool_requested_before_admission=false`.

The outer policy id is `hsai-p01b-local-policy-v1`. The nested admission
policy id is `hsai-p01b-local-admission-v1`. The nested maximum claim boundary
is `LocalOnly`; source artifacts are required; provider direct authority is
forbidden. Allowed kinds and targets are the singleton `ToolCall` and program
id sets. Maximum value is zero and non-secret model-lane provenance is
required.

The proposal and policy required-nonclaim set is exactly the existing
`gateway_required_nonclaims()` set in Rust `BTreeSet` wire order:

```text
no score-axis population
not Level2+ evidence
not accepted Evidence Ledger mutation
not direct authority
not model-granted authority
not production readiness
not semantic correctness
```

The separately bound A3L5C claim-boundary object retains its exact ten ordered
nonclaims and `Level1LocalReplayOrLower` ceiling. Neither nonclaim set may be
used as a substitute for the other.

## Exact Source Artifacts And Model Lane

The proposal source-artifact set contains exactly these ids in this order:

```text
p01b-a3l6-gate-bundle
p01b-claim-boundary
p01b-implementation-commit
p01b-implementation-tree
p01b-readiness-plan
p01b-user-authorization
```

Their `Hash` values are respectively:

- decoded A3L6 gate-bundle domain digest;
- decoded claim-boundary domain digest;
- SHA-256 of the lowercase ASCII implementation commit id;
- SHA-256 of the lowercase ASCII implementation tree id;
- decoded readiness-plan domain digest;
- decoded raw user-authorization SHA-256.

Missing, extra, duplicate-id, conflicting, zero, reordered, or differently
derived source artifacts reject.

The exact deterministic model lane is:

```text
lane_kind             Deterministic
model_family          hsai-p01b-authority-adapter
artifact_id           hsai-p01b-a3l7-authority-adapter-v1
runtime               python-stdlib-no-model-execution
non_secret            true
```

Its three inherited `Hash` fields are domain digests of these exact auxiliary
pure-data values:

```text
hsai:p01b-gateway-action-template:v1
  schema,program_id,action_kind,target,value_units

hsai:p01b-gateway-action-input:v1
  schema,program_id,user_authorization_sha256,implementation_commit,
  implementation_tree,a3l6_gate_bundle_sha256,readiness_plan_sha256,
  claim_boundary_sha256

hsai:p01b-gateway-action-output:v1
  schema,id,subject,action_kind,target,value_units,source_artifact_digests,
  nonclaims,threat_labels,direct_authority_requested,
  signer_or_tool_requested_before_admission
```

The schemas are respectively
`hsai-p01b-gateway-action-template-v1`,
`hsai-p01b-gateway-action-input-v1`, and
`hsai-p01b-gateway-action-output-v1`. The output intentionally excludes
`model_lane`, preventing a digest cycle. The lowercase digest hex is decoded
to the 32 integer bytes serialized by `Hash`. No model runs.

## Exact Semantic Reconstruction

The validator must perform all of the following before preauthorization or
C10 can accept:

1. Strictly parse each canonical wrapper; reject duplicate, missing, or extra
   wrapper and embedded fields.
2. Reconstruct each embedded Rust Serde type field-for-field, including exact
   unit-enum spelling, newtype strings, `Hash` arrays, set order, and the
   omitted empty `gateway_policy_violations` field.
3. Recompute the three production tagged hashes with Rust declaration order,
   compact UTF-8 Serde JSON, and the exact production tags.
4. Recompute the three auxiliary model-lane domains, six source-artifact
   values, and all four wrapper domains.
5. Reconstruct `gateway_action_candidate`; require exact equality, source kind
   `GatewayActionProposal`, `strict_typed=true`, null case/envelope, the exact
   embedded action, absent empty policy violations, `LocalOnly`, and all four
   provider/promotion/evidence flags false.
6. Reconstruct `evaluate_admission`; require `Accepted`, empty reasons, the
   exact candidate digest and policy id, and null accepted envelope.
7. Reconstruct `accepted_gateway_handoff` ephemerally and require an accepted
   handoff with the exact ToolCall id, subject, target, value, candidate digest,
   and decision digest. The handoff is validation output, not a fifth
   authority file and not permission for any other tool.
8. Cross-bind action, policy, evidence, and decision wrapper domain digests;
   common program/network/implementation/readiness/claim values; the raw user
   authorization; the A3L6 bundle; and the later expected-bindings document.
9. Revalidate the exact code-owned readiness, campaign, normal, and OOM plan
   grammars. Each postauthorization plan binds authorization-v3 one-way.
10. Reject any plan that violates the frozen network scope or introduces an
    authorization/plan digest cycle.

The P01B adapter independently mirrors the protected Rust semantics under the
explicit `reviewed-gate-test-code-honest` assumption. It does not alter or
claim to prove the Rust implementation.

## Acyclic Construction Order

```text
A  exact user bytes + implementation identities + accepted A3L6 bundle
   + fixed claim boundary
B  exact code-owned readiness plan
C  action and policy wrapper documents
D  recomputed gateway candidate and evidence-bundle wrapper
E  recomputed accepted admission decision wrapper
F  preauthorization-v2 binds the four wrapper digests, A3L6 bundle,
   implementation identities, user bytes, and readiness-plan digest
G  create/revalidate immutable snapshot; execute the six readiness commands
H  expected-bindings document
I  authorization root and authorization-v3
J  campaign, normal, and OOM plans bind authorization-v3 one-way
```

No action, policy, evidence, decision, preauthorization, authorization-root,
or authorization-v3 digest includes a postauthorization plan digest. The
adapter authorizes only the implementation-bound fixed plan grammar; the final
plans bind the resulting authorization digest. This preserves the A3L5C
acyclic graph.

## Frozen Empty-Object Domain Vectors

For canonical `{}` bytes:

```text
action-document     5583fd64e6dab08c03d25a478e380634fac45fed4b93ef1bae87c109ba13b3d9
policy-document     c75a491d000d7eb759e202c4ed207605c4b28a5731362e8e4f9ebe705b93ab41
evidence-bundle     db896051d190437c92de552cc224d5a44b7097972f6118e6526c13133e95702d
admission-decision  2c3ebf0c38e076cb94fb9f604cdd19457576f8ff4ed53cda9566ec43c80f2226
action-template     a07f52ce9a8e82e8a2e25cfc8b19b4b2ef9f7a06ca430480c66752a37ca6be1e
action-input        a6305ff8d1630ab036867b5eb2ec28e7bc52aa65cf7b00f54b46cb5c281ad423
action-output       280151bf4431ca28be7ec9a9fba362e7be19f3251d1b122daf838d21a50d4a81
```

## Mandatory Negative Tests

The exact 32-test focused evidence suite and exact 32-test focused execution
suite must retain their counts while covering at least:

- missing, extra, duplicate, or reordered wrapper/embedded fields;
- wrapper schema/domain drift and raw-file/domain-digest substitution;
- P01B NUL-domain and Rust tagged-digest substitution in both directions;
- Rust declaration-order, enum, newtype, `Hash`, set-order, UTF-8, or escape
  drift;
- fixed program, network, action, subject, policy, target, kind, value, threat,
  source-artifact, nonclaim, or model-lane drift;
- zero or mismatched model-lane/source-artifact domains;
- a policy above `LocalOnly`, extra allowed kind/target, nonzero value limit,
  disabled source requirement, enabled provider authority, or disabled
  non-secret requirement;
- any candidate not equal to `gateway_action_candidate`, any nonempty policy
  violation, any authority/promotion flag, or wrong source/boundary;
- any decision not equal to `evaluate_admission`, nonaccepted verdict,
  nonempty reasons, retained envelope, candidate drift, or policy drift;
- failed ephemeral accepted-handoff reconstruction;
- cross-wrapper, user, A3L6, readiness, claim, implementation, expected-binding,
  authorization, or postauthorization-plan drift;
- pull, build, login, tag resolution, registry/remote host, shell, caller
  argv/environment/endpoint override, or missing/changed `--network=none`;
- any introduced authorization-plan digest cycle.

The synthetic fixture remains hermetic regression data. It is not runtime
evidence, external reproduction, accepted Evidence Ledger evidence, or score
evidence.

## Acceptance And Claim Ceiling

A3L5H is kept only after two independent documentation reviews report zero
findings over the exact wrapper fields, production Serde mapping, digest
domains, fixed constants, network scope, construction order, and negative-test
requirements.

The required reviews completed with zero findings:

- `a3l5h-doc-review-security` independently checked the live Rust field and
  hash mapping, candidate/decision/handoff reconstruction, authority bypasses,
  digest cycles, network capability boundary, and claim ceiling;
- `a3l5h-doc-review-repro` independently recomputed the Serde encodings, all
  seven empty-object domain vectors, source-artifact ordering, auxiliary
  model-lane domains, wrapper graph, network scope, five-file implementability,
  and all four mirrors.

Neither reviewer modified a file. Both rechecked the protected admission
source at SHA-256
`41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de`.

This correction creates no runtime evidence and moves no score. A3L7 still
requires a committed, pinned, independently reviewed A3L6 implementation.
A3L8 still requires one retained accepted A3L7 result and final authorization.
Only a later durable A3L9 acceptance record over retained normal/OOM evidence
may move the local correspondence score under the A3L5C claim ceiling.
