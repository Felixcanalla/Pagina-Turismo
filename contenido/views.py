from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from .models import Categoria, Articulo

GUIAS_PER_PAGE = 12


def guias_index(request):
    categorias = Categoria.objects.all()
    return render(request, "contenido/index.html", {"categorias": categorias})


def categoria_list(request, categoria_slug):
    categoria = get_object_or_404(Categoria, slug=categoria_slug)

    qs = categoria.articulos.filter(publicado=True).select_related("categoria").order_by("-created_at")
    paginator = Paginator(qs, GUIAS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    canonical_url = request.build_absolute_uri(request.path)


    return render(
        request,
        "contenido/categoria_list.html",
        {"categoria": categoria, "page_obj": page_obj, "paginator": paginator,"canonical_url": canonical_url,},


    )


def articulo_detail(request, categoria_slug, articulo_slug):
    categoria = get_object_or_404(Categoria, slug=categoria_slug)
    articulo = get_object_or_404(
        Articulo,
        categoria=categoria,
        slug=articulo_slug,
        publicado=True
    )

    # ✅ Destinos relacionados (para mostrar “Relacionado con:”)
    destinos = (
        articulo.destinos
        .filter(publicado=True)
        .select_related("pais")
        .order_by("pais__nombre", "nombre")
    )

    # 1) Relacionados manuales (si existen)
    manuales = (
        articulo.relacionados_manual
        .filter(publicado=True)
        .select_related("categoria")
        .distinct()
    )

    if manuales.exists():
        relacionados = manuales[:6]
    else:
        base = (
            Articulo.objects
            .filter(publicado=True)
            .exclude(id=articulo.id)
            .select_related("categoria")
        )

        # 2) Automático: misma categoría + (si aplica) mismos destinos
        filtros = Q(categoria=articulo.categoria)

        destinos_ids = list(destinos.values_list("id", flat=True))
        if destinos_ids:
            filtros |= Q(destinos__in=destinos_ids)

        relacionados = (
            base.filter(filtros)
            .distinct()
            .order_by("-created_at")[:6]
        )

    return render(
        request,
        "contenido/articulo_detail.html",
        {
            "categoria": categoria,
            "articulo": articulo,
            "destinos": destinos,         # ✅ NECESARIO para tu template
            "relacionados": relacionados,
        },
    )
