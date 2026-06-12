from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    Emprestimo,
    NotificacaoFuncionario,
    Obra,
    Reserva,
)
from .servicos_circulacao import (
    expirar_reservas_vencidas,
    funcionario_aprovado,
    registrar_retirada_reserva,
    solicitar_obra,
)


def obter_endereco_ip(request):
    encaminhado = request.META.get("HTTP_X_FORWARDED_FOR")

    if encaminhado:
        return encaminhado.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def funcionario_required(view_function):
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if not funcionario_aprovado(request.user):
            messages.error(
                request,
                "Esta área é exclusiva para funcionários aprovados.",
            )
            return redirect("home")

        return view_function(request, *args, **kwargs)

    return wrapper


@login_required(login_url="login")
def meus_emprestimos(request):
    if request.user.is_superuser:
        messages.error(
            request,
            "O administrador não participa da circulação de livros.",
        )
        return redirect("home")

    expirar_reservas_vencidas()

    emprestimos_ativos = (
        Emprestimo.objects
        .filter(
            usuario=request.user,
            status=Emprestimo.Status.ATIVO,
        )
        .select_related(
            "exemplar",
            "exemplar__obra",
        )
        .order_by("data_prevista_devolucao")
    )

    historico = (
        Emprestimo.objects
        .filter(usuario=request.user)
        .exclude(status=Emprestimo.Status.ATIVO)
        .select_related(
            "exemplar",
            "exemplar__obra",
        )
        .order_by("-data_emprestimo")
    )

    reservas = (
        Reserva.objects
        .filter(
            usuario=request.user,
            status__in=[
                Reserva.Status.FILA,
                Reserva.Status.AGUARDANDO_RETIRADA,
            ],
        )
        .select_related(
            "obra",
            "exemplar",
        )
        .order_by("criada_em")
    )

    return render(
        request,
        "biblioteca/circulacao/meus_emprestimos.html",
        {
            "emprestimos_ativos": emprestimos_ativos,
            "historico": historico,
            "reservas": reservas,
        },
    )


@login_required(login_url="login")
@require_POST
def solicitar_livro(request, obra_id):
    obra = get_object_or_404(
        Obra,
        id=obra_id,
    )

    try:
        resultado = solicitar_obra(
            usuario=request.user,
            obra=obra,
            endereco_ip=obter_endereco_ip(request),
        )

    except ValidationError as erro:
        messages.error(
            request,
            " ".join(erro.messages),
        )

    else:
        if isinstance(resultado, Emprestimo):
            messages.success(
                request,
                (
                    f'Empréstimo de "{obra.titulo}" '
                    "registrado automaticamente. "
                    f"Devolução prevista para "
                    f"{resultado.data_prevista_devolucao:%d/%m/%Y}."
                ),
            )

        elif (
            resultado.status
            == Reserva.Status.AGUARDANDO_RETIRADA
        ):
            messages.success(
                request,
                (
                    f'O livro "{obra.titulo}" foi reservado. '
                    "Um funcionário deverá registrar a retirada "
                    "dentro de 24 horas."
                ),
            )

        else:
            messages.info(
                request,
                (
                    f'Você entrou na fila de espera por '
                    f'"{obra.titulo}".'
                ),
            )

    return redirect("listar_obras")


@funcionario_required
def notificacoes_funcionarios(request):
    expirar_reservas_vencidas()

    notificacoes = (
        NotificacaoFuncionario.objects
        .filter(ativa=True)
        .select_related(
            "reserva",
            "reserva__usuario",
            "reserva__obra",
            "reserva__exemplar",
        )
        .order_by("-criada_em")
    )

    itens = []

    for notificacao in notificacoes:
        itens.append(
            {
                "notificacao": notificacao,
                "lida": notificacao.lida_por.filter(
                    id=request.user.id
                ).exists(),
            }
        )

    return render(
        request,
        "biblioteca/circulacao/notificacoes.html",
        {
            "itens": itens,
        },
    )


@funcionario_required
@require_POST
def marcar_notificacao_lida(
    request,
    notificacao_id,
):
    notificacao = get_object_or_404(
        NotificacaoFuncionario,
        id=notificacao_id,
        ativa=True,
    )

    notificacao.lida_por.add(request.user)

    messages.success(
        request,
        "Notificação marcada como lida.",
    )

    return redirect("notificacoes_funcionarios")


@funcionario_required
@require_POST
def registrar_retirada(
    request,
    reserva_id,
):
    reserva = get_object_or_404(
        Reserva,
        id=reserva_id,
    )

    try:
        emprestimo = registrar_retirada_reserva(
            funcionario=request.user,
            reserva=reserva,
            endereco_ip=obter_endereco_ip(request),
        )

    except ValidationError as erro:
        messages.error(
            request,
            " ".join(erro.messages),
        )

    else:
        messages.success(
            request,
            (
                f'Retirada de "{emprestimo.exemplar.obra.titulo}" '
                f"registrada para "
                f"{emprestimo.usuario.username}. "
                f"Devolução prevista para "
                f"{emprestimo.data_prevista_devolucao:%d/%m/%Y}."
            ),
        )

    return redirect("notificacoes_funcionarios")
