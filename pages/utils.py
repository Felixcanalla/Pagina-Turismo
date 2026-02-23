# pages/utils.py
from django.utils.text import slugify
from wagtail.rich_text import RichText

def get_filtered_breadcrumb_ancestors(page):
    """
    Devuelve ancestors para breadcrumbs filtrando páginas no deseadas.
    Ajustá filtros según tu sitio.
    """
    # incluye root/home si querés; acá filtramos por títulos típicos
    excluded_titles = {"welcome", "home"}
    ancestors = page.get_ancestors().live().public()
    return [p for p in ancestors if (p.title or "").strip().lower() not in excluded_titles]

def build_toc_and_body_html(stream_value):
    """
    Construye:
    - toc: lista de items para menú/tabla de contenido
    - body_html: string HTML renderizado desde StreamField

    Nota: tu proyecto ya renderiza bloques con templates; esto es un fallback sencillo.
    Si ya tenías una versión más avanzada, reemplazala acá.
    """
    toc = []
    parts = []

    if not stream_value:
        return toc, ""

    for block in stream_value:
        btype = block.block_type
        val = block.value

        if btype == "section_title":
            title = (val.get("title") if isinstance(val, dict) else "") or ""
            title = title.strip()
            if title:
                anchor = slugify(title)
                toc.append({"title": title, "anchor": anchor})
                parts.append(f'<h2 id="{anchor}">{title}</h2>')

        elif btype == "rich_text":
            # RichTextBlock ya viene como HTML (string)
            html = str(val) if val else ""
            parts.append(html)

        elif btype == "quick_section":
            # Render mínimo: H2 + body (el template real lo renderiza mejor)
            title = (val.get("title") or "").strip()
            subtitle = (val.get("subtitle") or "").strip()
            body = val.get("body") or ""
            if title:
                anchor = slugify(title)
                toc.append({"title": title, "anchor": anchor})
                parts.append(f'<h2 id="{anchor}">{title}</h2>')
            if subtitle:
                parts.append(f"<p><em>{subtitle}</em></p>")
            if body:
                parts.append(str(RichText(body)))

        else:
            # Para otros bloques (image, map, youtube, etc.) no inventamos HTML acá,
            # porque normalmente se renderizan por template en el page template.
            # Los dejamos fuera de este fallback.
            pass

    return toc, "".join(parts)