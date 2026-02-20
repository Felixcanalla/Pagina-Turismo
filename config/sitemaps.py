from django.contrib.sitemaps import Sitemap
from wagtail.models import Page

from pages.models import ArticuloPage, DestinoPage


def _safe_url(obj):
    """
    Wagtail Page: obj.url puede ser None en algunos casos (no routable / sin site).
    """
    return obj.url or ""


class WagtailPagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        # Incluye todas las páginas públicas y vivas
        return Page.objects.live().public()

    def location(self, obj):
        return _safe_url(obj)


class ArticulosSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ArticuloPage.objects.live().public()

    def location(self, obj):
        return _safe_url(obj)


class DestinosSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return DestinoPage.objects.live().public()

    def location(self, obj):
        return _safe_url(obj)


sitemaps = {
    "wagtail": WagtailPagesSitemap,
    "articulos": ArticulosSitemap,
    "destinos": DestinosSitemap,
}
