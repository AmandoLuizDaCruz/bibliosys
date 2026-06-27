from django.urls import path

from . import views
from . import views_acesso
from . import views_auditoria
from . import views_circulacao
from . import views_gestao_perfis
from . import views_leitores
from . import views_livros
from . import views_perfil


urlpatterns = [
    path(
        "",
        views_acesso.inicio,
        name="home",
    ),
    path(
        "login/",
        views_acesso.entrar,
        name="login",
    ),
    path(
        "cadastro/",
        views_acesso.cadastrar_usuario,
        name="cadastro",
    ),
    path(
        "logout/",
        views_acesso.sair,
        name="logout",
    ),

    path(
        "perfil/",
        views_perfil.editar_meu_perfil,
        name="editar_meu_perfil",
    ),

    path(
        "cadastro-de-livros/",
        views_livros.cadastrar_livro,
        name="cadastrar_livro",
    ),

    path(
        "meus-emprestimos/",
        views_circulacao.meus_emprestimos,
        name="meus_emprestimos",
    ),
    path(
        "livros/<int:obra_id>/solicitar/",
        views_circulacao.solicitar_livro,
        name="solicitar_livro",
    ),
    path(
        "emprestimos/<int:emprestimo_id>/renovar/",
        views_circulacao.renovar_meu_emprestimo,
        name="renovar_meu_emprestimo",
    ),

    path(
        "leitores/",
        views_leitores.buscar_leitores,
        name="leitores_busca",
    ),
    path(
        "leitores/<int:usuario_id>/",
        views_leitores.perfil_leitor,
        name="perfil_leitor",
    ),
    path(
        (
            "leitores/<int:usuario_id>/"
            "reservas/<int:reserva_id>/retirada/"
        ),
        views_leitores.confirmar_retirada_leitor,
        name="confirmar_retirada_leitor",
    ),
    path(
        (
            "leitores/<int:usuario_id>/"
            "emprestimos/<int:emprestimo_id>/baixa/"
        ),
        views_leitores.dar_baixa_emprestimo,
        name="dar_baixa_emprestimo",
    ),

    # Compatibilidade com telas e testes anteriores.
    path(
        "livros/",
        views.listar_obras,
        name="listar_obras",
    ),
    path(
        "livros/cadastrar/",
        views_livros.cadastrar_livro,
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
        "cadastros/leitores/",
        views.listar_leitores,
        name="listar_leitores",
    ),
    path(
        "cadastros/leitores/cadastrar/",
        views.cadastrar_leitor,
        name="cadastrar_leitor",
    ),
    path(
        "cadastros/leitores/<int:leitor_id>/editar/",
        views.editar_leitor,
        name="editar_leitor",
    ),
    path(
        "cadastros/leitores/<int:leitor_id>/excluir/",
        views.excluir_leitor,
        name="excluir_leitor",
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
        (
            "gestao/solicitacoes/"
            "<int:solicitacao_id>/aprovar/"
        ),
        views.gestao_aprovar_solicitacao,
        name="gestao_aprovar_solicitacao",
    ),
    path(
        (
            "gestao/solicitacoes/"
            "<int:solicitacao_id>/recusar/"
        ),
        views.gestao_recusar_solicitacao,
        name="gestao_recusar_solicitacao",
    ),
    path(
        "gestao/historico/",
        views_auditoria.gestao_historico,
        name="gestao_historico",
    ),
    path(
        "multas/<int:multa_id>/pagar/",
        views_leitores.confirmar_quitacao,
        name="quitar_multas"
    )
]