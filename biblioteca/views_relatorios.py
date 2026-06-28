from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib import messages

from .models import Emprestimo, Reserva, Multa, Leitor


@login_required(login_url="login")
def relatorio_funcionario(request):
    if not request.user.groups.filter(name="Funcionarios").exists():
        messages.error(
            request,
            "Apenas funcionários podem acessar relatórios.",
        )
        return render(request, "biblioteca/relatorios/acesso_negado.html")

    total_emprestimos = Emprestimo.objects.count()
    emprestimos_ativos = Emprestimo.objects.filter(
        status=Emprestimo.Status.ATIVO
    ).count()
    emprestimos_atrasados = Emprestimo.objects.filter(
        status=Emprestimo.Status.ATIVO
    ).count()

    total_devolucoes = Emprestimo.objects.filter(
        status=Emprestimo.Status.DEVOLVIDO
    ).count()

    multas_pendentes = Multa.objects.filter(
        status=Multa.Status.PENDENTE
    ).count()
    total_multas_pendentes = sum(
        m.valor_total for m in Multa.objects.filter(
            status=Multa.Status.PENDENTE
        )
    )

    reservas_ativas = Reserva.objects.filter(
        status__in=[
            Reserva.Status.FILA,
            Reserva.Status.AGUARDANDO_RETIRADA,
        ]
    ).count()

    emprestimos_por_status = Emprestimo.objects.values(
        'status'
    ).annotate(
        total=Count('id')
    ).order_by('status')

    contexto = {
        'total_emprestimos': total_emprestimos,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_atrasados': emprestimos_atrasados,
        'total_devolucoes': total_devolucoes,
        'multas_pendentes': multas_pendentes,
        'total_multas_pendentes': total_multas_pendentes,
        'reservas_ativas': reservas_ativas,
        'emprestimos_por_status': emprestimos_por_status,
    }

    return render(
        request,
        'biblioteca/relatorios/relatorio_funcionario.html',
        contexto,
    )
