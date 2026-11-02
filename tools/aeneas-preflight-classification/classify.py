"""Classify HSAI Aeneas-lane stop docs (phases 667-764) by cause. Read-only, hermetic.

Evidence order (first decisive signal wins):
1. The doc's explicit ``Diagnostic: `X`.`` line, mapped by documented meaning.
2. The doc's stop code (backticked ``...Mismatch``/``...Unavailable`` etc.).
3. Filename keywords (fallback only, used when the doc states no diagnostic).
"""
import pathlib
import re
import sys

# Diagnostic identifiers mapped by the documented meaning of each failure.
DIAGNOSTIC_CAUSES = {
    # toolchain: the tool, identity, version, or environment that ran was wrong
    "PackagedToolIdentityMismatch": "toolchain",
    "DriverDynamicLinkUnavailable": "toolchain",
    "UnexpectedRustupAutoInstall": "toolchain",
    "RequiredLogScannerUnavailable": "toolchain",
    "UnsupportedLongVersionFlag": "toolchain",
    "LakeBuildMetadataSuffixUnspecified": "toolchain",
    "LeanSysrootPathUnboundForCacheHelper": "toolchain",
    "CharonCargoLockMismatch": "toolchain",
    "CharonPackageCanonicalPathMismatch": "toolchain",
    "PinnedLicensePathUsesLicenseInsteadOfLicenseMd": "toolchain",
    "RustupInstalledFilterSemanticDrift": "toolchain",
    "Rustup129EmitsFullInventoryWithInstalledMarkers": "toolchain",
    "ResultU8EqualityDecidableInstanceAbsent": "toolchain",
    "RunIoBindTokenMismatch": "toolchain",
    "LakefileCanonicalTextMismatch": "toolchain",
    "WrongRustupToolchainTokenInCharonFetch": "toolchain",
    "RustIdentityEnvironmentToolchainTokenMismatch": "toolchain",
    "GeneratedTypesOleanAbsent": "toolchain",
    "PipefailEarlyExitProducerFailure": "toolchain",
    "ZshScalarSplitDisabled": "toolchain",
    "UnsupportedOutputOption": "toolchain",
    "SandboxAttributionUnavailable": "toolchain",
    "DirectIpProbeStderrEmpty": "toolchain",
    "CompleteProcessGroupTimeoutRunnerAbsent": "toolchain",
    "LeanBuildDestinationAlreadyMaterialized": "provenance",
    # provenance: which artifact, source, or producer's output is trusted
    "MissingCommandCheckpoint": "provenance",
    "UncapturedCharonAndAeneasProducers": "provenance",
    "CondensedAeneasMaterializationProducers": "provenance",
    "IdentityProducerStderrUncaptured": "provenance",
    "AcquisitionStderrIncludedInTransferScan": "provenance",
    "StructuredEntryAndInventoryProvenanceRulesMissing": "provenance",
    "TarInfoNormalizationAndAncestorCollisionGap": "provenance",
    "RootMarkerRejectedAndStatusMasked": "provenance",
    "MainTopLevelSetMismatchAndAcceptanceStatusMasked": "provenance",
    "DuplicateListenerMaterializationAndUnretainedHelperSources": "provenance",
    "AlternateFixtureCommandsAndCaps": "provenance",
    "CombinedAssertionExitedNonzeroWhileDeclaredFactsMatched": "provenance",
    "FilteredComponentListSuffixAssumption": "provenance",
    "NetworkDenialDiagnosticMismatch": "provenance",
    # ordering: the protocol order, scope, or run state was wrong
    "NestedClientBeforeRunRoot": "ordering",
    "ClientMetadataAndPreAcquisitionOrderConflict": "ordering",
    "MaskedWrongToolchainNoOp": "ordering",
    "UnusedFixtureSpecLoop": "ordering",
    "PreExistingUserTestModification": "ordering",
    "PreservedConcurrentMeshSlicePresent": "ordering",
    "CleanPrimaryAssertionContradictsDetachedDirtyPrimaryRule": "ordering",
    "ExecutionProtocolUnexpectedCommand": "ordering",
}

FILENAME_RULES = [  # fallback only, first match wins
    ("toolchain", r"local-attempt|driver-link|rustup|rust-token|charon-(cargo-lock|canonical-path|license|version|fetch|identity)|leantar|lake-identity|lean-bind|version-flag|architecture|component|inventory|lean-build"),
    ("provenance", r"provenance|acquisition|archive|tarinfo|materialization|identity-(log|stderr)|metadata|unlocalized|parser|helper-spec|fixture|runner"),
    ("ordering", r"ordering|order|protocol|ambiguity|manual-orchestration|zsh|primary|worktree|run-root|assertion|scope|sandbox|timeout|unexpected|generated-module|witness"),
]

DIAG_RE = re.compile(r"Diagnostic:\s*`([A-Za-z0-9_]+)`")
CODE_RE = re.compile(r"`([A-Z][A-Za-z0-9]+(?:Mismatch|Unavailable|Ambiguous[A-Za-z]*|Incomplete|Failed|Stop|Unexpected[A-Za-z]*))`")


def classify_doc(name, text=""):
    """Return (category, evidence) for one stop doc."""
    m = DIAG_RE.search(text)
    if m and m.group(1) in DIAGNOSTIC_CAUSES:
        return DIAGNOSTIC_CAUSES[m.group(1)], f"diagnostic:{m.group(1)}"
    if m:
        return "unclassified", f"diagnostic-unmapped:{m.group(1)}"
    code = CODE_RE.search(text)
    if code and code.group(1) in DIAGNOSTIC_CAUSES:
        return DIAGNOSTIC_CAUSES[code.group(1)], f"code:{code.group(1)}"
    return classify_name(name), "filename"


def classify_name(name):
    for cat, pat in FILENAME_RULES:
        if re.search(pat, name):
            return cat
    return "unclassified"


def classify(name):
    return classify_name(name)


def collect_detailed(docs):
    out = {}
    for p in sorted(docs.glob("[67][0-9][0-9]-phase-hsai-gateway-threat-ordinal-*.md")):
        n = int(p.name[:3])
        if 667 <= n <= 764 and re.search(r"(stop|failure|mismatch)\.md$", p.name):
            out[p.name] = classify_doc(p.name, p.read_text(encoding="utf-8"))
    return out


def collect(docs):
    return {k: v[0] for k, v in collect_detailed(docs).items()}


if __name__ == "__main__":
    detailed = collect_detailed(pathlib.Path(sys.argv[1]))
    counts = {}
    evid = {}
    for cat, ev in detailed.values():
        counts[cat] = counts.get(cat, 0) + 1
        kind = ev.split(":")[0]
        evid[kind] = evid.get(kind, 0) + 1
    print(len(detailed), counts)
    print("evidence:", evid)
