from django.contrib import admin

from .models import ConsultaSQL


@admin.register(ConsultaSQL)
class ConsultaSQLAdmin(admin.ModelAdmin):
    list_display = ("nombre", "titulo", "activa", "actualizado")
    list_filter = ("activa",)
    search_fields = ("nombre", "titulo", "sql")