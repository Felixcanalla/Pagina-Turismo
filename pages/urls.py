from django.urls import path
from . import views

urlpatterns = [
    path("sobre-nosotros/", views.sobre_nosotros, name="sobre_nosotros"),
    path("contacto/", views.contacto, name="contacto"),
    path("politica-de-privacidad/", views.politica_privacidad, name="politica_privacidad"),
    path("aviso-de-afiliados/", views.aviso_afiliados, name="aviso_afiliados"),
]
