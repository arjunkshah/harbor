FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY harbor ./harbor
COPY openclaw ./openclaw
COPY scripts ./scripts
COPY examples ./examples
COPY checkpoints ./checkpoints

RUN pip install --no-cache-dir -e .

ENV HARBOR_DEMO=0
EXPOSE 8787

HEALTHCHECK CMD curl -f http://localhost:8787/health || exit 1

CMD ["harbor", "serve", "--host", "0.0.0.0", "--port", "8787"]
