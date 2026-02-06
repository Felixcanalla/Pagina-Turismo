from django.db import models
from django.apps import apps
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField, RichTextField
from wagtail.models import Page
from wagtail.search import index
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

from .blocks import (
    SectionTitleBlock,
    ImageBlock,
    GalleryBlock,
    HighlightsBlock,
    InfoGridBlock,
    MapEmbedBlock,
    CTAButtonBlock,
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

        destinos_qs = DestinoPage.objects.live().public().order_by("-first_published_at")
        if hasattr(DestinoPage, "destacado"):
            destinos_qs = destinos_qs.filter(destacado=True).order_by("-first_published_at")
        context["destinos"] = destinos_qs[:6]

        articulos_qs = ArticuloPage.objects.live().public().order_by("-first_published_at")
        if hasattr(ArticuloPage, "destacado"):
            articulos_qs = articulos_qs.filter(destacado=True).order_by("-first_published_at")
        context["articulos"] = articulos_qs[:6]

        return context

    class Meta:
        verbose_name = "Home"


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
        MultiFieldPanel(
        [FieldPanel("seo_description")],
        heading="SEO",
    ),
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
            # Articulo vive debajo de Categoria, así que filtramos por parent slug
            qs = qs.filter(path__startswith=self.path).filter(depth__gte=self.depth + 2).filter(
                url_path__contains=f"/{cat_slug}/"
            )

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
    MultiFieldPanel(
        [FieldPanel("seo_description")],
        heading="SEO",
    ),
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

    content_panels = Page.content_panels + [
        FieldPanel("descripcion_corta"),
        FieldPanel("intro"),
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


class DestinoPage(Page):
    template = "pages/destino_page.html"
    seo_description = models.CharField(max_length=160, blank=True)

    intro = models.CharField(max_length=250, blank=True)
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

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("hero_image"),
        FieldPanel("body"),
    ]

    promote_panels = Page.promote_panels + [
    MultiFieldPanel(
        [FieldPanel("seo_description")],
        heading="SEO",
    ),
]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    parent_page_types = ["pages.PaisPage"]
    subpage_types = []

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
    ]

    promote_panels = Page.promote_panels + [
    MultiFieldPanel(
        [FieldPanel("seo_description")],
        heading="SEO",
    ),
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

                # Render de heading con id fijo (para anclas)
                subtitle = (block.value.get("subtitle") or "").strip()
                if subtitle:
                    parts.append(format_html('<section class="block block-title"><h2 id="{}">{}</h2><p class="muted">{}</p></section>', anchor, title, subtitle))
                else:
                    parts.append(format_html('<section class="block block-title"><h2 id="{}">{}</h2></section>', anchor, title))
            else:
                parts.append(mark_safe(block.render()))

        return toc, mark_safe("".join(parts))

    def get_context(self, request):
        context = super().get_context(request)
        toc, body_html = self._build_toc_and_body_html()
        context["toc"] = toc
        context["body_html"] = body_html
        return context
