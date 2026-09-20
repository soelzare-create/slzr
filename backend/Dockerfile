# DaranX backend — production image (Django + DRF served by gunicorn).
FROM python:3.12-slim

# Python runtime hygiene.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps: psycopg[binary] ships its own libpq, so only minimal tools are
# needed. curl is used by the container HEALTHCHECK.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

# App source.
COPY . .

# Collect static assets (admin + DRF browsable API) into STATIC_ROOT.
# DEBUG=false so manifest/compressed storage is used.
RUN DEBUG=false SECRET_KEY=build-only-not-used python manage.py collectstatic --noinput

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
