#!/bin/sh
# State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v6.
# This entrypoint is a bounded offline batch runner. Provider submission is
# performed only by the separately reviewed launch operator.
set -eu

: "${H100_LAUNCH_MANIFEST:?launch manifest path is required}"
: "${H100_MODEL_ROOT:?sealed model root is required}"
: "${H100_RAW_ROOT:?sealed raw dataset root is required}"
: "${H100_SOURCE_ROOT:?sealed source bundle root is required}"
: "${H100_CORPUS_ROOT:?sealed corpus root is required}"
: "${H100_RESULT_ROOT:?empty result root is required}"
: "${H100_NETWORK_LOCK:?network lock is required}"
: "${H100_CONTAINER_NETWORK_MODE:?container network mode is required}"

if [ "${H100_NETWORK_LOCK}" != "network-none-v6" ]; then
  echo "invalid network lock" >&2
  exit 64
fi
if [ "${H100_CONTAINER_NETWORK_MODE}" != "none" ]; then
  echo "container network mode is not none" >&2
  exit 64
fi
if [ -r /proc/net/dev ] && [ "$(awk -F: 'NF > 1 {gsub(/ /, "", $1); print $1}' /proc/net/dev | sort | tr '\n' ' ')" != "lo " ]; then
  echo "network namespace contains a non-loopback device" >&2
  exit 64
fi
if [ ! -r /proc/net/route ] || [ "$(awk 'NR > 1 && NF >= 4 {print}' /proc/net/route)" != "" ]; then
  echo "network namespace has an IPv4 route" >&2
  exit 64
fi
if [ ! -r /proc/net/ipv6_route ] || [ "$(tr -d '[:space:]' </proc/net/ipv6_route)" != "" ]; then
  echo "network namespace has an IPv6 route" >&2
  exit 64
fi
if [ "${H100_TRAINING_ENABLED:-false}" != "false" ]; then
  echo "training is forbidden" >&2
  exit 64
fi
if [ "${H100_JOB_MODE:-batch}" != "batch" ] || [ "${H100_NODE_TYPE:-h100-1}" != "h100-1" ]; then
  echo "only one h100-1 batch job is permitted" >&2
  exit 64
fi

python -m experiments.continual_learning.validate_gemma3_fineweb_edu_replication_h100_v6 \
  --pre-effect \
  --raw-root "${H100_RAW_ROOT}" \
  --source-root "${H100_SOURCE_ROOT}" \
  --corpus-root "${H100_CORPUS_ROOT}" \
  --model-root "${H100_MODEL_ROOT}" \
  --launch-manifest "${H100_LAUNCH_MANIFEST}" \
  --repo-root /opt/h100-replication

python -m experiments.continual_learning.gemma3_fineweb_edu_replication_h100_v6 \
  --launch-manifest "${H100_LAUNCH_MANIFEST}" \
  --model-root "${H100_MODEL_ROOT}" \
  --raw-root "${H100_RAW_ROOT}" \
  --source-root "${H100_SOURCE_ROOT}" \
  --corpus-root "${H100_CORPUS_ROOT}" \
  --result-root "${H100_RESULT_ROOT}" \
  --repo-root /opt/h100-replication

exec python -m experiments.continual_learning.validate_gemma3_fineweb_edu_replication_h100_v6 \
  --result-root "${H100_RESULT_ROOT}" \
  --raw-root "${H100_RAW_ROOT}" \
  --source-root "${H100_SOURCE_ROOT}" \
  --corpus-root "${H100_CORPUS_ROOT}" \
  --model-root "${H100_MODEL_ROOT}" \
  --launch-manifest "${H100_LAUNCH_MANIFEST}" \
  --repo-root /opt/h100-replication
