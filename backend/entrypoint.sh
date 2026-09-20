#!/usr/bin/env sh
# Container entrypoint: apply migrations, optionally seed, then serve.
# Every step is idempotent, so restarts are safe.
set -e

# Wait for the database when a host is configured (compose/PaaS may start the
# app before Postgres is accepting connections).
python <<'PY'
import os, sys, time
from urllib.parse import urlparse

url = os.getenv("DATABASE_URL", "")
if url and not url.startswith("sqlite"):
    import socket
    p = urlparse(url)
    host, port = p.hostname, p.port or 5432
    for _ in range(60):
        try:
            with socket.create_connection((host, port), timeout=2):
                break
        except OSError:
            print(f"waiting for database at {host}:{port} ...", flush=True)
            time.sleep(2)
    else:
        print("database not reachable, giving up", file=sys.stderr)
        sys.exit(1)
PY

echo "==> Applying migrations"
python manage.py migrate --noinput

# Seed once: creates the RBAC matrix, roles, chart of accounts and the first
# admin. Safe to re-run (idempotent). Disable with SEED_ON_START=false.
if [ "${SEED_ON_START:-true}" = "true" ]; then
  echo "==> Seeding baseline data"
  python manage.py seed
fi

echo "==> Starting gunicorn"
exec gunicorn daranx.wsgi:application \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
