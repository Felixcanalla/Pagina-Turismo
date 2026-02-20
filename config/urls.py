from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from wagtail.contrib.sitemaps.views import sitemap  # ✅ Wagtail sitemap

urlpatterns = [
    path("admin/", include("wagtail.admin.urls")),
    path("django-admin/", admin.site.urls),

    path("", include("core.urls")),

    # ✅ Sitemap de Wagtail (NO usa get_absolute_url)
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps})

    path("", include("wagtail.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
