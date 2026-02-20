from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from pages.sitemaps import sitemaps

urlpatterns = [
    path("django-admin/", admin.site.urls),

    # Wagtail admin
    path("admin/", include("wagtail.admin.urls")),

    # Tus urls propias (si tenés)
    path("", include("core.urls")),

    # ✅ Sitemap Django (usa tu pages/sitemaps.py)
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}),

    # Wagtail pages
    path("", include("wagtail.urls")),
]
