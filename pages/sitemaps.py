from django.contrib.sitemaps import Sitemap
from wagtail.models import Page
from pages.models import ArticuloPage, DestinoPage


class WagtailPagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Page.objects.live().public()

    def location(self, obj):
        return obj.url or ""


class ArticulosSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ArticuloPage.objects.live().public()

    def location(self, obj):
        return obj.url or ""


class DestinosSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return DestinoPage.objects.live().public()

    def location(self, obj):
        return obj.url or ""


sitemaps = {
    "wagtail": WagtailPagesSitemap,
    "articulos": ArticulosSitemap,
    "destinos": DestinosSitemap,
}
