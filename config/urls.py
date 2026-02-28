from django.contrib import admin

from django.urls import include, path
from django.views.generic import TemplateView
from pages.views import search


from wagtail.contrib.sitemaps.views import sitemap


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
    path("sitemap.xml", sitemap),

    # Tus urls propias (si tenés)
   # path("", include("core.urls")),
    path("buscar/", search, name="search"),

    # Wagtail pages (SIEMPRE al final)
    path("", include("wagtail.urls")),
]
