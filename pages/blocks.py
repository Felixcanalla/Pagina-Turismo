from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class SectionTitleBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, max_length=80)
    subtitle = blocks.CharBlock(required=False, max_length=140)

    class Meta:
        icon = "title"
        template = "blocks/section_title.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False, max_length=180)

    class Meta:
        icon = "image"
        template = "blocks/image.html"


class GalleryBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=80)
    images = blocks.ListBlock(ImageChooserBlock(), min_num=1)

    class Meta:
        icon = "image"
        template = "blocks/gallery.html"


class HighlightsBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=80)
    items = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("title", blocks.CharBlock(required=True, max_length=60)),
                ("text", blocks.CharBlock(required=False, max_length=160)),
            ]
        ),
        min_num=1,
    )

    class Meta:
        icon = "list-ul"
        template = "blocks/highlights.html"


class InfoGridBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=80)
    rows = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("label", blocks.CharBlock(required=True, max_length=40)),
                ("value", blocks.CharBlock(required=True, max_length=80)),
            ]
        ),
        min_num=1,
    )

    class Meta:
        icon = "table"
        template = "blocks/info_grid.html"


class MapEmbedBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=80)
    map_url = blocks.URLBlock(required=True, help_text="Pegá la URL /maps/embed?... (NO el iframe completo)")

    class Meta:
        icon = "site"
        template = "blocks/map_embed.html"


class CTAButtonBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True, max_length=40)
    url = blocks.URLBlock(required=True)
    note = blocks.CharBlock(required=False, max_length=120)

    class Meta:
        icon = "link"
        template = "blocks/cta_button.html"


class YouTubeBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=80)
    video = EmbedBlock(required=True, help_text="Pegá el link de YouTube (o cualquier embed compatible)")

    class Meta:
        icon = "media"
        template = "blocks/youtube.html"


# ✅ FAQ PRO (1 bloque con lista de preguntas)
class FAQItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(required=True, label="Pregunta", max_length=180)
    answer = blocks.RichTextBlock(
        required=True,
        label="Respuesta",
        features=["bold", "italic", "link", "ul", "ol"],
    )

    class Meta:
        icon = "help"
        label = "Pregunta frecuente"


class FAQBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, label="Título (opcional)", default="Preguntas frecuentes")
    items = blocks.ListBlock(FAQItemBlock(), label="Preguntas", min_num=1)

    class Meta:
        icon = "help"
        label = "FAQ"
