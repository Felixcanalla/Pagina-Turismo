from django.apps import apps
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from modelcluster.fields import ParentalKey
from modelcluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from modelcluster.fields import ParentalManyToManyField 
from wagtail.search import index
from .blocks import FAQBlock
from django.utils.html import strip_tags
import json

from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from wagtail.rich_text import RichText



from .blocks import (
    CTAButtonBlock,
    GalleryBlock,
    HighlightsBlock,
    ImageBlock,
    InfoGridBlock,
    MapEmbedBlock,
    SectionTitleBlock,
    YouTubeBlock,
)


# =========================
# HOME (Wagtail como sitio principal)
# =========================

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


# =========================
# GUÍAS
# =========================

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
        context["articulos"] = (
            ArticuloPage.objects.live().public()
            .child_of(self)
            .order_by("-first_published_at")
        )
        return context

    class Meta:
        verbose_name = "Categoría"


# =========================
# DESTINOS
# =========================

class DestinosIndexPage(Page):
    """Índice editorial de Destinos. Vive debajo de HomePage."""
    seo_description = models.CharField(max_length=160, blank=True)

    parent_page_types = ["pages.HomePage"]
    subpage_types = ["pages.PaisPage"]
    template = "pages/destinos_index_page.html"

    def get_context(self, request):
        context = super().get_context(request)
        context["paises"] = (
            PaisPage.objects.live().public()
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
        context["destinos"] = (
            DestinoPage.objects.live().public()
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

    tags = ClusterTaggableManager(through=DestinoPageTag, blank=True)

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    body = StreamField(
        [
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

    # ✅ FAQ dinámico PRO (bloque con lista de preguntas)
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
        """
        Devuelve string JSON-LD (FAQPage) o "" si no hay FAQs.
        """
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
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        desired = 6

        # ✅ Breadcrumbs filtrados (sin Welcome/Home)
        context["breadcrumb_ancestors"] = [
            a.specific for a in self.get_ancestors().live().public()
            if a.depth >= 4
        ]

        # ✅ Relacionados por tags
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

        # ✅ Fallback: mismo país (hermanos)
        related_list = list(related)
        if len(related_list) < desired:
            siblings = (
                self.get_siblings()
                .live()
                .public()
                .exclude(id=self.id)
                .specific()
            )
            existing_ids = {p.id for p in related_list}
            for s in siblings:
                if s.id not in existing_ids:
                    related_list.append(s)
                    existing_ids.add(s.id)
                if len(related_list) >= desired:
                    break

        context["related_destinos"] = related_list

        # ✅ CTAs: manual override > automático por tags
        if self.cta_manual and len(self.cta_manual):
            context["ctas"] = self.cta_manual
            context["ctas_source"] = "manual"
            return context

        tag_names = set(t.name.lower() for t in self.tags.all())
        ctas_auto = []

        def add_cta(title, url, button_text="Ver opciones", note=""):
            ctas_auto.append({
                "title": title,
                "url": url,
                "button_text": button_text,
                "note": note,
            })

        # Reglas combinables
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

        # Dedup
        seen = set()
        unique_ctas = []
        for cta in ctas_auto:
            key = (cta["url"], cta["button_text"])
            if key in seen:
                continue
            seen.add(key)
            unique_ctas.append(cta)

        # Fallback general
        if not unique_ctas:
            unique_ctas = [
                {"title": "Buscar alojamientos", "url": "https://www.booking.com/", "button_text": "Ver alojamientos", "note": "Compará opciones"},
                {"title": "Seguro de viaje", "url": "https://www.assistcard.com/", "button_text": "Cotizar seguro", "note": ""},
            ]

        context["ctas"] = unique_ctas[:3]
        context["ctas_source"] = "auto"
        return context

    class Meta:
        verbose_name = "Destino"


# =========================
# ARTÍCULO / GUÍA (con TOC)
# =========================

class ArticuloPage(Page):
    template = "pages/articulo_page.html"
    seo_description = models.CharField(max_length=160, blank=True)

    intro = models.CharField(max_length=250, blank=True)

    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    destinos = ParentalManyToManyField(
        "pages.DestinoPage",
        blank=True,
        related_name="guias",
    )

    body = StreamField(
        [
            ("section_title", SectionTitleBlock()),
            ("rich_text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "ol", "ul", "link"])),
            ("image", ImageBlock()),
            ("gallery", GalleryBlock()),
            ("highlights", HighlightsBlock()),
            ("youtube", YouTubeBlock()),
            ("cta", CTAButtonBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("cover_image"),
        FieldPanel("body"),
        FieldPanel("destinos"),
    ]

    promote_panels = Page.promote_panels + [
        MultiFieldPanel([FieldPanel("seo_description")], heading="SEO"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    parent_page_types = ["pages.CategoriaPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Artículo"

    # --- TOC (Tabla de contenidos) basado en bloques section_title ---
    def _build_toc_and_body_html(self):
        used = {}
        toc = []
        parts = []

        for block in self.body:
            if block.block_type == "section_title":
                title = (block.value.get("title") or "").strip()
                if not title:
                    continue

                base = slugify(title) or "seccion"
                used[base] = used.get(base, 0) + 1
                anchor = base if used[base] == 1 else f"{base}-{used[base]}"

                toc.append({"title": title, "anchor": anchor, "level": 2})

                subtitle = (block.value.get("subtitle") or "").strip()
                if subtitle:
                    parts.append(format_html(
                        '<section class="block block-title"><h2 id="{}">{}</h2><p class="muted">{}</p></section>',
                        anchor, title, subtitle
                    ))
                else:
                    parts.append(format_html(
                        '<section class="block block-title"><h2 id="{}">{}</h2></section>',
                        anchor, title
                    ))
            else:
                parts.append(mark_safe(block.render()))

        return toc, mark_safe("".join(parts))

    def get_context(self, request):
        context = super().get_context(request)

        toc, body_html = self._build_toc_and_body_html()
        context["toc"] = toc
        context["body_html"] = body_html

        context["breadcrumb_ancestors"] = [
            a.specific for a in self.get_ancestors().live().public()
            if a.depth >= 4
        ]
        return context
