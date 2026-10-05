"""Entry point for cPanel's Phusion Passenger "Python App".

cPanel activates this project's virtualenv and imports this module,
expecting a WSGI-callable named ``application`` (the convention Passenger's
Python support uses — see cPanel's "Setup Python App").

This host has no shell access, so there is no way to run
`python manage.py migrate` / `seed` / `collectstatic` by hand after a
deploy. Passenger starts a fresh process on the first request after each
deploy (the workflow touches tmp/restart.txt, which is Passenger's standard
restart trigger), so that first boot runs them here instead — the same
idempotent steps entrypoint.sh runs for the Docker/VPS deployment. A marker
file skips the work on every later worker boot, and only redoes it once
tmp/restart.txt is touched again by the next deploy.
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daranx.settings")

import django  # noqa: E402

django.setup()


def _env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in {"1", "true", "yes", "on"}


def _needs_init() -> bool:
    marker = BASE_DIR / ".deployed"
    deploy_signal = BASE_DIR / "tmp" / "restart.txt"
    if not marker.is_file():
        return True
    if deploy_signal.is_file() and deploy_signal.stat().st_mtime > marker.stat().st_mtime:
        return True
    return False


def _run_startup_tasks() -> None:
    from django.core.management import call_command

    marker = BASE_DIR / ".deployed"
    try:
        print("==> Applying migrations", flush=True)
        call_command("migrate", interactive=False)
        if _env_bool("SEED_ON_START", True):
            print("==> Seeding baseline data", flush=True)
            call_command("seed")
        print("==> Collecting static files", flush=True)
        call_command("collectstatic", interactive=False, verbosity=0)
        marker.touch()
    except Exception:
        # A failed startup step must not take the whole app down silently —
        # surface it in cPanel's Python App error log and let the request
        # continue (an un-migrated DB will fail loudly per-request instead,
        # which is still debuggable; a dead app with no log would not be).
        traceback.print_exc()


if _needs_init():
    _run_startup_tasks()

from daranx.wsgi import application  # noqa: E402,F401
