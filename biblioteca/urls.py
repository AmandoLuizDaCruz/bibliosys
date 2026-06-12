from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.entrar, name="login"),
    path("cadastro/", views.cadastrar_usuario, name="cadastro"),
    path("logout/", views.sair, name="logout"),

    path("livros/", views.listar_obras, name="listar_obras"),
    path(
        "livros/cadastrar/",
        views.cadastrar_obra,
        name="cadastrar_obra",
    ),
    path(
        "livros/<int:obra_id>/editar/",
        views.editar_obra,
        name="editar_obra",
    ),
    path(
        "livros/<int:obra_id>/excluir/",
        views.excluir_obra,
        name="excluir_obra",
    ),

    path(
        "leitores/",
        views.listar_leitores,
        name="listar_leitores",
    ),
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

    path(
        "gestao/",
        views.gestao_dashboard,
        name="gestao_dashboard",
    ),
    path(
        "gestao/usuarios/",
        views.gestao_usuarios,
        name="gestao_usuarios",
    ),
    path(
        "gestao/usuarios/<int:usuario_id>/excluir/",
        views.gestao_excluir_usuario,
        name="gestao_excluir_usuario",
    ),
    path(
        "gestao/solicitacoes/",
        views.gestao_solicitacoes,
        name="gestao_solicitacoes",
    ),
    path(
        "gestao/solicitacoes/<int:solicitacao_id>/aprovar/",
        views.gestao_aprovar_solicitacao,
        name="gestao_aprovar_solicitacao",
    ),
    path(
        "gestao/solicitacoes/<int:solicitacao_id>/recusar/",
        views.gestao_recusar_solicitacao,
        name="gestao_recusar_solicitacao",
    ),
]