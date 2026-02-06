from django.contrib import admin
from .models import Categoria, Articulo


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug")
    search_fields = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "publicado", "created_at", "updated_at")
    list_filter = ("publicado", "categoria")
    search_fields = ("titulo", "extracto", "contenido")
    prepopulated_fields = {"slug": ("titulo",)}
    filter_horizontal = ("destinos", "relacionados_manual")
