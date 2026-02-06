import random
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings

from PIL import Image, ImageDraw, ImageFont

from contenido.models import Categoria, Articulo
from destinos.models import Destino


def _rand_color():
    return tuple(random.randint(30, 220) for _ in range(3))


def _make_image_bytes(width: int, height: int, title: str) -> bytes:
    """
    Genera una imagen simple con fondo de color + texto.
    No depende de fuentes externas.
    """
    img = Image.new("RGB", (width, height), _rand_color())
    draw = ImageDraw.Draw(img)

    # Texto (fallback seguro sin fuentes)
    text = title[:60]
    # Rectángulo oscuro semitransparente simulado (sobre RGB no hay alpha, usamos color oscuro)
    pad = 24
    box_h = 110
    draw.rectangle([(0, height - box_h), (width, height)], fill=(0, 0, 0))

    # Texto en blanco
    # Usamos fuente por defecto (Pillow)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((pad, height - box_h + 20), text, fill=(255, 255, 255), font=font)

    out = BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def _save_inline_image(path: str, title: str) -> str:
    """
    Guarda imagen inline en MEDIA y devuelve la URL para embebido en HTML.
    """
    data = _make_image_bytes(1200, 800, title)
    saved_path = default_storage.save(path, ContentFile(data))
    return f"{settings.MEDIA_URL}{saved_path}"


class Command(BaseCommand):
    help = "Crea contenido demo (categorías + artículos con imágenes) para ver el layout."

    def add_arguments(self, parser):
        parser.add_argument("--categories", type=int, default=4)
        parser.add_argument("--articles", type=int, default=12)
        parser.add_argument("--clear", action="store_true", help="Borra artículos/categorías existentes antes de crear demo.")

    def handle(self, *args, **options):
        n_categories = options["categories"]
        n_articles = options["articles"]
        clear = options["clear"]

        if clear:
            Articulo.objects.all().delete()
            Categoria.objects.all().delete()
            self.stdout.write(self.style.WARNING("Borrado: Articulo y Categoria (demo)."))

        # Categorías demo (si no existen)
        base_cats = ["Vuelos", "Alojamiento", "Itinerarios", "Consejos"]
        random.shuffle(base_cats)
        base_cats = base_cats[:max(1, n_categories)]

        categorias = []
        for name in base_cats:
            cat, _ = Categoria.objects.get_or_create(nombre=name)
            categorias.append(cat)

        # Generación de artículos
        titles = [
            "Cómo encontrar vuelos baratos desde Argentina",
            "Qué llevar en la valija según la época",
            "Cómo elegir barrio para alojarte (sin gastar de más)",
            "Itinerario de 3 días: ciudad, naturaleza y comida",
            "Errores comunes al comprar pasajes (y cómo evitarlos)",
            "Apps útiles para moverte y ahorrar en viaje",
            "Cómo armar un presupuesto realista de viaje",
            "Cómo viajar ligero: guía práctica",
            "Consejos para viajar en temporada alta",
            "Cómo elegir seguro de viaje sin pagar de más",
            "Cómo planificar un viaje por primera vez",
            "Checklist final antes de salir"
        ]

        # Si piden más artículos que títulos, generamos variaciones
        while len(titles) < n_articles:
            titles.append(f"Guía práctica #{len(titles)+1}: planificá mejor tu viaje")

        created = 0
        for i in range(n_articles):
            titulo = titles[i]
            categoria = random.choice(categorias)

            # Evitar colisiones de slug
            base_slug = slugify(titulo)
            slug = base_slug
            suffix = 2
            while Articulo.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            extracto = "Guía breve y accionable en español, pensada para viajeros de Argentina y LATAM."

            # 1) Imagen principal (hero)
            hero_bytes = _make_image_bytes(1400, 900, titulo)

            articulo = Articulo(
                categoria=categoria,
                titulo=titulo,
                slug=slug,
                extracto=extracto,
                contenido="(se completa luego)",  # lo seteamos después para incluir URLs inline
                publicado=True,
            )
            articulo.imagen.save(f"{slug}.jpg", ContentFile(hero_bytes), save=False)
            articulo.save()

            # Asociar 0-2 destinos al artículo (si ya existen destinos demo)
            destinos_disponibles = list(Destino.objects.all()[:30])
            if destinos_disponibles:
                k = random.choice([0, 0, 1, 1, 2])
                if k:
                    articulo.destinos.set(random.sample(destinos_disponibles, k=min(k, len(destinos_disponibles))))

            # 2) Imágenes dentro del contenido (2 inline)
            inline1_url = _save_inline_image(f"articulos/inline/{slug}-1.jpg", f"Foto inline 1 · {titulo}")
            inline2_url = _save_inline_image(f"articulos/inline/{slug}-2.jpg", f"Foto inline 2 · {titulo}")

            # 3) Contenido HTML (para que quede “blog real”)
            contenido_html = f"""
<h2>Resumen rápido</h2>
<p>Si querés mejorar precios y evitar errores típicos, esta guía te deja un método simple y repetible.</p>

<img src="{inline1_url}" alt="Imagen ilustrativa 1" style="width:100%;height:auto;border-radius:12px;border:1px solid #e5e7eb;margin:12px 0;">

<h2>Paso a paso</h2>
<ul>
  <li>Definí fechas flexibles (aunque sea ±2 días).</li>
  <li>Buscá primero “panorama” y recién después concretá.</li>
  <li>Guardá alertas y repetí la búsqueda en horarios distintos.</li>
</ul>

<h2>Tips prácticos</h2>
<p>Un pequeño cambio de día u horario puede mover bastante el precio. Anotá resultados y compará con calma.</p>

<img src="{inline2_url}" alt="Imagen ilustrativa 2" style="width:100%;height:auto;border-radius:12px;border:1px solid #e5e7eb;margin:12px 0;">

<h2>Cierre</h2>
<p>Si querés, después armamos una sección fija de “recursos recomendados” al final (lista perfecta para afiliados).</p>
""".strip()

            articulo.contenido = contenido_html
            articulo.save(update_fields=["contenido"])

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Listo: {created} artículos demo creados en {len(categorias)} categorías."))
        self.stdout.write("Tip: asegurate de renderizar contenido con |safe si querés que las <img> se vean dentro del artículo.")
