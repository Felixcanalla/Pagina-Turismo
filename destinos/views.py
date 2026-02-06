from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from .models import Pais, Destino, SeccionDestino

PAISES_PER_PAGE = 24
DESTINOS_PER_PAGE = 12


def destinos_index(request):
    # (opcional) solo países con al menos 1 destino publicado:
    # qs = Pais.objects.filter(destinos__publicado=True).distinct()
    qs = Pais.objects.all()

    paginator = Paginator(qs, PAISES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "destinos/index.html", {
        "page_obj": page_obj,
        "paginator": paginator,
        "canonical_url": request.build_absolute_uri(request.path),
    })


def pais_detail(request, pais_slug):
    pais = get_object_or_404(Pais, slug=pais_slug)

    qs = (
        pais.destinos
        .filter(publicado=True)
        .select_related("pais")
        .order_by("nombre")
    )
    paginator = Paginator(qs, DESTINOS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "destinos/pais_detail.html", {
        "pais": pais,
        "page_obj": page_obj,
        "paginator": paginator,
        "canonical_url": request.build_absolute_uri(request.path),
    })


def destino_detail(request, pais_slug, destino_slug):
    pais = get_object_or_404(Pais, slug=pais_slug)
    destino = get_object_or_404(Destino, pais=pais, slug=destino_slug, publicado=True)

    secciones = (
        destino.secciones
        .filter(publicado=True)
        .order_by("orden", "titulo")
    )

    articulos_relacionados = (
        destino.articulos
        .filter(publicado=True)
        .select_related("categoria")
        .distinct()[:6]
    )

    return render(request, "destinos/destino_detail.html", {
        "pais": pais,
        "destino": destino,
        "secciones": secciones,
        "articulos_relacionados": articulos_relacionados,
        "canonical_url": request.build_absolute_uri(request.path),
    })


def seccion_destino_detail(request, pais_slug, destino_slug, seccion_slug):
    pais = get_object_or_404(Pais, slug=pais_slug)
    destino = get_object_or_404(Destino, pais=pais, slug=destino_slug, publicado=True)
    seccion = get_object_or_404(SeccionDestino, destino=destino, slug=seccion_slug, publicado=True)

    otras_secciones = (
        destino.secciones
        .filter(publicado=True)
        .exclude(id=seccion.id)
        .order_by("orden", "titulo")[:6]
    )

    articulos_relacionados = (
        destino.articulos
        .filter(publicado=True)
        .select_related("categoria")
        .distinct()[:6]
    )

    return render(request, "destinos/seccion_detail.html", {
        "pais": pais,
        "destino": destino,
        "seccion": seccion,
        "otras_secciones": otras_secciones,
        "articulos_relacionados": articulos_relacionados,
        "canonical_url": request.build_absolute_uri(request.path),
    })
