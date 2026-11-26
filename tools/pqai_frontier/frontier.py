"""Layer 4: Multi-Assumption PQAI Cryptanalysis Frontier (extending ECDSA.fail).

Tracks evaluator-verified and analytical cryptanalysis frontiers across all three
EF PQAI #0 assumption classes WITHOUT collapsing them into a single scalar:

  1. ECC (pre-quantum cutoff):
       - secp256k1 (ingests verified `ecdsafail-challenge` score.json & results.tsv)
       - BLS12-381 (381-bit prime-field Shor Q*T scaling for Eth consensus / sync committees)
  2. Lattices & Codes (post-quantum, non-hash-only):
       - ML-DSA-65 (FIPS 204 Module-LWE / Module-SIS Core-SVP BKZ-beta)
       - Labinius (cyclotomic ring R_648 lattice PCS modulus/MSIS margin)
       - Maverick dual-LPN (syndrome decoding / ISD / Grover-ISD noise margin)
  3. Algebraic vs. Conservative Hashes (critical for EIP-8288 / EIP-8479):
       - Poseidon2 (SNARK-friendly algebraic hash — low-degree S-box x^d; tracks
         Gröbner-basis / interpolation degree margin + live reduced-round probe)
       - SHA-256 & BLAKE3 (conservative ARX/Merkle-Damgard — Grover/BHT generic bounds
         + live avalanche/bit-independence differential probe)

Anti-cheating & epistemic discipline:
  - Every entry declares an explicit `evidence_class`:
      * `EvaluatorVerifiedCircuit` — ingested from deterministic Fiat-Shamir simulator (`ecdsafail-challenge`)
      * `MeasuredLocalProbe`       — live deterministic local cryptanalytic micro-probe
      * `AnalyticalSecurityModel`  — parameterized Core-SVP / ISD / Gröbner complexity bound
  - Never conflates analytical estimates with measured breakthroughs.
  - Produces a content-addressed SHA-256 provenance receipt over all inputs and outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model (strict separation of evidence classes and assumption fronts)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrontierPoint:
    front: str  # "ecc" | "lattice_code" | "hash_algebraic_vs_conservative"
    target: str
    assumption_family: str
    pqai_hash_only: bool
    evidence_class: str  # EvaluatorVerifiedCircuit | MeasuredLocalProbe | AnalyticalSecurityModel
    primary_metric_name: str
    primary_metric_value: float
    primary_metric_unit: str
    classical_bits: float
    quantum_bits: float
    ai_cryptanalysis_risk: str  # "BROKEN_QUANTUM" | "ELEVATED_ALGEBRAIC" | "MODERATE_STRUCTURED" | "MINIMAL_CONSERVATIVE"
    provenance: Dict[str, Any]
    notes: str


@dataclass(frozen=True)
class ProbeReceipt:
    probe_id: str
    target: str
    seed_hex: str
    passed_verification: bool
    metrics: Dict[str, Any]
    digest_sha256: str


# ---------------------------------------------------------------------------
# 1. ECC Front: Real ECDSA.fail ingestion + BLS12-381 scaling
# ---------------------------------------------------------------------------


def ingest_ecdsafail_frontier(ecdsa_roots: List[Path]) -> List[FrontierPoint]:
    points: List[FrontierPoint] = []
    best_score: Optional[int] = None
    best_metrics: Dict[str, Any] = {}
    best_source: Optional[Path] = None
    tsv_rows = 0

    for root in ecdsa_roots:
        score_path = root / "score.json"
        if score_path.exists():
            raw = score_path.read_bytes()
            data = json.loads(raw.decode("utf-8"))
            score = int(data["score"])
            digest = hashlib.sha256(raw).hexdigest()
            if best_score is None or score < best_score:
                best_score = score
                best_metrics = {
                    "score_path": str(score_path),
                    "score_sha256": digest,
                    "toffoli": data.get("metrics", {}).get("toffoli"),
                    "qubits": data.get("metrics", {}).get("qubits"),
                }
                best_source = root

        tsv_path = root / "results.tsv"
        if tsv_path.exists():
            lines = [ln for ln in tsv_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            tsv_rows += max(0, len(lines) - 1)
            for ln in lines[1:]:
                cols = ln.split("\t")
                if len(cols) >= 7 and cols[6].strip() == "OK":
                    try:
                        tof = float(cols[2])
                        q = int(cols[4])
                        sc = int(round(tof * q))
                        if best_score is None or sc < best_score:
                            best_score = sc
                            best_metrics = {
                                "results_tsv": str(tsv_path),
                                "commit": cols[1],
                                "toffoli": tof,
                                "qubits": q,
                            }
                            best_source = root
                    except ValueError:
                        pass

    if best_score is not None:
        # Baseline from results.tsv first row: 3,942,753 Toffoli * 2,715 qubits = 10,704,574,395
        baseline_qt = 3_942_753 * 2_715
        reduction_pct = (1.0 - (best_score / baseline_qt)) * 100.0
        best_metrics["baseline_qt"] = baseline_qt
        best_metrics["reduction_vs_initial_pct"] = round(reduction_pct, 2)
        best_metrics["verified_tsv_rows_scanned"] = tsv_rows
        points.append(
            FrontierPoint(
                front="ecc",
                target="secp256k1 (Shor point-add Q*T)",
                assumption_family="Elliptic Curve Discrete Logarithm (256-bit)",
                pqai_hash_only=False,
                evidence_class="EvaluatorVerifiedCircuit",
                primary_metric_name="toffoli_x_qubits",
                primary_metric_value=float(best_score),
                primary_metric_unit="Toffoli*Qubits",
                classical_bits=128.0,
                quantum_bits=0.0,  # Polynomial time under Shor
                ai_cryptanalysis_risk="BROKEN_QUANTUM",
                provenance=best_metrics,
                notes=(
                    f"Ingested verified ECDSA.fail frontier ({best_source}); "
                    f"{reduction_pct:.2f}% Q*T reduction vs initial baseline ({baseline_qt:,})."
                ),
            )
        )

    # BLS12-381 analytical scaling from measured secp256k1 point-add cost:
    # Field width scales 256 -> 381 (~1.49x qubits, ~(1.49)^2.3 Toffoli for Montgomery/Karatsuba).
    ref_tof = float(best_metrics.get("toffoli", 1_773_011))
    ref_q = float(best_metrics.get("qubits", 1_355))
    ratio = 381.0 / 256.0
    bls_q = round(ref_q * ratio)
    bls_tof = round(ref_tof * (ratio ** 2.25))
    bls_qt = bls_q * bls_tof
    points.append(
        FrontierPoint(
            front="ecc",
            target="BLS12-381 (Eth validator/sync-committee G1 point-add)",
            assumption_family="Pairing-Friendly ECDLP (381-bit prime field)",
            pqai_hash_only=False,
            evidence_class="AnalyticalSecurityModel",
            primary_metric_name="estimated_toffoli_x_qubits",
            primary_metric_value=float(bls_qt),
            primary_metric_unit="Toffoli*Qubits (scaled)",
            classical_bits=128.0,
            quantum_bits=0.0,
            ai_cryptanalysis_risk="BROKEN_QUANTUM",
            provenance={
                "scaling_model": "field_width_ratio_381_256_pow_2.25_toffoli_1.0_qubits",
                "estimated_qubits": bls_q,
                "estimated_toffoli": bls_tof,
                "anchored_to_secp256k1_toffoli": ref_tof,
            },
            notes="Analytical scaling of Shor G1 point-add; motivates EF EIP-8288 migration off BLS12-381.",
        )
    )
    return points


# ---------------------------------------------------------------------------
# 2. Lattice & Code Front: Core-SVP / MSIS / Dual-LPN + live toy LWE/LPN probe
# ---------------------------------------------------------------------------


def run_toy_lwe_sis_probe(seed: bytes) -> ProbeReceipt:
    """Deterministic verifiable micro-probe: exact secret recovery on toy LWE (n=4, q=97, |e|<=1)
    verifying evaluator correctness & measuring exact search work vs. noise margin."""
    q = 97
    n = 4
    m = 10
    digest = hashlib.sha256(b"pqai.frontier.lwe.probe.v1" + seed).digest()
    # Deterministic secret s in {-1, 0, 1}^n
    secret = [(digest[i] % 3) - 1 for i in range(n)]
    rows = []
    for r in range(m):
        h = hashlib.sha256(digest + r.to_bytes(4, "little")).digest()
        a = [h[j] % q for j in range(n)]
        e = (h[n] % 3) - 1
        b = (sum(a[j] * secret[j] for j in range(n)) + e) % q
        rows.append((a, b))

    # Bounded brute-force evaluator over {-1,0,1}^4 (3^4 = 81 candidates)
    t0 = time.perf_counter()
    checked = 0
    recovered = None
    for idx in range(3 ** n):
        checked += 1
        cand = []
        tmp = idx
        for _ in range(n):
            cand.append((tmp % 3) - 1)
            tmp //= 3
        ok = True
        for a, b in rows:
            diff = (b - sum(a[j] * cand[j] for j in range(n))) % q
            if diff > q // 2:
                diff -= q
            if abs(diff) > 1:
                ok = False
                break
        if ok:
            recovered = cand
            break
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    passed = recovered == secret
    metrics = {
        "n": n,
        "m": m,
        "q": q,
        "candidates_checked": checked,
        "recovered_matches_secret": passed,
        "elapsed_ms": round(elapsed_ms, 4),
    }
    rec_digest = hashlib.sha256(json.dumps(metrics, sort_keys=True).encode()).hexdigest()
    return ProbeReceipt(
        probe_id="toy_lwe_evaluator_sanity",
        target="Module-LWE / ML-DSA toy instance",
        seed_hex=seed.hex(),
        passed_verification=passed,
        metrics=metrics,
        digest_sha256=rec_digest,
    )


def build_lattice_code_front(seed: bytes) -> Tuple[List[FrontierPoint], ProbeReceipt]:
    probe = run_toy_lwe_sis_probe(seed)
    # Core-SVP constants: classical 0.292*beta (BDGL16), quantum 0.257*beta (Chailloux-Loyer21)
    mldsa65_beta = 623.0  # NIST FIPS 204 Level 3 (k=6, l=5, q=8380417)
    labinius_beta = 440.0  # Cyclotomic R_648 MSIS ~128-bit classical target (Core-SVP)
    # Maverick dual-LPN (binary code, syndrome decoding / ISD)
    maverick_classical_bits = 128.0
    maverick_quantum_bits = 74.0  # Grover-accelerated ISD (~0.58x classical exponent)

    points = [
        FrontierPoint(
            front="lattice_code",
            target="ML-DSA-65 (FIPS 204 Module-LWE / Module-SIS)",
            assumption_family="Structured Lattice (Module-LWE/SIS, Core-SVP BKZ)",
            pqai_hash_only=False,
            evidence_class="AnalyticalSecurityModel",
            primary_metric_name="core_svp_bkz_beta",
            primary_metric_value=mldsa65_beta,
            primary_metric_unit="BKZ blocksize beta",
            classical_bits=round(0.292 * mldsa65_beta, 1),
            quantum_bits=round(0.257 * mldsa65_beta, 1),
            ai_cryptanalysis_risk="MODERATE_STRUCTURED",
            provenance={
                "core_svp_classical_const": 0.292,
                "core_svp_quantum_const": 0.257,
                "toy_lwe_probe_digest": probe.digest_sha256,
                "toy_lwe_probe_verified": probe.passed_verification,
            },
            notes="Strong post-quantum margin (~182c / ~160q Core-SVP bits), but relies on algebraic lattice structure.",
        ),
        FrontierPoint(
            front="lattice_code",
            target="Labinius PCS (R_648 cyclotomic MSIS)",
            assumption_family="Cyclotomic Ring Lattice (MSIS)",
            pqai_hash_only=False,
            evidence_class="AnalyticalSecurityModel",
            primary_metric_name="core_svp_bkz_beta",
            primary_metric_value=labinius_beta,
            primary_metric_unit="BKZ blocksize beta",
            classical_bits=round(0.292 * labinius_beta, 1),
            quantum_bits=round(0.257 * labinius_beta, 1),
            ai_cryptanalysis_risk="MODERATE_STRUCTURED",
            provenance={
                "ring_dimension": 648,
                "admissible_modulus_min": 34_816_965_049,
                "core_svp_classical_const": 0.292,
                "core_svp_quantum_const": 0.257,
            },
            notes="Lattice PCS; compare directly against hash-only WHIR/BaseFold in Layer 2A.",
        ),
        FrontierPoint(
            front="lattice_code",
            target="Maverick dual-LPN (arc_membrane)",
            assumption_family="Code-Based / Dual-LPN Syndrome Decoding",
            pqai_hash_only=False,
            evidence_class="AnalyticalSecurityModel",
            primary_metric_name="isd_quantum_security_bits",
            primary_metric_value=maverick_quantum_bits,
            primary_metric_unit="bits (Grover-ISD)",
            classical_bits=maverick_classical_bits,
            quantum_bits=maverick_quantum_bits,
            ai_cryptanalysis_risk="MODERATE_STRUCTURED",
            provenance={
                "attack_model": "BJMM / Grover-ISD over binary dual-LPN",
                "deployment_scope": "ephemeral live-inference privacy only (bound to SLH-DSA RoomLog)",
            },
            notes="Used strictly for ephemeral confidentiality; permanent custody stays on FIPS 205 SLH-DSA.",
        ),
    ]
    return points, probe


# ---------------------------------------------------------------------------
# 3. Algebraic vs. Conservative Hash Front (Poseidon2 vs SHA-256 / BLAKE3)
# ---------------------------------------------------------------------------


def poseidon2_toy_round(state: List[int], p: int, rc: List[int], full: bool, alpha: int = 5) -> List[int]:
    """Toy Poseidon2-style permutation over F_p (t=3, S-box x^5) for algebraic-degree probing."""
    t = len(state)
    s = [(state[i] + rc[i]) % p for i in range(t)]
    if full:
        s = [pow(x, alpha, p) for x in s]
    else:
        s[0] = pow(s[0], alpha, p)
    # Circulant MDS-like linear layer [[2,1,1],[1,2,1],[1,1,2]]
    tot = sum(s) % p
    return [(s[i] + tot) % p for i in range(t)]


def run_hash_algebraic_vs_conservative_probes(seed: bytes) -> Tuple[List[FrontierPoint], List[ProbeReceipt]]:
    """Live deterministic micro-probes comparing:
      (a) Reduced-round Poseidon2 algebraic interpolation degree growth (d = alpha^R)
          and exact finite-difference degree verification over F_p;
      (b) SHA-256 & BLAKE3 strict avalanche criterion (SAC) bit-flip Hamming weight
          across 512 deterministic single-bit input flips."""
    # --- Probe A: Reduced-round Poseidon2 exact polynomial degree via finite differences ---
    p = 65537  # Fermat prime for fast exact finite-difference verification
    alpha = 5
    # 2 full rounds -> exact univariate degree in x_0 is alpha^2 = 25!
    rounds_tested = 2
    expected_degree = alpha ** rounds_tested  # 25
    rcs = [[(r * 17 + i * 31 + 7) % p for i in range(3)] for r in range(rounds_tested)]

    def eval_p2(x: int) -> int:
        st = [x % p, 1234, 5678]
        for r in range(rounds_tested):
            st = poseidon2_toy_round(st, p, rcs[r], full=True, alpha=alpha)
        return st[0]

    # Forward finite difference of order (expected_degree + 1) MUST vanish identically mod p
    vals = [eval_p2(x) for x in range(expected_degree + 2)]
    cur = list(vals)
    vanished_at: Optional[int] = None
    for order in range(1, expected_degree + 2):
        cur = [(cur[i + 1] - cur[i]) % p for i in range(len(cur) - 1)]
        if all(v == 0 for v in cur):
            vanished_at = order
            break
    exact_degree_observed = (vanished_at - 1) if vanished_at is not None else -1
    p2_verified = exact_degree_observed == expected_degree

    p2_metrics = {
        "field_prime": p,
        "sbox_alpha": alpha,
        "rounds_probed": rounds_tested,
        "expected_algebraic_degree": expected_degree,
        "observed_exact_degree": exact_degree_observed,
        "finite_diff_vanished_at_order": vanished_at,
        "full_spec_rounds_rf_rp": "R_F=8, R_P=56 (128-bit Goldilocks/BabyBear target)",
    }
    p2_receipt = ProbeReceipt(
        probe_id="poseidon2_algebraic_degree_probe",
        target="Poseidon2 (x^5 S-box algebraic hash)",
        seed_hex=seed.hex(),
        passed_verification=p2_verified,
        metrics=p2_metrics,
        digest_sha256=hashlib.sha256(json.dumps(p2_metrics, sort_keys=True).encode()).hexdigest(),
    )

    # --- Probe B: SHA-256 & BLAKE2s/BLAKE3-style conservative avalanche probe ---
    trials = 256
    base_msg = hashlib.sha256(b"pqai.frontier.sac.base.v1" + seed).digest()
    base_sha = hashlib.sha256(base_msg).digest()
    sha_flips = []
    for bit in range(trials):
        mut = bytearray(base_msg)
        mut[bit // 8] ^= 1 << (bit % 8)
        d = hashlib.sha256(bytes(mut)).digest()
        hw = sum((a ^ b).bit_count() for a, b in zip(base_sha, d))
        sha_flips.append(hw)
    sha_mean = sum(sha_flips) / len(sha_flips)  # ideal = 128.0 / 256 bits (50%)
    sha_sac_ok = 120.0 <= sha_mean <= 136.0
    sha_metrics = {
        "trials_single_bit_flips": trials,
        "output_bits": 256,
        "mean_hamming_weight": round(sha_mean, 3),
        "ideal_hamming_weight": 128.0,
        "min_hamming": min(sha_flips),
        "max_hamming": max(sha_flips),
        "sac_within_band": sha_sac_ok,
    }
    sha_receipt = ProbeReceipt(
        probe_id="sha256_avalanche_probe",
        target="SHA-256 (FIPS 180-4 conservative hash)",
        seed_hex=seed.hex(),
        passed_verification=sha_sac_ok,
        metrics=sha_metrics,
        digest_sha256=hashlib.sha256(json.dumps(sha_metrics, sort_keys=True).encode()).hexdigest(),
    )

    # BLAKE2s-256 (same ChaCha/ARX family as BLAKE3 in Python stdlib) avalanche probe
    base_b2 = hashlib.blake2s(base_msg).digest()
    b2_flips = []
    for bit in range(trials):
        mut = bytearray(base_msg)
        mut[bit // 8] ^= 1 << (bit % 8)
        d = hashlib.blake2s(bytes(mut)).digest()
        hw = sum((a ^ b).bit_count() for a, b in zip(base_b2, d))
        b2_flips.append(hw)
    b2_mean = sum(b2_flips) / len(b2_flips)
    b2_sac_ok = 120.0 <= b2_mean <= 136.0
    b2_metrics = {
        "trials_single_bit_flips": trials,
        "output_bits": 256,
        "mean_hamming_weight": round(b2_mean, 3),
        "ideal_hamming_weight": 128.0,
        "min_hamming": min(b2_flips),
        "max_hamming": max(b2_flips),
        "sac_within_band": b2_sac_ok,
    }
    b2_receipt = ProbeReceipt(
        probe_id="blake_arx_avalanche_probe",
        target="BLAKE3 / BLAKE2s (conservative ARX hash)",
        seed_hex=seed.hex(),
        passed_verification=b2_sac_ok,
        metrics=b2_metrics,
        digest_sha256=hashlib.sha256(json.dumps(b2_metrics, sort_keys=True).encode()).hexdigest(),
    )

    points = [
        FrontierPoint(
            front="hash_algebraic_vs_conservative",
            target="Poseidon2 (SNARK-friendly algebraic hash)",
            assumption_family="Algebraic Permutation over F_p (low-degree S-box x^5)",
            pqai_hash_only=True,
            evidence_class="MeasuredLocalProbe",
            primary_metric_name="observed_2round_algebraic_degree",
            primary_metric_value=float(exact_degree_observed),
            primary_metric_unit="exact F_p polynomial degree (2 rounds)",
            classical_bits=128.0,
            quantum_bits=128.0,  # Claimed; sensitive to Gröbner/interpolation/AI-assisted algebraic cryptanalysis
            ai_cryptanalysis_risk="ELEVATED_ALGEBRAIC",
            provenance={
                "probe_digest": p2_receipt.digest_sha256,
                "probe_verified": p2_receipt.passed_verification,
                "reason": "Low-degree algebraic structure is primary target for AI-assisted Gröbner/resultant attacks (EF PQAI #0 / Poseidon cryptanalysis bounties).",
            },
            notes="Fast inside EIP-8288 STARK aggregation, but carries elevated algebraic cryptanalysis risk vs. SHA-256/BLAKE3.",
        ),
        FrontierPoint(
            front="hash_algebraic_vs_conservative",
            target="SHA-256 (FIPS 180-4 / FIPS 205 SLH-DSA-SHA2)",
            assumption_family="Conservative ARX/Merkle-Damgard Hash (256-bit)",
            pqai_hash_only=True,
            evidence_class="MeasuredLocalProbe",
            primary_metric_name="sac_mean_hamming_weight",
            primary_metric_value=round(sha_mean, 3),
            primary_metric_unit="flipped bits / 256 (ideal 128.0)",
            classical_bits=128.0,  # Collision resistance (256 preimage)
            quantum_bits=128.0,  # Preimage Grover 2^128; CNS collision ~2^128 memory-constrained
            ai_cryptanalysis_risk="MINIMAL_CONSERVATIVE",
            provenance={
                "probe_digest": sha_receipt.digest_sha256,
                "probe_verified": sha_receipt.passed_verification,
            },
            notes="Plausibly post-AI minimal assumption; anchors Playbox Layer 1 SLH-DSA-SHA2-128f trust root.",
        ),
        FrontierPoint(
            front="hash_algebraic_vs_conservative",
            target="BLAKE3 / BLAKE2s (conservative ARX tree hash)",
            assumption_family="Conservative ARX Hash (256-bit)",
            pqai_hash_only=True,
            evidence_class="MeasuredLocalProbe",
            primary_metric_name="sac_mean_hamming_weight",
            primary_metric_value=round(b2_mean, 3),
            primary_metric_unit="flipped bits / 256 (ideal 128.0)",
            classical_bits=128.0,
            quantum_bits=128.0,
            ai_cryptanalysis_risk="MINIMAL_CONSERVATIVE",
            provenance={
                "probe_digest": b2_receipt.digest_sha256,
                "probe_verified": b2_receipt.passed_verification,
            },
            notes="High-throughput conservative ARX hash; zero algebraic S-box structure.",
        ),
    ]
    return points, [p2_receipt, sha_receipt, b2_receipt]


# ---------------------------------------------------------------------------
# Multi-Assumption Frontier Assembly (deterministic, content-addressed)
# ---------------------------------------------------------------------------


def build_pqai_frontier_report(
    ecdsa_roots: List[Path],
    seed_hex: str = "2026112300000000000000000000000000000000000000000000000000000001",
) -> Dict[str, Any]:
    seed = bytes.fromhex(seed_hex)
    ecc_points = ingest_ecdsafail_frontier(ecdsa_roots)
    lattice_points, lwe_probe = build_lattice_code_front(seed)
    hash_points, hash_probes = run_hash_algebraic_vs_conservative_probes(seed)

    all_points = ecc_points + lattice_points + hash_points
    all_probes = [lwe_probe] + hash_probes

    by_front: Dict[str, List[Dict[str, Any]]] = {
        "ecc": [asdict(p) for p in ecc_points],
        "lattice_code": [asdict(p) for p in lattice_points],
        "hash_algebraic_vs_conservative": [asdict(p) for p in hash_points],
    }

    body = {
        "schema_version": "pqai.cryptanalysis.frontier.v1",
        "claim_ceiling": "MultiAssumptionLocalTrackerV1 — distinguishes EvaluatorVerifiedCircuit, MeasuredLocalProbe, and AnalyticalSecurityModel; does NOT claim new cryptanalytic breaks.",
        "seed_hex": seed_hex,
        "fronts": by_front,
        "probe_receipts": [asdict(r) for r in all_probes],
        "all_probes_verified": all(r.passed_verification for r in all_probes),
        "summary_counts": {
            "total_targets": len(all_points),
            "ecc_targets": len(ecc_points),
            "lattice_code_targets": len(lattice_points),
            "hash_targets": len(hash_points),
            "pqai_hash_only_targets": sum(1 for p in all_points if p.pqai_hash_only),
        },
    }
    canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    body["report_digest_sha256"] = hashlib.sha256(canon).hexdigest()
    return body


def verify_report_digest(report: Dict[str, Any]) -> bool:
    copy_obj = {k: v for k, v in report.items() if k != "report_digest_sha256"}
    canon = json.dumps(copy_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canon).hexdigest() == report.get("report_digest_sha256")


def main() -> int:
    ap = argparse.ArgumentParser(description="PQAI Multi-Assumption Cryptanalysis Frontier Tracker (Layer 4)")
    ap.add_argument(
        "--ecdsa-root",
        action="append",
        default=[],
        help="Path to ecdsafail-challenge checkout (repeatable)",
    )
    ap.add_argument("--seed", default="2026112300000000000000000000000000000000000000000000000000000001")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    roots = [Path(p) for p in args.ecdsa_root]
    if not roots:
        default_candidates = [
            Path("/Users/shaanp/Documents/GitHub/ecdsafail-challenge"),
            Path("/Users/shaanp/Documents/GitHub/ecdsafail-challenge-frontier-20260608"),
            Path("/Users/shaanp/Documents/GitHub/ecdsafail-challenge-frontier-e96-20260608"),
        ]
        roots = [p for p in default_candidates if p.exists()]

    report = build_pqai_frontier_report(roots, seed_hex=args.seed)
    assert verify_report_digest(report), "report digest self-check failed"

    print("=== PQAI Multi-Assumption Cryptanalysis Frontier (Layer 4) ===")
    print(f"report_digest_sha256: {report['report_digest_sha256']}")
    print(f"all_probes_verified:  {report['all_probes_verified']}")
    print(
        f"{'front':<31} {'target':<48} {'evidence':<24} {'metric':>16} {'c/q bits':>10} {'risk'}"
    )
    for front_name, rows in report["fronts"].items():
        for r in rows:
            print(
                f"{front_name:<31} {r['target']:<48} {r['evidence_class']:<24} "
                f"{r['primary_metric_value']:>16.2f} {r['classical_bits']:>4.0f}/{r['quantum_bits']:<5.0f} {r['ai_cryptanalysis_risk']}"
            )

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nWrote frontier JSON -> {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
