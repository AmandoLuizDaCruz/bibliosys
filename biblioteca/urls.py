from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("obras/", views.listar_obras, name="listar_obras"),
    path("obras/cadastrar/", views.cadastrar_obra, name="cadastrar_obra"),
    path("obras/<int:obra_id>/editar/", views.editar_obra, name="editar_obra"),
    path("obras/<int:obra_id>/excluir/", views.excluir_obra, name="excluir_obra"),
]
