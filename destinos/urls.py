from django.urls import path
from . import views

urlpatterns = [
    path("", views.destinos_index, name="destinos_index"),
    path("<slug:pais_slug>/", views.pais_detail, name="pais_detail"),
    path("<slug:pais_slug>/<slug:destino_slug>/", views.destino_detail, name="destino_detail"),
    path("<slug:pais_slug>/<slug:destino_slug>/<slug:seccion_slug>/", views.seccion_destino_detail, name="seccion_destino_detail"),
]
