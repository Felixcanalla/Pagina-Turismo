from django.contrib.sitemaps import Sitemap
from wagtail.models import Page


class WagtailPagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Page.objects.live().public()

    def location(self, obj):
        # ✅ URLs relativas -> evita example.com y funciona perfecto en Google
        return obj.url or "/"


sitemaps = {
    "wagtail": WagtailPagesSitemap,
}
