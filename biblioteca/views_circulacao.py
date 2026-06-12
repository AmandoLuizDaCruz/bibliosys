from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    Emprestimo,
    Exemplar,
    NotificacaoFuncionario,
    Obra,
    Reserva,
)
from .servicos_circulacao import (
    expirar_reservas_vencidas,
    funcionario_aprovado,
    registrar_retirada_reserva,
    renovar_emprestimo,
    solicitar_obra,
)


def obter_endereco_ip(request):
    encaminhado = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

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
            return redirect("meus_emprestimos")

        return view_function(
            request,
            *args,
            **kwargs,
        )

    return wrapper


@login_required(login_url="login")
def meus_emprestimos(request):
    if request.user.is_superuser:
        return redirect("gestao_dashboard")

    expirar_reservas_vencidas()

    consulta = request.GET.get(
        "q",
        "",
    ).strip()

    obras = (
        Obra.objects
        .annotate(
            exemplares_disponiveis=Count(
                "exemplares",
                filter=Q(
                    exemplares__numero__gt=1,
                    exemplares__somente_consulta=False,
                    exemplares__status=(
                        Exemplar.Status.DISPONIVEL
                    ),
                ),
            )
        )
        .order_by("titulo")
    )

    if consulta:
        obras = obras.filter(
            Q(titulo__icontains=consulta)
            | Q(autor__icontains=consulta)
            | Q(isbn__icontains=consulta)
            | Q(categoria__icontains=consulta)
        )

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
            "obras": obras,
            "consulta": consulta,
            "emprestimos_ativos": emprestimos_ativos,
            "historico": historico,
            "reservas": reservas,
            "eh_funcionario": funcionario_aprovado(
                request.user
            ),
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
                    "registrado automaticamente."
                ),
            )

        elif (
            resultado.status
            == Reserva.Status.AGUARDANDO_RETIRADA
        ):
            messages.success(
                request,
                (
                    f'"{obra.titulo}" foi separado para você. '
                    "O prazo de retirada é de 24 horas."
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

    return redirect("meus_emprestimos")


@login_required(login_url="login")
@require_POST
def renovar_meu_emprestimo(
    request,
    emprestimo_id,
):
    emprestimo = get_object_or_404(
        Emprestimo,
        id=emprestimo_id,
        usuario=request.user,
    )

    try:
        emprestimo = renovar_emprestimo(
            usuario=request.user,
            emprestimo=emprestimo,
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
                "Empréstimo renovado até "
                f"{emprestimo.data_prevista_devolucao:%d/%m/%Y}."
            ),
        )

    return redirect("meus_emprestimos")


# Mantido para compatibilidade com os testes anteriores.
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
        registrar_retirada_reserva(
            funcionario=request.user,
            reserva=reserva,
            endereco_ip=obter_endereco_ip(request),
        )

    except ValidationError as erro:
        messages.error(
            request,
            " ".join(erro.messages),
        )

    return redirect("notificacoes_funcionarios")