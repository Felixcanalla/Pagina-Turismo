from django.db import models
from django.utils.text import slugify

from django.db import models
from django.utils.text import slugify

class Pais(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="paises/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Destino(models.Model):
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, related_name="destinos")
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    resumen = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="destinos/", blank=True, null=True)
    contenido = models.TextField(blank=True)  # luego podés migrar a RichText/Markdown
    publicado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("pais", "slug")]
        ordering = ["pais__nombre", "nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.pais.nombre})"


class SeccionDestino(models.Model):
    """
    Para subpáginas tipo:
    /destinos/argentina/bariloche/donde-dormir/
    /destinos/argentina/bariloche/que-hacer/
    """
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name="secciones")
    titulo = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, blank=True)
    contenido = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    publicado = models.BooleanField(default=True)

    class Meta:
        unique_together = [("destino", "slug")]
        ordering = ["orden", "titulo"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.destino} - {self.titulo}"
