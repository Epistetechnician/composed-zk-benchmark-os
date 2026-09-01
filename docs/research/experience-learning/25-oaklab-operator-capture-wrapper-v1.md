# Oak Lab operator capture wrapper V1

State slice: `oaklab-experience-learning-benchmark-v2`

`experiments/experience_learning/capture_operator_campaign_v1.sh` is the
bounded operator wrapper for the exact real-panel campaign. It starts
privileged macOS `powermetrics` before the workload, runs the fixed matrix,
guard, and backend commands, and stops the sampler only after the workload
has exited.

The wrapper requires an empty external output root and four existing custody
roots. It writes `powermetrics.txt`, `powermetrics.stderr`, and
`workload_transcript.txt` plus the workload result files. The transcript has
explicit `campaign_start_utc`, `power_capture_start_utc`,
`workload_start_utc`, `workload_end_utc`, `capture_stop_utc`, and
`workload_exit_status` markers.

Example invocation:

```sh
experiments/experience_learning/capture_operator_campaign_v1.sh \
  --output-root /ABSOLUTE/EXTERNAL/oaklab-capture-rN \
  --powered-root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-powered-v2 \
  --derived-root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-derived-v1 \
  --event-root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-event-long-v1
```

The wrapper fails closed on missing roots, a non-empty output root, or a
sampler that exits before workload start. Cleanup sends `TERM`, waits for a
bounded interval, escalates to `KILL`, and always records the stop marker.
The shell cleanup path is tested with a fake sampler and workload:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  experiments/experience_learning/tests/test_capture_operator_campaign_v1.py
```

This wrapper does not integrate joules, infer energy from operations, or
authorize publication. The raw trace still requires the declared conversion,
campaign binding, and independent validation steps.
