# syntax=docker/dockerfile:1
#
# Shared Dockerfile for every FastAPI microservice under services/*.
# Each service shares the top-level `shared` package, so the build
# context must be the backend/ root (not an individual service dir).
#
# Build (from backend/):
#   docker build --build-arg SERVICE_NAME=api_gateway_service -t maatitrace/api-gateway-service .
#
# Run:
#   docker run -p 8000:8000 --env-file .env maatitrace/api-gateway-service

FROM python:3.12-slim AS base

ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN test -n "$SERVICE_NAME" || (echo "SERVICE_NAME build-arg is required" && exit 1)

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-base.txt ./
COPY services/${SERVICE_NAME}/requirements.txt services/${SERVICE_NAME}/requirements.txt
RUN pip install --no-cache-dir -r services/${SERVICE_NAME}/requirements.txt

COPY shared/ shared/
COPY services/${SERVICE_NAME}/ services/${SERVICE_NAME}/

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3).status == 200 else 1)"

CMD ["sh", "-c", "gunicorn services.${SERVICE_NAME}.app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2}"]
