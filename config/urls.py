from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap

from config import sitemaps as project_sitemaps
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ✅ Wagtail Admin (CMS real)
    path("admin/", include("wagtail.admin.urls")),

    # (opcional) Django Admin separado para usuarios/DB
    path("django-admin/", admin.site.urls),

    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": project_sitemaps.sitemaps}, name="sitemap"),

    # Sitio público (páginas Wagtail)
    path("", include("wagtail.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)