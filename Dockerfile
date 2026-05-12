FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

WORKDIR /app
COPY pyproject.toml .
RUN uv sync

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg \
    && echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list \
    && apt-get update && apt-get install -y microsoft-edge-stable

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

WORKDIR /app/TC002
RUN if [ -f msedgedriver ]; then chmod +x msedgedriver; fi

CMD ["xvfb-run", "/app/.venv/bin/python", "-m", "unittest", "T_003"]