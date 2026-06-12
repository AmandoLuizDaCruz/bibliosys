from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ObraForm
from .models import RegistroAuditoria
from .views_circulacao import funcionario_required


def obter_endereco_ip(request):
    encaminhado = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if encaminhado:
        return encaminhado.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


@funcionario_required
def cadastrar_livro(request):
    formulario = ObraForm(
        request.POST or None
    )

    if request.method == "POST" and formulario.is_valid():
        obra = formulario.save()

        RegistroAuditoria.registrar(
            usuario=request.user,
            acao=RegistroAuditoria.Acao.CADASTRO,
            entidade="Livro",
            objeto_id=obra.id,
            descricao=(
                f'Cadastrou o livro "{obra.titulo}" '
                f"com {obra.quantidade} exemplar(es)."
            ),
            endereco_ip=obter_endereco_ip(request),
        )

        messages.success(
            request,
            f'O livro "{obra.titulo}" foi cadastrado.',
        )

        return redirect("cadastrar_livro")

    return render(
        request,
        "biblioteca/obras/cadastro.html",
        {
            "formulario": formulario,
        },
    )
