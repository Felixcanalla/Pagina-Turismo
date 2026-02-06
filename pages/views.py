from django.shortcuts import render

def sobre_nosotros(request):
    return render(request, "pages/sobre_nosotros.html")

def contacto(request):
    return render(request, "pages/contacto.html")

def politica_privacidad(request):
    return render(request, "pages/politica_privacidad.html")

def aviso_afiliados(request):
    return render(request, "pages/aviso_afiliados.html")
