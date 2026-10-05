"""Root URL configuration for the DaranX API + the React SPA it serves."""
from django.conf import settings
from django.contrib import admin
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import include, path, re_path


def health(_request):
    return JsonResponse({"status": "ok"})


_index_html_cache: str | None = None


def spa_index(_request, *args, **kwargs):
    """Serve the built React app's index.html for any non-API route.

    WhiteNoise's middleware already intercepts requests for an actual file
    under FRONTEND_DIST (the hashed JS/CSS Vite emits) before the URL
    resolver even runs, so this view only ever fires for a "soft" client-side
    route — /, /invoices, /customers/42, a hard refresh on any of them, etc.
    Absent in local dev (no frontend_dist there); returns 404 rather than a
    stack trace if it's ever hit without a build in place.
    """
    global _index_html_cache
    if _index_html_cache is None:
        index_path = settings.FRONTEND_DIST / "index.html"
        if not index_path.is_file():
            raise Http404("frontend build not found — see FRONTEND_DIST in settings.py")
        _index_html_cache = index_path.read_text(encoding="utf-8")
    return HttpResponse(_index_html_cache, content_type="text/html; charset=utf-8")


urlpatterns = [
    path("health", health),
    path("admin/", admin.site.urls),
    path("api/", include("daranx.api_urls")),
    # Everything else is the React SPA — keep this last.
    re_path(r"^.*$", spa_index),
]
