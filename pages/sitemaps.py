from django.contrib.sitemaps import Sitemap
from wagtail.models import Page


class WagtailPagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        qs = Page.objects.live().public().distinct()

        # ✅ sacar el root de Wagtail (depth=1)
        qs = qs.exclude(depth=1)

        # ✅ evitar home duplicada: quedate con una sola URL "/"
        # Nos quedamos con la primera página más "profunda" que resuelva a "/"
        # (normalmente tu HomePage), y excluimos el resto.
        home_candidates = [p for p in qs if (p.url == "/" or p.url == "")]
        if len(home_candidates) > 1:
            # elegimos la que tenga mayor depth (más específica)
            keep = sorted(home_candidates, key=lambda p: p.depth, reverse=True)[0]
            qs = qs.exclude(pk__in=[p.pk for p in home_candidates if p.pk != keep.pk])

        return qs

    def location(self, obj):
        return obj.url or "/"


sitemaps = {"wagtail": WagtailPagesSitemap}
