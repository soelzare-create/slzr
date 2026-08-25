"""Root URL configuration for the DaranX API."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def root(_request):
    return JsonResponse({
        "app": "DaranX",
        "motto": "همه چیز سر جای خودش",
        "api": "/api/",
    })


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", root),
    path("health", health),
    path("admin/", admin.site.urls),
    path("api/", include("daranx.api_urls")),
]
