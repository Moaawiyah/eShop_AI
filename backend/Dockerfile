# eShop_AI backend image (SHOP-122, basic). Build context: backend/.
# Production hardening (digest pins, scanning, SBOM) is M7 (SHOP-075).

FROM python:3.13.18-slim-trixie AS builder
ENV UV_COMPILE_BYTECODE=0 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
# uv from its official image (pinned); dependencies come only from uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.11.10 /uv /usr/local/bin/uv
WORKDIR /app
# Dependency layer: cached until pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY app ./app

FROM python:3.13.18-slim-trixie AS runtime
ENV BACKEND_HOST=0.0.0.0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder --chown=root:root /app/.venv /app/.venv
COPY --from=builder --chown=root:root /app/app /app/app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"]
# Exec form: no shell in between, so SIGTERM (forwarded by the Compose init
# process) reaches uvicorn for graceful shutdown.
CMD ["python", "-m", "app"]
