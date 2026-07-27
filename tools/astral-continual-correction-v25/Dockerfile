FROM python@sha256:76d4b7b6305788c6b4c6a19d6a22a3921bf802e9af4d5e1e5bd771208dba74bf

LABEL org.opencontainers.image.title="Astral V25 continual-correction simulation"
LABEL org.opencontainers.image.description="Hermetic synthetic protocol validation only"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY Dockerfile experiment-contract.json v25.py /app/source/
COPY experiment-contract.json v25.py /app/

USER 65532:65532
ENTRYPOINT ["python", "/app/v25.py"]
