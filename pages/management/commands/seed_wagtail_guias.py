from __future__ import annotations

import random
import string
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from wagtail.models import Page, Site
from wagtail.rich_text import RichText
from wagtail.images import get_image_model

from pages.models import GuiasIndexPage, ArticuloPage


def _unique_slug(parent: Page, base: str) -> str:
    base = slugify(base)[:60] or "guia"
    slug = base
    i = 2
    while parent.get_children().filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _lorem_paragraph() -> str:
    parts = [
        "Esta guía está pensada para ayudarte a planificar el viaje con información clara y práctica.",
        "Incluimos recomendaciones editoriales, tiempos estimados y consejos para aprovechar mejor cada día.",
        "Recordá revisar horarios y precios porque pueden variar según temporada.",
    ]
    return random.choice(parts)


class Command(BaseCommand):
    help = "Crea automáticamente una página Guías y artículos Wagtail para probar layout y paginación."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=30, help="Cantidad de artículos a crear (default: 30)")
        parser.add_argument("--clear", action="store_true", help="Borra artículos creados previamente (solo los de este seed)")
        parser.add_argument("--with-hero", action="store_true", help="Asigna hero_image aleatoria si existen imágenes en Wagtail")
        parser.add_argument("--seed-tag", type=str, default="seed-auto", help="Marca interna para poder limpiar (default: seed-auto)")

    def handle(self, *args, **opts):
        count: int = opts["count"]
        clear: bool = opts["clear"]
        with_hero: bool = opts["with_hero"]
        seed_tag: str = opts["seed_tag"]

        # Obtener Site y Home
        site = Site.objects.get(is_default_site=True)
        home = site.root_page

        # Asegurar GuiasIndexPage
        guias = home.get_children().type(GuiasIndexPage).first()
        if not guias:
            guias = GuiasIndexPage(
                title="Guías",
                slug=_unique_slug(home, "guias"),
            )
            home.add_child(instance=guias)
            guias.save_revision().publish()
            self.stdout.write(self.style.SUCCESS(f"✅ Creada GuiasIndexPage: {guias.url_path}"))

        # Preparar imágenes (opcional)
        hero_pool = []
        if with_hero:
            Image = get_image_model()
            hero_pool = list(Image.objects.all()[:50])

        # Limpieza (solo artículos con un "marcador" en el resumen)
        if clear:
            qs = guias.get_children().type(ArticuloPage).live().filter(resumen__contains=f"[{seed_tag}]")
            deleted = 0
            for p in qs:
                p.delete()
                deleted += 1
            self.stdout.write(self.style.WARNING(f"🧹 Eliminados {deleted} artículos seed (tag={seed_tag})."))

        # Crear artículos
        created = 0
        for i in range(1, count + 1):
            title = f"Guía demo #{i}: qué hacer y cómo moverse"
            slug = _unique_slug(guias, title)

            # StreamField: heading + párrafos + (opcional) un bloque imagen sin caption
            blocks = [
                ("heading", "Resumen del destino"),
                ("paragraph", RichText(f"<p>{_lorem_paragraph()}</p>")),
                ("heading", "Qué hacer"),
                ("paragraph", RichText(f"<p>{_lorem_paragraph()}</p>")),
                ("heading", "Cómo moverse"),
                ("paragraph", RichText(f"<p>{_lorem_paragraph()}</p>")),
            ]

            articulo = ArticuloPage(
                title=title,
                slug=slug,
                resumen=RichText(f"<p>[{seed_tag}] Guía de prueba para validar layout, navegación y paginación.</p>"),
                body=blocks,
            )

            if hero_pool:
                articulo.hero_image = random.choice(hero_pool)

            guias.add_child(instance=articulo)
            articulo.save_revision().publish()
            created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Artículos creados: {created}"))
        self.stdout.write(self.style.SUCCESS("👉 Probá: /w/guias/ y /w/guias/?page=2"))
