from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path("obras/", views.listar_obras, name="listar_obras"),
    path("obras/cadastrar/", views.cadastrar_obra, name="cadastrar_obra"),
    path(
        "obras/<int:obra_id>/editar/",
        views.editar_obra,
        name="editar_obra",
    ),
    path(
        "obras/<int:obra_id>/excluir/",
        views.excluir_obra,
        name="excluir_obra",
    ),

    path("leitores/", views.listar_leitores, name="listar_leitores"),
    path(
        "leitores/cadastrar/",
        views.cadastrar_leitor,
        name="cadastrar_leitor",
    ),
    path(
        "leitores/<int:leitor_id>/editar/",
        views.editar_leitor,
        name="editar_leitor",
    ),
    path(
        "leitores/<int:leitor_id>/excluir/",
        views.excluir_leitor,
        name="excluir_leitor",
    ),
]