# Oak Lab measured-energy path V1

State slice: `oaklab-experience-learning-benchmark-v2`

## Declared path

The first hardware path is macOS Apple Silicon CPU power sampled by
`powermetrics --samplers cpu_power`. `measure_energy_v1.py` accepts a
timestamped `timestamp_s,power_w` trace, integrates watts with the fixed
trapezoidal rule, and writes the digest-bound one-row receipt consumed by
`energy.py`. Operation counts remain a separate proxy.

Example operator sequence after granting the terminal the required privileged
power-sampling entitlement:

```sh
sudo powermetrics --samplers cpu_power -i 1000 -n 30 > /path/to/powermetrics.txt
# Convert only the declared CPU power samples to timestamp_s,power_w CSV.
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.measure_energy_v1 \
  --trace /path/to/cpu_power_trace.csv \
  --output /path/to/energy_receipt.csv \
  --run-id backend-parity-event-camera \
  --hardware macos:powermetrics:cpu_power \
  --events 1280
```

The generated CSV includes the power-trace SHA-256, sample count, duration,
state slice, integration rule, and (when supplied) the exact campaign,
matrix, guard, and backend digests; the CLI also reports the final receipt
SHA-256. At least two strictly increasing samples are required; non-finite,
negative, or non-monotonic samples fail closed. The V2 publication gate
rejects energy receipts that lack complete campaign binding or do not match
its matrix, guard, and backend inputs.

## Current execution status

No joule measurement was produced in this environment. `powermetrics` refused
the unprivileged invocation, and `sudo -n` confirmed that no passwordless
privilege is available. This is an environment gate, not a measured zero. The
repository now has the integration and validation path; an operator must run
the declared sampling path on a privileged host before any joule claim.

## Boundary

The current backend receipts contain operation counts and no joules. A valid
energy receipt still does not establish a learning-quality win or SOTA result.
Fresh-cohort plasticity-guard assessment and the multi-stream quality/resource
publication gate remain closed.

The same privilege result was rechecked on 2026-08-30 while attempting the
powered campaign: `powermetrics --samplers cpu_power -n 1 -i 1000` returned
`must be invoked as the superuser`, and `sudo -n` returned `a password is
required`. No joule receipt was created.
