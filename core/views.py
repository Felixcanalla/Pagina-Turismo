from django.shortcuts import render
from destinos.models import Destino
from contenido.models import Articulo

def home(request):
    destinos = Destino.objects.filter(publicado=True).order_by("-updated_at")[:6]
    articulos = Articulo.objects.filter(publicado=True).order_by("-created_at")[:6]
    return render(request, "core/home.html", {"destinos": destinos, "articulos": articulos})

def sobre_nosotros(request):
    return render(request, "core/sobre_nosotros.html")

def contacto(request):
    return render(request, "core/contacto.html")

def politica_privacidad(request):
    return render(request, "core/politica_privacidad.html")

def aviso_afiliados(request):
    return render(request, "core/aviso_afiliados.html")