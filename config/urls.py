# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from config import sitemaps as project_sitemaps
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", include("wagtail.admin.urls")),
    path("django-admin/", admin.site.urls),

    # ✅ robots.txt (utilidades del sitio)
    path("", include("core.urls")),

    path("sitemap.xml", sitemap, {"sitemaps": project_sitemaps.sitemaps}, name="sitemap"),
    path("", include("wagtail.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
