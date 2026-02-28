from django.shortcuts import render
from django.shortcuts import render
from wagtail.models import Page

def search(request):
    q = (request.GET.get("q") or "").strip()
    results = Page.objects.none()

    if q:
        results = (
            Page.objects.live().public()
            .search(q)  # usa Wagtail Search
            .specific()
        )

    return render(request, "pages/search.html", {
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
