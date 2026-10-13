/* State slices: private-decision-model-fhe-review-preparation-v1 and global-experiment-assurance-lifecycle-v1. */

import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const paths = {
  manifest: "docs/research/private-decision-model-fhe-review-artifact-manifest-v1.json",
  target: "docs/research/private-decision-model-fhe-review-target-v1.json",
  packet: "docs/research/private-decision-model-fhe-review-packet-v1.json",
  protocol: "docs/research/private-decision-model-fhe-review-protocol-v1.json"
};
const archivePath = path.join(
  os.homedir(),
  ".local/share/private-decision-model-fhe-review-v1/private-decision-model-fhe-review-v1.zip"
);
const stagePath = path.dirname(archivePath);
const expected = Object.freeze({
  manifestSha256: "e5526c254f1351584aa2dd9d0f4201da16119d518f940991cb6d7812f6b8d44f",
  targetSha256: "43d300f3e910704016e6b953f417a7a457b2a9b69cd35f44d6620e832f39793d",
  packetCanonicalSha256: "94ae6b4460aba7bbabab32f853a075d43dfd1e5a949103c7e4665853fc41defc",
  protocolCanonicalSha256: "4ce1c4382da99e8b8e4bac171268f71f05944039edbc513ac33dea1ec57f5c82",
  archiveSha256: "90836174530b563179a4e7ff95ca20109f15ea2ed806d5491139f07d702e9f3a",
  claimCeiling: "LocalDevelopmentSyntheticFHEInferenceV1"
});

const errors = [];
const check = (condition, code) => { if (!condition) errors.push(code); };
const readRepo = (relative) => fs.readFileSync(path.join(root, relative));
const readJson = (relative) => JSON.parse(readRepo(relative).toString("utf8"));
const manifestBytes = readRepo(paths.manifest);
const targetBytes = readRepo(paths.target);
const packetBytes = readRepo(paths.packet);
const protocolBytes = readRepo(paths.protocol);
const manifest = JSON.parse(manifestBytes.toString("utf8"));
const target = JSON.parse(targetBytes.toString("utf8"));
const packet = JSON.parse(packetBytes.toString("utf8"));
const protocol = JSON.parse(protocolBytes.toString("utf8"));

check(Array.isArray(manifest) && manifest.length === 13, "manifest_shape_or_count");
check(sha256(manifestBytes) === expected.manifestSha256, "manifest_digest_mismatch");
check(sha256(canonicalJson(target)) === expected.targetSha256, "canonical_target_digest_mismatch");
check(sha256(canonicalJson(packet)) === expected.packetCanonicalSha256, "canonical_packet_digest_mismatch");
check(sha256(canonicalJson(protocol)) === expected.protocolCanonicalSha256, "canonical_protocol_digest_mismatch");

const manifestByPath = new Map();
for (const item of Array.isArray(manifest) ? manifest : []) {
  check(isRecord(item) && typeof item.path === "string" && /^[a-f0-9]{64}$/.test(item.sha256), "manifest_entry_invalid");
  if (!isRecord(item) || typeof item.path !== "string") continue;
  check(!manifestByPath.has(item.path), "manifest_path_duplicated");
  manifestByPath.set(item.path, item);
  const absolutePath = path.resolve(root, item.path);
  check(isInside(root, absolutePath), "manifest_path_escapes_repository");
  if (!isInside(root, absolutePath) || !fs.existsSync(absolutePath)) {
    errors.push("manifest_source_missing:" + item.path);
    continue;
  }
  check(sha256(fs.readFileSync(absolutePath)) === item.sha256, "manifest_source_digest_mismatch:" + item.path);
}

check(Array.isArray(target.target_artifacts) && target.target_artifacts.length === 10, "target_artifact_count");
for (const item of Array.isArray(target.target_artifacts) ? target.target_artifacts : []) {
  check(manifestByPath.get(item.path)?.sha256 === item.sha256, "target_manifest_binding_mismatch:" + item.path);
}
check(target.claim_ceiling === expected.claimCeiling && packet.claim_ceiling === expected.claimCeiling, "claim_ceiling_changed");
check(target.target_state_slice === "private-decision-model-fhe-inference-v1", "target_state_slice_changed");
check(target.state_slices?.preparation === "private-decision-model-fhe-review-preparation-v1", "preparation_state_slice_changed");
check(target.state_slices?.governance === "global-experiment-assurance-lifecycle-v1", "governance_state_slice_changed");
check(target.reviewer_status === "EXTERNAL_REVIEW_UNAVAILABLE", "reviewer_status_changed");
check(target.protocol_path === paths.protocol && target.review_packet_path === paths.packet, "target_bound_paths_changed");
check(target.protocol_file_sha256 === sha256(protocolBytes) && target.protocol_sha256 === sha256(protocolBytes), "target_protocol_file_binding_mismatch");
check(target.review_packet_file_sha256 === sha256(packetBytes) && target.review_packet_sha256 === sha256(packetBytes), "target_packet_file_binding_mismatch");
check(packet.state_slices?.preparation === "private-decision-model-fhe-review-preparation-v1", "packet_preparation_state_slice_changed");
check(packet.state_slices?.governance === "global-experiment-assurance-lifecycle-v1", "packet_governance_state_slice_changed");
check(packet.state_slices?.target === "private-decision-model-fhe-inference-v1", "packet_target_state_slice_changed");
check(protocol.state_slice === "private-decision-model-fhe-review-preparation-v1", "protocol_state_slice_changed");
check(protocol.execution_authorized === false && protocol.reviewer_submission_authorized_by_this_protocol === false, "protocol_authority_widened");
check(protocol.target_state_slice === "private-decision-model-fhe-inference-v1", "protocol_target_state_slice_changed");

if (!fs.existsSync(stagePath) || !fs.existsSync(archivePath)) {
  errors.push("owner_only_archive_missing");
} else {
  check((fs.lstatSync(stagePath).mode & 0o777) === 0o700, "staging_directory_permissions_not_0700");
  check((fs.lstatSync(archivePath).mode & 0o777) === 0o600, "archive_permissions_not_0600");
  check(fs.lstatSync(stagePath).isDirectory() && !fs.lstatSync(stagePath).isSymbolicLink(), "staging_directory_type_invalid");
  check(fs.lstatSync(archivePath).isFile() && !fs.lstatSync(archivePath).isSymbolicLink(), "archive_file_type_invalid");
  if (typeof process.getuid === "function") check(fs.statSync(archivePath).uid === process.getuid(), "archive_owner_mismatch");
  const archiveBytes = fs.readFileSync(archivePath);
  check(sha256(archiveBytes) === expected.archiveSha256, "archive_digest_mismatch");
  if (sha256(archiveBytes) === expected.archiveSha256) {
    const names = execFileSync("unzip", ["-Z1", archivePath], { encoding: "utf8", maxBuffer: 2 * 1024 * 1024 })
      .trim().split("\n").filter(Boolean);
    const expectedNames = [...manifestByPath.keys()];
    check(names.length === expectedNames.length, "archive_entry_count_mismatch");
    check([...names].sort().join("\n") === [...expectedNames].sort().join("\n"), "archive_entry_set_mismatch");
    for (const relative of expectedNames) {
      const payload = execFileSync("unzip", ["-p", archivePath, relative], { maxBuffer: 16 * 1024 * 1024 });
      check(sha256(payload) === manifestByPath.get(relative)?.sha256, "archive_payload_digest_mismatch:" + relative);
    }
  }
}

if (errors.length) throw new Error("FHE review V1 local verification failed: " + [...new Set(errors)].join(", "));
console.log("validated frozen FHE review V1 packet, target, protocol, manifest, and owner-only archive");
console.log("target_artifacts=10; manifest_entries=13; archive_entries=13");
console.log(`target_sha256=${expected.targetSha256}`);
console.log(`archive_sha256=${expected.archiveSha256}`);
console.log("archive_mode=0600; staging_mode=0700; reviewer_status=EXTERNAL_REVIEW_UNAVAILABLE");
console.log("review_submission=false; artifact_transfer=false; execution_authorized=false; spend_ceiling_usd=0");

function isInside(parent, child) {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}
function isRecord(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
function sha256(value) { return createHash("sha256").update(value).digest("hex"); }
function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
}
