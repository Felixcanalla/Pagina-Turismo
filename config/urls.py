from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from pages.sitemaps import sitemaps

urlpatterns = [
    path("django-admin/", admin.site.urls),

    # Wagtail admin
    path("admin/", include("wagtail.admin.urls")),

    # ✅ robots.txt (template)
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),

    # ✅ sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}),

    # Tus urls propias (si tenés)
   # path("", include("core.urls")),

    # Wagtail pages (SIEMPRE al final)
    path("", include("wagtail.urls")),
]
