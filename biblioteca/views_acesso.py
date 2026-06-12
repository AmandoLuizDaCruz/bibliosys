from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import CadastroUsuarioForm
from .models import SolicitacaoFuncionario
from .servicos_circulacao import funcionario_aprovado


def destino_usuario(usuario):
    if usuario.is_superuser:
        return "gestao_dashboard"

    if funcionario_aprovado(usuario):
        return "leitores_busca"

    return "meus_emprestimos"


def inicio(request):
    if not request.user.is_authenticated:
        return redirect("login")

    return redirect(
        destino_usuario(request.user)
    )


def entrar(request):
    if request.user.is_authenticated:
        return redirect(
            destino_usuario(request.user)
        )

    formulario = AuthenticationForm(
        request,
        data=request.POST or None,
    )

    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.get_user()
        login(request, usuario)

        return redirect(
            destino_usuario(usuario)
        )

    return render(
        request,
        "biblioteca/autenticacao/login.html",
        {
            "formulario": formulario,
        },
    )


def cadastrar_usuario(request):
    if request.user.is_authenticated:
        return redirect(
            destino_usuario(request.user)
        )

    formulario = CadastroUsuarioForm(
        request.POST or None
    )

    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()
        login(request, usuario)

        try:
            usuario.solicitacao_funcionario
        except SolicitacaoFuncionario.DoesNotExist:
            messages.success(
                request,
                "Conta de leitor criada com sucesso.",
            )
        else:
            messages.info(
                request,
                (
                    "Conta criada. Sua solicitação para funcionário "
                    "está aguardando aprovação."
                ),
            )

        return redirect("meus_emprestimos")

    return render(
        request,
        "biblioteca/autenticacao/cadastro.html",
        {
            "formulario": formulario,
        },
    )


@login_required(login_url="login")
def sair(request):
    logout(request)
    return redirect("login")
