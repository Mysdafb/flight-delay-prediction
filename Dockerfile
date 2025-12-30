# syntax=docker/dockerfile:1.2
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV VENV_PATH=/app/.venv
ENV PATH="$VENV_PATH/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY uv.lock /app/uv.lock
COPY challenge /app/challenge

RUN uv sync --group cloud --no-dev --lockfile /app/uv.lock

EXPOSE 8080

CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]