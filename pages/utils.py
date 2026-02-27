# pages/utils.py
import re
import unicodedata
from typing import Dict, List, Tuple

from django.utils.html import strip_tags
from django.utils.text import slugify
from wagtail.models import Page


def _unique_anchor(title: str, used: dict) -> str:
    title = (title or "").strip()
    norm = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    base = slugify(norm) or "seccion"
    used[base] = used.get(base, 0) + 1
    return base if used[base] == 1 else f"{base}-{used[base]}"


def get_filtered_breadcrumb_ancestors(page: Page):
    ancestors = []
    for p in page.get_ancestors().live().public():
        p = p.specific
        if getattr(p, "url", None) == "/":
            continue  # evita duplicar "Inicio"
        ancestors.append(p)
    return ancestors


def build_toc_and_body_html(stream_value):
    toc = []
    parts = []
    used = {}

    if not stream_value:
        return toc, ""

    for block in stream_value:
        btype = block.block_type
        val = block.value

        if btype == "section_title":
            title = (val.get("title") if isinstance(val, dict) else "") or ""
            title = title.strip()
            if title:
                anchor = _unique_anchor(title, used)
                toc.append({"title": title, "anchor": anchor})
                parts.append(f'<h2 id="{anchor}">{title}</h2>')

        elif btype == "rich_text":
            html = str(val) if val else ""

            # Si hay <h2> dentro del rich_text, les inyecta id y los suma al TOC
            if html:
                def repl(match):
                    inner = match.group(1)
                    title = strip_tags(inner).strip()
                    if not title:
                        return match.group(0)
                    anchor = _unique_anchor(title, used)
                    toc.append({"title": title, "anchor": anchor})
                    return f'<h2 id="{anchor}">{inner}</h2>'

                html = re.sub(r"<h2[^>]*>(.*?)</h2>", repl, html, flags=re.IGNORECASE | re.DOTALL)
                parts.append(html)

        elif btype == "quick_section":
            title = (val.get("title") or "").strip()
            subtitle = (val.get("subtitle") or "").strip()
            body = val.get("body") or ""

            if title:
                anchor = _unique_anchor(title, used)
                toc.append({"title": title, "anchor": anchor})
                parts.append(f'<h2 id="{anchor}">{title}</h2>')
            if subtitle:
                parts.append(f"<p><em>{subtitle}</em></p>")
            if body:
                # body YA es HTML que vos armaste en la conversión
                parts.append(str(body))

        # otros bloques: se renderizan por template si no usás body_html

    return toc, "".join(parts)