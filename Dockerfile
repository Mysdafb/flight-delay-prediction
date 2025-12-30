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

ADD https://astral.sh/uv/0.6.17/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

COPY uv.lock /app/uv.lock
COPY pyproject.toml /app/pyproject.toml
COPY challenge /app/challenge

RUN uv sync --group cloud --no-dev

EXPOSE 8080

CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]