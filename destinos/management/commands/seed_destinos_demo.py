import random
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from PIL import Image, ImageDraw, ImageFont

from destinos.models import Pais, Destino, SeccionDestino


def _rand_color():
    return tuple(random.randint(30, 220) for _ in range(3))


def _make_image_bytes(width: int, height: int, title: str) -> bytes:
    img = Image.new("RGB", (width, height), _rand_color())
    draw = ImageDraw.Draw(img)

    box_h = 120
    draw.rectangle([(0, height - box_h), (width, height)], fill=(0, 0, 0))

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((24, height - box_h + 24), title[:70], fill=(255, 255, 255), font=font)

    out = BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def _save_inline_image(path: str, title: str) -> str:
    data = _make_image_bytes(1200, 800, title)
    saved_path = default_storage.save(path, ContentFile(data))
    return f"{settings.MEDIA_URL}{saved_path}"


class Command(BaseCommand):
    help = "Crea países, destinos y secciones demo con imágenes para ver el sitio con contenido."

    def add_arguments(self, parser):
        parser.add_argument("--countries", type=int, default=2)
        parser.add_argument("--destinos", type=int, default=8)
        parser.add_argument("--secciones", type=int, default=4)
        parser.add_argument("--clear", action="store_true", help="Borra países/destinos/secciones antes de crear demo.")

    def handle(self, *args, **options):
        n_countries = options["countries"]
        n_destinos = options["destinos"]
        n_secciones = options["secciones"]
        clear = options["clear"]

        if clear:
            SeccionDestino.objects.all().delete()
            Destino.objects.all().delete()
            Pais.objects.all().delete()
            self.stdout.write(self.style.WARNING("Borrado: Pais/Destino/SeccionDestino (demo)."))

        base_paises = ["Argentina", "Chile", "Uruguay", "Brasil", "Perú", "Colombia"]
        random.shuffle(base_paises)
        base_paises = base_paises[:max(1, n_countries)]

        paises = []
        for nombre in base_paises:
            slug = slugify(nombre)
            pais, _ = Pais.objects.get_or_create(nombre=nombre, defaults={"slug": slug})
            if not pais.slug:
                pais.slug = slug
                pais.save(update_fields=["slug"])
            paises.append(pais)

        base_destinos = [
            "Bariloche", "Mendoza", "Salta", "Ushuaia", "Cataratas del Iguazú",
            "Buenos Aires", "El Calafate", "Córdoba",
            "Santiago", "Valparaíso", "Montevideo", "Punta del Este",
            "Río de Janeiro", "Florianópolis", "Cusco", "Lima"
        ]
        random.shuffle(base_destinos)
        base_destinos = base_destinos[:max(1, n_destinos)]

        secciones_base = [
            ("Qué hacer", "Actividades y planes para aprovechar el destino sin correr."),
            ("Dónde dormir", "Zonas recomendadas, pros y contras y tips para reservar."),
            ("Cómo moverse", "Transporte, traslados y qué conviene según tu plan."),
            ("Mejor época", "Clima, temporadas y cómo elegir fechas para ahorrar."),
            ("Presupuesto", "Costos estimados y cómo recortar sin perder experiencia."),
        ]

        created_destinos = 0
        created_secciones = 0

        for nombre_destino in base_destinos:
            pais = random.choice(paises)

            base_slug = slugify(nombre_destino)
            slug = base_slug
            suffix = 2
            while Destino.objects.filter(pais=pais, slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1

            resumen = f"Guía de {nombre_destino}: consejos, itinerarios y secciones prácticas para planificar mejor."
            hero_bytes = _make_image_bytes(1400, 900, f"{nombre_destino} · {pais.nombre}")

            destino = Destino(
                pais=pais,
                nombre=nombre_destino,
                slug=slug,
                resumen=resumen,
                contenido=(
                    f"<p>Guía base de <strong>{nombre_destino}</strong>. "
                    "Acá vas a encontrar secciones con info práctica para armar tu viaje.</p>"
                ),
                publicado=True,
            )
            destino.imagen.save(f"{pais.slug}-{slug}.jpg", ContentFile(hero_bytes), save=False)
            destino.save()
            created_destinos += 1

            picks = secciones_base[:]
            random.shuffle(picks)
            picks = picks[:max(1, n_secciones)]

            for idx, (titulo, bajada) in enumerate(picks, start=1):
                base_sec_slug = slugify(titulo)
                sec_slug = base_sec_slug
                ssuf = 2
                while SeccionDestino.objects.filter(destino=destino, slug=sec_slug).exists():
                    sec_slug = f"{base_sec_slug}-{ssuf}"
                    ssuf += 1

                inline_url = _save_inline_image(
                    f"destinos/inline/{pais.slug}-{destino.slug}-{sec_slug}.jpg",
                    f"{titulo} · {nombre_destino}"
                )

                contenido = f"""
<p><strong>{bajada}</strong></p>
<p>Este contenido es demo para ver layout con texto + imagen dentro de la sección.</p>

<img src="{inline_url}" alt="{titulo} en {nombre_destino}"
     style="width:100%;height:auto;border-radius:12px;border:1px solid #e5e7eb;margin:12px 0;">

<ul>
  <li>Tip 1: elegí un plan simple por bloques (mañana/tarde/noche).</li>
  <li>Tip 2: evitá traslados innecesarios.</li>
  <li>Tip 3: guardá puntos clave en Maps.</li>
</ul>
""".strip()

                SeccionDestino.objects.create(
                    destino=destino,
                    titulo=titulo,
                    slug=sec_slug,
                    contenido=contenido,
                    orden=idx,
                    publicado=True,
                )
                created_secciones += 1

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {created_destinos} destinos en {len(paises)} países y {created_secciones} secciones creadas."
        ))
        self.stdout.write("Nota: para ver <img> dentro del contenido, renderizá seccion.contenido con |safe.")
