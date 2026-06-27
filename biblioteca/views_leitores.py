import re

from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    Emprestimo,
    Leitor,
    Multa,
    RegistroAuditoria,
    Reserva,
)
from .servicos_circulacao import (
    expirar_reservas_vencidas,
    registrar_devolucao,
    registrar_retirada_reserva,
)
from .views_circulacao import (
    funcionario_required,
    obter_endereco_ip,
)


User = get_user_model()


def formatar_busca_cpf(valor):
    numeros = re.sub(r"\D", "", valor)

    if len(numeros) != 11:
        return None

    return (
        f"{numeros[:3]}."
        f"{numeros[3:6]}."
        f"{numeros[6:9]}-"
        f"{numeros[9:]}"
    )


@funcionario_required
def buscar_leitores(request):
    expirar_reservas_vencidas()

    consulta = request.GET.get(
        "q",
        "",
    ).strip()

    usuarios = User.objects.none()

    if consulta:
        filtro = (
            Q(username__icontains=consulta)
            | Q(first_name__icontains=consulta)
            | Q(last_name__icontains=consulta)
            | Q(email__icontains=consulta)
            | Q(
                perfil_leitor__nome_completo__icontains=consulta
            )
            | Q(
                perfil_leitor__cpf__icontains=consulta
            )
            | Q(
                perfil_leitor__telefone__icontains=consulta
            )
        )

        cpf_formatado = formatar_busca_cpf(
            consulta
        )

        if cpf_formatado:
            filtro |= Q(
                perfil_leitor__cpf=cpf_formatado
            )

        usuarios = (
            User.objects
            .filter(
                filtro,
                is_superuser=False,
                perfil_leitor__isnull=False,
            )
            .select_related("perfil_leitor")
            .distinct()
            .order_by(
                "perfil_leitor__nome_completo"
            )[:50]
        )

    return render(
        request,
        "biblioteca/leitores/busca.html",
        {
            "usuarios": usuarios,
            "consulta": consulta,
        },
    )


@funcionario_required
def perfil_leitor(request, usuario_id):
    expirar_reservas_vencidas()

    usuario = get_object_or_404(
        User.objects.select_related(
            "perfil_leitor"
        ),
        id=usuario_id,
        is_superuser=False,
    )

    perfil = get_object_or_404(
        Leitor,
        usuario=usuario,
    )

    pedidos = (
        Reserva.objects
        .filter(
            usuario=usuario,
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

    emprestimos_ativos = (
        Emprestimo.objects
        .filter(
            usuario=usuario,
            status=Emprestimo.Status.ATIVO,
        )
        .select_related(
            "exemplar",
            "exemplar__obra",
        )
        .order_by("data_prevista_devolucao")
    )

    historico_emprestimos = (
        Emprestimo.objects
        .filter(usuario=usuario)
        .exclude(status=Emprestimo.Status.ATIVO)
        .select_related(
            "exemplar",
            "exemplar__obra",
        )
        .order_by("-data_emprestimo")[:50]
    )

    multas = (
        Multa.objects
        .filter(
            emprestimo__usuario=usuario
        )
        .select_related(
            "emprestimo",
            "emprestimo__exemplar",
            "emprestimo__exemplar__obra",
        )
        .order_by("-criada_em")
    )

    acoes = (
        RegistroAuditoria.objects
        .filter(
            Q(usuario=usuario)
            | Q(
                descricao__icontains=usuario.username
            )
        )
        .select_related("usuario")
        .distinct()
        .order_by("-criada_em")[:50]
    )

    return render(
        request,
        "biblioteca/leitores/perfil.html",
        {
            "conta": usuario,
            "perfil": perfil,
            "pedidos": pedidos,
            "emprestimos_ativos": emprestimos_ativos,
            "historico_emprestimos": historico_emprestimos,
            "multas": multas,
            "acoes": acoes,
        },
    )

@funcionario_required
@require_POST
def confirmar_quitacao(
    request,
    multa_id,
):
    multa = get_object_or_404(
        Multa,
        id = multa_id,
    )
    if multa.status == Multa.Status.PENDENTE:
        multa.status = multa.Status.PAGA
        multa.paga_em = timezone.now()

        multa.save(update_fields=['status', 'paga_em'])

        messages.success(
            request,
            f"A multa no valor de R$ {multa.valor_total} foi marcada como paga."
        )
    else:
        messages.warning(
            request,
            "Esta multa já foi paga ou cancelada."
        )

    return redirect("perfil_leitor", usuario_id=multa.emprestimo.usuario.id)

@funcionario_required
@require_POST
def confirmar_retirada_leitor(
    request,
    usuario_id,
    reserva_id,
):
    usuario = get_object_or_404(
        User,
        id=usuario_id,
        is_superuser=False,
    )

    reserva = get_object_or_404(
        Reserva,
        id=reserva_id,
        usuario=usuario,
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
                "registrada com sucesso."
            ),
        )

    return redirect(
        "perfil_leitor",
        usuario_id=usuario.id,
    )


@funcionario_required
@require_POST
def dar_baixa_emprestimo(
    request,
    usuario_id,
    emprestimo_id,
):
    usuario = get_object_or_404(
        User,
        id=usuario_id,
        is_superuser=False,
    )

    emprestimo = get_object_or_404(
        Emprestimo,
        id=emprestimo_id,
        usuario=usuario,
    )

    try:
        emprestimo, multa, promovida = registrar_devolucao(
            funcionario=request.user,
            emprestimo=emprestimo,
            endereco_ip=obter_endereco_ip(request),
        )

    except ValidationError as erro:
        messages.error(
            request,
            " ".join(erro.messages),
        )

    else:
        mensagem = (
            f'Devolução de "{emprestimo.exemplar.obra.titulo}" '
            "registrada."
        )

        if multa:
            mensagem += (
                f" Multa: R$ {multa.valor_total} "
                f"por {multa.dias_atraso} dia(s) de atraso."
            )

        if promovida:
            mensagem += (
                " O exemplar foi automaticamente separado "
                "para a próxima pessoa da fila."
            )

        messages.success(
            request,
            mensagem,
        )

    return redirect(
        "perfil_leitor",
        usuario_id=usuario.id,
    )
