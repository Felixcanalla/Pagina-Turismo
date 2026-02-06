from django.contrib.sitemaps import Sitemap
from wagtail.models import Page

from pages.models import (
    HomePage,
    SimplePage,
    GuiasIndexPage,
    CategoriaPage,
    ArticuloPage,
    DestinosIndexPage,
    PaisPage,
    DestinoPage,
)


class WagtailPagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        # Incluye todas las páginas públicas y vivas
        return Page.objects.live().public()

    def location(self, obj):
        return obj.url


# Si querés sitemaps separados por tipo (opcional)
class ArticulosSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ArticuloPage.objects.live().public()


class DestinosSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return DestinoPage.objects.live().public()


sitemaps = {
    "wagtail": WagtailPagesSitemap,
    "articulos": ArticulosSitemap,
    "destinos": DestinosSitemap,
}
