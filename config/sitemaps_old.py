from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from pages.sitemaps import sitemaps

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include("wagtail.admin.urls")),

    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}),

    path("", include("core.urls")),
    path("", include("wagtail.urls")),
]

def items(self):
    return Page.objects.live().public().distinct()

