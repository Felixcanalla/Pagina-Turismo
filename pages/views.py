from django.shortcuts import render
from pages.models import ArticuloPage, DestinoPage


def search(request):
    q = (request.GET.get("q") or "").strip()

    articulos = ArticuloPage.objects.none()
    destinos = DestinoPage.objects.none()
    results = []

    if q:
        destinos = DestinoPage.objects.live().public().search(q)
        articulos = ArticuloPage.objects.live().public().search(q)

        # Primero destinos, después guías (o invertí si preferís)
        results = list(destinos) + list(articulos)

    return render(request, "pages/search_results.html", {
        "query": q,
        "results": results,
        "destinos": destinos,
        "articulos": articulos,
    })


def sobre_nosotros(request):
    return render(request, "pages/sobre_nosotros.html")


def contacto(request):
    return render(request, "pages/contacto.html")


def politica_privacidad(request):
    return render(request, "pages/politica_privacidad.html")


def aviso_afiliados(request):
    return render(request, "pages/aviso_afiliados.html")