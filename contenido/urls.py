from django.urls import path
from . import views

urlpatterns = [
    path("", views.guias_index, name="guias_index"),
    path("<slug:categoria_slug>/", views.categoria_list, name="categoria_list"),
    path("<slug:categoria_slug>/<slug:articulo_slug>/", views.articulo_detail, name="articulo_detail"),
]
