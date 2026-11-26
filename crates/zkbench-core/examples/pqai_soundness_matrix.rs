use zkbench_core::pqai::{run_pqai_soundness_before_speed_matrix, SoundnessStatus};

fn main() {
    let matrix = run_pqai_soundness_before_speed_matrix();
    println!("=== Composed ZK Benchmark OS: PQAI Soundness-Before-Speed Matrix (EIP-8288 + EIP-8479) ===");
    println!("Claim boundary: {:?}", matrix.claim_boundary);
    println!(
        "\n{:<36} {:<24} {:>8} {:>10} {:>14} {:>14}",
        "candidate", "soundness", "caught", "unsound", "8288 us", "8479 us"
    );
    for c in &matrix.candidates {
        let s8288 = match c.median_verify_us_eip8288 {
            Some(v) => format!("{v:.1} us"),
            None => format!("QUAR({:.1})", c.raw_quarantined_verify_us_eip8288),
        };
        let s8479 = match c.median_verify_us_eip8479 {
            Some(v) => format!("{v:.1} us"),
            None => format!("QUAR({:.1})", c.raw_quarantined_verify_us_eip8479),
        };
        println!(
            "{:<36} {:<24} {:>4}/{:<3} {:>10} {:>14} {:>14}",
            c.candidate_id,
            match c.soundness_status {
                SoundnessStatus::SoundnessAdmitted => "ADMITTED",
                SoundnessStatus::SoundnessDisqualified => "DISQUALIFIED",
            },
            c.mutations_caught,
            c.total_mutations,
            c.unsound_acceptances,
            s8288,
            s8479
        );
    }

    if let Some(out) = std::env::args().nth(1) {
        let json = serde_json::to_string_pretty(&matrix).expect("serialize matrix");
        std::fs::write(&out, json).expect("write json");
        println!("\nWrote JSON matrix -> {out}");
    }
}
