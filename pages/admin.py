from django.contrib import admin
from wagtail.models import Page
from django.contrib.admin.sites import NotRegistered

# Evita que crashee si Page no está registrado
try:
    admin.site.unregister(Page)
except NotRegistered:
    pass
