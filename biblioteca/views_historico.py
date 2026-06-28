from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import render

from .models import Emprestimo, Obra, Leitor

User = get_user_model()


@login_required(login_url="login")
def historico_emprestimos(request):
    emprestimos = Emprestimo.objects.select_related(
        'usuario', 'exemplar__obra'
    ).order_by('-data_emprestimo')

    status_filter = request.GET.get('status', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    leitor_filter = request.GET.get('leitor', '')
    obra_filter = request.GET.get('obra', '')

    if status_filter:
        emprestimos = emprestimos.filter(status=status_filter)

    if data_inicio:
        emprestimos = emprestimos.filter(
            data_emprestimo__gte=data_inicio
        )

    if data_fim:
        emprestimos = emprestimos.filter(
            data_emprestimo__lte=data_fim
        )

    if leitor_filter:
        emprestimos = emprestimos.filter(
            usuario__username__icontains=leitor_filter
        )

    if obra_filter:
        emprestimos = emprestimos.filter(
            exemplar__obra__titulo__icontains=obra_filter
        )

    total_emprestimos = emprestimos.count()
    emprestimos_ativos = emprestimos.filter(
        status=Emprestimo.Status.ATIVO
    ).count()
    emprestimos_devolvidos = emprestimos.filter(
        status=Emprestimo.Status.DEVOLVIDO
    ).count()

    contexto = {
        'emprestimos': emprestimos[:100],
        'status_choices': Emprestimo.Status.choices,
        'total_emprestimos': total_emprestimos,
        'emprestimos_ativos': emprestimos_ativos,
        'emprestimos_devolvidos': emprestimos_devolvidos,
        'filtros': {
            'status': status_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'leitor': leitor_filter,
            'obra': obra_filter,
        }
    }

    return render(
        request,
        'biblioteca/historico/historico_emprestimos.html',
        contexto,
    )
