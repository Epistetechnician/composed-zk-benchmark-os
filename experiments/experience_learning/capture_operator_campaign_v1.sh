#!/usr/bin/env bash

# State slice: oaklab-experience-learning-benchmark-v2.
# Capture the exact real-panel workload while a privileged powermetrics
# sampler is running. The output root must be external and empty so an
# operator never overwrites an existing custody package.

set -Eeuo pipefail

usage() {
  printf '%s\n' \
    "usage: $0 --output-root PATH --powered-root PATH --derived-root PATH --event-root PATH" >&2
}

OUTPUT_ROOT=""
POWERED_ROOT=""
DERIVED_ROOT=""
EVENT_ROOT=""

while (($#)); do
  case "$1" in
    --output-root) OUTPUT_ROOT=${2:-}; shift 2 ;;
    --powered-root) POWERED_ROOT=${2:-}; shift 2 ;;
    --derived-root) DERIVED_ROOT=${2:-}; shift 2 ;;
    --event-root) EVENT_ROOT=${2:-}; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

if [[ -z "$OUTPUT_ROOT" || -z "$POWERED_ROOT" || -z "$DERIVED_ROOT" || -z "$EVENT_ROOT" ]]; then
  usage
  exit 2
fi

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$REPO_ROOT"

for required_root in "$POWERED_ROOT" "$DERIVED_ROOT" "$EVENT_ROOT"; do
  [[ -d "$required_root" ]] || { printf 'missing custody root: %s\n' "$required_root" >&2; exit 1; }
done

mkdir -p "$OUTPUT_ROOT"
if find "$OUTPUT_ROOT" -mindepth 1 -maxdepth 1 -print -quit | grep -q .; then
  printf 'output root must be empty: %s\n' "$OUTPUT_ROOT" >&2
  exit 1
fi

TRANSCRIPT="$OUTPUT_ROOT/workload_transcript.txt"
POWER_TRACE="$OUTPUT_ROOT/powermetrics.txt"
POWER_STDERR="$OUTPUT_ROOT/powermetrics.stderr"
POWER_PID=""
WORKLOAD_STATUS=125
WORKLOAD_STARTED=0
CAPTURE_STOP_UTC=""

utc_now() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

stop_power_capture() {
  if [[ -n "$POWER_PID" ]] && kill -0 "$POWER_PID" 2>/dev/null; then
    kill -TERM "$POWER_PID" 2>/dev/null || true
    local ticks=0
    while kill -0 "$POWER_PID" 2>/dev/null && ((ticks < 50)); do
      sleep 0.1
      ((ticks += 1))
    done
    if kill -0 "$POWER_PID" 2>/dev/null; then
      kill -KILL "$POWER_PID" 2>/dev/null || true
    fi
    wait "$POWER_PID" 2>/dev/null || true
  fi
  CAPTURE_STOP_UTC=$(utc_now)
  POWER_PID=""
}

finish() {
  local status=$?
  trap - EXIT INT TERM
  stop_power_capture
  if ((WORKLOAD_STARTED)); then
    printf 'workload_end_utc=%s\n' "$(utc_now)" >> "$TRANSCRIPT"
    printf 'capture_stop_utc=%s\n' "$CAPTURE_STOP_UTC" >> "$TRANSCRIPT"
    printf 'workload_exit_status=%s\n' "$WORKLOAD_STATUS" >> "$TRANSCRIPT"
  fi
  if ((status == 0)); then
    exit "$WORKLOAD_STATUS"
  fi
  exit "$status"
}

trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'campaign_start_utc=%s\n' "$(utc_now)" > "$TRANSCRIPT"
printf 'state_slice=oaklab-experience-learning-benchmark-v2\n' >> "$TRANSCRIPT"

sudo powermetrics --samplers cpu_power -i 1000 -n 30 > "$POWER_TRACE" 2> "$POWER_STDERR" &
POWER_PID=$!
sleep 1
if ! kill -0 "$POWER_PID" 2>/dev/null; then
  printf 'powermetrics exited before workload start; see %s\n' "$POWER_STDERR" >&2
  exit 1
fi
printf 'power_capture_start_utc=%s\n' "$(utc_now)" >> "$TRANSCRIPT"

WORKLOAD_STARTED=1
{
  printf 'workload_start_utc=%s\n' "$(utc_now)"
  PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_real_benchmark_v1 \
    --root "$POWERED_ROOT" --output "$OUTPUT_ROOT/real_matrix.json"
  PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_real_derived_benchmark_v1 \
    --root "$DERIVED_ROOT" --output "$OUTPUT_ROOT/real_derived_matrix.json"
  PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_real_benchmark_v1 \
    --root "$EVENT_ROOT" --output "$OUTPUT_ROOT/event_long_matrix.json"
  for dataset in noisy_mnist sensor long_horizon event_camera; do
    PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_plasticity_guard_assessment_v2 \
      --root "$POWERED_ROOT" --dataset "$dataset" --output "$OUTPUT_ROOT/guard_${dataset}.json"
  done
  for dataset in noisy_mnist sensor long_horizon event_camera; do
    PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_backend_parity_v1 \
      --root "$POWERED_ROOT" --dataset "$dataset" --output "$OUTPUT_ROOT/backend_${dataset}.json"
  done
} 2>&1 | tee -a "$TRANSCRIPT"
WORKLOAD_STATUS=${PIPESTATUS[0]}
exit "$WORKLOAD_STATUS"
