# State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v5.
# The image digest is supplied at build/launch time and is never inferred.
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04@sha256:0a1cb6e7bd047a1067efe14efdf0276352d5ca643dfd77963dab1a4f05a003a4

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/h100-replication/.venv \
    PATH=/opt/h100-replication/.venv/bin:${PATH} \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    TOKENIZERS_PARALLELISM=false

WORKDIR /opt/h100-replication
COPY experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5.py /opt/h100-replication/experiments/continual_learning/
COPY experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_preflight.py /opt/h100-replication/experiments/continual_learning/
COPY experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v5.py /opt/h100-replication/experiments/continual_learning/
COPY experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v5.py /opt/h100-replication/experiments/continual_learning/
COPY experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v5_preflight.py /opt/h100-replication/experiments/continual_learning/tests/
COPY experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v5.py /opt/h100-replication/experiments/continual_learning/tests/
COPY docs/research/continual-learning/267-gemma3-fineweb-edu-replication-h100-v5-protocol.md /opt/h100-replication/docs/research/continual-learning/
COPY docs/research/continual-learning/268-gemma3-fineweb-edu-replication-h100-v5-review-packet.md /opt/h100-replication/docs/research/continual-learning/
COPY docs/research/continual-learning/269-gemma3-fineweb-edu-replication-h100-v5-implementation-manifest.json /opt/h100-replication/docs/research/continual-learning/
COPY AGENTS.md /opt/h100-replication/AGENTS.md
COPY experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/run_h100_v5.sh /opt/h100-replication/
COPY experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/runtime-lock.json /opt/h100-replication/
COPY experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/requirements.lock /opt/h100-replication/

RUN chmod 0555 /opt/h100-replication/run_h100_v5.sh \
    && test -s /opt/h100-replication/runtime-lock.json \
    && test -s /opt/h100-replication/requirements.lock \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        ca-certificates \
        python3.11 \
        python3.11-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3.11 -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/python" -m pip install \
        --no-input \
        --no-deps \
        --requirement /opt/h100-replication/requirements.lock \
    && "${VIRTUAL_ENV}/bin/python" -m pip check \
    && python -c 'import importlib.metadata as m, json, platform, torch; lock=json.load(open("/opt/h100-replication/runtime-lock.json")); assert ".".join(platform.python_version().split(".")[:2]) == lock["python"]; assert m.version("accelerate").split("+")[0] == lock["accelerate"]; assert m.version("cryptography").split("+")[0] == lock["cryptography"]; assert torch.__version__.split("+")[0] == lock["pytorch"]; assert str(torch.version.cuda) == lock["cuda_runtime"]; assert m.version("transformers").split("+")[0] == lock["transformers"]; assert m.version("safetensors").split("+")[0] == lock["safetensors"]; assert m.version("tokenizers").split("+")[0] == lock["tokenizers"]; assert m.version("pyarrow").split("+")[0] == lock["pyarrow"]; assert lock["package_install_at_runtime"] is False'

ENTRYPOINT ["/opt/h100-replication/run_h100_v5.sh"]
