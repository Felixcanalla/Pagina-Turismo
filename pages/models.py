from django.apps import apps
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.utils.html import format_html, strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from .utils import build_toc_and_body_html, get_filtered_breadcrumb_ancestors
import json

from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.rich_text import RichText
from wagtail.search import index

from .blocks import (
    CTAButtonBlock,
    FAQBlock,
    GalleryBlock,
    HighlightsBlock,
    ImageBlock,
    InfoGridBlock,
    MapEmbedBlock,
    QuickSectionBlock,
    QuickSectionsBlock,
    SectionTitleBlock,
    YouTubeBlock,
)


# ============================================================
# Helpers
# ============================================================

def build_toc_and_body_html(stream):
    """
    Genera:
      - toc: lista de {title, anchor, level}
      - body_html: HTML renderizado del StreamField, insertando <h2 id="...">
        para bloques section_title y quick_section(s) sin duplicar títulos.

    Importante:
      - Los bloques se renderizan con block.render(), pero cuando un bloque trae
        un título (section_title / quick_section / quick_sections) nosotros
        rendereamos el <h2 id="..."> manualmente para TOC y luego renderizamos
        el bloque completo "sin título" usando CSS (.qs__rendered--no-title).
    """
    used = {}
    toc = []
    parts = []

    def unique_anchor(title: str) -> str:
        base = slugify(title) or "seccion"
        used[base] = used.get(base, 0) + 1
        return base if used[base] == 1 else f"{base}-{used[base]}"

    def add_heading(title: str, subtitle: str = ""):
        anchor = unique_anchor(title)
        toc.append({"title": title, "anchor": anchor, "level": 2})

        title = strip_tags(title)
        subtitle = strip_tags(subtitle)

        if subtitle:
            parts.append(
                format_html(
                    '<section class="block block-title"><h2 id="{}">{}</h2><p class="muted">{}</p></section>',
                    anchor,
                    title,
                    subtitle,
                )
            )
        else:
            parts.append(
                format_html(
                    '<section class="block block-title"><h2 id="{}">{}</h2></section>',
                    anchor,
                    title,
                )
            )

    if not stream:
        return [], mark_safe("")

    for block in stream:
        # 1) Título explícito
        if block.block_type == "section_title":
            title = (block.value.get("title") or "").strip()
            if not title:
                continue
            subtitle = (block.value.get("subtitle") or "").strip()
            add_heading(title, subtitle)
            continue

        # 2) QuickSection: si tiene title, lo metemos en TOC y luego renderizamos bloque sin repetir H2
        if block.block_type == "quick_section":
            title = (block.value.get("title") or "").strip()
            subtitle = (block.value.get("subtitle") or "").strip()

            if title:
                add_heading(title, subtitle)
                parts.append(
                    format_html(
                        '<div class="qs__rendered qs__rendered--no-title">{}</div>',
                        mark_safe(block.render()),
                    )
                )
            else:
                parts.append(mark_safe(block.render()))
            continue

        # 3) QuickSections: contenedor con varias secciones
        if block.block_type == "quick_sections":
            sections = block.value.get("sections") or []
            for s in sections:
                title = (getattr(s, "get", lambda *_: None)("title") or "").strip()
                if not title:
                    continue
                subtitle = (getattr(s, "get", lambda *_: None)("subtitle") or "").strip()
                add_heading(title, subtitle)

                # Render de la sección completa, pero sin título (ya lo agregamos)
                parts.append(
                    format_html(
                        '<div class="qs__rendered qs__rendered--no-title">{}</div>',
                        mark_safe(s.render()),
                    )
                )
            continue

        # 4) Otros bloques: render normal
        parts.append(mark_safe(block.render()))

    return toc, mark_safe("".join(parts))


def get_filtered_breadcrumb_ancestors(page: Page):
    """
    Breadcrumbs filtrados (sin Welcome/Home) usando depth>=4 como ya venías haciendo.
    """
    return [
        a.specific
        for a in page.get_ancestors().live().public()
        if a.depth >= 4
    ]


# ============================================================
# HOME / SIMPLE
# ============================================================

class HomePage(Page):
    """Home servido por Wagtail usando el template existente (templates/core/home.html)."""

    subpage_types = ["pages.GuiasIndexPage", "pages.DestinosIndexPage", "pages.SimplePage"]
    template = "core/home.html"

    seo_description = models.CharField(max_length=160, blank=True)

    def get_context(self, request):
        context = super().get_context(request)

        DestinoPage = apps.get_model("pages", "DestinoPage")
        ArticuloPage = apps.get_model("pages", "ArticuloPage")

        destinos_qs = DestinoPage.objects.live().public().order_by("-first_published_at")
        if "destacado" in [f.name for f in DestinoPage._meta.get_fields()]:
            destinos_qs = destinos_qs.filter(destacado=True).order_by("-first_published_at")
        context["destinos"] = destinos_qs[:6]

        articulos_qs = ArticuloPage.objects.live().public().order_by("-first_published_at")
        if "destacado" in [f.name for f in ArticuloPage._meta.get_fields()]:
            articulos_qs = articulos_qs.filter(destacado=True).order_by("-first_published_at")
        context["articulos"] = articulos_qs[:6]

        return context


class SimplePage(Page):
    template = "pages/simple_page.html"
    seo_description = models.CharField(max_length=160, blank=True)

    body = StreamField(
        [
            ("rich_text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "link", "ul", "ol"])),
            ("youtube", YouTubeBlock()),
            ("image", ImageBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel([FieldPanel("seo_description")], heading="SEO"),
    ]

    parent_page_types = ["pages.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Página simple"


# ============================================================
# GUÍAS
# ============================================================

class GuiasIndexPage(Page):
    """Índice editorial de guías. Listado + filtros por categoría + paginación."""

    parent_page_types = ["pages.HomePage"]
    subpage_types = ["pages.CategoriaPage"]
    template = "pages/guias_index_page.html"

    def get_context(self, request):
        context = super().get_context(request)

        CategoriaPageModel = apps.get_model("pages", "CategoriaPage")
        categorias = (
            self.get_children()
            .type(CategoriaPageModel)
            .live()
            .public()
            .order_by("title")
        )
        context["categorias"] = categorias

        ArticuloPageModel = apps.get_model("pages", "ArticuloPage")
        qs = (
            self.get_descendants()
            .type(ArticuloPageModel)
            .live()
            .public()
            .order_by("-first_published_at")
        )

        # filtro por categoría via ?cat=slug
        cat_slug = request.GET.get("cat")
        if cat_slug:
            # Articulo vive debajo de Categoria, así que filtramos por url_path
            qs = qs.filter(url_path__contains=f"/{cat_slug}/")

        context["cat_activa"] = cat_slug

        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        context["page_obj"] = page_obj

        params = request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()

        return context

    class Meta:
        verbose_name = "Índice de Guías"


class CategoriaPage(Page):
    """Landing editorial de categoría (SEO). Vive debajo de GuiasIndexPage."""

    seo_description = models.CharField(max_length=160, blank=True)

    parent_page_types = ["pages.GuiasIndexPage"]
    subpage_types = ["pages.ArticuloPage"]
    template = "pages/categoria_page.html"

    descripcion_corta = models.CharField(max_length=180, blank=True)
    intro = RichTextField(blank=True, features=["bold", "italic", "link"])

    content_panels = Page.content_panels + [
        FieldPanel("descripcion_corta"),
        FieldPanel("intro"),
    ]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel([FieldPanel("seo_description")], heading="SEO"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        ArticuloPageModel = apps.get_model("pages", "ArticuloPage")
        context["articulos"] = (
            ArticuloPageModel.objects.live().public()
            .child_of(self)
            .order_by("-first_published_at")
        )
        return context

    class Meta:
        verbose_name = "Categoría"


# ============================================================
# DESTINOS
# ============================================================

class DestinosIndexPage(Page):
    """Índice editorial de Destinos. Vive debajo de HomePage."""

    seo_description = models.CharField(max_length=160, blank=True)

    parent_page_types = ["pages.HomePage"]
    subpage_types = ["pages.PaisPage"]
    template = "pages/destinos_index_page.html"

    def get_context(self, request):
        context = super().get_context(request)
        PaisPageModel = apps.get_model("pages", "PaisPage")
        context["paises"] = (
            PaisPageModel.objects.live().public()
            .child_of(self)
            .order_by("title")
        )
        return context

    class Meta:
        verbose_name = "Índice de Destinos"


class PaisPage(Page):
    parent_page_types = ["pages.DestinosIndexPage"]
    subpage_types = ["pages.DestinoPage"]
    template = "pages/pais_page.html"

    seo_description = models.CharField(max_length=160, blank=True)
    descripcion_corta = models.CharField(max_length=180, blank=True)
    intro = RichTextField(blank=True, features=["bold", "italic", "link"])

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("descripcion_corta"),
        FieldPanel("intro"),
        FieldPanel("hero_image"),
    ]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel([FieldPanel("seo_description")], heading="SEO"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        DestinoPageModel = apps.get_model("pages", "DestinoPage")
        context["destinos"] = (
            DestinoPageModel.objects.live().public()
            .child_of(self)
            .order_by("title")
        )
        return context

    class Meta:
        verbose_name = "País"


class DestinoPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "pages.DestinoPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )





class DestinoPage(Page):
    template = "pages/destino_page.html"

    seo_description = models.CharField(max_length=160, blank=True)
    intro = models.CharField(max_length=250, blank=True)

    tags = ClusterTaggableManager(through="pages.DestinoPageTag", blank=True)

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ✅ Campo temporal para pegar HTML (Docs/Word)
    contenido_bruto = models.TextField(
        blank=True,
        help_text="Pegá HTML (Docs/Word). Al guardar, se convierte a bloques automáticamente.",
    )

    body = StreamField(
        [
            ("quick_sections", QuickSectionsBlock()),
            ("quick_section", QuickSectionBlock()),
            ("section_title", SectionTitleBlock()),
            ("rich_text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "ol", "ul", "link"])),
            ("image", ImageBlock()),
            ("gallery", GalleryBlock()),
            ("highlights", HighlightsBlock()),
            ("info_grid", InfoGridBlock()),
            ("map", MapEmbedBlock()),
            ("youtube", YouTubeBlock()),
            ("cta", CTAButtonBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    # ✅ CTAs manuales (override)
    cta_manual = StreamField(
        [
            ("cta", CTAButtonBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    # ✅ FAQ dinámico PRO
    faq = StreamField(
        [
            ("faq", FAQBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("hero_image"),
        FieldPanel("contenido_bruto"),  # ✅
        FieldPanel("body"),
        FieldPanel("tags"),
        MultiFieldPanel([FieldPanel("cta_manual")], heading="CTAs (Manual override)"),
        MultiFieldPanel([FieldPanel("faq")], heading="FAQ (Preguntas frecuentes)"),
    ]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel([FieldPanel("seo_description")], heading="SEO"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    parent_page_types = ["pages.PaisPage"]
    subpage_types = []

    # -------------------------
    # FAQ helpers (sin cambios)
    # -------------------------
    def get_faq_items(self):
        out = []
        faq_stream = getattr(self, "faq", None)
        if not faq_stream:
            return out

        for block in faq_stream:
            if block.block_type != "faq":
                continue

            items = block.value.get("items") or []
            for item in items:
                q = (item.get("question") or "").strip()
                a = item.get("answer")

                if not q or not a:
                    continue

                answer_html = RichText(a).source or ""
                answer_text = strip_tags(answer_html).strip()

                if answer_text:
                    out.append({"question": q, "answer_text": answer_text})

        return out

    def get_faq_jsonld(self):
        faqs = self.get_faq_items()
        if not faqs:
            return ""

        data = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f["answer_text"],
                    },
                }
                for f in faqs
            ],
        }
        return mark_safe(json.dumps(data, ensure_ascii=False))

    # -------------------------
    # Import HTML -> StreamField
    # -------------------------
    def _looks_like_youtube(self, url: str) -> bool:
        u = (url or "").lower()
        return ("youtube.com" in u) or ("youtu.be" in u)

    def _looks_like_maps(self, url: str) -> bool:
        u = (url or "").lower()
        return ("google.com/maps" in u) or ("/maps" in u)

    def _clean_html_fragment(self, html: str) -> str:
        return (html or "").strip()

    def _html_to_stream_data_quicksections(self, html: str, fill_embed_urls: bool = True):
        """
        Importa HTML:
        - Cada <h2> => 1 quick_section
        - <p> + <h3> => body (HTML) dentro de quick_section.body
        - primer <img> por sección => quick_section.image placeholder (None)
        - imgs extra => bloque image placeholder
        - iframes => bloque youtube/map (con src si fill_embed_urls=True o vacío si False)
        - contenido antes del primer <h2> => rich_text suelto
        """
        soup = BeautifulSoup(html or "", "html.parser")
        root = soup.body or soup

        stream_data = []

        current = None
        section_chunks = []
        section_has_image = False

        def flush_current_section():
            nonlocal current, section_chunks, section_has_image
            if not current:
                return

            body_html = self._clean_html_fragment("".join(section_chunks))
            current["body"] = body_html

            stream_data.append({"type": "quick_section", "value": current})

            current = None
            section_chunks = []
            section_has_image = False

        def flush_intro_as_rich_text():
            nonlocal section_chunks
            if section_chunks:
                combined = self._clean_html_fragment("".join(section_chunks))
                if combined:
                    stream_data.append({"type": "rich_text", "value": combined})
                section_chunks = []

        for node in root.descendants:
            if not getattr(node, "name", None):
                continue

            tag = node.name.lower()
            if tag in ("html", "head", "body", "div", "span"):
                continue

            if tag == "h2":
                flush_current_section()
                flush_intro_as_rich_text()

                title = node.get_text(" ", strip=True)
                if not title:
                    continue

                current = {
                    "title": title,
                    "subtitle": "",
                    "body": "",
                    "image": None,  # placeholder: elegir imagen luego
                    "caption": "",
                    "cta_text": "",
                    "cta_url": "",
                    "cta_note": "",
                }
                continue

            # Antes del primer H2 => intro
            if current is None:
                if tag == "p":
                    inner = node.decode_contents().strip()
                    if inner and node.get_text(" ", strip=True):
                        section_chunks.append(f"<p>{inner}</p>")
                elif tag == "h3":
                    text = node.get_text(" ", strip=True)
                    if text:
                        section_chunks.append(f"<h3>{text}</h3>")
                continue

            # Dentro de sección
            if tag == "p":
                inner = node.decode_contents().strip()
                if not inner or node.get_text(" ", strip=True) == "":
                    continue
                section_chunks.append(f"<p>{inner}</p>")

            elif tag == "h3":
                text = node.get_text(" ", strip=True)
                if text:
                    section_chunks.append(f"<h3>{text}</h3>")

            elif tag == "img":
                if not section_has_image:
                    current["image"] = None
                    current["caption"] = ""
                    section_has_image = True
                else:
                    stream_data.append({"type": "image", "value": {"image": None, "caption": ""}})

            elif tag == "iframe":
                src = node.get("src", "") or ""
                if self._looks_like_youtube(src):
                    stream_data.append(
                        {
                            "type": "youtube",
                            "value": {"title": "", "video": (src if fill_embed_urls else "")},
                        }
                    )
                elif self._looks_like_maps(src):
                    stream_data.append(
                        {
                            "type": "map",
                            "value": {"title": "", "map_url": (src if fill_embed_urls else "")},
                        }
                    )
                else:
                    safe = src.replace('"', "&quot;")
                    section_chunks.append(
                        f"<p>📌 Embed pendiente: <a href=\"{safe}\" target=\"_blank\" rel=\"noopener\">{safe}</a></p>"
                    )

        if current:
            flush_current_section()
        else:
            flush_intro_as_rich_text()

        return stream_data

    def save(self, *args, **kwargs):
        if self.contenido_bruto and self.contenido_bruto.strip() and (not self.body or len(self.body) == 0):
            self.body = self._html_to_stream_data_quicksections(self.contenido_bruto, fill_embed_urls=True)
            self.contenido_bruto = ""
        super().save(*args, **kwargs)

    # -------------------------
    # Context (sin cambios)
    # -------------------------
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        desired = 6

        context["breadcrumb_ancestors"] = get_filtered_breadcrumb_ancestors(self)

        related = DestinoPage.objects.none()
        if self.tags.exists():
            tag_ids = list(self.tags.all().values_list("id", flat=True))
            related = (
                DestinoPage.objects.live().public()
                .exclude(id=self.id)
                .filter(tagged_items__tag_id__in=tag_ids)
                .annotate(shared=Count("tagged_items__tag_id"))
                .order_by("-shared", "-first_published_at")
                .distinct()
            )[:desired]

        related_list = list(related)
        if len(related_list) < desired:
            siblings = self.get_siblings().live().public().exclude(id=self.id).specific()
            existing_ids = {p.id for p in related_list}
            for s in siblings:
                if s.id not in existing_ids:
                    related_list.append(s)
                    existing_ids.add(s.id)
                if len(related_list) >= desired:
                    break

        context["related_destinos"] = related_list

        if self.cta_manual and len(self.cta_manual):
            context["ctas"] = self.cta_manual
            context["ctas_source"] = "manual"
        else:
            tag_names = set(t.name.lower() for t in self.tags.all())
            ctas_auto = []

            def add_cta(title, url, button_text="Ver opciones", note=""):
                ctas_auto.append({"title": title, "url": url, "button_text": button_text, "note": note})

            if "playa" in tag_names:
                add_cta("Alojamientos cerca de la playa", "https://www.booking.com/", "Ver alojamientos", "Compará precios y disponibilidad")
                add_cta("Snorkel y paseos en barco", "https://www.getyourguide.com/", "Ver actividades", "Experiencias típicas de playa")

            if "montaña" in tag_names or "trekking" in tag_names:
                add_cta("Excursiones y trekking guiado", "https://www.getyourguide.com/", "Ver excursiones", "Opciones según dificultad y tiempo")
                add_cta("Seguro de viaje", "https://www.assistcard.com/", "Cotizar seguro", "Recomendado para actividades al aire libre")

            if "ciudad" in tag_names:
                add_cta("Tours y experiencias en la ciudad", "https://www.getyourguide.com/", "Ver tours", "Walking tours, museos y gastronomía")
                add_cta("Alojamiento bien ubicado", "https://www.booking.com/", "Buscar hotel", "Mejor ubicación = menos traslados")

            if "familia" in tag_names:
                add_cta("Alojamientos ideales para familias", "https://www.booking.com/", "Ver opciones", "Filtrá por cocina, pileta y espacio")

            if "pareja" in tag_names:
                add_cta("Experiencias para parejas", "https://www.getyourguide.com/", "Ver experiencias", "Atardeceres, paseos y actividades románticas")

            if "presupuesto" in tag_names or "barato" in tag_names:
                add_cta("Opciones económicas", "https://www.booking.com/", "Ver ofertas", "Ordená por precio y mirá reviews")

            seen = set()
            unique_ctas = []
            for cta in ctas_auto:
                key = (cta["url"], cta["button_text"])
                if key in seen:
                    continue
                seen.add(key)
                unique_ctas.append(cta)

            if not unique_ctas:
                unique_ctas = [
                    {"title": "Buscar alojamientos", "url": "https://www.booking.com/", "button_text": "Ver alojamientos", "note": "Compará opciones"},
                    {"title": "Seguro de viaje", "url": "https://www.assistcard.com/", "button_text": "Cotizar seguro", "note": ""},
                ]

            context["ctas"] = unique_ctas[:3]
            context["ctas_source"] = "auto"

        toc, body_html = build_toc_and_body_html(self.body)
        context["toc"] = toc
        context["body_html"] = body_html
        return context

    class Meta:
        verbose_name = "Destino"


# ============================================================
# ARTÍCULO / GUÍA (con TOC)
# ============================================================

from bs4 import BeautifulSoup

class ArticuloPage(Page):
    contenido_bruto = models.TextField(blank=True)

    body = StreamField(
        [
            ("section_title", SectionTitleBlock()),
            ("rich_text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "ol", "ul", "link"])),
            ("image", ImageBlock()),
            ("gallery", GalleryBlock()),
            ("highlights", HighlightsBlock()),
            ("youtube", YouTubeBlock()),
            ("cta", CTAButtonBlock()),
            ("quick_sections", QuickSectionsBlock()),
            ("quick_section", QuickSectionBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("contenido_bruto"),
        FieldPanel("body"),
    ]

    def _html_to_stream_data(self, html: str):
        soup = BeautifulSoup(html or "", "html.parser")
        root = soup.body or soup

        stream_data = []
        pending_paragraphs = []

        def flush_paragraphs():
            nonlocal pending_paragraphs
            if pending_paragraphs:
                combined = "".join(pending_paragraphs).strip()
                if combined:
                    stream_data.append({"type": "rich_text", "value": combined})
                pending_paragraphs = []

        def looks_like_youtube(url: str) -> bool:
            u = (url or "").lower()
            return ("youtube.com" in u) or ("youtu.be" in u)

        # Recorremos tags “principales” en orden
        for node in root.descendants:
            if not getattr(node, "name", None):
                continue

            tag = node.name.lower()

            # ignorar wrappers típicos
            if tag in ("html", "head", "body", "div", "span"):
                continue

            if tag == "h2":
                flush_paragraphs()
                title = node.get_text(" ", strip=True)
                if title:
                    stream_data.append({
                        "type": "section_title",
                        "value": {"title": title, "subtitle": ""}
                    })

            elif tag == "p":
                inner_html = node.decode_contents().strip()
                text = node.get_text(" ", strip=True)

                # evitar <p><br></p> y vacíos
                if not inner_html or text == "":
                    continue

                pending_paragraphs.append(f"<p>{inner_html}</p>")

            elif tag == "img":
                flush_paragraphs()

                # Placeholder vacío: vos elegís la imagen luego
                # (Opcional: guardar src original en caption)
                # src = node.get("src", "")
                # caption = f"Fuente original: {src}" if src else ""
                caption = ""

                stream_data.append({
                    "type": "image",
                    "value": {"image": None, "caption": caption}
                })

            elif tag == "iframe":
                flush_paragraphs()
                src = node.get("src", "")

                if looks_like_youtube(src):
                    # Placeholder vacío: vos pegás URL luego
                    stream_data.append({
                        "type": "youtube",
                        "value": {"title": "", "video": ""}  # requiere video required=False
                    })
                else:
                    # No tenés bloque map/embed en body: lo dejamos como nota en rich_text
                    note = "📌 Aquí iba un iframe (maps u otro embed). Pegá la URL manualmente: "
                    safe_src = src.replace('"', "&quot;")
                    stream_data.append({
                        "type": "rich_text",
                        "value": f"<p>{note}<a href=\"{safe_src}\" target=\"_blank\" rel=\"noopener\">{safe_src}</a></p>"
                    })

        flush_paragraphs()
        return stream_data

    def save(self, *args, **kwargs):
        if self.contenido_bruto and self.contenido_bruto.strip():
            self.body = self._html_to_stream_data(self.contenido_bruto)

            # para no reimportar cada vez
            self.contenido_bruto = ""

        super().save(*args, **kwargs)

class ArticuloDestinoRelation(Orderable):
    articulo = ParentalKey(
        "pages.ArticuloPage",
        on_delete=models.CASCADE,
        related_name="destinos_relacionados",
    )
    destino = models.ForeignKey(
        "pages.DestinoPage",
        on_delete=models.CASCADE,
        related_name="articulos_relacionados",
    )

    panels = [
        PageChooserPanel("destino", "pages.DestinoPage"),
    ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["articulo", "destino"],
                name="unique_articulo_destino_relation_v4",
            )
        ]
