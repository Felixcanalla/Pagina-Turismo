from __future__ import annotations

from pathlib import Path
from typing import Optional

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from wagtail.models import Page, Site
from wagtail.rich_text import RichText
from wagtail.images.models import Image as WagtailImage

from contenido.models import Categoria as LegacyCategoria, Articulo as LegacyArticulo
from destinos.models import Pais as LegacyPais, Destino as LegacyDestino, SeccionDestino as LegacySeccion


def unique_child_slug(parent: Page, base: str) -> str:
    base = slugify(base)[:60] or "item"
    slug = base
    i = 2
    while parent.get_children().filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def import_wagtail_image_from_file(path: str | None, title: str) -> Optional[WagtailImage]:
    """
    Importa un archivo de imagen (del media legacy) a la librería de Wagtail Images.
    Si no existe o falla, devuelve None.
    """
    if not path:
        return None

    p = Path(path)
    if not p.exists() or not p.is_file():
        return None

    filename = p.name

    # evitar duplicados simples
    existing = WagtailImage.objects.filter(title=title, file__icontains=filename).first()
    if existing:
        return existing

    try:
        with p.open("rb") as f:
            img = WagtailImage(title=title)
            img.file.save(filename, File(f), save=True)
            return img
    except Exception:
        return None


class Command(BaseCommand):
    help = "Migra contenido legacy (contenido/destinos) a Wagtail Pages y deja Wagtail como CMS principal."

    def handle(self, *args, **options):
        # === Resolver modelos Wagtail Pages desde apps (evita imports frágiles) ===
        HomePage = apps.get_model("pages", "HomePage")
        GuiasIndexPage = apps.get_model("pages", "GuiasIndexPage")
        CategoriaPage = apps.get_model("pages", "CategoriaPage")
        ArticuloPage = apps.get_model("pages", "ArticuloPage")

        DestinosIndexPage = apps.get_model("pages", "DestinosIndexPage")
        PaisPage = apps.get_model("pages", "PaisPage")
        DestinoPage = apps.get_model("pages", "DestinoPage")
        SeccionDestinoPage = apps.get_model("pages", "SeccionDestinoPage")

        site = Site.objects.get(is_default_site=True)
        root = site.root_page  # normalmente 'Root'

        # 1) HomePage
        home = root.get_children().type(HomePage).first()
        if not home:
            home = HomePage(title="Home", slug=unique_child_slug(root, "home"))
            root.add_child(instance=home)
            home.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("✅ HomePage creada"))

        # Apuntar el Site a HomePage
        if site.root_page_id != home.id:
            site.root_page = home
            site.save()
            self.stdout.write(self.style.SUCCESS("✅ Site.root_page actualizado a HomePage"))

        # 2) Índices Guías / Destinos
        guias_index = home.get_children().type(GuiasIndexPage).first()
        if not guias_index:
            guias_index = GuiasIndexPage(title="Guías", slug=unique_child_slug(home, "guias"))
            home.add_child(instance=guias_index)
            guias_index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("✅ GuiasIndexPage creada (/guias/)"))

        destinos_index = home.get_children().type(DestinosIndexPage).first()
        if not destinos_index:
            destinos_index = DestinosIndexPage(title="Destinos", slug=unique_child_slug(home, "destinos"))
            home.add_child(instance=destinos_index)
            destinos_index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("✅ DestinosIndexPage creada (/destinos/)"))

        # 3) Migrar Países
        pais_map: dict[int, Page] = {}
        for p in LegacyPais.objects.all():
            nombre = getattr(p, "nombre", None) or getattr(p, "name", None) or "País"
            slug = unique_child_slug(destinos_index, getattr(p, "slug", None) or nombre)

            # buscar por title para evitar duplicados por ejecuciones repetidas
            page = destinos_index.get_children().type(PaisPage).filter(title=nombre).first()
            if not page:
                page = PaisPage(
                    title=nombre,
                    slug=slug,
                    descripcion_corta=(getattr(p, "descripcion", "") or "")[:180],
                    intro=RichText(getattr(p, "descripcion", "") or ""),
                )
                destinos_index.add_child(instance=page)
                page.save_revision().publish()

            pais_map[p.id] = page

        self.stdout.write(self.style.SUCCESS(f"✅ Países migrados: {len(pais_map)}"))

        # 4) Migrar Destinos (incluye imagen si existe)
        destino_map: dict[int, Page] = {}
        for d in LegacyDestino.objects.all():
            parent = pais_map.get(d.pais_id)
            if not parent:
                continue

            nombre = getattr(d, "nombre", None) or getattr(d, "name", None) or "Destino"
            slug = unique_child_slug(parent, getattr(d, "slug", None) or nombre)

            page = parent.get_children().type(DestinoPage).filter(title=nombre).first()
            if not page:
                page = DestinoPage(
                    title=nombre,
                    slug=slug,
                    descripcion_corta=(getattr(d, "resumen", "") or "")[:180],
                    intro=RichText(getattr(d, "contenido", "") or ""),
                    destacado=False,
                )

                # Imagen legacy -> Wagtail Image
                legacy_img = getattr(d, "imagen", None)
                if legacy_img:
                    try:
                        img_path = legacy_img.path
                    except Exception:
                        img_path = None
                    hero = import_wagtail_image_from_file(img_path, title=f"Destino: {nombre}")
                    if hero:
                        page.hero_image = hero

                parent.add_child(instance=page)
                page.save_revision().publish()

            destino_map[d.id] = page

        self.stdout.write(self.style.SUCCESS(f"✅ Destinos migrados: {len(destino_map)}"))

        # 5) Migrar Secciones (contenido a StreamField)
        sec_count = 0
        for s in LegacySeccion.objects.all().order_by("destino_id", "orden"):
            parent = destino_map.get(s.destino_id)
            if not parent:
                continue

            titulo = getattr(s, "titulo", None) or "Sección"
            slug = unique_child_slug(parent, getattr(s, "slug", None) or titulo)

            page = parent.get_children().type(SeccionDestinoPage).filter(title=titulo).first()
            if not page:
                page = SeccionDestinoPage(title=titulo, slug=slug)
                parent.add_child(instance=page)

                contenido = getattr(s, "contenido", "") or ""
                if contenido:
                    page.body = [("paragraph", RichText(contenido))]

                page.save_revision().publish()
                sec_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Secciones migradas: {sec_count}"))

        # 6) Migrar Categorías
        cat_map: dict[int, Page] = {}
        for c in LegacyCategoria.objects.all():
            nombre = getattr(c, "nombre", None) or "Categoría"
            slug = unique_child_slug(guias_index, getattr(c, "slug", None) or nombre)

            page = guias_index.get_children().type(CategoriaPage).filter(title=nombre).first()
            if not page:
                page = CategoriaPage(
                    title=nombre,
                    slug=slug,
                    descripcion_corta="",
                    intro=RichText(""),
                )
                guias_index.add_child(instance=page)
                page.save_revision().publish()

            cat_map[c.id] = page

        self.stdout.write(self.style.SUCCESS(f"✅ Categorías migradas: {len(cat_map)}"))

        # 7) Migrar Artículos (incluye imagen, destino_principal, destinos m2m)
        articulo_map: dict[int, Page] = {}
        for a in LegacyArticulo.objects.all().order_by("created_at"):
            titulo = getattr(a, "titulo", None) or "Artículo"
            slug = unique_child_slug(guias_index, getattr(a, "slug", None) or titulo)

            page = guias_index.get_children().type(ArticuloPage).filter(title=titulo).first()
            if not page:
                page = ArticuloPage(
                    title=titulo,
                    slug=slug,
                    destacado=False,
                    categoria=cat_map.get(a.categoria_id),
                    resumen=RichText(getattr(a, "extracto", "") or ""),
                )

                # Imagen legacy -> Wagtail Image
                legacy_img = getattr(a, "imagen", None)
                if legacy_img:
                    try:
                        img_path = legacy_img.path
                    except Exception:
                        img_path = None
                    hero = import_wagtail_image_from_file(img_path, title=f"Artículo: {titulo}")
                    if hero:
                        page.hero_image = hero

                # body
                contenido = getattr(a, "contenido", "") or ""
                if contenido:
                    page.body = [("paragraph", RichText(contenido))]

                # destino_principal = primer destino si existe
                legacy_destinos = list(a.destinos.all())
                if legacy_destinos:
                    page.destino_principal = destino_map.get(legacy_destinos[0].id)

                guias_index.add_child(instance=page)
                page.save_revision().publish()

            articulo_map[a.id] = page

            # ManyToMany destinos (si existe el campo destinos en ArticuloPage)
            if hasattr(page, "destinos"):
                legacy_destinos = list(a.destinos.all())
                if legacy_destinos:
                    page.destinos.set([destino_map[d.id] for d in legacy_destinos if d.id in destino_map])
                    page.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Artículos migrados: {len(articulo_map)}"))

        # 8) Relacionados manuales (si existe)
        rel_count = 0
        for a in LegacyArticulo.objects.all():
            page = articulo_map.get(a.id)
            if not page or not hasattr(page, "relacionados_manual"):
                continue

            related_pages = []
            for rel in a.relacionados_manual.all():
                rel_page = articulo_map.get(rel.id)
                if rel_page:
                    related_pages.append(rel_page)

            if related_pages:
                page.relacionados_manual.set(related_pages)
                page.save()
                rel_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Relacionados manuales migrados en: {rel_count} artículos"))
        self.stdout.write(self.style.SUCCESS("🎉 Migración completada. Entrá a /cms/ para editar contenido."))
