FROM python:3.12-slim

# libgomp1: torch needs it at runtime on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements-ml.txt is byte-identical to api-bird-detection-microservice's copy, so this layer
# (the ~3GB fastai/torch/torchvision install) hashes the same in both builds and Docker
# stores/caches it once instead of once per service. All of this service's deps live here — no
# service-specific requirements.txt needed.
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY app ./app

# app/ml/*.pkl is gitignored local data, not part of the image — mount it as a volume at runtime
# (see docker-compose.yml). The container fails fast on startup if it's missing, which is the point.

# Consumer-only — no HTTP server, nothing to EXPOSE.
CMD ["python", "-m", "app.main"]
