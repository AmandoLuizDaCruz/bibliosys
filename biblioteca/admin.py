from django.contrib import admin

from .models import Leitor, Obra


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "isbn",
        "categoria",
        "quantidade",
    )

    search_fields = (
        "titulo",
        "autor",
        "isbn",
    )


@admin.register(Leitor)
class LeitorAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "cpf",
        "email",
        "tipo_vinculo",
        "ativo",
    )

    search_fields = (
        "nome_completo",
        "cpf",
        "email",
    )

    list_filter = (
        "tipo_vinculo",
        "ativo",
    )