from django.urls import path

from . import views
from . import views_circulacao
from . import views_gestao_perfis
from . import views_perfil


urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "login/",
        views.entrar,
        name="login",
    ),
    path(
        "cadastro/",
        views.cadastrar_usuario,
        name="cadastro",
    ),
    path(
        "logout/",
        views.sair,
        name="logout",
    ),

    path(
        "perfil/",
        views_perfil.editar_meu_perfil,
        name="editar_meu_perfil",
    ),

    path(
        "livros/",
        views.listar_obras,
        name="listar_obras",
    ),
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
        "gestao/usuarios/<int:usuario_id>/editar/",
        views_gestao_perfis.gestao_editar_usuario,
        name="gestao_editar_usuario",
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

    path(
        "circulacao/meus-emprestimos/",
        views_circulacao.meus_emprestimos,
        name="meus_emprestimos",
    ),
    path(
        "circulacao/livros/<int:obra_id>/solicitar/",
        views_circulacao.solicitar_livro,
        name="solicitar_livro",
    ),
    path(
        "circulacao/notificacoes/",
        views_circulacao.notificacoes_funcionarios,
        name="notificacoes_funcionarios",
    ),
    path(
        (
            "circulacao/notificacoes/"
            "<int:notificacao_id>/lida/"
        ),
        views_circulacao.marcar_notificacao_lida,
        name="marcar_notificacao_lida",
    ),
    path(
        (
            "circulacao/reservas/"
            "<int:reserva_id>/retirada/"
        ),
        views_circulacao.registrar_retirada,
        name="registrar_retirada",
    ),
]