from django.shortcuts import render
from wagtail.models import Page
from pages.models import ArticuloPage, DestinoPage  # ajustá si tus imports difieren


def search(request):
    q = (request.GET.get("q") or "").strip()
    results = []

    if q:
        articulos = ArticuloPage.objects.live().public().search(q)
        destinos = DestinoPage.objects.live().public().search(q)
        

        # Convertimos a específicos (ya lo son, pero mantiene consistencia)
        results = list(articulos) + list(destinos)
    return render(request, "pages/search_results.html", {
        "query": q,
        "results": results,
    })

def sobre_nosotros(request):
    return render(request, "pages/sobre_nosotros.html")

def contacto(request):
    return render(request, "pages/contacto.html")

def politica_privacidad(request):
    return render(request, "pages/politica_privacidad.html")

def aviso_afiliados(request):
    return render(request, "pages/aviso_afiliados.html")
