from django.db import models
from django.utils.text import slugify


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Articulo(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="articulos")

    # Relación editorial (guías ↔ destinos)
    destinos = models.ManyToManyField(
        "destinos.Destino",
        blank=True,
        related_name="articulos",
        help_text="Destinos a los que aplica esta guía (puede ser más de uno).",
    )

    # Curación editorial (si está vacío, se usan relacionados automáticos)
    relacionados_manual = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="relacionado_por",
        help_text="Artículos recomendados manualmente (prioridad sobre los automáticos).",
    )

    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    extracto = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="articulos/", blank=True, null=True)
    contenido = models.TextField()
    publicado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
