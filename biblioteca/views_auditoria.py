from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from .models import RegistroAuditoria
from .views import administrador_required


@administrador_required
def gestao_historico(request):
    consulta = request.GET.get(
        "q",
        "",
    ).strip()

    acao_selecionada = request.GET.get(
        "acao",
        "",
    ).strip()

    registros = (
        RegistroAuditoria.objects
        .select_related("usuario")
        .all()
        .order_by("-criada_em")
    )

    if consulta:
        registros = registros.filter(
            Q(
                usuario__username__icontains=consulta
            )
            | Q(
                usuario__first_name__icontains=consulta
            )
            | Q(
                usuario__last_name__icontains=consulta
            )
            | Q(
                entidade__icontains=consulta
            )
            | Q(
                descricao__icontains=consulta
            )
            | Q(
                endereco_ip__icontains=consulta
            )
        )

    acoes_validas = {
        valor
        for valor, descricao
        in RegistroAuditoria.Acao.choices
    }

    if acao_selecionada in acoes_validas:
        registros = registros.filter(
            acao=acao_selecionada
        )
    else:
        acao_selecionada = ""

    paginador = Paginator(
        registros,
        25,
    )

    pagina = paginador.get_page(
        request.GET.get("pagina")
    )

    return render(
        request,
        "biblioteca/gestao/historico.html",
        {
            "pagina": pagina,
            "consulta": consulta,
            "acao_selecionada": acao_selecionada,
            "acoes": RegistroAuditoria.Acao.choices,
        },
    )
