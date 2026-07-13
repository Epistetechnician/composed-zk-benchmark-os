mod runtime;

use std::io::{self, Read, Write};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    run()
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let current_policy_id = parse_current_policy_id()?;
    let mut input = Vec::new();
    io::stdin()
        .take((runtime::MAX_INPUT_BYTES + 1) as u64)
        .read_to_end(&mut input)?;
    let decision = runtime::evaluate(&input, &current_policy_id)?;
    let encoded = serde_json::to_vec(&decision)?;
    let mut stdout = io::stdout().lock();
    stdout.write_all(&encoded)?;
    stdout.write_all(b"\n")?;
    Ok(())
}

fn parse_current_policy_id() -> Result<String, &'static str> {
    let mut arguments = std::env::args().skip(1);
    let Some(flag) = arguments.next() else {
        return Err("missing --current-policy-id");
    };
    if flag != "--current-policy-id" {
        return Err("expected --current-policy-id as the first argument");
    }
    let Some(policy_id) = arguments.next() else {
        return Err("missing value for --current-policy-id");
    };
    if arguments.next().is_some() {
        return Err("unexpected additional arguments");
    }
    Ok(policy_id)
}
